# France Travail MCP — design notes & roadmap

Working document. Captures *why* the server is built the way it is, and where it could go.

## Design principles

1. **Official API over scraping.** France Travail offers a free, structured, real-time API. Scraping Indeed/LinkedIn for French jobs is fragile and loses data (salary, ROME, skills). We go to the source.
2. **Zero dependencies.** Pure Python stdlib, single file, stdio JSON-RPC by hand. Reasons: trivial to audit, no supply-chain risk, no version conflicts (a common MCP pain: SDK ↔ pydantic/zod mismatches), runs anywhere Python runs.
3. **Slim the output for lists, keep it whole for detail.** `search_jobs` returns trimmed cards (the fields you scan); `get_job` returns the full record. Agents stay within context limits while still being able to drill down.
4. **Surface the free wins.** The search endpoint returns `filtresPossibles` (aggregations). Most clients ignore them — we expose them as market stats. Counting offers by contract/experience/qualification is genuinely useful and costs nothing extra.
5. **ROME as a precision layer.** Keyword search is noisy. The ROME occupation code makes searches exact. `rome_search` → code → `search_jobs(codeROME=...)` is the recommended flow.

## What the offer object actually contains (observed)

Rich and well-structured: `intitule`, `description`, `lieuTravail{libelle, lat/lon, codePostal}`, `romeCode/romeLibelle`, `typeContrat`, `natureContrat`, `experienceLibelle`, `salaire{libelle}`, `competences[{code, libelle, exigence}]`, `qualificationLibelle`, `secteurActiviteLibelle`, `codeNAF`, `entreprise{nom, description?, logo?, url?}`, `trancheEffectifEtab`, `contact{...}`, `origineOffre{urlOrigine}`, `nombrePostes`, `accessibleTH`, `contexteTravail{horaires}`.

Notable gaps: **no SIRET** on offers (only company name + NAF + size band) → cross-referencing a registry means searching by name. Salary is a free-text `libelle` (sometimes empty, sometimes hourly) → a parser to normalize to annual € is a natural enhancement.

## ROME notes

- `rome_search?q=` is broad/fuzzy — returns a count in the thousands and loosely related occupations. Pick by `libelle`. (A future improvement: rank by string similarity to the query before returning.)
- `rome_metier/{code}` is a goldmine: definition, `accesEmploi`, `competencesMobiliseesPrincipales`, `competencesMobiliseesEmergentes` (skills trending up for the occupation), sectors, `emploiCadre`, ecological/numeric/demographic transition flags.
- The ROME **Compétences** API uses a different URL structure than the obvious `/competences/metier/{code}` (which 404s). Needs the competence-tree endpoints — left out of v1 on purpose.

## Roadmap ideas

### Near term
- [ ] **Salary parser** — extract `{min, max, period, currency}` from `salaire.libelle` and the description; normalize hourly/monthly → annual €.
- [ ] **Skill extraction** — pull a tech-stack list from the description (regex + dictionary) to complement the structured `competences`.
- [ ] **Better `rome_search`** — rank results by similarity to the query so the top hit is usually the right one.
- [ ] **Local token cache to disk** — survive restarts without re-authing.

### Medium term
- [ ] **More FT APIs** as additional tools, when subscribed: *La Bonne Boîte* (companies likely to hire even without a posted offer — great for prospecting), *Soft Skills*, *Marché du travail / statistics*, territorial context.
- [ ] **Reference data helpers** — resolve a city name → INSEE commune code automatically (today the caller passes codes).
- [ ] **`search_jobs` extras** — `publieeDepuis` (date filter), `sort`, multi-page auto-fetch for >150 results.

### Nice to have
- [ ] HTTP/SSE transport option (in addition to stdio) for hosted/shared deployments.
- [ ] A thin CLI wrapper (`francetravail search ...`) reusing the same core, for non-MCP use.

## Non-goals
- Not a scraper. If the API doesn't expose it, we don't fake it.
- Not international. France Travail = France. International coverage belongs to other sources/servers.
- No user authentication (France Travail Connect / OIDC) — this server is read-only public job data via client-credentials. Personal-account data is a different product and out of scope.
