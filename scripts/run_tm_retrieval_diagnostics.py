"""Generate synthetic diagnostics for translation memory retrieval."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.tm_retrieval import build_reference_pack, retrieve_translation_memory


SYNTHETIC_TM = [
    {
        "tm_id": "tm_syn_001",
        "pair_id": "synthetic_travel",
        "source_lang": "EN",
        "target_lang": "TR",
        "source_text": "The coach arrived late at night.",
        "target_text": "Posta arabası gece geç saatte geldi.",
        "alignment_confidence": "high",
        "usage_policy": {"scope": "local_private_reference", "do_not_commit_full_text": True},
    },
    {
        "tm_id": "tm_syn_002",
        "pair_id": "synthetic_travel",
        "source_lang": "EN",
        "target_lang": "TR",
        "source_text": "The carriage reached the village before dawn.",
        "target_text": "Araba şafaktan önce köye vardı.",
        "alignment_confidence": "medium",
        "usage_policy": {"scope": "local_private_reference", "do_not_commit_full_text": True},
    },
    {
        "tm_id": "tm_syn_003",
        "pair_id": "synthetic_weather",
        "source_lang": "EN",
        "target_lang": "TR",
        "source_text": "Heavy rain covered the empty fields.",
        "target_text": "Şiddetli yağmur boş tarlaları kapladı.",
        "alignment_confidence": "high",
        "usage_policy": {"scope": "local_private_reference", "do_not_commit_full_text": True},
    },
    {
        "tm_id": "tm_syn_004",
        "pair_id": "synthetic_low",
        "source_lang": "EN",
        "target_lang": "TR",
        "source_text": "The coach stopped near the inn.",
        "target_text": "Araba hanın yanında durdu.",
        "alignment_confidence": "low",
        "usage_policy": {"scope": "local_private_reference", "do_not_commit_full_text": True},
    },
]

QUERIES = [
    "The coach arrived late at night.",
    "A carriage entered the village before sunrise.",
    "Rain fell over the fields.",
]


def main() -> None:
    output = PROJECT_ROOT / "outputs" / "tm_retrieval_diagnostics_report.md"
    lines = [
        "# Translation Memory Retrieval Diagnostics",
        "",
        "## Summary",
        "",
        f"- Synthetic TM entries: `{len(SYNTHETIC_TM)}`",
        f"- Queries tested: `{len(QUERIES)}`",
        "- Default minimum confidence: `medium`",
        "- Low-confidence entries are excluded by default.",
        "",
        "## Retrieval Examples",
        "",
    ]
    total_retrieved = 0
    for index, query in enumerate(QUERIES, start=1):
        retrieved = retrieve_translation_memory(query, SYNTHETIC_TM, top_k=2)
        pack = build_reference_pack(query, retrieved, max_chars_per_side=100)
        total_retrieved += len(retrieved)
        lines.extend(
            [
                f"### Query {index}",
                "",
                f"- Query: `{query}`",
                f"- References retrieved: `{len(retrieved)}`",
                f"- TM IDs: `{[item['tm_id'] for item in retrieved]}`",
                f"- Scores: `{[item['similarity_score'] for item in retrieved]}`",
                f"- Reference-only flags: `{all(ref['use_mode'] == 'reference_only' for ref in pack['references'])}`",
                "",
            ]
        )

    high_only = retrieve_translation_memory(
        QUERIES[0],
        SYNTHETIC_TM,
        top_k=5,
        min_alignment_confidence="high",
        min_score=0.0,
    )
    low_allowed = retrieve_translation_memory(
        QUERIES[0],
        SYNTHETIC_TM,
        top_k=5,
        min_alignment_confidence="low",
        min_score=0.0,
    )
    lines.extend(
        [
            "## Confidence Filtering",
            "",
            f"- High-only results: `{len(high_only)}`",
            f"- Low-allowed results: `{len(low_allowed)}`",
            f"- Total references retrieved across example queries: `{total_retrieved}`",
            "",
            "## Limitations",
            "",
            "- This is retrieval infrastructure, not fine-tuning.",
            "- Retrieved examples are reference-only.",
            "- Human review is required.",
            "- Local real TM artifacts may contain copyrighted text and must remain untracked.",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"TM retrieval diagnostics written to: {output}")


if __name__ == "__main__":
    main()
