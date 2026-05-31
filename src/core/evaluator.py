from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.core.config import Config

class EvaluationReportSchema(BaseModel):
    accuracy_score: int = Field(
        description="Score from 1 (poor) to 5 (excellent) evaluating if all original meaning and facts are preserved."
    )
    fluency_score: int = Field(
        description="Score from 1 (poor) to 5 (excellent) evaluating if the translation reads naturally like it was written by a native."
    )
    grammar_score: int = Field(
        description="Score from 1 (poor) to 5 (excellent) evaluating spelling, punctuation, grammar, and terminology consistency."
    )
    evaluation_summary: str = Field(
        description="A detailed 2-3 paragraph constructive review in Turkish detailing the strengths, weaknesses, and concrete recommendations for future translation runs."
    )

class TranslationEvaluator:
    @classmethod
    def evaluate_translation(cls, source_text: str, translated_text: str, genre: str = "literary") -> dict:
        """
        Evaluate the overall quality of a translation against its source text.
        Returns scores and a detailed report.
        """
        llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=Config.MAIN_MODEL,  # Use main model for robust evaluation
            temperature=0
        )
        
        prompt = f"""
You are a highly demanding bilingual quality control expert. Evaluate the translation below against its source text for a {genre} domain.

### Original Source Text:
{source_text}

### Translated Target Text:
{translated_text}

### Evaluation Criteria:
1. **Accuracy (Doğruluk):** Score 1-5. Did the translation omit details, add unauthorized content, or shift the meaning?
2. **Fluency (Akıcılık):** Score 1-5. Does the text flow beautifully in the target language (Turkish), or does it sound like a translated/clunky text?
3. **Grammar & Terminology (İmla ve Terim Tutarlılığı):** Score 1-5. Are there grammar errors, spelling mistakes, punctuation issues, or inconsistent technical terms?

Provide a fair but strict score and compile a detailed review in Turkish containing:
- Strengths (Çevirinin Güçlü Yanları)
- Weaknesses (Zayıf Yanları ve Hatalar)
- Concrete Recommendations (Öneriler)
"""

        structured_llm = llm.with_structured_output(EvaluationReportSchema)
        result = structured_llm.invoke(prompt)
        
        return {
            "accuracy": result.accuracy_score,
            "fluency": result.fluency_score,
            "grammar": result.grammar_score,
            "summary": result.evaluation_summary
        }
