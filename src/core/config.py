import os
from pathlib import Path
from dotenv import load_dotenv

# Define project directories
CORE_DIR = Path(__file__).resolve().parent
SRC_DIR = CORE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    
    # Observability (Langfuse)
    ENABLE_LANGFUSE = os.getenv("ENABLE_LANGFUSE", "false").lower() == "true"
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # Experiment Tracking (MLflow)
    ENABLE_MLFLOW = os.getenv("ENABLE_MLFLOW", "false").lower() == "true"
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
    MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "transcraft_translation_quality")
    
    # Models
    MINI_MODEL = os.getenv("DEFAULT_MINI_MODEL", "gpt-4o-mini")
    MAIN_MODEL = os.getenv("DEFAULT_MAIN_MODEL", "gpt-4o")
    
    # Memory Quality
    ENABLE_TIE_REVIEWER_LLM = os.getenv("ENABLE_TIE_REVIEWER_LLM", "false").lower() == "true"
    ENABLE_MEMORY_EFFECTIVENESS_LLM = os.getenv("ENABLE_MEMORY_EFFECTIVENESS_LLM", "false").lower() == "true"
    ENABLE_MEMORY_AWARE_ROUTER = os.getenv("ENABLE_MEMORY_AWARE_ROUTER", "true").lower() == "true"
    ENABLE_TRANSLATION_STRATEGY_PLANNER = os.getenv("ENABLE_TRANSLATION_STRATEGY_PLANNER", "true").lower() == "true"
    
    # Reference Paths
    DATA_DIR = PROJECT_ROOT / "data"
    INPUTS_DIR = DATA_DIR / "inputs"
    REFERENCE_DIR = DATA_DIR / "reference"
    MEMORY_DIR = PROJECT_ROOT / "memory"
    CONFIG_DIR = DATA_DIR / "config"
    AUTHOR_MAPPING_PATH = CONFIG_DIR / "author_mapping.json"
    LANGUAGE_PROFILES_DIR = DATA_DIR / "language_profiles"
    
    STYLES_DIR = DATA_DIR / "styles"
    
    STYLE_GUIDE_PATH = REFERENCE_DIR / "literary" / "style_guide.txt"
    GLOSSARY_PATH = REFERENCE_DIR / "literary" / "glossary.json"
    IDIOMS_PATH = REFERENCE_DIR / "idioms_en_tr.json"

    
    @classmethod
    def get_genre_paths(cls, genre: str = "literary"):
        """Get style guide and glossary paths for a specific genre."""
        genre_dir = cls.REFERENCE_DIR / genre
        if not genre_dir.exists():
            # Default fallback
            genre_dir = cls.REFERENCE_DIR / "literary"
            
        return genre_dir / "style_guide.txt", genre_dir / "glossary.json"

    @classmethod
    def get_style_path(cls, style_preset: str) -> Path:
        """Get the path to a specific style preset markdown file."""
        return cls.STYLES_DIR / f"{style_preset}.md"
    
    # Graph Settings
    MAX_REVISIONS = 3

    @classmethod
    def validate(cls):
        """Validate critical configuration elements."""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please create a '.env' file in the "
                "project root and add your OpenAI API key."
            )
        
        # Verify directories exist
        cls.INPUTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
