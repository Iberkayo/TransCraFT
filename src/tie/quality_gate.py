"""Deterministic quality gate for TIE QA layers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


Flag = Dict[str, Any]


class QualityGate:
    """Combine QA flags into accept/review/reject."""

    def evaluate(
        self,
        source_quality: Optional[Dict[str, Any]] = None,
        foreign_residue: Optional[Dict[str, Any]] = None,
        boundary_flags: Optional[Iterable[Flag]] = None,
        semantic_flags: Optional[Iterable[Flag]] = None,
        fluency_flags: Optional[Iterable[Flag]] = None,
    ) -> Dict[str, Any]:
        critical_flags: List[Flag] = []
        major_flags: List[Flag] = []
        minor_flags: List[Flag] = []
        reject = False

        if source_quality and source_quality.get("recommendation") == "reject":
            flag = {
                "type": "source_extraction_reject",
                "severity": "critical",
                "recommendation": "re-extract source before translation",
            }
            critical_flags.append(flag)
            reject = True

        for residue in (foreign_residue or {}).get("residues", []):
            flag = dict(residue)
            if flag.get("severity") == "critical":
                critical_flags.append(flag)
                reject = True
            else:
                major_flags.append(flag)

        for flag in list(boundary_flags or []) + list(semantic_flags or []) + list(fluency_flags or []):
            severity = flag.get("severity", "minor")
            if severity == "critical":
                critical_flags.append(flag)
            elif severity == "major":
                major_flags.append(flag)
            else:
                minor_flags.append(flag)

        if reject:
            recommendation = "reject"
        elif critical_flags or major_flags:
            recommendation = "review"
        elif minor_flags:
            recommendation = "review"
        else:
            recommendation = "accept"

        return {
            "recommendation": recommendation,
            "critical_flags": critical_flags,
            "major_flags": major_flags,
            "minor_flags": minor_flags,
        }
