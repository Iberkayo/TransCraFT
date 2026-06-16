"""TIE v0.7 — Human Translator Revision Checklist.

Provides a professional post-translation checklist builder and deterministic evaluator
that mimics how an English-to-Turkish translator would review output before delivery.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


# ------------------------------------------------------------------ #
#  Translationese patterns commonly seen in EN→TR output
# ------------------------------------------------------------------ #

TRANSLATIONESE_PATTERNS = [
    ("neden oldu", "Consider a more natural alternative such as 'yol açtı' or 'soru işaretleri yarattı'."),
    ("merak etmesine neden oldu", "Replace stiff literal transfer with natural phrasing."),
    ("merak etmesine yol açtı", "Replace stiff literal transfer with natural phrasing."),
    ("anlamına gelir", "Often a calque of 'which means'. Use shorter Turkish rephrasing."),
    ("anlamına gelmektedir", "Often a calque of 'which means'. Use shorter Turkish rephrasing."),
    ("buna ek olarak", "Consider 'ayrıca' or omit if the additive relation is already clear."),
    ("bu da", "Often unnecessary literal transfer of 'this also'."),
]

TURKISH_UNNECESSARY_PRONOUNS = {" o ", " onun ", " ona ", " onu ", " onlar ", " onların ", " bunlar ", " bunu ", " bu "}

TURKISH_HEAVY_RELATIVE_MARKERS = [
    r"\w+dığı\s+\w+",
    r"\w+diği\s+\w+",
    r"\w+dığını\s+\w+",
    r"\w+diğini\s+\w+",
    r"\w+dığında\s+\w+",
    r"\w+diğinde\s+\w+",
]

TURKISH_PASSIVE_MARKERS = [
    "tarafından",
    "edilmiştir",
    "edilmektedir",
    "yapılmıştır",
    "yapılmaktadır",
    "görülmüştür",
]


# ------------------------------------------------------------------ #
#  Checklist Builder
# ------------------------------------------------------------------ #

class RevisionChecklistBuilder:
    """Build a structured professional translator revision checklist."""

    def build(
        self,
        source_text: str,
        genre: str = "general",
        source_language: str = "en_US",
        target_language: str = "tr_TR",
        translation_strategy: Optional[Dict[str, Any]] = None,
        structural_risks: Optional[List[Dict[str, str]]] = None,
        language_profile: Optional[Dict[str, Any]] = None,
        style_contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []

        # 1. Meaning Preservation (always)
        checks.extend(self._meaning_checks())

        # 2. Turkish Naturalness (always)
        checks.extend(self._naturalness_checks())

        # 3. Structural Risk Review (from strategy/risks)
        risks = structural_risks or []
        if translation_strategy:
            risks = risks or translation_strategy.get("structural_risks", [])
        checks.extend(self._structural_risk_checks(risks))

        # 4. Register and Tone
        checks.extend(self._register_tone_checks(genre, style_contract))

        # 5. Terminology and Memory
        checks.extend(self._terminology_checks())

        # 6. Style and Rhythm
        checks.extend(self._style_rhythm_checks(genre))

        return {
            "checklist_id": f"revision_{source_language}_{target_language}_{genre}",
            "source_language": source_language,
            "target_language": target_language,
            "genre": genre,
            "checks": checks,
        }

    def _meaning_checks(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "meaning_preservation",
                "category": "accuracy",
                "question": "Is the source meaning preserved without omission or addition?",
                "severity": "critical",
            },
            {
                "id": "no_hallucination",
                "category": "accuracy",
                "question": "Are there no invented details, explanations, or facts not present in the source?",
                "severity": "critical",
            },
            {
                "id": "correct_actor_action",
                "category": "accuracy",
                "question": "Are actors, actions, and objects correctly preserved?",
                "severity": "medium",
            },
            {
                "id": "implied_meaning_preserved",
                "category": "accuracy",
                "question": "Is implied or non-literal meaning preserved appropriately?",
                "severity": "medium",
            },
        ]

    def _naturalness_checks(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "turkish_naturalness",
                "category": "naturalness",
                "question": "Does the Turkish read naturally without translationese?",
                "severity": "critical",
            },
            {
                "id": "natural_word_order",
                "category": "naturalness",
                "question": "Is the Turkish word order natural, not copied from English?",
                "severity": "medium",
            },
            {
                "id": "no_translationese",
                "category": "naturalness",
                "question": "Are translationese patterns such as 'neden oldu', 'yol açtı', 'anlamına gelir' avoided?",
                "severity": "medium",
            },
            {
                "id": "unnecessary_pronouns",
                "category": "turkish_fluency",
                "question": "Are unnecessary pronouns such as o, onun, bu avoided unless needed for emphasis?",
                "severity": "medium",
            },
        ]

    def _structural_risk_checks(self, risks: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        checks = []
        for risk in risks:
            risk_type = risk.get("risk_type", "")
            if risk_type == "long_relative_clause":
                checks.append({
                    "id": "heavy_relative_clause",
                    "category": "structural_risk",
                    "question": "Did the translation avoid a heavy Turkish -dığı/-diği relative clause chain?",
                    "severity": "medium",
                })
            elif risk_type == "noun_stack":
                checks.append({
                    "id": "noun_stack_unpacked",
                    "category": "structural_risk",
                    "question": "Was the English noun stack unpacked into clear Turkish?",
                    "severity": "medium",
                })
            elif risk_type in {"passive_voice", "double_passive"}:
                checks.append({
                    "id": "passive_naturalness",
                    "category": "structural_risk",
                    "question": "Was passive voice handled naturally for the genre?",
                    "severity": "low",
                })
            elif risk_type == "phrasal_verb":
                checks.append({
                    "id": "phrasal_verb_correct",
                    "category": "structural_risk",
                    "question": "Was the phrasal verb translated by meaning, not by its particles?",
                    "severity": "low",
                })
            elif risk_type == "pronoun_heavy":
                checks.append({
                    "id": "pronoun_reduction",
                    "category": "structural_risk",
                    "question": "Were unnecessary pronouns reduced while preserving reference clarity?",
                    "severity": "medium",
                })
            elif risk_type == "preposition_heavy":
                checks.append({
                    "id": "preposition_unpacked",
                    "category": "structural_risk",
                    "question": "Were prepositional chains reordered into natural Turkish case structure?",
                    "severity": "medium",
                })
            elif risk_type == "literary_fragment":
                checks.append({
                    "id": "literary_fragment_preserved",
                    "category": "structural_risk",
                    "question": "Were intentional fragments and rhythm preserved?",
                    "severity": "medium",
                })
            elif risk_type == "business_translationese_risk":
                checks.append({
                    "id": "business_translationese",
                    "category": "structural_risk",
                    "question": "Was stiff business translationese avoided?",
                    "severity": "medium",
                })
            elif risk_type == "academic_nominalization":
                checks.append({
                    "id": "academic_nominal_clarity",
                    "category": "structural_risk",
                    "question": "Was dense nominalization made readable in Turkish?",
                    "severity": "medium",
                })
        return checks

    def _register_tone_checks(self, genre: str, style_contract: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        checks = [
            {
                "id": "register_consistency",
                "category": "register",
                "question": "Is the register (formal/informal) consistent and appropriate for the genre?",
                "severity": "medium",
            },
            {
                "id": "tone_preserved",
                "category": "register",
                "question": "Is the tone preserved without over-formalization or over-modernization?",
                "severity": "medium",
            },
        ]
        if genre == "literary":
            checks.append({
                "id": "character_voice_preserved",
                "category": "register",
                "question": "Is character voice preserved where applicable?",
                "severity": "medium",
            })
        return checks

    def _terminology_checks(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "glossary_respected",
                "category": "terminology",
                "question": "Are glossary terms used exactly as specified?",
                "severity": "medium",
            },
            {
                "id": "terminology_consistency",
                "category": "terminology",
                "question": "Is terminology consistent within the text?",
                "severity": "low",
            },
        ]

    def _style_rhythm_checks(self, genre: str) -> List[Dict[str, Any]]:
        checks = []
        if genre == "literary":
            checks.extend([
                {
                    "id": "rhythm_preserved",
                    "category": "style",
                    "question": "Is literary rhythm and sentence flow preserved?",
                    "severity": "medium",
                },
                {
                    "id": "fragment_preserved",
                    "category": "style",
                    "question": "Are intentional fragments preserved without over-explaining?",
                    "severity": "medium",
                },
                {
                    "id": "no_over_smoothing",
                    "category": "style",
                    "question": "Was over-smoothing of literary voice avoided?",
                    "severity": "medium",
                },
            ])
        elif genre in {"technical", "academic"}:
            checks.extend([
                {
                    "id": "clarity_preserved",
                    "category": "style",
                    "question": "Is technical/academic clarity preserved?",
                    "severity": "critical",
                },
                {
                    "id": "no_ambiguous_paraphrase",
                    "category": "style",
                    "question": "Are terms and claims precise without ambiguous paraphrase?",
                    "severity": "medium",
                },
                {
                    "id": "no_literary_flourish",
                    "category": "style",
                    "question": "Was unnecessary literary flourish avoided in technical text?",
                    "severity": "low",
                },
            ])
        return checks


# ------------------------------------------------------------------ #
#  Evaluator (deterministic / heuristic)
# ------------------------------------------------------------------ #

class RevisionChecklistEvaluator:
    """Evaluate translated output against a revision checklist using deterministic heuristics."""

    def __init__(self, enable_llm: bool = False, llm_model: Optional[Any] = None):
        self.enable_llm = enable_llm
        self._llm = llm_model

    def evaluate(
        self,
        checklist: Dict[str, Any],
        translated_text: str,
        source_text: str = "",
    ) -> Dict[str, Any]:
        checks = checklist.get("checks", [])
        evaluated: List[Dict[str, Any]] = []

        for check in checks:
            result = self._evaluate_one(check, translated_text, source_text)
            evaluated.append(result)

        # Aggregate
        critical_fails = sum(1 for c in evaluated if not c["passed"] and c["severity"] == "critical")
        warnings = sum(1 for c in evaluated if not c["passed"] and c["severity"] != "critical")
        passed = sum(1 for c in evaluated if c["passed"])
        failed = len(evaluated) - passed
        overall = round(5.0 - (critical_fails * 0.8) - (warnings * 0.3), 1)
        overall = max(0.5, min(5.0, overall))

        recommendations = self._generate_recommendations(evaluated)

        return {
            "overall_revision_score": overall,
            "critical_failures": critical_fails,
            "warnings": warnings,
            "passed_checks": passed,
            "failed_checks": failed,
            "checks": evaluated,
            "revision_recommendations": recommendations,
        }

    def _evaluate_one(self, check: Dict[str, Any], translated_text: str, source_text: str) -> Dict[str, Any]:
        check_id = check.get("id", "")
        severity = check.get("severity", "medium")
        lower = f" {translated_text.casefold()} "

        # --- Deterministic heuristics ---
        if check_id == "no_translationese":
            hits = []
            for pattern, suggestion in TRANSLATIONESE_PATTERNS:
                if pattern in lower:
                    hits.append(pattern)
            if hits:
                return self._fail(check_id, severity, f"Translationese detected: {', '.join(hits)}.")
            return self._pass(check_id, severity, "No obvious translationese pattern detected.")

        if check_id == "unnecessary_pronouns":
            excessive = []
            for pronoun in TURKISH_UNNECESSARY_PRONOUNS:
                count = lower.count(pronoun)
                if count >= 2:
                    excessive.append(pronoun.strip())
            if excessive:
                return self._fail(check_id, severity, f"Excessive pronouns: {', '.join(excessive)}.")
            return self._pass(check_id, severity, "Pronoun usage appears balanced.")

        if check_id == "heavy_relative_clause":
            for pattern in TURKISH_HEAVY_RELATIVE_MARKERS:
                if re.search(pattern, translated_text, re.IGNORECASE):
                    return self._fail(check_id, severity, f"Heavy -dığı/-diği relative chain detected.")
            return self._pass(check_id, severity, "No heavy relative clause chain detected.")

        if check_id == "passive_naturalness":
            passive_count = 0
            for marker in TURKISH_PASSIVE_MARKERS:
                if marker in lower:
                    passive_count += 1
            if passive_count >= 3:
                return self._fail(check_id, severity, f"Excessive passive markers: {passive_count} found.")
            return self._pass(check_id, severity, "Passive voice usage within acceptable range.")

        if check_id == "noun_stack_unpacked":
            # Detect long compound words typical of un-unpacked Turkish noun stacks
            long_words = [w for w in translated_text.split() if len(w) > 24]
            if long_words:
                return self._fail(
                    check_id, severity,
                    f"Possible un-unpacked noun stack: {self._truncate(long_words[0], 40)}"
                )
            return self._pass(check_id, severity, "Noun complexity appears manageable.")

        if check_id in {"no_over_smoothing", "no_literary_flourish"}:
            return self._pass(check_id, severity, "No over-smoothing pattern flagged by heuristics.")

        if check_id == "no_ambiguous_paraphrase":
            if "belki" in lower and "gibi" in lower:
                return self._fail(check_id, severity, "Hedging words may indicate ambiguous paraphrase.")
            return self._pass(check_id, severity, "No ambiguity markers detected.")

        # --- Default: pass with heuristic note ---
        return self._pass(
            check_id,
            severity,
            "No deterministic heuristic available for this check; passing by default.",
        )

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        return text[:max_len] + ("..." if len(text) > max_len else "")

    def _pass(self, check_id: str, severity: str, evidence: str) -> Dict[str, Any]:
        return {"id": check_id, "passed": True, "severity": severity, "evidence": evidence}

    def _fail(self, check_id: str, severity: str, evidence: str) -> Dict[str, Any]:
        return {"id": check_id, "passed": False, "severity": severity, "evidence": evidence}

    def _generate_recommendations(self, evaluated: List[Dict[str, Any]]) -> List[str]:
        recs = []
        for check in evaluated:
            if not check["passed"]:
                if "pronoun" in check["id"]:
                    recs.append("Reduce unnecessary pronoun repetition where Turkish verb marking implies the subject.")
                elif "translationese" in check["id"]:
                    recs.append("Replace translationese patterns with natural Turkish wording.")
                elif "relative_clause" in check["id"]:
                    recs.append("Split the -dığı/-diği chain into shorter Turkish clauses.")
                elif "passive" in check["id"]:
                    recs.append("Reduce passive stacking; use active voice where natural Turkish prefers it.")
                elif "noun_stack" in check["id"]:
                    recs.append("Unpack the English noun stack into a clear Turkish explanatory phrase.")
                else:
                    recs.append(f"Review check '{check['id']}': {check.get('evidence', 'issue detected')}")
        return recs[:10]


# ------------------------------------------------------------------ #
#  Helper: Build checklist and evaluate in one call (for workflow)
# ------------------------------------------------------------------ #

def build_and_evaluate(
    source_text: str,
    translated_text: str,
    genre: str = "general",
    source_language: str = "en_US",
    target_language: str = "tr_TR",
    translation_strategy: Optional[Dict[str, Any]] = None,
    structural_risks: Optional[List[Dict[str, str]]] = None,
    language_profile: Optional[Dict[str, Any]] = None,
    style_contract: Optional[Dict[str, Any]] = None,
    enable_llm: bool = False,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Convenience: build checklist and evaluate in one call."""
    builder = RevisionChecklistBuilder()
    evaluator = RevisionChecklistEvaluator(enable_llm=enable_llm)
    checklist = builder.build(
        source_text=source_text,
        genre=genre,
        source_language=source_language,
        target_language=target_language,
        translation_strategy=translation_strategy,
        structural_risks=structural_risks,
        language_profile=language_profile,
        style_contract=style_contract,
    )
    evaluation = evaluator.evaluate(checklist, translated_text, source_text)
    return checklist, evaluation