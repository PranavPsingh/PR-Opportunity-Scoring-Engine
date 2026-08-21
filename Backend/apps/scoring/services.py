"""Deterministic, explainable PR opportunity scoring (v1).

No network, LLM, or extraction-confidence calls are made here.  Scores are a
sum of explicit signals, capped at 100; absent data is recorded as missing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Callable

from apps.opportunities.models import Opportunity

SCORING_VERSION = "v1"
WEIGHTS = {"newsworthiness": Decimal("0.25"), "media_appeal": Decimal("0.20"), "timeliness": Decimal("0.20"), "credibility": Decimal("0.15"), "audience_interest": Decimal("0.20")}
HIGH_POTENTIAL_THRESHOLD = 80
MEDIUM_POTENTIAL_THRESHOLD = 60
HIGH_FUNDING_THRESHOLD = Decimal("5000000")
CUSTOMER_TRACTION_THRESHOLD = 100
RECENT_DAYS_THRESHOLD = 30
UPCOMING_DAYS_THRESHOLD = 90

MISSING_INFORMATION_LABELS = {
    "funding_amount": "No funding amount provided",
    "product_launch_status": "No product launch status provided",
    "customer_traction": "No customer count provided",
    "spokesperson_availability": "No named spokesperson availability provided",
    "quantified_media_hook": "No quantified media hook provided",
    "announcement_or_launch_date": "No specific launch or announcement date provided",
    "official_documentation": "No official documentation referenced",
    "investor_confirmation": "No investor confirmation provided",
    "independent_customer_evidence": "No independent customer evidence provided",
    "third_party_validation": "No third-party validation provided",
    "measurable_results": "No measurable results provided",
    "target_audience": "No target audience provided",
}


@dataclass
class Dimension:
    dimension: str
    positive_factors: list[dict] = field(default_factory=list)
    negative_factors: list[dict] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)

    def add(self, factor: str, impact: int) -> None:
        (self.positive_factors if impact > 0 else self.negative_factors).append({"factor": factor, "impact": impact})

    def result(self) -> dict:
        score = max(0, min(100, sum(item["impact"] for item in self.positive_factors + self.negative_factors)))
        return {"dimension": self.dimension, "score": score, "positive_factors": self.positive_factors, "negative_factors": self.negative_factors, "missing_information": self.missing_information, "scoring_signals_used": [*self.positive_factors, *self.negative_factors]}


class ScoringService:
    """Rules are deliberately isolated so future scoring versions can coexist."""
    def __init__(self, opportunity: Opportunity, *, today: date | None = None):
        self.opportunity = opportunity
        self.today = today or date.today()
        self.text_fields = ("title", "description", "story_type", "revenue_information", "geographic_relevance", "target_audience", "supporting_information", "client_briefing")
        self.text = " ".join(filter(None, [opportunity.title, opportunity.description, opportunity.story_type, opportunity.revenue_information, opportunity.geographic_relevance, opportunity.target_audience, opportunity.supporting_information, opportunity.client_briefing])).lower()

    def contains(self, *terms: str) -> bool:
        return any(term in self.text for term in terms)

    @staticmethod
    def json_value(value: object) -> object:
        return str(value) if isinstance(value, (Decimal, date)) else value

    def source_for_factor(self, factor: str) -> tuple[str, object, str]:
        """Return only source data that caused an existing deterministic rule."""
        field_rules = {
            "Funding announcement": ("funding_amount", "The recorded funding amount creates a concrete business-news hook."),
            "Funding meets the significant-round threshold": ("funding_amount", "The recorded funding amount meets the significant-round threshold."),
            "Product launch": ("product_launched", "A confirmed product launch is a discrete news event."),
            "Measurable customer traction": ("customer_count", "The recorded customer count meets the traction threshold."),
            "Founder or spokesperson available for interviews": ("founder_available", "A confirmed spokesperson gives media an interview option."),
            "Announcement date is recent": ("product_launch_date", "The recorded date falls within the recent-event window."),
            "Launch or milestone is upcoming": ("product_launch_date", "The recorded date falls within the upcoming-event window."),
            "Provided announcement date is old": ("product_launch_date", "The recorded date is outside the recent-event window."),
            "A target audience is identified": ("target_audience", "The opportunity identifies who the story is intended to reach."),
            "Meaningful audience reach or traction": ("customer_count", "The recorded customer count meets the traction threshold."),
            "Credible spokesperson is available": ("founder_available", "A confirmed spokesperson can substantiate the story."),
        }
        if factor in field_rules:
            field, reason = field_rules[factor]
            return field, self.json_value(getattr(self.opportunity, field)), reason
        text_rules = {
            "Acquisition or merger event": ("acquisition", "acquired", "merger"), "Partnership announcement": ("partner", "partnership"),
            "Geographic expansion": ("expand", "expansion", "new market"), "Measurable business growth or result": ("growth", "yoy", "arr", "revenue", "%"),
            "Notable milestone, appointment, or research": ("milestone", "appointed", "appointment", "research", "study", "report"),
            "Strong local or regional relevance": ("uae", "dubai", "abu dhabi", "gcc", "saudi", "middle east"),
            "Human or founder story": ("founder", "entrepreneur", "journey", "woman-led", "family"),
            "Recognizable investor or partner signal": ("investor", "backed by", "partnered with"),
            "Specific numbers support the hook": ("%", "customers", "arr", "revenue", "million"),
            "Compelling industry relevance": ("ai", "technology", "health", "climate", "fintech", "cyber"),
            "Differentiated story": ("first", "only", "unique", "differentiated", "patent"),
            "Briefing identifies a current or upcoming hook": ("today", "this week", "this month", "upcoming", "launching", "current", "2026"),
            "Connected to a current market trend": ("trend", "regulation", "market demand", "industry interest"),
            "Official documentation is referenced": ("official", "press release", "documentation", "filing"),
            "Investor confirmation or named investor": ("investor confirmation", "investor", "funded by"),
            "Named customer evidence": ("customer testimonial", "named customer", "customer evidence", "case study"),
            "Independent research or third-party validation": ("independent", "third-party", "research", "report", "validated"),
            "Consumer relevance": ("consumer", "consumer-facing", "customers"), "Business relevance": ("enterprise", "business", "b2b", "companies"),
            "Technology relevance": ("ai", "technology", "digital", "software"), "UAE relevance": ("uae", "dubai", "abu dhabi"),
            "GCC or regional relevance": ("gcc", "saudi", "middle east", "gulf"), "Clear industry or societal impact": ("impact", "reduce", "improve", "efficiency", "access"),
        }
        if factor == "Clear headline-worthy event":
            if self.opportunity.funding_amount is not None: return "funding_amount", self.json_value(self.opportunity.funding_amount), "The recorded funding event provides a clear headline."
            if self.opportunity.product_launched is True: return "product_launched", True, "The confirmed product launch provides a clear headline."
            text_rules[factor] = ("acquisition", "partner", "expansion")
        if factor == "Measurable results are provided" and self.opportunity.customer_count is not None:
            return "customer_count", self.json_value(self.opportunity.customer_count), "The recorded customer count is a measurable result."
        terms = text_rules.get(factor)
        if terms:
            for field in self.text_fields:
                value = getattr(self.opportunity, field)
                if value and any(term in value.lower() for term in terms):
                    return field, value, "This factor is supported by the recorded opportunity text."
        return "opportunity_data", None, "No supporting source field was recorded for this limiting factor."

    def enrich_explanations(self, dimensions: dict[str, dict]) -> None:
        for dimension in dimensions.values():
            dimension["missing_information"] = [MISSING_INFORMATION_LABELS.get(item, item) for item in dimension["missing_information"]]
            for factor in dimension["positive_factors"] + dimension["negative_factors"]:
                source_field, source_value, reason = self.source_for_factor(factor["factor"])
                factor.update({"source_field": source_field, "source_value": source_value, "reason": reason})
            dimension["scoring_signals_used"] = [*dimension["positive_factors"], *dimension["negative_factors"]]

    def calculate_newsworthiness(self) -> dict:
        d = Dimension("newsworthiness")
        if self.opportunity.funding_amount is not None: d.add("Funding announcement", 15)
        else: d.missing_information.append("funding_amount")
        if self.opportunity.funding_amount is not None and self.opportunity.funding_amount >= HIGH_FUNDING_THRESHOLD: d.add("Funding meets the significant-round threshold", 10)
        if self.contains("acquisition", "acquired", "merger"): d.add("Acquisition or merger event", 15)
        if self.opportunity.product_launched is True: d.add("Product launch", 12)
        elif self.opportunity.product_launched is None: d.missing_information.append("product_launch_status")
        if self.contains("partner", "partnership"): d.add("Partnership announcement", 10)
        if self.contains("expand", "expansion", "new market"): d.add("Geographic expansion", 10)
        if self.opportunity.customer_count is not None and self.opportunity.customer_count >= CUSTOMER_TRACTION_THRESHOLD: d.add("Measurable customer traction", 10)
        elif self.opportunity.customer_count is None: d.missing_information.append("customer_traction")
        if self.contains("growth", "yoy", "arr", "revenue", "%"): d.add("Measurable business growth or result", 10)
        if self.contains("milestone", "appointed", "appointment", "research", "study", "report"): d.add("Notable milestone, appointment, or research", 10)
        if self.contains("uae", "dubai", "abu dhabi", "gcc", "saudi", "middle east"): d.add("Strong local or regional relevance", 8)
        if not d.positive_factors: d.add("No clear news event is documented", -15)
        return d.result()

    def calculate_media_appeal(self) -> dict:
        d = Dimension("media_appeal")
        if self.opportunity.funding_amount is not None or self.opportunity.product_launched is True or self.contains("acquisition", "partner", "expansion"): d.add("Clear headline-worthy event", 20)
        else: d.add("No documented headline-worthy event", -10)
        if self.opportunity.founder_available is True or self.contains("spokesperson available"): d.add("Founder or spokesperson available for interviews", 12)
        elif self.opportunity.founder_available is None: d.missing_information.append("spokesperson_availability")
        if self.contains("founder", "entrepreneur", "journey", "woman-led", "family"): d.add("Human or founder story", 10)
        if self.contains("investor", "backed by", "partnered with"): d.add("Recognizable investor or partner signal", 10)
        if self.contains("%", "customers", "arr", "revenue", "million", "million"): d.add("Specific numbers support the hook", 12)
        else: d.missing_information.append("quantified_media_hook")
        if self.contains("ai", "technology", "health", "climate", "fintech", "cyber"): d.add("Compelling industry relevance", 10)
        if self.contains("first", "only", "unique", "differentiated", "patent"): d.add("Differentiated story", 10)
        return d.result()

    def calculate_timeliness(self) -> dict:
        d = Dimension("timeliness")
        launch_date = self.opportunity.product_launch_date
        if launch_date:
            days = (launch_date - self.today).days
            if -RECENT_DAYS_THRESHOLD <= days <= RECENT_DAYS_THRESHOLD: d.add("Announcement date is recent", 35)
            elif 0 < days <= UPCOMING_DAYS_THRESHOLD: d.add("Launch or milestone is upcoming", 30)
            elif days < -RECENT_DAYS_THRESHOLD: d.add("Provided announcement date is old", -20)
        else: d.missing_information.append("announcement_or_launch_date")
        if self.contains("today", "this week", "this month", "upcoming", "launching", "current", "2026"): d.add("Briefing identifies a current or upcoming hook", 25)
        if self.contains("trend", "regulation", "market demand", "industry interest"): d.add("Connected to a current market trend", 20)
        if not d.positive_factors: d.add("No specific timing or current hook is documented", -10)
        return d.result()

    def calculate_credibility(self) -> dict:
        d = Dimension("credibility")
        if self.contains("official", "press release", "documentation", "filing"): d.add("Official documentation is referenced", 20)
        else: d.missing_information.append("official_documentation")
        if self.contains("investor confirmation", "investor", "funded by"): d.add("Investor confirmation or named investor", 15)
        else: d.missing_information.append("investor_confirmation")
        if self.contains("customer testimonial", "named customer", "customer evidence", "case study"): d.add("Named customer evidence", 18)
        else: d.missing_information.append("independent_customer_evidence")
        if self.contains("independent", "third-party", "research", "report", "validated"): d.add("Independent research or third-party validation", 18)
        else: d.missing_information.append("third_party_validation")
        if self.opportunity.customer_count is not None or self.contains("%", "arr", "revenue", "reduction"): d.add("Measurable results are provided", 12)
        else: d.missing_information.append("measurable_results")
        if self.opportunity.founder_available is True: d.add("Credible spokesperson is available", 7)
        if not d.positive_factors: d.add("Claims have no documented supporting evidence", -15)
        return d.result()

    def calculate_audience_interest(self) -> dict:
        d = Dimension("audience_interest")
        if self.opportunity.target_audience.strip(): d.add("A target audience is identified", 15)
        else: d.missing_information.append("target_audience")
        if self.contains("consumer", "consumer-facing", "customers"): d.add("Consumer relevance", 12)
        if self.contains("enterprise", "business", "b2b", "companies"): d.add("Business relevance", 15)
        if self.contains("ai", "technology", "digital", "software"): d.add("Technology relevance", 15)
        if self.contains("uae", "dubai", "abu dhabi"): d.add("UAE relevance", 15)
        if self.contains("gcc", "saudi", "middle east", "gulf"): d.add("GCC or regional relevance", 12)
        if self.opportunity.customer_count is not None and self.opportunity.customer_count >= CUSTOMER_TRACTION_THRESHOLD: d.add("Meaningful audience reach or traction", 12)
        if self.contains("impact", "reduce", "improve", "efficiency", "access"): d.add("Clear industry or societal impact", 10)
        if not d.positive_factors: d.add("Limited documented audience relevance", -10)
        return d.result()

    def calculate_overall_score(self, dimensions: dict[str, dict]) -> int:
        return int(round(sum(Decimal(dimensions[key]["score"]) * weight for key, weight in WEIGHTS.items())))

    @staticmethod
    def potential_for(score: int) -> str:
        return "HIGH" if score >= HIGH_POTENTIAL_THRESHOLD else "MEDIUM" if score >= MEDIUM_POTENTIAL_THRESHOLD else "LOW"

    def score(self) -> dict:
        dimensions = {"newsworthiness": self.calculate_newsworthiness(), "media_appeal": self.calculate_media_appeal(), "timeliness": self.calculate_timeliness(), "credibility": self.calculate_credibility(), "audience_interest": self.calculate_audience_interest()}
        self.enrich_explanations(dimensions)
        overall_score = self.calculate_overall_score(dimensions)
        weighted_total = sum(Decimal(dimensions[key]["score"]) * weight for key, weight in WEIGHTS.items())
        calculation = [{"dimension": key, "score": dimensions[key]["score"], "weight": str(weight), "weighted_score": str(Decimal(dimensions[key]["score"]) * weight)} for key, weight in WEIGHTS.items()]
        return {"scoring_version": SCORING_VERSION, "overall_score": overall_score, "potential": self.potential_for(overall_score), "dimensions": dimensions, "weights": {key: str(value) for key, value in WEIGHTS.items()}, "calculation": {"formula": "Sum of each dimension score multiplied by its configured weight, rounded to the nearest whole number.", "weighted_total": str(weighted_total), "rounded_overall_score": overall_score, "dimensions": calculation}, "overall_explanation": {"strong_points": [factor for item in dimensions.values() for factor in item["positive_factors"]], "areas_holding_back": [factor for item in dimensions.values() for factor in item["negative_factors"]]}}
