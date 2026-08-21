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
        self.text = " ".join(filter(None, [opportunity.title, opportunity.description, opportunity.story_type, opportunity.revenue_information, opportunity.geographic_relevance, opportunity.target_audience, opportunity.supporting_information, opportunity.client_briefing])).lower()

    def contains(self, *terms: str) -> bool:
        return any(term in self.text for term in terms)

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
        overall_score = self.calculate_overall_score(dimensions)
        return {"scoring_version": SCORING_VERSION, "overall_score": overall_score, "potential": self.potential_for(overall_score), "dimensions": dimensions, "weights": {key: str(value) for key, value in WEIGHTS.items()}}
