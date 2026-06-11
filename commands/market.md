---
description: Show French job-market stats for a role/zone (contract mix, experience demand)
argument-hint: <role> in <department or region>
---

Show job-market statistics using the `francetravail` MCP server.

User request: $ARGUMENTS

Steps:
1. Identify the role (optionally resolve a ROME code via `rome_search` for precision) and the zone (department number, or region).
2. Call `search_jobs` with a small range and read the returned aggregations, or use the dedicated stats if available.
3. Summarize: total offers, contract breakdown (permanent / fixed-term / temp / freelance), experience levels demanded, share of cadre roles.
4. Add a one-line read of the market tension (e.g. "high demand, mostly permanent senior roles").
