from src.tie.turkish_fluency_qa import TurkishFluencyAnomalyChecker


def test_flags_broken_ne_ne_de_phrase():
    result = TurkishFluencyAnomalyChecker().check("Ne okuyup yazma bilir ne de doğru dürüst konuşurdu.")
    assert any(flag["type"] == "broken_turkish_grammar" for flag in result["flags"])


def test_flags_gozlerini_kafeslerler():
    result = TurkishFluencyAnomalyChecker().check("Gözlerini kafeslerler ve beklerler.")
    assert any(flag["type"] == "literal_calque_or_nonsense" for flag in result["flags"])


def test_flags_dolu_salonda_oynuyordu():
    result = TurkishFluencyAnomalyChecker().check("Rahip Green dolu salonda oynuyordu.")
    assert any(flag["type"] == "register_semantic_oddity" for flag in result["flags"])


def test_flags_fittik():
    result = TurkishFluencyAnomalyChecker().check("Neredeyse yedi fittik boyundaydı.")
    assert any(flag["type"] == "unit_or_typo_risk" for flag in result["flags"])


def test_flags_double_spaces():
    result = TurkishFluencyAnomalyChecker().check("Yüzü tuhaf  masumdur.")
    assert any(flag["type"] == "double_space" for flag in result["flags"])


def test_flags_suspicious_akisiz_siddet_egilim():
    result = TurkishFluencyAnomalyChecker().check("İçinde akılsız bir şiddete eğilim büyür.")
    assert any(flag["type"] == "suspicious_literary_phrase" for flag in result["flags"])


def test_clean_literary_turkish_accepts():
    result = TurkishFluencyAnomalyChecker().check("Çocuk ateşin yanında çömelir ve adamı izler.")
    assert result["recommendation"] == "accept"
    assert result["flags"] == []
