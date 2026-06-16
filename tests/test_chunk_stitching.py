from src.tie.chunk_stitching import ChunkBoundaryQualityChecker, SentenceSafeChunker


def test_does_not_split_inside_sentence_when_possible():
    text = "First sentence is complete. Second sentence is also complete. Third sentence closes."
    result = SentenceSafeChunker(max_chars=45).chunk_text(text, chunk_id_prefix="t")
    assert all(chunk["text"].strip().endswith(".") for chunk in result["chunks"])


def test_flags_lowercase_chunk_start():
    chunk = {"chunk_id": "x", "text": "it begins in the middle of a source sentence."}
    result = ChunkBoundaryQualityChecker().check(chunk)
    assert any(flag["type"] == "lowercase_chunk_start" for flag in result["flags"])
    assert result["recommendation"] == "review"


def test_flags_continuation_start_itself():
    chunk = {"chunk_id": "x", "text": "itself vindicated."}
    result = ChunkBoundaryQualityChecker().check(chunk)
    assert any(flag["type"] == "continuation_chunk_start" for flag in result["flags"])


def test_accepts_clean_sentence_boundary():
    chunk = {"chunk_id": "x", "text": "The boy watches the fire. Night falls."}
    result = ChunkBoundaryQualityChecker().check(chunk)
    assert result["recommendation"] == "accept"
    assert result["flags"] == []


def test_preserves_literary_fragments():
    text = "He waited. Silent. Unmoving. The fire dimmed."
    result = SentenceSafeChunker(max_chars=20).chunk_text(text, chunk_id_prefix="lit")
    assert result["recommendation"] == "accept"
    assert any("Silent." in chunk["text"] for chunk in result["chunks"])
