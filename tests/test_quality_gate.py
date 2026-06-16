from src.tie.quality_gate import QualityGate


def test_rejects_foreign_residue_critical():
    result = QualityGate().evaluate(
        foreign_residue={"residues": [{"type": "english_phrase", "severity": "critical", "text": "All races"}]}
    )
    assert result["recommendation"] == "reject"


def test_reviews_semantic_critical():
    result = QualityGate().evaluate(
        semantic_flags=[{"type": "semantic_mistranslation_risk", "severity": "critical"}]
    )
    assert result["recommendation"] == "review"


def test_reviews_chunk_boundary_major():
    result = QualityGate().evaluate(boundary_flags=[{"type": "lowercase_chunk_start", "severity": "major"}])
    assert result["recommendation"] == "review"


def test_accepts_clean_flags():
    result = QualityGate().evaluate(
        source_quality={"recommendation": "accept"},
        foreign_residue={"residues": []},
        boundary_flags=[],
        semantic_flags=[],
        fluency_flags=[],
    )
    assert result["recommendation"] == "accept"
