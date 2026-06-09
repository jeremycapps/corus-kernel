"""Implementation-only interpretation signal heuristics — not Corus declared objects."""

from __future__ import annotations

import re
from typing import Any

ACTION_VERBS = frozenset({
    "drive", "define", "validate", "deliver", "design", "build", "translate",
    "advise", "maintain", "align", "develop", "create", "surface", "identify",
    "enable", "embed", "support", "evaluate", "implement",
})

OUTPUT_NOUNS = frozenset({
    "business case", "business cases", "roi metrics", "implementation strategy",
    "technical design", "technical designs", "account strategy",
    "analytics", "data pipeline", "data pipelines", "value framework",
    "stakeholder map", "workflow", "training session", "workshop", "integration",
    "integrations", "custom solution", "custom solutions", "evidence package",
    "review cadence", "decision package", "value delivery reviews",
    "value delivery review", "business outcomes", "business outcome",
})

ACCOUNTABILITY_LANGUAGE = frozenset({
    "accountable for", "responsible for", "ensure", "own", "ownership",
    "deliver", "validate", "lead", "primary", "trusted advisor",
    "trusted technical advisor", "trusted commercial and technical advisor",
})

STAKEHOLDER_LANGUAGE = frozenset({
    "customers", "executives", "customer engineers", "business stakeholders",
    "regulators", "account team", "sales team", "deployment team",
    "technical contributors", "enterprise stakeholders", "customer sites",
    "senior leaders", "stakeholder landscape", "stakeholder landscapes",
    "customer stakeholder",
})

EVIDENCE_DECISION_LANGUAGE = frozenset({
    "value", "proof", "roi", "risk", "decision", "business outcome",
    "business outcomes", "implementation", "adoption", "approval", "defensible",
    "justification", "assumption", "model", "metric", "metrics",
    "quantifiable roi", "value definition", "value validation",
})

OUTCOME_CONSEQUENCE_LANGUAGE = frozenset({
    "outcome", "outcomes", "impact", "result", "results", "value delivered",
    "materially better off", "growth", "expansion", "mitigation", "approval",
    "risk reduction", "capital confidence", "customer value",
})

OWNERSHIP_MAINTENANCE_NOUNS = frozenset({
    "strategy", "framework", "cadence", "review", "roadmap", "workflow",
    "relationship", "account plan", "account strategy", "evidence package",
    "implementation path", "delivery plan", "living account strategy",
})

TRANSFORMATION_VERBS = frozenset({
    "convert", "map", "surface", "synthesize", "prioritize", "operationalize",
    "embed", "enable", "unblock", "translate", "turn into", "bring to life",
})

COORDINATION_HANDOFF_LANGUAGE = frozenset({
    "collaborate", "work closely with", "align", "navigate", "consensus",
    "stakeholder landscape", "multi-level relationships", "cross-functional",
    "team leadership", "handoff", "unblock", "orchestrator",
    "role for an orchestrator", "stakeholder navigation", "value-driven delivery",
})

NEGATIVE_FILTERS = frozenset({
    "strong communication skills", "competitive salary", "compensation",
    "benefits", "hybrid", "remote", "on-site", "full-time", "full time",
    "low ego", "low ego culture", "culture", "nice to have", "nice-to-have",
    "employment type", "location", "san francisco", "new york", "nyc",
    "equal opportunity", "diversity", "inclusive workplace",
})

SIGNAL_GROUPS: dict[str, frozenset[str]] = {
    "action_verbs": ACTION_VERBS,
    "output_nouns": OUTPUT_NOUNS,
    "accountability_language": ACCOUNTABILITY_LANGUAGE,
    "stakeholder_language": STAKEHOLDER_LANGUAGE,
    "evidence_decision_language": EVIDENCE_DECISION_LANGUAGE,
    "outcome_consequence_language": OUTCOME_CONSEQUENCE_LANGUAGE,
    "ownership_maintenance_nouns": OWNERSHIP_MAINTENANCE_NOUNS,
    "transformation_verbs": TRANSFORMATION_VERBS,
    "coordination_handoff_language": COORDINATION_HANDOFF_LANGUAGE,
}

