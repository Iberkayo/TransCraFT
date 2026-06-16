"""TIE v0.9.1 — Translation Error Taxonomy.

Provides normalization, counting, severity summarization, and
next-fix recommendation based on human review error tags.
"""

from collections import Counter
from typing import Any, Dict, List


ALLOWED_TAGS = {
    "meaning_loss",
    "added_meaning",
    "omitted_meaning",
    "translationese",
    "unnatural_turkish",
    "over_editing",
    "under_editing",
    "wrong_register",
    "terminology_issue",
    "protected_term_loss",
    "number_date_issue",
    "pronoun_overuse",
    "heavy_relative_clause",
    "noun_stack_literalness",
    "passive_stiffness",
    "idiom_literalness",
    "style_loss",
    "rhythm_loss",
    "too_verbose",
    "too_flat",
    "no_clear_difference",
}

TAG_TO_CATEGORY = {
    "translationese": "naturalness",
    "unnatural_turkish": "naturalness",
    "pronoun_overuse": "naturalness",
    "heavy_relative_clause": "structural_risk",
    "noun_stack_literalness": "structural_risk",
    "passive_stiffness": "structural_risk",
    "meaning_loss": "accuracy",
    "added_meaning": "accuracy",
    "omitted_meaning": "accuracy",
    "terminology_issue": "protected_terms",
    "protected_term_loss": "protected_terms",
    "number_date_issue": "protected_terms",
    "style_loss": "style",
    "rhythm_loss": "style",
    "too_flat": "style",
    "over_editing": "safety",
    "too_verbose": "safety",
    "under_editing": "safety",
    "wrong_register": "register",
    "idiom_literalness": "idiom",
    "no_clear_difference": "other",
}

CATEGORY_TO_FIX = {
    "naturalness": "Improve target naturalness pass and revision checklist detection.",
    "structural_risk": "Strengthen structural risk planning in strategy planner.",
    "accuracy": "Strengthen accuracy critic and source-grounded review.",
    "protected_terms": "Strengthen protected term safety checks.",
    "style": "Improve literary style preservation in v0.3.1 style critic.",
    "safety": "Make final naturalness pass more conservative; avoid over-editing.",
    "register": "Improve register detection in strategy planner and revision checklist.",
    "idiom": "Improve idiom detection in structural risk detector.",
    "other": "No clear fix target; consider more aggressive differentiation.",
}


class TranslationErrorTaxonomy:
    """Normalize and validate error tags against the v0.9.1 taxonomy."""

    @staticmethod
    def normalize_error_tags(tags: List[str]) -> List[str]:
        """Return only recognized, normalized tags, ignoring unknown ones."""
        return [tag.strip().casefold() for tag in tags if tag.strip().casefold() in ALLOWED_TAGS]

    @staticmethod
    def validate_error_tags(tags: List[str]) -> List[str]:
        """Return a list of tags that are NOT in the allowed taxonomy."""
        return [tag.strip().casefold() for tag in tags if tag.strip().casefold() not in ALLOWED_TAGS]


class ErrorTaxonomyAnalyzer:
    """Analyze human review results to find patterns and recommend fixes."""

    @staticmethod
    def count_error_tags(reviews: List[Dict[str, Any]]) -> Dict[str, int]:
        """Return frequency of each error tag across all reviews."""
        counts: Counter = Counter()
        for review in reviews:
            tags = review.get("error_tags", [])
            normalized = TranslationErrorTaxonomy.normalize_error_tags(tags)
            counts.update(normalized)
        return dict(counts.most_common())

    @staticmethod
    def summarize_severity(reviews: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count reviews by severity level."""
        summary: Counter = Counter()
        for review in reviews:
            severity = review.get("severity", "none")
            summary[severity] += 1
        return dict(summary)

    @staticmethod
    def recommend_next_fixes(error_counts: Dict[str, int]) -> List[str]:
        """Map top error categories to recommended next fixes."""
        category_scores: Counter = Counter()
        for tag, count in error_counts.items():
            category = TAG_TO_CATEGORY.get(tag, "other")
            category_scores[category] += count

        recommendations = []
        for category, _ in category_scores.most_common():
            fix = CATEGORY_TO_FIX.get(category)
            if fix and fix not in recommendations:
                recommendations.append(fix)
        return recommendations[:5]

    @staticmethod
    def summarize_calibration(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Produce a full calibration summary from human review results."""
        if not reviews:
            return {
                "total_reviewed": 0,
                "message": "No real human review results found. This is a template/infrastructure report only.",
            }

        preferred = Counter(r.get("preferred_output", "tie") for r in reviews)
        severity = ErrorTaxonomyAnalyzer.summarize_severity(reviews)
        error_tags = ErrorTaxonomyAnalyzer.count_error_tags(reviews)
        over_edit = sum(1 for r in reviews if r.get("over_editing_detected"))
        protected_issues = sum(1 for r in reviews if r.get("protected_term_issue"))
        recs = ErrorTaxonomyAnalyzer.recommend_next_fixes(error_tags)

        total = len(reviews)
        fc_wins = preferred.get("full_chain", 0)
        return {
            "total_reviewed": total,
            "baseline_wins": preferred.get("baseline", 0),
            "strategy_only_wins": preferred.get("strategy_only", 0),
            "full_chain_wins": fc_wins,
            "ties": preferred.get("tie", 0),
            "cannot_judge": severity.get("cannot_judge", 0),
            "full_chain_over_edit_count": over_edit,
            "protected_term_issue_count": protected_issues,
            "critical_errors": severity.get("critical", 0),
            "major_errors": severity.get("major", 0),
            "minor_errors": severity.get("minor", 0),
            "error_tag_frequency": error_tags,
            "full_chain_win_rate": round(fc_wins / max(1, total), 3),
            "full_chain_harm_rate": round(preferred.get("baseline", 0) / max(1, total), 3),
            "top_error_categories": [CATEGORY_TO_FIX.get(TAG_TO_CATEGORY.get(tag, "other"), "No fix target") for tag in list(error_tags.keys())[:5]],
            "recommendations": recs,
        }