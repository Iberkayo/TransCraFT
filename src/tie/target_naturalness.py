"""TIE v0.8 — Target-Only Turkish Naturalness Pass.

Reviews only the Turkish output for final readability polish.
Conservative rewrites only. Better unchanged than wrong.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


# ------------------------------------------------------------------ #
#  Conservative high-confidence Turkish naturalness rewrites
# ------------------------------------------------------------------ #

# Only rewrite when the pattern is clearly translationese and the
# replacement is a known-safe natural Turkish alternative.
SAFE_REWRITES: List[Tuple[str, str, str]] = [
    ("merak etmesine neden oldu", "soru i\u015faretleri yaratt\u0131", "stiff literal 'wondering caused'"),
    ("merak etmesine yol a\u00e7t\u0131", "soru i\u015faretleri yaratt\u0131", "stiff literal 'wondering led to'"),
    ("anlam\u0131na gelir", "demektir", "calque of 'which means'"),
    ("anlam\u0131na gelmektedir", "demektir", "calque of 'which means'"),
    ("buna ek olarak", "ayr\u0131ca", "unnecessary additive phrasing"),
    ("bir \u015fekilde", "", "weakened literal filler (context-dependent)"),
]

# Patterns that trigger a recommendation but NOT automatic rewrite
# because context may change the appropriateness.
RECOMMEND_ONLY_PATTERNS: List[Tuple[str, str]] = [
    ("neden oldu", "may be stiff translationese; consider a more natural phrasing"),
    ("yol a\u00e7t\u0131", "may be stiff translationese; consider a more natural phrasing"),
    ("bu da", "often unnecessary literal transfer of 'this also'"),
    (" olan ", "chain of 'olan' may be heavy; consider rephrasing"),
    (" eden ", "chain of 'eden' may be heavy; consider rephrasing"),
    (" yapan ", "chain of 'yapan' may be heavy; consider rephrasing"),
]

TURKISH_PRONOUNS = {" o ", " onun ", " ona ", " onu ", " onlar ", " onlar\u0131n ", " bunlar ", " bunu "}

# Numeric / protected patterns that must not be changed
PROTECTED_PATTERNS = [
    r"\d+[\.,]?\d*\s*(%|y\u00fczde|TL|USD|EUR|GBP|bin|milyon|milyar)?",
    r"\d{1,2}\s+(Ocak|\u015eubat|Mart|Nisan|May\u0131s|Haziran|Temmuz|A\u011fustos|Eyl\u00fcl|Ekim|Kas\u0131m|Aral\u0131k)\s+\d{4}",
    r"\d{1,2}[\/\.]\d{1,2}[\/\.]\d{2,4}",
    r"\d{1,2}:\d{2}",
]


class TargetOnlyNaturalnessPass:
    """Apply conservative target-only Turkish polish rewrites."""

    def apply(
        self,
        turkish_text: str,
        genre: Optional[str] = None,
        target_language: str = "tr_TR",
        translation_strategy: Optional[Dict[str, Any]] = None,
        revision_evaluation: Optional[Dict[str, Any]] = None,
        revision_recommendations: Optional[List[str]] = None,
        language_profile: Optional[Dict[str, Any]] = None,
        glossary_terms: Optional[List[str]] = None,
        protected_terms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not turkish_text or not turkish_text.strip():
            return self._empty_result(turkish_text)

        if not target_language.startswith("tr"):
            return self._unchanged_result(turkish_text, "non-Turkish target language, pass skipped")

        original = turkish_text
        protected = set(protected_terms or [])
        if glossary_terms:
            protected.update(glossary_terms)

        # Extract numbers/dates for protection
        extracted_protected = self._extract_protected(turkish_text)
        protected.update(extracted_protected)

        before_score = self._naturalness_score(turkish_text)
        before_translationese = self._count_translationese(turkish_text)
        before_pronouns = self._count_pronouns(turkish_text)

        # Apply safe rewrites
        revised = turkish_text
        changes: List[Dict[str, str]] = []
        for pattern, replacement, reason in SAFE_REWRITES:
            if pattern in revised:
                revised = revised.replace(pattern, replacement)
                changes.append({
                    "type": "translationese_reduction",
                    "before": pattern,
                    "after": replacement,
                    "reason": reason,
                })

        # Collect recommendations for patterns we did NOT auto-rewrite
        recommendations: List[str] = list(revision_recommendations or [])
        for pattern, suggestion in RECOMMEND_ONLY_PATTERNS:
            if pattern in revised:
                recommendations.append(f"{pattern}: {suggestion}")

        # Safety checks
        protected_lost = self._check_protected_lost(original, revised, protected)
        length_delta = abs(len(revised) - len(original)) / max(1, len(original))
        empty_output = not revised.strip()
        risk_flags: List[str] = []

        if protected_lost:
            risk_flags.append(f"Protected terms lost: {', '.join(protected_lost[:5])}")
        if length_delta > 0.35:
            risk_flags.append(f"Large length change: {length_delta:.1%}")
        if empty_output:
            risk_flags.append("Output is empty")

        # Genre safety
        if genre == "literary" and any(c["type"] == "translationese_reduction" for c in changes):
            # Re-validate literary fragments were not over-smoothed
            original_fragments = len([s for s in re.split(r"[.!?]+", original) if len(s.split()) <= 3])
            revised_fragments = len([s for s in re.split(r"[.!?]+", revised) if len(s.split()) <= 3])
            if revised_fragments < original_fragments:
                risk_flags.append("Literary fragments may have been over-smoothed")

        after_score = self._naturalness_score(revised)
        after_translationese = self._count_translationese(revised)
        after_pronouns = self._count_pronouns(revised)

        # Recommendation decision
        if empty_output or protected_lost:
            recommendation = "reject"
        elif length_delta > 0.35:
            recommendation = "review"
        elif risk_flags:
            recommendation = "review"
        elif changes:
            recommendation = "accept"
        else:
            recommendation = "accept"

        return {
            "original_text": original,
            "revised_text": revised,
            "changed": len(changes) > 0,
            "naturalness_score_before": before_score,
            "naturalness_score_after": after_score,
            "translationese_patterns_before": before_translationese,
            "translationese_patterns_after": after_translationese,
            "pronoun_count_before": before_pronouns,
            "pronoun_count_after": after_pronouns,
            "protected_terms_preserved": not protected_lost,
            "risk_flags": risk_flags,
            "changes": changes,
            "recommendation": recommendation,
        }

    def _extract_protected(self, text: str) -> List[str]:
        protected = []
        for pattern in PROTECTED_PATTERNS:
            for match in re.findall(pattern, text, re.IGNORECASE):
                if isinstance(match, tuple):
                    protected.extend(m for m in match if m)
                else:
                    protected.append(match)
        return list(set(str(p) for p in protected if p))

    def _check_protected_lost(self, original: str, revised: str, protected: set) -> List[str]:
        lost = []
        for term in protected:
            if term and term in original and term not in revised:
                lost.append(term)
        return lost

    def _count_translationese(self, text: str) -> int:
        lower = f" {text.casefold()} "
        count = 0
        for pattern, _, _ in SAFE_REWRITES:
            if pattern in lower:
                count += 1
        for pattern, _ in RECOMMEND_ONLY_PATTERNS:
            if pattern in lower:
                count += 1
        return count

    def _count_pronouns(self, text: str) -> int:
        lower = f" {text.casefold()} "
        return sum(lower.count(p) for p in TURKISH_PRONOUNS if p in lower)

    def _naturalness_score(self, text: str) -> float:
        t_count = self._count_translationese(text)
        p_count = self._count_pronouns(text)
        # Check for "olan/eden/yapan" chain density
        chain_count = len(re.findall(r"\b(olan|eden|yapan)\b", text, re.IGNORECASE))
        raw = 5.0 - (t_count * 0.4) - (min(p_count, 8) * 0.2) - (min(chain_count, 6) * 0.15)
        return round(max(0.5, min(5.0, raw)), 1)

    def _empty_result(self, text: str) -> Dict[str, Any]:
        return {
            "original_text": text,
            "revised_text": text,
            "changed": False,
            "naturalness_score_before": 0.0,
            "naturalness_score_after": 0.0,
            "translationese_patterns_before": 0,
            "translationese_patterns_after": 0,
            "pronoun_count_before": 0,
            "pronoun_count_after": 0,
            "protected_terms_preserved": True,
            "risk_flags": ["Empty input text"],
            "changes": [],
            "recommendation": "reject",
        }

    def _unchanged_result(self, text: str, reason: str) -> Dict[str, Any]:
        return {
            "original_text": text,
            "revised_text": text,
            "changed": False,
            "naturalness_score_before": 0.0,
            "naturalness_score_after": 0.0,
            "translationese_patterns_before": 0,
            "translationese_patterns_after": 0,
            "pronoun_count_before": 0,
            "pronoun_count_after": 0,
            "protected_terms_preserved": True,
            "risk_flags": [reason],
            "changes": [],
            "recommendation": "accept",
        }


class TargetNaturalnessEvaluator:
    """Evaluate whether the naturalness pass improved quality without harming correctness."""

    def evaluate(
        self,
        result: Dict[str, Any],
        protected_terms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        protected = set(protected_terms or [])
        rec = result.get("recommendation", "review")
        changed = result.get("changed", False)
        score_before = result.get("naturalness_score_before", 0)
        score_after = result.get("naturalness_score_after", 0)
        risk_flags = result.get("risk_flags", [])
        protected_preserved = result.get("protected_terms_preserved", True)

        improved = score_after > score_before
        worsened = score_after < score_before
        safe = rec == "accept" and protected_preserved and not risk_flags

        return {
            "improved_naturalness": improved,
            "worsened_naturalness": worsened,
            "score_change": round(score_after - score_before, 1),
            "safe_to_apply": safe,
            "protected_terms_preserved": protected_preserved,
            "risk_flags": risk_flags,
            "verdict": "apply" if safe else ("review" if not risk_flags else "reject"),
        }