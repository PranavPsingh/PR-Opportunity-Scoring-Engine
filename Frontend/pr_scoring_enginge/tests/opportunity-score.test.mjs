import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

const panel = readFileSync(new URL("../components/opportunity-score.tsx", import.meta.url), "utf8");

test("opportunity score panel renders API score, explanations, and re-score history", () => {
  for (const text of ["PR Opportunity Score", "Analyze opportunity", "Re-score opportunity", "Missing information", "getLatestScore", "getScoreHistory", "scoreOpportunity"]) assert.match(panel, new RegExp(text));
  assert.doesNotMatch(panel, /calculate_overall_score/);
});
