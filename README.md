# PR Opportunity Scoring Engine
 
A decision-support tool that scores prospective PR opportunities before a consultancy commits time or resources to pitching them.
 
Given structured details about a client and their story (funding, industry, founder availability, product stage, etc.), the engine returns an overall opportunity score, a breakdown across five weighted dimensions, ranked pitch angles, and a concrete recommendation for what would make the story stronger.
 
Built for pay-on-results PR models, where taking on a weak story is a direct commercial loss, not just a missed opportunity.
 
---
 
## Why
 
Consultants currently judge "is this publishable?" on instinct. That doesn't scale, isn't consistent across consultants, and gives the client no structured feedback on how to improve their pitch. This tool turns that judgment call into a repeatable, explainable process — one that surfaces *why* a story scores the way it does, not just a number.
 
---
 
## Example
 
**Input**
 
```
Industry:        AI / SaaS
Location:         Dubai, UAE
Funding:          $5M Series A
Founder:          Available for interviews
Product status:   Launched 3 months ago
Customer data:    Not provided
```
 
**Output**
 
```
PR OPPORTUNITY SCORE
Overall: 87/100
 
Newsworthiness       92
Media Appeal         88
Timeliness           94
Credibility          81
Audience Interest    85
 
RECOMMENDED ANGLES
1. Funding announcement        — Potential: HIGH
2. UAE AI ecosystem story      — Potential: HIGH
3. Founder thought leadership  — Potential: MEDIUM
4. Product announcement        — Potential: LOW
 
WHAT WOULD MAKE THIS STRONGER
Weakness: No independent customer data.
Recommendation: Provide 2-3 measurable results from existing
customers (e.g. % efficiency gain, revenue impact, retention).
```
 
---
 
## How Scoring Works
 
Scoring is **rules-based and transparent** — not a black box. Every input field maps to point contributions across five dimensions via a defined rubric, so every score is fully explainable and defensible to a client who asks "why 87?"
 
| Dimension | Captures |
|---|---|
| Newsworthiness | Is there an actual news hook (funding, launch, milestone)? |
| Timeliness | Does this connect to a live news cycle or trend? |
| Credibility | Can the claims be substantiated? |
| Media Appeal | Is there a human angle, visual hook, or novelty? |
| Audience Interest | Does this matter to a broad or influential readership? |
 
An LLM layer (v2+) is planned for parsing free-text client briefs into structured input and generating qualitative reasoning — but the numeric scoring itself stays rule-based, so the system remains auditable as it grows.
 
See [`PR_Opportunity_Scoring_Engine_Project_Description.md`](./PR_Opportunity_Scoring_Engine_Project_Description.md) for the full scoring rubric, methodology, and roadmap.
 
---
 
## Tech Stack
 
| Layer | Choice |
|---|---|
| Frontend | React |
| Backend | Django (or lightweight Node/Express) |
| Database | PostgreSQL |
| LLM layer (v2+) | Gemini / Claude API, structured JSON output |
| Deployment | Docker, GCP |
 
---
 
## Project Status
 
🚧 **In development — MVP stage**
 
- [ ] Structured intake form
- [ ] Rules-based scoring engine (5 dimensions)
- [ ] Score + breakdown UI
- [ ] Angle ranking against angle library
- [ ] Single weakness + recommendation output
- [ ] Save/compare scored opportunities over time
---
 
## Getting Started
 
```bash
# Clone the repo
git clone <repo-url>
cd pr-opportunity-scoring-engine
 
# Backend
cd backend
# install dependencies, configure .env, run migrations
 
# Frontend
cd Frontend/pr_scoring_enginge
npm install
npm run dev
```

### Docker

The Docker setup runs the Next.js frontend and Django backend. The Django
project currently uses its configured SQLite database.

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000) for the frontend and
[http://localhost:8000/admin/](http://localhost:8000/admin/) for Django. Stop
the application with `docker compose down`.
 
### Environment Variables
 
```
DATABASE_URL=
LLM_API_KEY=        # required from v2 onward
```
 
---
 
## Project Structure
 
```
pr-opportunity-scoring-engine/
├── backend/
│   ├── scoring/          # rubric logic, dimension calculators
│   ├── angles/            # angle library + matching logic
│   ├── api/                # endpoints for scoring, history
│   └── models/            # Opportunity, Score, Angle
├── frontend/
│   ├── src/
│   │   ├── components/    # intake form, score dashboard, angle cards
│   │   └── pages/
└── docs/
    └── PR_Opportunity_Scoring_Engine_Project_Description.md
```
 
*(Structure is a proposed starting point — adjust as the build evolves.)*
 
---
 
## Roadmap
 
**v1 (MVP)** — rules-based scoring, structured intake, angle ranking, single weakness/recommendation
**v2** — free-text intake parsed by LLM, multiple weaknesses, configurable rubric weights, side-by-side comparison
**v3** — outcome feedback loop (log actual publish/no-publish results to recalibrate rubric weights over time), journalist/outlet fit suggestions
 
---
