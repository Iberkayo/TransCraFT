import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.core.config import Config

logger = logging.getLogger(__name__)


class StyleContractSchema(BaseModel):
    tone: str = Field(description="Core tone constraint")
    sentence_rhythm: str = Field(description="Sentence rhythm constraint")
    rules: List[str] = Field(description="List of high-priority translation rules/directives")


class StyleContractGenerator:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent.parent.parent / "memory"
        else:
            self.base_dir = Path(base_dir)

    def load_or_generate_contract(
        self,
        work_id: str,
        author_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Load a work style contract or compile one from the author profile."""
        if not work_id:
            work_id = "default_work"
        work_id = work_id.lower().strip().replace(" ", "_")

        style_dir = self.base_dir / "works" / work_id / "style"
        style_dir.mkdir(parents=True, exist_ok=True)
        contract_path = style_dir / "style_contract.json"

        if contract_path.exists():
            try:
                with open(contract_path, "r", encoding="utf-8") as f:
                    logger.info(f"Loaded existing style contract for {work_id}")
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading style contract at {contract_path}: {e}")

        logger.info(f"Style contract for work '{work_id}' not found. Compiling new contract...")
        contract = self.generate_contract(author_profile)

        try:
            with open(contract_path, "w", encoding="utf-8") as f:
                json.dump(contract, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved style contract for {work_id} to {contract_path}")
        except Exception as e:
            logger.error(f"Error saving style contract for {work_id}: {e}")

        return contract

    def generate_contract(self, author_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Compile a benchmark-agnostic style contract from a style profile."""
        author_name = author_profile.get("author_name", "Unknown")
        attributes = author_profile.get("attributes", {})

        if not Config.OPENAI_API_KEY:
            return self._fallback_contract(attributes)

        llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            model=Config.MINI_MODEL,
            temperature=0,
        )

        prompt = f"""
You are a master Translation Architect.
Analyze the style profile of author '{author_name}' and compile a Translation Style Contract for translating their works into Turkish.

### Author Style Attributes:
- Tone: {attributes.get('tone')}
- Sentence Rhythm: {attributes.get('sentence_rhythm')}
- Fragment Density: {attributes.get('fragment_density')}
- Language Register: {attributes.get('language_register')}
- Dialogue Density: {attributes.get('dialogue_density')}
- Imagery Density: {attributes.get('imagery_density')}

### Guidelines for Turkish Style Contract:
1. Formulate 4-6 concrete, actionable rules in English for the Turkish translator and stylist.
2. Address sentence rhythm, fragment preservation, avoiding explanatory additions, and preferred tone register.
3. Include work-specific rendering rules only when they are supported by the provided profile attributes or retrieved memory.
4. Do not invent benchmark-specific examples or hard-code specific source sentences.
"""
        try:
            structured_llm = llm.with_structured_output(StyleContractSchema, method="function_calling")
            contract_obj = structured_llm.invoke(prompt)
            return contract_obj.model_dump()
        except Exception as e:
            logger.error(f"Failed to generate style contract using structured LLM: {e}")
            return self._fallback_contract(attributes)

    def _fallback_contract(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "tone": attributes.get("tone", "neutral"),
            "sentence_rhythm": attributes.get("sentence_rhythm", "standard narrative pacing"),
            "rules": [
                "Preserve the source author's stated tone and pacing in Turkish.",
                "Preserve intentional sentence fragments and rhythm when the profile indicates fragmentary prose.",
                "Avoid adding explanatory conjunctions or filler when the profile indicates sparse or paratactic narration.",
                "Keep terminology and recurring renderings consistent with retrieved work memory.",
            ],
        }
