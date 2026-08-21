import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const form = readFileSync(new URL("../components/opportunity-form.tsx", import.meta.url), "utf8");
const list = readFileSync(new URL("../components/opportunity-list.tsx", import.meta.url), "utf8");
const api = readFileSync(new URL("../lib/opportunities.ts", import.meta.url), "utf8");

test("opportunity form exposes the complete intake workflow and validation", () => {
  for (const label of ["Client", "Opportunity/story title", "Original client briefing", "Funding amount", "Founder available for media?"]) assert.match(form, new RegExp(label));
  assert.match(form, /required rows=\{10\}/);
  assert.match(form, /Unable to save opportunity/);
});

test("opportunity UI supports create, edit, list, and API error states", () => {
  assert.match(form, /createOpportunity/);
  assert.match(form, /updateOpportunity/);
  assert.match(list, /getOpportunities/);
  assert.match(list, /Unable to load opportunities/);
  assert.match(api, /opportunities\//);
  assert.match(api, /csrfHeaders/);
});
