import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

const dashboard = readFileSync(new URL("../components/dashboard.tsx", import.meta.url), "utf8");

test("dashboard renders real pipeline sections without evidence UI", () => {
  for (const text of ["Total opportunities", "Opportunity distribution", "Recently analyzed", "Top opportunities", "requiring attention", "Opportunity trends", "getDashboardSummary", "Retry"]) assert.match(dashboard, new RegExp(text));
  assert.doesNotMatch(dashboard, /Evidence|evidence/);
});

test("dashboard recent table has the requested analysis actions", () => {
  assert.match(dashboard, /View opportunity/);
  assert.match(dashboard, /View analysis/);
  assert.match(dashboard, /Last analyzed/);
});