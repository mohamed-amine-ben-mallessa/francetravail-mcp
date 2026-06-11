---
description: Search French job offers (France Travail) by keyword and location, with market stats
argument-hint: <keywords> [in <location>]
---

Search live French job offers using the `francetravail` MCP server (`search_jobs` tool).

User request: $ARGUMENTS

Steps:
1. Parse the keywords and any location (city → INSEE commune code, or a department number like 75/69/13). If a department is given, use `departement`; for a city, you may resolve it via `list_referentiel` (communes) or use `commune`.
2. If the role is ambiguous, call `rome_search` first to get the precise ROME code, then pass it as `codeROME` for sharper results.
3. Call `search_jobs` with sensible filters (default 15 results).
4. Present a clean table: **Title · Company · Location · Contract · Salary · Date · Link**.
5. Report the **market aggregations** that come back (e.g. "65 permanent / 14 fixed-term / 7 apprenticeships") — they're free and useful.
6. Offer to fetch full details of any offer with `get_job`.
