import json

from src.core.scoped_glossary import ScopedGlossaryStore


def test_scoped_glossary_isolates_work_and_genre(tmp_path):
    store = ScopedGlossaryStore(tmp_path / "runtime")

    literary = store.merge(
        {"White Rabbit": "Beyaz Tavsan"},
        genre="literary",
        work_id="alice_in_wonderland",
        user_id="berkay",
    )
    technical = store.merge(
        {"self-attention": "oz-dikkat"},
        genre="tech",
        work_id="attention_is_all_you_need",
        user_id="berkay",
    )

    assert literary == {"White Rabbit": "Beyaz Tavsan"}
    assert technical == {"self-attention": "oz-dikkat"}
    assert "self-attention" not in store.load("literary", "alice_in_wonderland", "berkay")
    assert "White Rabbit" not in store.load("tech", "attention_is_all_you_need", "berkay")

    literary_path = store.path_for("literary", "alice_in_wonderland", "berkay")
    assert literary_path.exists()
    assert "genre-literary__work-alice_in_wonderland__user-berkay" in str(literary_path)

    with open(literary_path, "r", encoding="utf-8") as f:
        assert json.load(f)["White Rabbit"] == "Beyaz Tavsan"
