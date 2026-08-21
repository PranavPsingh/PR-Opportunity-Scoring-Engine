import { readFile } from "node:fs/promises";
import test from "node:test";
import assert from "node:assert/strict";

const component = await readFile(new URL("../components/story-strengthening.tsx", import.meta.url), "utf8");
const api = await readFile(new URL("../lib/opportunities.ts", import.meta.url), "utf8");
const detail = await readFile(new URL("../components/opportunity-detail.tsx", import.meta.url), "utf8");

test("story strengthening exposes grounded analysis and workflow states", () => {
  assert.match(component, /Analyze Story/);
  assert.match(component, /Re-analyze story/);
  assert.match(component, /Loading story strengthening/);
  assert.match(component, /No supported weaknesses/);
  assert.match(component, /Evidence needed/);
  assert.match(component, /COMPLETED/);
  assert.match(component, /DISMISSED/);
  assert.match(component, /Reopen/);
  assert.match(component, /expected_benefit/);
});

test("story strengthening API contract uses authenticated opportunity routes", () => {
  assert.match(api, /getStoryStrengthening/);
  assert.match(api, /strengthening\/`/);
  assert.match(api, /analyzeStoryStrengthening/);
  assert.match(api, /strengthening\/analyze/);
  assert.match(api, /updateStrengtheningStatus/);
});

test("opportunity detail mounts story strengthening between score and angles", () => {
  assert.match(detail, /<OpportunityScorePanel/);
  assert.match(detail, /<StoryStrengtheningPanel/);
  assert.match(detail, /<PRAnglesPanel/);
});
