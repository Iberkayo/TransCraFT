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
    
    # Models
    MINI_MODEL = os.getenv("DEFAULT_MINI_MODEL", "gpt-4o-mini")
    MAIN_MODEL = os.getenv("DEFAULT_MAIN_MODEL", "gpt-4o")
    
    # Reference Paths
    DATA_DIR = PROJECT_ROOT / "data"
    INPUTS_DIR = DATA_DIR / "inputs"
    REFERENCE_DIR = DATA_DIR / "reference"
    
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
