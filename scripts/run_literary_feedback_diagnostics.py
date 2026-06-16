"""v0.9.4 — Literary feedback diagnostics."""
import argparse, json, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.literary_feedback import LiteraryCorrectionFeedbackStore, LiterarySuggestionGenerator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs" / "literary_feedback_diagnostics_report.md")
    args = parser.parse_args()

    store = LiteraryCorrectionFeedbackStore()
    gen = LiterarySuggestionGenerator(store)

    # Test with a sample translated text containing known issues
    sample = "babası aslında bir okul müdürüymüş. Bulaşıkhanede ateşi karıştırıyor. Leonidlermiş adları. Kepçe devrilmişti. o kan gömleğinden akarken bara yaslanır. dolu salonda oynuyordu. yedi fittik boyundaydı."
    result = gen.generate_suggestions(translated_text=sample)

    lines = [
        "# Literary Feedback Diagnostics Report",
        "",
        "## 1. Executive Summary",
        "",
        f"Correction dataset loaded: {len(store.corrections)} entries",
        f"Critical corrections: {store.critical_count()}",
        f"Major corrections: {store.major_count()}",
        f"Minor corrections: {store.minor_count()}",
        f"Suggestions generated from sample: {result['suggestion_count']}",
        f"Critical suggestions: {result['critical_suggestions']}",
        f"Recommendation: {result['recommendation']}",
        "",
        "This is human correction feedback infrastructure, not automatic proof of literary quality.",
        "Suggestions require human review before application.",
        "",
        "## 2. Example Source-Target Pairs",
        "",
        "| ID | Source Phrase | Current Target | Suggested Target | Severity |",
        "| -- | ------------- | ------------- | --------------- | -------- |",
    ]

    for c in store.corrections[:5]:
        lines.append(f"| {c['id']} | {c['source_phrase']} | {c['current_target']} | {c['suggested_target']} | {c['severity']} |")

    lines.extend([
        "",
        "## 3. Generated Suggestions from Sample Text",
        "",
    ])
    for s in result["suggestions"]:
        lines.append(f"- **{s['correction_id']}**: `{s['current_target']}` → `{s['suggested_target']}` [{s['severity']}] — {s['reason']}")

    lines.extend([
        "",
        "## 4. Recommendation",
        "",
        f"Recommendation: {result['recommendation']}",
        "",
        "## 5. Limitations",
        "",
        "This is human correction feedback infrastructure, not automatic proof of literary quality.",
        "Suggestions require human review before application.",
        "Correction dataset is based on Berkay's review of first 5 pages only.",
        "Not all suggestions may apply to different contexts of the same source phrase.",
    ])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {args.output}")
    print(f"Suggestions: {result['suggestion_count']}, Recommendation: {result['recommendation']}")


if __name__ == "__main__":
    main()