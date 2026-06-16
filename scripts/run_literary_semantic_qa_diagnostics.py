"""Run diagnostics for v0.9.3 literary semantic and fluency QA."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.chunk_stitching import ChunkBoundaryQualityChecker
from src.tie.literary_semantic_qa import LiterarySemanticQAChecker
from src.tie.quality_gate import QualityGate
from src.tie.turkish_fluency_qa import TurkishFluencyAnomalyChecker


CASES = [
    {
        "id": "flatboat_mistranslation",
        "source": "He was taken on for a flatboat.",
        "target": "Bir düzenbaz için alındı.",
        "chunk": "He was taken on for a flatboat.",
    },
    {
        "id": "schoolmaster_risk",
        "source": "His father has been a schoolmaster.",
        "target": "Babası okul müdürü olmuştu.",
        "chunk": "His father has been a schoolmaster.",
    },
    {
        "id": "scullery_fire_risk",
        "source": "He stokes the scullery fire.",
        "target": "Bulaşık ocağını besler.",
        "chunk": "He stokes the scullery fire.",
    },
    {
        "id": "dipper_context",
        "source": "The Dipper stove.",
        "target": "Kepçe devrildi.",
        "chunk": "The Dipper stove.",
    },
    {
        "id": "full_house_risk",
        "source": "The Reverend Green preached to a full house.",
        "target": "Rahip Green dolu salonda oynuyordu.",
        "chunk": "The Reverend Green preached to a full house.",
    },
    {
        "id": "lowercase_chunk_continuation",
        "source": "he feels mankind itself vindicated.",
        "target": "kendini haklı çıkarmıştı.",
        "chunk": "itself vindicated.",
    },
    {
        "id": "broken_turkish_ne_ne_de",
        "source": "He can neither read nor write.",
        "target": "Ne okuyup yazma bilir ne de.",
        "chunk": "He can neither read nor write.",
    },
    {
        "id": "typo_fittik",
        "source": "He was seven foot tall.",
        "target": "Neredeyse yedi fittik boyundaydı.",
        "chunk": "He was seven foot tall.",
    },
    {
        "id": "double_spaces",
        "source": "His face remained oddly innocent.",
        "target": "Yüzü tuhaf  masumdur.",
        "chunk": "His face remained oddly innocent.",
    },
    {
        "id": "clean_literary_sentence",
        "source": "The boy crouches by the fire and watches him.",
        "target": "Çocuk ateşin yanında çömelir ve onu izler.",
        "chunk": "The boy crouches by the fire and watches him.",
    },
]


def main() -> None:
    output = PROJECT_ROOT / "outputs" / "literary_semantic_qa_diagnostics_report.md"
    semantic_checker = LiterarySemanticQAChecker()
    fluency_checker = TurkishFluencyAnomalyChecker()
    boundary_checker = ChunkBoundaryQualityChecker()
    quality_gate = QualityGate()

    lines = [
        "# Literary Semantic QA Diagnostics",
        "",
        "## Summary",
        "",
        "Deterministic diagnostics for literary semantic risk, Turkish fluency anomalies, and chunk boundary risks.",
        "",
        "## Cases",
        "",
    ]

    for case in CASES:
        semantic = semantic_checker.check(case["source"], case["target"])
        fluency = fluency_checker.check(case["target"])
        boundary = boundary_checker.check({"chunk_id": case["id"], "text": case["chunk"]})
        gate = quality_gate.evaluate(
            source_quality={"recommendation": "accept"},
            foreign_residue={"residues": []},
            boundary_flags=boundary["flags"],
            semantic_flags=semantic["flags"],
            fluency_flags=fluency["flags"],
        )
        lines.extend(
            [
                f"### {case['id']}",
                "",
                "**Source**",
                "",
                "```text",
                case["source"],
                "```",
                "",
                "**Target**",
                "",
                "```text",
                case["target"],
                "```",
                "",
                f"- Semantic flags: `{semantic['flags']}`",
                f"- Fluency flags: `{fluency['flags']}`",
                f"- Chunk boundary flags: `{boundary['flags']}`",
                f"- Recommendation: `{gate['recommendation']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Limitations",
            "",
            "This is deterministic QA, not proof of semantic correctness.",
            "Human literary review is still required.",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Literary semantic QA diagnostics written to: {output}")


if __name__ == "__main__":
    main()
