import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

const panel = readFileSync(new URL("../components/pr-angles.tsx", import.meta.url), "utf8");
const client = readFileSync(new URL("../lib/opportunities.ts", import.meta.url), "utf8");

test("PR angles UI exposes generation, loading, detail, grounding and error states", () => {
  for (const text of ["Generate PR Angles", "Extracting facts and generating PR angles", "Why this angle works", "What could make this angle stronger", "Supporting facts", "Risks and weaknesses", "View details", "extracted text is not displayed"]) assert.match(panel, new RegExp(text));
  assert.match(client, /generatePRAngles/); assert.match(client, /getPRAngles/);
  assert.doesNotMatch(panel, /press release|journalist outreach/i);
});
