import json
from pathlib import Path

from src.tie.book_runner import BookTranslationRunner, build_book_run_config
from src.tie.export_pdf import export_translation_pdf


def _translator(text: str, context: dict) -> str:
    assert context["tm_reference_usage"] == "metadata_only"
    return "Bu, doğal ve eksiksiz bir deneme çevirisidir."


def test_config_defaults_to_reference_only_tm():
    config = build_book_run_config("sample.txt")
    assert config["tm"]["use_mode"] == "reference_only"
    assert config["tm"]["auto_inject"] is False


def test_runner_writes_standardized_local_outputs(tmp_path: Path):
    source = tmp_path / "arbitrary_input.txt"
    source.write_text("A complete source sentence for a generic document.", encoding="utf-8")
    output_root = tmp_path / "book_runs"
    config = build_book_run_config(
        str(source),
        first_words=20,
        tm_enabled=False,
        output_root=str(output_root),
        write_side_by_side=True,
    )

    result = BookTranslationRunner(translator=_translator).run(config)

    assert result.chunks_translated == 1
    assert Path(result.output_paths["translation_markdown"]).exists()
    assert Path(result.output_paths["metadata_json"]).exists()
    assert Path(result.output_paths["quality_report"]).exists()
    assert Path(result.output_paths["side_by_side_markdown"]).exists()


def test_runner_records_tm_pack_without_prompt_injection(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text("The visitor opened the old wooden door.", encoding="utf-8")

    def tm_builder(*args, **kwargs):
        return {
            "references": [{"tm_id": "tm-1", "source_preview": "The visitor arrived."}],
            "warnings": [],
        }

    config = build_book_run_config(
        str(source),
        first_words=20,
        output_root=str(tmp_path / "outputs"),
    )
    result = BookTranslationRunner(translator=_translator, tm_builder=tm_builder).run(config)
    metadata = json.loads(Path(result.output_paths["metadata_json"]).read_text(encoding="utf-8"))

    pack = metadata["chunks"][0]["tm_reference_pack"]
    assert pack["auto_inject"] is False
    assert pack["references"][0]["tm_id"] == "tm-1"


def test_missing_tm_directory_degrades_gracefully(tmp_path: Path):
    source = tmp_path / "book.txt"
    source.write_text("A short and complete sentence.", encoding="utf-8")
    config = build_book_run_config(
        str(source),
        first_words=10,
        tm_dir=str(tmp_path / "missing"),
        output_root=str(tmp_path / "outputs"),
    )

    result = BookTranslationRunner(translator=_translator).run(config)
    metadata = json.loads(Path(result.output_paths["metadata_json"]).read_text(encoding="utf-8"))

    assert metadata["chunks"][0]["tm_reference_pack"]["references"] == []
    assert result.chunks_translated == 1


def test_runner_has_no_book_specific_input_contract(tmp_path: Path):
    source = tmp_path / "unrelated_title.txt"
    source.write_text("The laboratory closed at sunset.", encoding="utf-8")
    config = build_book_run_config(
        str(source),
        first_words=10,
        tm_enabled=False,
        output_root=str(tmp_path / "outputs"),
    )

    result = BookTranslationRunner(translator=_translator).run(config)

    assert result.run_id.startswith("unrelated_title_")


def test_pdf_export_writes_unicode_output(tmp_path: Path):
    result = export_translation_pdf(
        str(tmp_path / "translation.pdf"),
        ["İstasyonda sessizce bekledi."],
        {
            "input_path": "synthetic.txt",
            "target_language": "tr_TR",
            "range": {"mode": "first_words", "selected_word_count": 5},
            "page_definition": "word_based_page_equivalents",
            "tm_retrieval": {"enabled": False},
        },
        {"recommendation": "accept", "human_review_required": True},
    )

    assert result["written"] is True
    assert Path(result["path"]).stat().st_size > 0
