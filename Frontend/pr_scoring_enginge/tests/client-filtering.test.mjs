import assert from "node:assert/strict";
import test from "node:test";

import { filterClients } from "../lib/client-filtering.js";

const clients = [
  { company_name: "Northstar Health", industry: "Healthcare", location: "London", company_size: "51-200" },
  { company_name: "Beacon Finance", industry: "Finance", location: "Dubai", company_size: "201-500" },
];

test("client list filtering matches search and selected filters", () => {
  assert.deepEqual(filterClients(clients, { search: "dubai", industry: "", companySize: "" }), [clients[1]]);
  assert.deepEqual(filterClients(clients, { search: "", industry: "Healthcare", companySize: "51-200" }), [clients[0]]);
  assert.deepEqual(filterClients(clients, { search: "", industry: "Finance", companySize: "51-200" }), []);
});