# Phrase lists for substring matching (multi-word phrases first).
PHRASE_GROUPS: dict[str, tuple[str, ...]] = {
    "action_verbs": tuple(sorted(ACTION_VERBS, key=len, reverse=True)),
    "output_nouns": tuple(sorted(OUTPUT_NOUNS, key=len, reverse=True)),
    "accountability_language": tuple(sorted(ACCOUNTABILITY_LANGUAGE, key=len, reverse=True)),
    "stakeholder_language": tuple(sorted(STAKEHOLDER_LANGUAGE, key=len, reverse=True)),
    "evidence_decision_language": tuple(sorted(EVIDENCE_DECISION_LANGUAGE, key=len, reverse=True)),
    "outcome_consequence_language": tuple(sorted(OUTCOME_CONSEQUENCE_LANGUAGE, key=len, reverse=True)),
    "ownership_maintenance_nouns": tuple(sorted(OWNERSHIP_MAINTENANCE_NOUNS, key=len, reverse=True)),
    "transformation_verbs": tuple(sorted(TRANSFORMATION_VERBS, key=len, reverse=True)),
    "coordination_handoff_language": tuple(
        sorted(COORDINATION_HANDOFF_LANGUAGE, key=len, reverse=True)
    ),
    "negative_filters": tuple(sorted(NEGATIVE_FILTERS, key=len, reverse=True)),
}

CVA_ARTIFACT_PHRASES = frozenset({
    "value definition", "value validation", "quantifiable roi", "business cases",
    "business case", "roi metrics", "value delivery reviews", "value delivery review",
    "business outcomes", "customer stakeholder",
})

FDE_ARTIFACT_PHRASES = frozenset({
    "technical design", "technical designs", "implementation strategy",
    "implementation strategies", "sdk", "api", "integrations", "integration",
    "workflow automation", "custom solution", "custom solutions",
    "custom visualizations", "calculations", "configuration", "reporting",
    "data integration",
})

DIRECTOR_BOUNDARY_PHRASES = frozenset({
    "orchestrator", "role for an orchestrator", "account strategy",
    "living account strategy", "value-driven delivery", "team leadership",
    "stakeholder navigation", "stakeholder landscapes", "high-stakes enterprise",
    "decisive judgment", "unblock",
})

RVO_BOUNDARY_PHRASES = frozenset({
    "asset-level intelligence", "intervention scenarios", "cost-benefit",
    "cost benefit", "auditable analyses", "auditable analysis",
    "regulator-ready", "regulator ready", "what-if", "risk and value",
    "risk spend", "evaluate and implement interventions",
})

DATA_SCIENTIST_FUTURE_PHRASES = frozenset({
    "digital twin", "wildfire risk", "predictive model", "predictive models",
    "data pipeline", "data pipelines", "lidar", "gis", "a/b test", "a/b tests",
    "experiments", "analytics and metrics",
})


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def match_phrases(text: str, phrases: tuple[str, ...] | frozenset[str]) -> list[str]:
    normalized = normalize_text(text)
    matched: list[str] = []
    for phrase in phrases:
        if phrase.lower() in normalized:
            matched.append(phrase)
    return matched


def match_signals(text: str) -> dict[str, list[str]]:
    """Match phrase groups against source text deterministically."""
    result: dict[str, list[str]] = {}
    for group_name, phrases in PHRASE_GROUPS.items():
        if group_name == "negative_filters":
            continue
        found = match_phrases(text, phrases)
        if found:
            result[group_name] = found
    return result


def match_negative_filters(text: str) -> list[str]:
    return match_phrases(text, PHRASE_GROUPS["negative_filters"])


def signal_groups_for_phrases(matched_phrases: list[str], text: str) -> list[str]:
    """Map matched phrases back to signal group names."""
    normalized = normalize_text(text)
    groups: list[str] = []
    for group_name, phrases in PHRASE_GROUPS.items():
        if group_name == "negative_filters":
            continue
        for phrase in phrases:
            if phrase.lower() in normalized and phrase in matched_phrases:
                if group_name not in groups:
                    groups.append(group_name)
                break
    return groups


def artifact_inference_strength(matched_signals: dict[str, list[str]]) -> str:
    """Heuristic confidence from non-negative signal density."""
    score = sum(len(v) for k, v in matched_signals.items() if k != "negative_filters")
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def has_artifact_evidence(matched_signals: dict[str, list[str]], role_phrases: frozenset[str], text: str) -> bool:
    """Require role-specific phrases plus non-filter signal groups."""
    role_hits = match_phrases(text, role_phrases)
    if not role_hits:
        return False
    non_empty_groups = [
        g for g, hits in matched_signals.items() if hits and g != "negative_filters"
    ]
    return len(non_empty_groups) >= 2


def build_source_signal_report(source_id: str, text: str, extraction_status: str) -> dict[str, Any]:
    matched_signals = match_signals(text)
    negatives = match_negative_filters(text)
    return {
        "source_id": source_id,
        "extraction_status": extraction_status,
        "matched_signals": matched_signals,
        "negative_filters_applied": negatives,
    }
