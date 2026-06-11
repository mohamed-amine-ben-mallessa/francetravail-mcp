---
name: francetravail
description: >
  Search official French job offers (France Travail / ex-Pôle Emploi) and the ROME occupation
  reference via the francetravail MCP server. Use whenever the user looks for jobs in France,
  wants the French job market for a role/area, needs an occupation's official code or skills,
  or wants structured offer data (salary, contract, company, application link).
  Keywords: job, emploi, France Travail, Pôle Emploi, offre, ROME, métier, CDI, CDD, alternance,
  marché de l'emploi, French jobs, recruitment France.
license: MIT
---

# France Travail — official French job data

Use the `francetravail` MCP server (5 tools) to query France's official employment API. Structured data, no scraping. Respond in the user's language; salaries are already in €.

## Tools
| Tool | Use |
|------|-----|
| `search_jobs` | search offers + market aggregations |
| `get_job` | full detail of one offer (description, salary, skills, contact, application URL) |
| `rome_search` | occupation name → official ROME code |
| `rome_metier` | full occupation sheet (definition, core + emerging skills) |
| `list_referentiel` | reference lists (contracts, communes, sectors…) |

## Recommended flow
1. If the role is fuzzy, `rome_search("data engineer")` → take the code whose label fits best, then `search_jobs(codeROME=...)` for precise results (much better than keywords alone).
2. `search_jobs` filters: `departement` (e.g. "75"), `commune` (INSEE code) + `distance` (km), `typeContrat`, `experience` (1/2/3), `qualification` (0 non-cadre / 9 cadre), `alternance` (bool), `salaireMin` (annual €), `resultsWanted` (default 15, max 150).
3. Present a table: **Title · Company · Location · Contract · Salary · ROME · Date · Link**, and surface the market aggregations returned with the search.
4. `get_job(id)` for full detail and the direct application link.

## Notes
- France only. For international/private-tech jobs, combine with other sources.
- Offers expose company name + sector + NAF + size band, but **no SIRET** (cross-reference a registry by name).
- `rome_search` is fuzzy: pick by label; the right code also appears in each offer's `romeCode`.
- Rate limit 4 req/s; OAuth handled automatically by the server.

## Setup
Needs `FT_CLIENT_ID` / `FT_CLIENT_SECRET` (free France Travail developer app subscribed to "Offres d'emploi v2"). See the server's CONFIGURATION.md.
