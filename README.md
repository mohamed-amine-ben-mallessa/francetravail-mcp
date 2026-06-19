<h1 align="center">🇫🇷 France Travail MCP</h1>

<p align="center">
  <b>Real-time French job-market data for your AI agent — straight from the official API. No scraping.</b>
</p>

<p align="center">
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-stdio-blue" alt="MCP"></a>
  <a href="https://pypi.org/project/francetravail-mcp/"><img src="https://img.shields.io/pypi/v/francetravail-mcp?label=PyPI" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-%E2%89%A53.8-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/dependencies-0-brightgreen" alt="Zero dependencies">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT">
  <img src="https://img.shields.io/badge/data-official%20API-success" alt="Official API">
  <img src="https://img.shields.io/badge/status-unofficial-lightgrey" alt="Unofficial">
</p>

<p align="center">
  <a href="media/launch-video.mp4"><img src="media/launch-preview.gif" alt="France Travail MCP — launch video" width="760"></a>
</p>
<p align="center"><sub>▶️ <a href="media/launch-video.mp4">Watch the full 60s launch video (MP4)</a> · rendered with <a href="https://hyperframes.heygen.com">HyperFrames</a></sub></p>

<p align="center">
  <img src="assets/logo-france-travail-io.svg" alt="France Travail" height="42">
  &nbsp;&nbsp;·&nbsp;&nbsp;
  <img src="assets/logo-sollea.png" alt="Sollea AI" height="42">
</p>

---

You have a meeting tomorrow. You want to know which companies in Lyon are hiring data engineers, what they pay, and what skills they ask for.

You Google it. You get three aggregator sites, a paywall, and offers from 2024.

**`francetravail` asks the source.** Every active job posted to France Travail — France's public employment service — with structured salary, official occupation codes, required skills, company size, and a direct application link. Plus free market stats most tools never surface: *"65 permanent contracts, 14 fixed-term, 7 apprenticeships for this role in Paris — right now."*

> The first open-source MCP server for the official France Travail APIs. Built because every "French jobs" tool out there scrapes Indeed and loses half the data.

## Why it's different

| Most job tools | `francetravail` MCP |
|---|---|
| Scrape Indeed/LinkedIn (breaks weekly) | Hits the **official API** |
| Lose salary, skills, occupation codes | **Structured fields**, nothing dropped |
| One offer at a time | **Market aggregations** for free |
| Pile of npm/pip deps | **Zero dependencies**, one file |
| Keyword guessing | **Official ROME codes** = precise search |

## Install (1 minute)

### Option A — pip (recommended)
```bash
pip install francetravail-mcp
# then set FT_CLIENT_ID and FT_CLIENT_SECRET env vars
```

### Option B — git clone
```bash
git clone https://github.com/mohamed-amine-ben-mallessa/francetravail-mcp.git
cp francetravail-mcp/.env.example francetravail-mcp/.env
# paste your free France Travail credentials into .env  (see below)
```

Then point any MCP client at it:

```json
{
  "mcpServers": {
    "francetravail": {
      "command": "python",
      "args": ["/absolute/path/to/francetravail-mcp/server.py"],
      "env": {
        "FT_CLIENT_ID": "your_client_id",
        "FT_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

No `pip install`. No SDK. Pure Python standard library — runs anywhere Python ≥ 3.8 runs.

### Getting free credentials → see [CONFIGURATION.md](./CONFIGURATION.md)

## What you can ask

```
"Find web developer jobs in Paris — how many are permanent vs apprenticeship?"
"What's the ROME code for data engineer, then search those roles in Lyon."
"Show the ROME sheet for M1805 — which skills are trending up for this job?"
"Get the full detail and application link for offer 209QKVF."
```

### Example: market snapshot in one call

> *"Developer jobs around Lyon (69)?"*

```
193 offers · 149 permanent (CDI) · 29 fixed-term · 10 temp · 5 freelance
Experience asked: 36% senior, 36% mid, 28% junior/none
```

That breakdown is returned **with every search**, for free, from the API's own aggregations.

## The 5 tools

| Tool | Does | Returns |
|------|------|---------|
| **`search_jobs`** | Search offers by keyword, location, ROME code, contract, experience, salary, apprenticeship | Clean offer cards **+ market aggregations** |
| **`get_job`** | Full detail of one offer | 30+ fields incl. description, salary, skills, company, contact, **application URL** |
| **`rome_search`** | Occupation name → official ROME code | `[{code, libelle}]` |
| **`rome_metier`** | Full occupation sheet | Definition, access-to-employment, **core + emerging skills**, sectors |
| **`list_referentiel`** | Official reference lists | Contract types, communes, departments, sectors… |

💡 **Pro flow:** `rome_search("data engineer")` → get code → `search_jobs(codeROME=...)`. ROME codes make searches exact where keywords are noisy.

## Requirements

- **Python ≥ 3.8** — standard library only
- A free **[France Travail developer account](https://francetravail.io)** with the *Offres d'emploi v2* API subscribed
- *(Optional)* the *ROME Métiers* API subscribed, for the `rome_*` tools

## Limitations (read before you ship)

- 🇫🇷 **France only.** It's the French public employment operator. Pair with other sources for international/private-tech jobs.
- 🪪 **No SIRET in offers.** You get company **name + sector + NAF + size band**, not the SIRET. Cross-referencing a company registry means searching by name.
- 🔀 **`rome_search` is fuzzy.** It can return many loosely-related occupations — pick the one whose label fits (the right code also appears in each offer's `romeCode`).
- ⏱️ **4 requests/second** per app (plenty for agents). Tokens are cached & refreshed automatically.
- 📄 **150 results/search** (API page limit).

## How it works

```
agent ──stdio JSON-RPC──> server.py ──OAuth2 (client_credentials)──> France Travail APIs
                                        token cached per scope
```

`stdout` = JSON-RPC only · logs → `stderr` · single file · no framework.

## Data source

Data comes from the official **France Travail** APIs (*Offres d'emploi v2*, *ROME Métiers*),
documented at [francetravail.io](https://francetravail.io). The data is provided by France
Travail; this project is only a client that calls those public APIs.

## Built by

Created and maintained by **Mohamed Amine Ben Mallessa**.
Used in production by **[Sollea AI](https://sollea-ai.com)**.

## Roadmap & design notes

See **[BRAINSTORM.md](./BRAINSTORM.md)** — salary parser, skill extraction, more FT APIs (*La Bonne Boîte* for prospecting), smarter ROME ranking, HTTP/SSE transport.

## Disclaimer

> **Unofficial project.** This is an independent, open-source MCP client. It is **not developed,
> affiliated with, sponsored, or endorsed by France Travail**. "France Travail", "Pôle Emploi"
> and their logos are trademarks of their respective owners. This project only consumes France
> Travail's public APIs under their terms of use. Use responsibly and respect the API rate limits
> and conditions.

## License

MIT.
