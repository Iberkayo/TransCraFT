from pathlib import Path
from unittest.mock import MagicMock, patch

from src.agents.critic import evaluate_translation
from src.agents.translator import translate_draft
from src.core.graph import run_strategy_planner
from src.tie.language_profile import LanguageProfileLoader
from src.tie.strategy_planner import (
    REQUIRED_STRATEGY_FIELDS,
    TranslationStrategyPlanner,
    build_strategy_prompt_context,
)
from scripts.run_strategy_planner_diagnostics import generate_report, run_diagnostics


def test_language_profile_loader_loads_tr_profile():
    profile = LanguageProfileLoader().load_profile("Turkish")

    assert profile["language_code"] == "tr_TR"
    assert any("Drop pronouns" in rule for rule in profile["core_rules"])
    assert any("word order" in rule for rule in profile["core_rules"])


def test_strategy_planner_returns_required_fields():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The child stood by the fire.",
        source_language="English",
        target_language="Turkish",
        genre="literary",
    )

    assert set(REQUIRED_STRATEGY_FIELDS).issubset(strategy.keys())


def test_fallback_strategy_for_literary_genre():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The child stood by the fire.",
        source_language="English",
        target_language="Turkish",
        genre="literary",
    )

    assert strategy["text_type"] == "literary_fiction"
    assert strategy["literalness_level"] == "medium_low"
    assert any("fragments" in note for note in strategy["turkish_reconstruction_notes"])


def test_fallback_strategy_for_technical_genre():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The model uses attention mechanisms.",
        source_language="English",
        target_language="Turkish",
        genre="tech",
    )

    assert strategy["text_type"] == "technical"
    assert any("terminology consistency" in item for item in strategy["translator_instructions"])
    assert strategy["register"] == "formal technical"


def test_translator_receives_strategy_context():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The child stood by the fire.",
        source_language="English",
        target_language="Turkish",
        genre="literary",
    )
    state = {
        "source_text": "The child stood by the fire.",
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
        llm.invoke.return_value = MagicMock(content="Cocuk atesin yaninda durdu.")
        mock_chat.return_value = llm

        result = translate_draft(state)

    prompt = llm.invoke.call_args.args[0]
    assert result["raw_translation"] == "Cocuk atesin yaninda durdu."
    assert "Translation Strategy Plan" in prompt
    assert "Avoid literal English word order" in prompt or "avoid literal English word order" in prompt
    assert "The child stood by the fire." in prompt


def test_missing_language_profile_uses_safe_defaults():
    loader = LanguageProfileLoader()
    profile = loader.load_profile("xx_XX")
    strategy = TranslationStrategyPlanner(profile_loader=loader).plan(
        source_text="A short sentence.",
        source_language="xx_XX",
        target_language="yy_YY",
        genre="general",
    )

    assert profile["fallback_used"] is True
    assert profile["language_code"] == "xx_XX"
    assert set(REQUIRED_STRATEGY_FIELDS).issubset(strategy.keys())


def test_strategy_planner_failure_uses_fallback():
    state = {
        "source_text": "The child stood by the fire.",
        "source_language": "English",
        "target_language": "Turkish",
        "genre": "literary",
        "style_preset": "default",
        "compact_memory_context": "",
        "logs": [],
        "trace_id": None,
    }

    with patch("src.tie.strategy_planner.TranslationStrategyPlanner.plan", side_effect=RuntimeError("boom")):
        result = run_strategy_planner(state)

    assert result["strategy_planner_fallback_used"] is True
    assert result["translation_strategy"]["fallback_used"] is True
    assert result["translation_strategy"]["planner_error"] == "boom"


def test_critic_checklist_generated():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The child stood by the fire.",
        source_language="English",
        target_language="Turkish",
        genre="literary",
    )

    assert "Turkish naturalness" in strategy["critic_checklist"]
    assert "translationese patterns avoided" in strategy["critic_checklist"]
    assert "style and rhythm preservation" in strategy["critic_checklist"]


def test_critic_receives_strategy_checklist():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The child stood by the fire.",
        source_language="English",
        target_language="Turkish",
        genre="literary",
    )
    state = {
        "source_text": "The child stood by the fire.",
        "stylized_translation": "Cocuk atesin yaninda durdu.",
        "style_guide": "Plain literary Turkish.",
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

        result = evaluate_translation(state)

    prompt = structured.invoke.call_args.args[0]
    assert result["is_approved"] is True
    assert "Strategy Critic Checklist" in prompt
    assert "translationese patterns avoided" in prompt


def test_no_hidden_cot_required():
    strategy = TranslationStrategyPlanner().plan(
        source_text="The child stood by the fire.",
        source_language="English",
        target_language="Turkish",
        genre="literary",
    )
    context = build_strategy_prompt_context(strategy, LanguageProfileLoader().load_profile("Turkish"))
    serialized = f"{strategy} {context}".casefold()

    assert "chain-of-thought" not in serialized
    assert "hidden" not in serialized
    assert "step-by-step reasoning" not in serialized


def test_diagnostics_report_generation(tmp_path: Path):
    result = run_diagnostics(
        [
            {
                "name": "Tiny sample",
                "source": "The model uses attention.",
                "genre": "tech",
                "work_id": "attention_is_all_you_need",
            }
        ]
    )
    output_path = generate_report(result, tmp_path / "strategy_report.md")

    report = output_path.read_text(encoding="utf-8")
    assert "Strategy Planner Diagnostics Report" in report
    assert "Generated Translation Strategy" in report
    assert "Critic Checklist" in report
