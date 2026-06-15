import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from src.core.config import Config

logger = logging.getLogger(__name__)

class AuthorStyleProfile(BaseModel):
    author_id: str = Field(description="Normalized author identifier (lowercase, underscore separated, e.g. 'cormac_mccarthy')")
    author_name: str = Field(description="Full name of the author")
    type: str = Field(default="author_style", description="Type of memory item")
    attributes: Dict[str, str] = Field(description="Style attributes including tone, sentence_rhythm, fragment_density, language_register, dialogue_density, imagery_density")
    inferred: bool = Field(default=False, description="True if dynamically inferred from text chunks")
    confidence: float = Field(default=1.0, description="Confidence score from 0.0 to 1.0")
    usage_count: int = Field(default=1, description="Number of times this profile has been used")

class AuthorStyleProfiler:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent.parent.parent / "memory"
        else:
            self.base_dir = Path(base_dir)
        self.authors_dir = self.base_dir / "global" / "authors"
        self.authors_dir.mkdir(parents=True, exist_ok=True)

    def load_or_infer_profile(self, 
                               author_id: str, 
                               author_name: Optional[str] = None, 
                               sample_chunks: Optional[list] = None) -> Dict[str, Any]:
        """
        Loads the author profile if it exists. If not, and sample chunks are provided,
        dynamically infers the profile and saves it for future runs.
        """
        if not author_id:
            author_id = "unknown_author"
        author_id = author_id.lower().strip().replace(" ", "_")
        
        profile_path = self.authors_dir / f"{author_id}.json"
        
        # A. Load Known Author Profile
        if profile_path.exists():
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Loaded existing author profile for {author_id}")
                    # Increment usage count
                    data["usage_count"] = data.get("usage_count", 0) + 1
                    with open(profile_path, "w", encoding="utf-8") as fw:
                        json.dump(data, fw, indent=2, ensure_ascii=False)
                    return data
            except Exception as e:
                logger.error(f"Error reading author profile at {profile_path}: {e}")

        # B. Infer Style Profile for Unknown Author
        if sample_chunks and len(sample_chunks) > 0:
            logger.info(f"Author profile for '{author_id}' not found. Inferring style dynamically...")
            inferred = self.infer_style_profile(author_id, author_name or author_id, sample_chunks)
            if inferred:
                # Save to disk for future runs
                try:
                    with open(profile_path, "w", encoding="utf-8") as f:
                        json.dump(inferred, f, indent=2, ensure_ascii=False)
                    logger.info(f"Saved inferred style profile for {author_id} to {profile_path}")
                except Exception as e:
                    logger.error(f"Error saving inferred profile for {author_id}: {e}")
                return inferred

        # Fallback profile if inference is skipped or fails
        fallback = {
            "author_id": author_id,
            "author_name": author_name or author_id,
            "type": "author_style",
            "attributes": {
                "tone": "neutral, narrative",
                "sentence_rhythm": "standard narrative pacing",
                "fragment_density": "low",
                "language_register": "modern, standard",
                "dialogue_density": "medium",
                "imagery_density": "medium"
            },
            "inferred": True,
            "confidence": 0.5,
            "usage_count": 1
        }
        return fallback

    def infer_style_profile(self, author_id: str, author_name: str, chunks: list) -> Dict[str, Any]:
        """Use LLM structured output to extract a yazar style profile from text chunks."""
        if not Config.OPENAI_API_KEY:
            return {}
            
        llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            model=Config.MINI_MODEL,
            temperature=0
        )
        
        sample_text = "\n\n--- Chunk Boundary ---\n\n".join(chunks[:2])
        
        prompt = f"""
You are an expert literary scholar and narrative style analyst.
Analyze the following text sample by yazar '{author_name}' and extract their signature style.

### Text Sample:
{sample_text}

### Style Attribute Guidelines:
1. **tone**: Tone and emotional register of the narration (e.g. bleak, objective, intimate, ironic).
2. **sentence_rhythm**: Rhythm, sentence length variety, use of parataxis or complex coordinate clauses.
3. **fragment_density**: Omission of verbs, use of sentence fragments.
4. **language_register**: Diction, use of archaisms, dialect, scientific terms, or colloquial language.
5. **dialogue_density**: Frequency and style of dialogues (unlabeled, quotation marks, spacing).
6. **imagery_density**: Richness of sensory detail, metaphors, and descriptions.

Provide the attributes in a concise, compact manner.
"""
        try:
            structured_llm = llm.with_structured_output(AuthorStyleProfile, method="function_calling")
            profile_obj = structured_llm.invoke(prompt)
            profile_dict = profile_obj.model_dump()
            profile_dict["inferred"] = True
            profile_dict["confidence"] = 0.8
            return profile_dict
        except Exception as e:
            logger.error(f"Failed to infer style profile using structured LLM: {e}")
            return {}
