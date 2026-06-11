# Configuration

## Getting free France Travail API credentials

1. Create a developer account at **[francetravail.io](https://francetravail.io)**.
2. Go to **"Mes applications"** → create an application (any name).
3. **Subscribe the application to the API "Offres d'emploi v2"**
   (scope: `api_offresdemploiv2 o2dsoffre`).
4. *(Optional, for the `rome_search` / `rome_metier` tools)* also subscribe to
   **"ROME 4.0 - Métiers"** (scope: `api_rome-metiersv1 nomenclatureRome`).
5. Copy the application's **client ID** and **client secret**.

> ⚠️ **The #1 setup mistake:** creating the application but **forgetting to subscribe it
> to the API**. Without the subscription, the token request fails with
> `{"error":"invalid_client"}` — even though your keys are correct.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FT_CLIENT_ID` | ✅ | Your application's client ID (starts with `PAR_`) |
| `FT_CLIENT_SECRET` | ✅ | Your application's client secret (64-char hex) |

Set them in your MCP client config (`env` block), or via a `.env` file
(copy `.env.example` → `.env`).

## Verifying it works

A quick manual token check (replace with your values):

```bash
curl -s -X POST \
  "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=$FT_CLIENT_ID" \
  -d "client_secret=$FT_CLIENT_SECRET" \
  -d "scope=api_offresdemploiv2 o2dsoffre"
```

A JSON response with an `access_token` field means you're good to go.
`invalid_client` means the app isn't subscribed to the API (see the warning above).

## Rate limits

- **4 requests/second** per application (global API limit is 100/s shared across all apps).
- The server caches OAuth tokens per scope and refreshes them automatically before expiry,
  so you don't spend requests re-authenticating.
