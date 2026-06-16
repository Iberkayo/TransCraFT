"""Apply accepted suggestions from suggested edits file to the translated output."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tie.literary_feedback import (
    parse_reviewer_decisions_from_suggested_edits,
    write_edited_translation_file,
)

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TRANSLATION = OUTPUTS_DIR / "blood_meridian_first5_translation_tr.md"
SUGGESTED = OUTPUTS_DIR / "blood_meridian_first5_suggested_edits.md"
EDITED = OUTPUTS_DIR / "blood_meridian_first5_translation_tr_edited.md"
REPORT = OUTPUTS_DIR / "blood_meridian_first5_accepted_edits_report.md"


def main() -> None:
    if not SUGGESTED.exists():
        print("No suggested edits file found. Run translate_blood_meridian_first5_pages.py first.")
        return
    if not TRANSLATION.exists():
        print("No translation file found. Run translate_blood_meridian_first5_pages.py first.")
        return

    suggested_text = SUGGESTED.read_text(encoding="utf-8")
    decisions = parse_reviewer_decisions_from_suggested_edits(suggested_text)
    accepted = [d for d in decisions if d.get("decision") == "accept"]

    print(f"Accepted suggestions found: {len(accepted)}")

    if not accepted:
        print("No accepted suggestions to apply.")
        return

    result = write_edited_translation_file(TRANSLATION, EDITED, accepted)
    print(f"Applied: {result['applied_count']}")
    print(f"Skipped: {result['skipped_count']}")

    # Write report
    lines = ["# Accepted Edits Report", ""]
    lines.append("## Applied")
    for a in result["applied"]:
        lines.append(f"- **{a['correction_id']}**: `{a['before']}` → `{a['after']}`")
    if result["skipped"]:
        lines.append("")
        lines.append("## Skipped")
        for s in result["skipped"]:
            lines.append(f"- **{s.get('correction_id')}**: {s.get('reason')}")
    lines.append("")
    lines.append(f"- Edited translation: `{EDITED}`")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Edited translation: {EDITED}")
    if result["applied_count"] > 0:
        print("Review the edited translation at the path above. The original file was NOT overwritten.")


if __name__ == "__main__":
    main()