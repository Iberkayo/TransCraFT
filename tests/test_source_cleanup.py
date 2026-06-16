from src.tie.source_cleanup import SourceExtractionCleaner, SourceExtractionQualityChecker


def test_repairs_missing_space_stokesthe():
    result = SourceExtractionCleaner().clean("He stokesthe scullery fire.")
    assert "stokes the" in result["cleaned_text"]
    assert result["changed"] is True


def test_repairs_missing_space_woodsbeyond():
    result = SourceExtractionCleaner().clean("There are darker woodsbeyond the fields.")
    assert "woods beyond" in result["cleaned_text"]


def test_repairs_missing_space_hisshoulders():
    result = SourceExtractionCleaner().clean("Hisshoulders are narrow.")
    assert "His shoulders" in result["cleaned_text"]


def test_flags_suspected_merged_token():
    result = SourceExtractionCleaner().clean("This unknownmergedtoken remains uncertain.")
    assert any(flag["type"] == "suspected_merged_token" for flag in result["quality_flags"])
    assert result["recommendation"] == "review"


def test_adds_space_after_punctuation():
    result = SourceExtractionCleaner().clean("He watches him.He waits,he listens.")
    assert "him. He" in result["cleaned_text"]
    assert "waits, he" in result["cleaned_text"]


def test_quality_checker_accepts_clean_text():
    result = SourceExtractionQualityChecker().check(
        "The boy crouches by the fire and watches him. The night is cold."
    )
    assert result["recommendation"] == "accept"
    assert result["should_translate"] is True


def test_quality_checker_reviews_suspicious_text():
    result = SourceExtractionQualityChecker().check(
        "The boy crouches by the fire and unknownmergedtoken appears twice unknownmergedtoken."
    )
    assert result["recommendation"] == "review"
    assert result["should_translate"] is True


def test_output_schema_complete():
    result = SourceExtractionCleaner().clean("He stokesthe fire.")
    assert {
        "original_text",
        "cleaned_text",
        "changed",
        "repairs",
        "quality_flags",
        "recommendation",
    }.issubset(result.keys())
