from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.angles.models import PRAngle
from apps.opportunities.models import Opportunity
from apps.scoring.models import OpportunityScore

from .models import StoryStrengtheningAnalysis, StoryStrengtheningRecommendation


@dataclass(frozen=True)
class Weakness:
    title: str
    weakness: str
    affected_dimension: str
    severity: str
    explanation: str
    recommendation: str
    required_information: list[str]
    required_evidence: list[str]
    expected_benefit: str
    source_factors: list[str]
    angle: PRAngle | None = None


def _dimension(score: OpportunityScore, name: str) -> dict:
    return (score.metadata or {}).get("dimensions", {}).get(name, {})


def _missing(dimension: dict, label: str) -> bool:
    return label in dimension.get("missing_information", [])


def _negative(dimension: dict, *factors: str) -> list[str]:
    return [item.get("factor", "") for item in dimension.get("negative_factors", []) if item.get("factor") in factors]


def identify_weaknesses(opportunity: Opportunity, score: OpportunityScore, angles: list[PRAngle]) -> list[Weakness]:
    weaknesses: list[Weakness] = []
    credibility = _dimension(score, "credibility")
    traction_present = opportunity.customer_count is not None
    if traction_present and _missing(credibility, "No independent customer evidence provided"):
        weaknesses.append(Weakness(
            title="Add independent customer evidence",
            weakness="The opportunity contains customer traction claims but no independent customer validation.",
            affected_dimension="Credibility", severity="HIGH",
            explanation="Independent evidence would make the recorded customer traction claim more credible to journalists.",
            recommendation="Provide 2-3 customer case studies with measurable outcomes and at least one customer testimonial.",
            required_information=["Customer names", "Business outcomes", "Customer results"],
            required_evidence=["Customer testimonial", "Customer case study", "Measurable customer results"],
            expected_benefit="Could strengthen the Credibility dimension.",
            source_factors=["customer_count", "No independent customer evidence provided"],
        ))
    if _missing(credibility, "No measurable results provided") and (traction_present or opportunity.revenue_information.strip()):
        weaknesses.append(Weakness(
            title="Add measurable outcomes",
            weakness="The story references traction or business activity without a measurable outcome.",
            affected_dimension="Credibility", severity="MEDIUM",
            explanation="Specific results help journalists assess the significance of the claim.",
            recommendation="Provide a verified customer, revenue, efficiency, adoption, or other business result without estimating or inventing figures.",
            required_information=["Outcome metric", "Time period", "Source of the result"],
            required_evidence=["Customer data", "Official business metric", "Documented result"],
            expected_benefit="Could strengthen the Credibility dimension.",
            source_factors=["No measurable results provided"],
        ))

    timeliness = _dimension(score, "timeliness")
    if _negative(timeliness, "Provided announcement date is old", "No specific timing or current hook is documented"):
        weaknesses.append(Weakness(
            title="Find a legitimate current news hook",
            weakness="The opportunity does not contain a recent or upcoming event that makes the story timely.",
            affected_dimension="Timeliness", severity="MEDIUM",
            explanation="A current, verifiable event gives media a reason to cover the story now.",
            recommendation="Identify a legitimate current milestone, customer announcement, market expansion, funding event, research finding, or other news hook. Do not invent one.",
            required_information=["Event or milestone", "Relevant date", "Why it is current"],
            required_evidence=["Official announcement", "Dated company update", "Verified research or event record"],
            expected_benefit="Could strengthen the Timeliness dimension.",
            source_factors=_negative(timeliness, "Provided announcement date is old", "No specific timing or current hook is documented"),
        ))

    audience = _dimension(score, "audience_interest")
    if _missing(audience, "No target audience provided"):
        weaknesses.append(Weakness(
            title="Clarify the audience relevance",
            weakness="The opportunity does not identify a clear audience or the broader relevance of the story.",
            affected_dimension="Audience Interest", severity="MEDIUM",
            explanation="A defined audience helps the consultant connect the story to relevant media and reader interests.",
            recommendation="Identify the audience most affected by the story and provide a specific industry, customer, or societal outcome that matters to them.",
            required_information=["Primary audience", "Audience need", "Relevant outcome"],
            required_evidence=["Customer or market evidence", "Documented outcome", "Industry context"],
            expected_benefit="Could strengthen the Audience Interest dimension.",
            source_factors=["No target audience provided"],
        ))

    for angle in angles:
        if angle.missing_information:
            weaknesses.append(Weakness(
                title=f"Strengthen the {angle.title} angle",
                weakness=f"The {angle.title} angle still has missing supporting information.",
                affected_dimension="PR Angle", severity="LOW",
                explanation="Filling the angle's recorded information gaps would make its pitch more specific and supportable.",
                recommendation="Review the missing information listed for this angle and add only verified facts or evidence.",
                required_information=list(angle.missing_information),
                required_evidence=list(angle.required_evidence),
                expected_benefit="Could make this PR angle more specific and supportable.",
                source_factors=["angle_missing_information"], angle=angle,
            ))
    return weaknesses


@transaction.atomic
def analyze_story(opportunity: Opportunity, *, score: OpportunityScore, angles: list[PRAngle]) -> StoryStrengtheningAnalysis:
    weaknesses = identify_weaknesses(opportunity, score, angles)
    source_snapshot = {
        "score_id": score.pk,
        "scoring_version": score.scoring_version,
        "dimensions": (score.metadata or {}).get("dimensions", {}),
        "opportunity_id": opportunity.pk,
    }
    analysis = StoryStrengtheningAnalysis.objects.create(opportunity=opportunity, score=score, source_snapshot=source_snapshot)
    StoryStrengtheningRecommendation.objects.bulk_create([
        StoryStrengtheningRecommendation(
            analysis=analysis, opportunity=opportunity, angle=item.angle, title=item.title,
            weakness=item.weakness, affected_dimension=item.affected_dimension, severity=item.severity,
            explanation=item.explanation, recommendation=item.recommendation,
            required_information=item.required_information, required_evidence=item.required_evidence,
            expected_benefit=item.expected_benefit, source_factors=item.source_factors,
        ) for item in weaknesses
    ])
    return analysis
