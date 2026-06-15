import pytest
import json
from unittest.mock import MagicMock, patch
from src.tie.style_critic import StyleConsistencyCritic
from src.agents.critic import evaluate_translation
from src.core.state import TranslationState

def test_style_critic_evaluate_direct():
    critic = StyleConsistencyCritic()
    
    # Mock LLM structure call
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {
        "style_preservation": 4,
        "rhythm_preservation": 4,
        "voice_consistency": 5,
        "literary_force": 4,
        "issues": [],
        "suggestions": []
    }
    
    # We patch ChatOpenAI to return a mock that when invoked returns our schema
    with patch("src.tie.style_critic.ChatOpenAI") as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        mock_structured = MagicMock()
        mock_instance.with_structured_output.return_value = mock_structured
        mock_structured.invoke.return_value = mock_result
        
        evaluation = critic.evaluate(
            source_text="See the child.",
            translated_text="Çocuğa bakın.",
            author_style_profile={"attributes": {"tone": "bleak"}},
            style_contract={"rules": ["Scenic presentation"]}
        )
        
        assert evaluation["style_preservation"] == 4
        assert evaluation["voice_consistency"] == 5
        assert len(evaluation["issues"]) == 0

def test_style_critic_low_score_triggers_revision():
    # Mock the LLM structured calls for both accuracy critic and style critic
    mock_accuracy_result = MagicMock()
    mock_accuracy_result.is_approved = True
    mock_accuracy_result.critique = "None"
    
    mock_style_result = MagicMock()
    mock_style_result.model_dump.return_value = {
        "style_preservation": 2, # Under threshold
        "rhythm_preservation": 3,
        "voice_consistency": 4,
        "literary_force": 3,
        "issues": ["Declarative suffix used"],
        "suggestions": ["Change sıskadır to sıska"]
    }
    
    state = {
        "source_text": "See the child. He is pale and thin.",
        "source_language": "English",
        "target_language": "Turkish",
        "style_guide": "Rules",
        "glossary": [],
        "positive_glossary": {},
        "negative_glossary": {},
        "stylized_translation": "Çocuğu görün. O solgun ve sıskadır.",
        "is_approved": False,
        "revision_count": 0,
        "style_revision_count": 0,
        "enable_tie": True,
        "work_id": "blood_meridian",
        "logs": []
    }
    
    # Mock the calls
    with patch("src.agents.critic.ChatOpenAI") as mock_accuracy_chat, \
         patch("src.tie.style_critic.ChatOpenAI") as mock_style_chat:
        
        # Setup accuracy critic mock
        acc_instance = MagicMock()
        mock_accuracy_chat.return_value = acc_instance
        acc_structured = MagicMock()
        acc_instance.with_structured_output.return_value = acc_structured
        acc_structured.invoke.return_value = mock_accuracy_result
        
        # Setup style critic mock
        sty_instance = MagicMock()
        mock_style_chat.return_value = sty_instance
        sty_structured = MagicMock()
        sty_instance.with_structured_output.return_value = sty_structured
        sty_structured.invoke.return_value = mock_style_result
        
        res = evaluate_translation(state)
        
        # Assertions
        assert res["is_approved"] is False  # Overridden by style critic
        assert res["style_revision_count"] == 1  # Incremented
        assert "Stylistic Criticism" in res["critique"]

def test_style_critic_high_score_bypasses_revision():
    mock_accuracy_result = MagicMock()
    mock_accuracy_result.is_approved = True
    mock_accuracy_result.critique = "None"
    
    mock_style_result = MagicMock()
    mock_style_result.model_dump.return_value = {
        "style_preservation": 4, # Above threshold
        "rhythm_preservation": 4,
        "voice_consistency": 4,
        "literary_force": 4,
        "issues": [],
        "suggestions": []
    }
    
    state = {
        "source_text": "See the child. He is pale and thin.",
        "source_language": "English",
        "target_language": "Turkish",
        "style_guide": "Rules",
        "glossary": [],
        "positive_glossary": {},
        "negative_glossary": {},
        "stylized_translation": "Çocuğa bakın. Solgun ve sıska.",
        "is_approved": False,
        "revision_count": 0,
        "style_revision_count": 0,
        "enable_tie": True,
        "work_id": "blood_meridian",
        "logs": []
    }
    
    with patch("src.agents.critic.ChatOpenAI") as mock_accuracy_chat, \
         patch("src.tie.style_critic.ChatOpenAI") as mock_style_chat:
        
        acc_instance = MagicMock()
        mock_accuracy_chat.return_value = acc_instance
        acc_structured = MagicMock()
        acc_instance.with_structured_output.return_value = acc_structured
        acc_structured.invoke.return_value = mock_accuracy_result
        
        sty_instance = MagicMock()
        mock_style_chat.return_value = sty_instance
        sty_structured = MagicMock()
        sty_instance.with_structured_output.return_value = sty_structured
        sty_structured.invoke.return_value = mock_style_result
        
        res = evaluate_translation(state)
        
        assert res["is_approved"] is True
        assert res["style_revision_count"] == 0

def test_style_critic_loop_limit():
    # If style_revision_count is already 1, a low score should not trigger another loop
    mock_accuracy_result = MagicMock()
    mock_accuracy_result.is_approved = True
    mock_accuracy_result.critique = "None"
    
    mock_style_result = MagicMock()
    mock_style_result.model_dump.return_value = {
        "style_preservation": 2, # Under threshold
        "rhythm_preservation": 3,
        "voice_consistency": 2,
        "literary_force": 3,
        "issues": ["Issues"],
        "suggestions": ["Suggestions"]
    }
    
    state = {
        "source_text": "See the child. He is pale and thin.",
        "source_language": "English",
        "target_language": "Turkish",
        "style_guide": "Rules",
        "glossary": [],
        "positive_glossary": {},
        "negative_glossary": {},
        "stylized_translation": "Çocuğu görün. O solgun ve sıskadır.",
        "is_approved": False,
        "revision_count": 0,
        "style_revision_count": 1,  # Max style loop limit hit!
        "enable_tie": True,
        "work_id": "blood_meridian",
        "logs": []
    }
    
    with patch("src.agents.critic.ChatOpenAI") as mock_accuracy_chat, \
         patch("src.tie.style_critic.ChatOpenAI") as mock_style_chat:
        
        acc_instance = MagicMock()
        mock_accuracy_chat.return_value = acc_instance
        acc_structured = MagicMock()
        acc_instance.with_structured_output.return_value = acc_structured
        acc_structured.invoke.return_value = mock_accuracy_result
        
        sty_instance = MagicMock()
        mock_style_chat.return_value = sty_instance
        sty_structured = MagicMock()
        sty_instance.with_structured_output.return_value = sty_structured
        sty_structured.invoke.return_value = mock_style_result
        
        res = evaluate_translation(state)
        
        assert res["is_approved"] is True  # Should stay approved (bypass/loop-limit)
        assert res["style_revision_count"] == 1  # Unchanged

