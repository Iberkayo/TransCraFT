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


def test_repairs_split_initial_see():
    result = SourceExtractionCleaner().clean("S ee the child.")
    assert result["cleaned_text"] == "See the child."
    assert any(r["type"] == "split_initial_letter_repair" for r in result["repairs"])


def test_repairs_split_initial_now():
    result = SourceExtractionCleaner().clean("N ow come days.")
    assert result["cleaned_text"] == "Now come days."
    assert any(r["before"] == "N ow" for r in result["repairs"])


def test_repairs_invisible_word_split_neighbor():
    result = SourceExtractionCleaner().clean("Neigh\u200bbor, you caint get shed of him.")
    assert "Neighbor" in result["cleaned_text"]
    assert any(r["type"] == "invisible_word_split_repair" for r in result["repairs"])


def test_repairs_invisible_word_split_clothing():
    result = SourceExtractionCleaner().clean("from his cloth\u200bing")
    assert result["cleaned_text"] == "from his clothing"


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


def test_quality_checker_reviews_unrepaired_split_letter_artifact():
    result = SourceExtractionQualityChecker().check("S ee the child. He waits.")
    assert result["recommendation"] == "review"
    assert any(flag["type"] == "split_letter_artifact" for flag in result["flags"])


def test_quality_checker_does_not_accept_split_letter_artifacts_as_perfect():
    result = SourceExtractionQualityChecker().check("N ow come days of begging.")
    assert result["quality_score"] < 1.0
    assert result["recommendation"] != "accept"


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
