from src.tie.foreign_residue import ForeignResidueDetector


def test_detects_all_races_all_breeds():
    result = ForeignResidueDetector().detect("All races, all breeds. Hepsi oradaydı.")
    assert result["foreign_residue_count"] >= 1
    assert any(r["text"] == "All races, all breeds" for r in result["residues"])


def test_detects_hisshoulders():
    result = ForeignResidueDetector().detect("Hisshoulders dardır.")
    assert any(r["text"] == "Hisshoulders" for r in result["residues"])


def test_detects_untranslated_men():
    result = ForeignResidueDetector().detect("Konuşmaları kaba olan Men oradaydı.")
    assert any(r["text"] == "Men" for r in result["residues"])


def test_detects_untranslated_blacks():
    result = ForeignResidueDetector().detect("Tarlalarda Blacks çalışıyordu.")
    assert any(r["text"] == "Blacks" for r in result["residues"])


def test_allows_protected_place_names():
    result = ForeignResidueDetector().detect(
        "Memphis'ten New Orleans'a gider.",
        protected_terms=["Memphis", "New Orleans"],
    )
    assert result["foreign_residue_count"] == 0


def test_allows_proper_nouns():
    result = ForeignResidueDetector().detect(
        "Leonids gökteydi ve Dipper görünüyordu.",
        proper_nouns=["Leonids", "Dipper"],
    )
    assert result["foreign_residue_count"] == 0


def test_rejects_critical_english_residue():
    result = ForeignResidueDetector().detect("All races, all breeds.")
    assert result["recommendation"] == "reject"


def test_review_for_uncertain_residue():
    result = ForeignResidueDetector().detect("Çocuk fire yanında durdu.")
    assert result["recommendation"] == "review"


def test_output_schema_complete():
    result = ForeignResidueDetector().detect("Temiz Türkçe metin.")
    assert {"foreign_residue_count", "residues", "recommendation"}.issubset(result.keys())


def test_no_hidden_cot_phrasing():
    result = ForeignResidueDetector().detect("Temiz Türkçe metin.")
    serialized = str(result).casefold()
    assert "chain of thought" not in serialized
    assert "reasoning" not in serialized
