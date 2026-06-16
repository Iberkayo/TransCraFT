from src.tie.literary_semantic_qa import LiterarySemanticQAChecker


def test_flags_flatboat_as_duzenbaz_critical():
    result = LiterarySemanticQAChecker().check("He was taken on for a flatboat.", "Bir düzenbaz için alındı.")
    assert any(flag["type"] == "semantic_mistranslation_risk" and flag["severity"] == "critical" for flag in result["flags"])


def test_flags_schoolmaster_as_okul_muduru_risky():
    result = LiterarySemanticQAChecker().check("His father has been a schoolmaster.", "Babası okul müdürü olmuştu.")
    assert any(flag["source_term"] == "schoolmaster" for flag in result["flags"])


def test_flags_scullery_fire_as_bulasik_ocagi_risky():
    result = LiterarySemanticQAChecker().check("He stokes the scullery fire.", "Bulaşık ocağını besler.")
    assert any(flag["source_term"] == "scullery fire" for flag in result["flags"])


def test_flags_full_house_as_oynuyordu_risky():
    result = LiterarySemanticQAChecker().check("He preached to a full house.", "Dolu salonda oynuyordu.")
    assert any(flag["source_term"] == "full house" for flag in result["flags"])


def test_allows_place_name_variants():
    result = LiterarySemanticQAChecker().check("He rode into Texas.", "Teksas'a sürdü.")
    assert not any(flag["type"] == "missing_source_entity" for flag in result["flags"])


def test_flags_missing_source_entity():
    result = LiterarySemanticQAChecker().check("He met Judge Holden in Texas.", "Teksas'ta biriyle karşılaştı.")
    assert any(flag["source_entity"] == "Judge Holden" for flag in result["flags"])


def test_flags_fittik_unit_typo():
    result = LiterarySemanticQAChecker().check("He was seven foot tall.", "Neredeyse yedi fittik boyundaydı.")
    assert any(flag["type"] == "unit_or_typo_risk" for flag in result["flags"])


def test_clean_pair_has_no_critical_flags():
    result = LiterarySemanticQAChecker().check("He rode into Memphis.", "Memphis'e girdi.")
    assert not any(flag["severity"] == "critical" for flag in result["flags"])
