import json

from django.test import SimpleTestCase

from apps.extraction.services import FIELD_NAMES, SYSTEM_PROMPT, parse_provider_json, validate_extraction


class ExtractionNormalizationTests(SimpleTestCase):
    def test_validator_accepts_safe_provider_formatting_variations(self):
        fields = {}
        for name in ("company_name", "industry", "company_description", "location", "website", "funding_amount", "funding_currency", "funding_stage", "funding_date", "investors", "product_name", "product_description", "product_launched", "product_launch_date", "customer_count", "user_count", "revenue", "revenue_growth", "other_growth_metrics", "headquarters_location", "operating_markets", "expansion_markets", "geographic_relevance", "founder_names", "founder_roles", "founder_available_for_interview", "spokesperson_available", "target_audience", "target_industries", "key_claims", "notable_announcements", "important_dates", "milestones", "potential_news_hooks"):
            fields[name] = {"value": None, "confidence": "0", "source_text": None, "extraction_status": "NOT_FOUND"}
        fields["funding_amount"] = {"value": "5,000,000", "confidence": "0.9", "source_text": "5,000,000", "extraction_status": "EXTRACTED"}
        cleaned = validate_extraction(parse_provider_json('{"fields": ' + json.dumps(fields) + "}"), "Raised 5,000,000")
        self.assertEqual(cleaned["funding_amount"]["value"], 5000000.0)

    def test_prompt_requires_every_field_in_a_strict_json_response(self):
        self.assertIn("Return ONLY one valid JSON object", SYSTEM_PROMPT)
        self.assertIn("Never omit the field", SYSTEM_PROMPT)
        self.assertIn('"fields"', SYSTEM_PROMPT)
        for field in FIELD_NAMES:
            self.assertIn(field, SYSTEM_PROMPT)

    def test_partial_provider_response_safely_fills_missing_fields(self):
        cleaned = validate_extraction({"fields": {"company_name": {"value": "Pathos", "confidence": 0.9, "source_text": "Pathos", "extraction_status": "extracted"}}}, "Pathos")
        self.assertEqual(cleaned["company_name"]["value"], "Pathos")
        self.assertEqual(cleaned["industry"]["extraction_status"], "not_found")
