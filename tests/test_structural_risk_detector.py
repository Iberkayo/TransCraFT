from unittest.mock import MagicMock, patch

from src.agents.critic import evaluate_translation
from src.agents.translator import translate_draft
from src.tie.language_profile import LanguageProfileLoader
from src.tie.structural_risk_detector import StructuralRiskDetector
from src.tie.strategy_planner import TranslationStrategyPlanner


def risk_types(text: str, genre: str = "general") -> set[str]:
    return {risk["risk_type"] for risk in StructuralRiskDetector().detect(text, genre=genre)}


def test_detects_long_relative_clause():
    text = "The policy applies to vendors who process records, which means every contract must be updated this month."

    assert "long_relative_clause" in risk_types(text, genre="business")


def test_detects_noun_stack():
    text = "The customer data privacy compliance monitoring system needs an update."

    assert "noun_stack" in risk_types(text, genre="business")


def test_detects_passive_voice():
    text = "The report was reviewed by the committee and was approved after revisions."

    risks = risk_types(text, genre="business")
    assert "passive_voice" in risks
    assert "double_passive" in risks


def test_detects_phrasal_verb():
    text = "The team will follow up with the branch office tomorrow."

    assert "phrasal_verb" in risk_types(text, genre="business")


def test_detects_literary_fragment():
    text = "He waited. Silent. Alone."

    assert "literary_fragment" in risk_types(text, genre="literary")


def test_strategy_uses_detected_risks():
    strategy = TranslationStrategyPlanner().plan(
        source_text=(
            "The legacy software is expected to be phased out by the end of Q3, "
            "a decision which has left many departments wondering how their daily operations will be affected."
        ),
        source_language="English",
        target_language="Turkish",
        genre="business",
    )

    risk_types_in_strategy = {risk["risk_type"] for risk in strategy["structural_risks"]}
    assert "long_relative_clause" in risk_types_in_strategy
    assert "business_translationese_risk" in risk_types_in_strategy
    assert any("Use two Turkish sentences" in note for note in strategy["turkish_reconstruction_notes"])
    assert any("soru isaretleri yaratti" in note for note in strategy["turkish_reconstruction_notes"])


def test_translator_prompt_treats_strategy_as_constraint():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The policy applies to vendors who process records, which means every contract must be updated.",
        source_language="English",
        target_language="Turkish",
        genre="business",
    )
    state = {
        "source_text": "The policy applies to vendors who process records, which means every contract must be updated.",
        "source_language": "English",
        "target_language": "Turkish",
        "glossary": [],
        "positive_glossary": {},
        "negative_glossary": {},
        "auto_glossary_candidates": {},
        "compact_memory_context": "",
        "translation_strategy": strategy,
        "language_profile": LanguageProfileLoader().load_profile("Turkish"),
        "logs": [],
        "trace_id": None,
        "chunk_index": 0,
    }

    with patch("src.agents.translator.ChatOpenAI") as mock_chat:
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content="ceviri")
        mock_chat.return_value = llm
        translate_draft(state)

    prompt = llm.invoke.call_args.args[0]
    assert "constraint, not optional background" in prompt
    assert "Structural risks:" in prompt
    assert "actively avoid those risks" in prompt


def test_critic_receives_structural_risk_checklist():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The policy applies to vendors who process records, which means every contract must be updated.",
        source_language="English",
        target_language="Turkish",
        genre="business",
    )
    state = {
        "source_text": "The policy applies to vendors who process records, which means every contract must be updated.",
        "target_language": "Turkish",
        "stylized_translation": "Tedarikciler icin politika uygulanir.",
        "style_guide": "Natural Turkish.",
        "positive_glossary": {},
        "negative_glossary": {},
        "auto_glossary_candidates": {},
        "revision_count": 0,
        "style_revision_count": 0,
        "enable_tie": False,
        "translation_strategy": strategy,
        "logs": [],
        "trace_id": None,
        "chunk_index": 0,
    }

    with patch("src.agents.critic.ChatOpenAI") as mock_chat:
        result_model = MagicMock()
        result_model.is_approved = True
        result_model.critique = "None"
        structured = MagicMock()
        structured.invoke.return_value = result_model
        llm = MagicMock()
        llm.with_structured_output.return_value = structured
        mock_chat.return_value = llm
        evaluate_translation(state)

    prompt = structured.invoke.call_args.args[0]
    assert "Strategy Critic Checklist" in prompt
    assert "heavy English relative-clause structure" in prompt


def test_no_hidden_cot_phrasing():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The customer data privacy compliance monitoring system needs an update.",
        source_language="English",
        target_language="Turkish",
        genre="business",
    )
    serialized = str(strategy).casefold()

    assert "chain-of-thought" not in serialized
    assert "think step by step" not in serialized
    assert "show your reasoning" not in serialized
    assert "reveal reasoning" not in serialized
