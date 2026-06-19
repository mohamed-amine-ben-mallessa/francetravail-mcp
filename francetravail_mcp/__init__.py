#!/usr/bin/env python3
"""
MCP France Travail — serveur stdio JSON-RPC pur (sans dépendance SDK).

Expose les API officielles France Travail :
  - Offres d'emploi v2 : search_jobs, get_job, list_referentiel
  - ROME Métiers v1     : rome_search, rome_metier
Auth : OAuth2 client credentials (FT_CLIENT_ID / FT_CLIENT_SECRET en env).

Transport : stdio, framing JSON-RPC une ligne par message (newline-delimited).
stdout = JSON-RPC uniquement ; tous les logs vont sur stderr.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

def log(*a):
    print(*a, file=sys.stderr, flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# Auth OAuth2 (client credentials) avec cache de token par scope
# ─────────────────────────────────────────────────────────────────────────────
TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
API_BASE = "https://api.francetravail.io/partenaire"
_token_cache = {}  # scope -> (token, expiry_epoch)

def get_token(scope):
    now = time.time()
    cached = _token_cache.get(scope)
    if cached and cached[1] - 30 > now:
        return cached[0]
    cid = os.environ.get("FT_CLIENT_ID", "").strip()
    csec = os.environ.get("FT_CLIENT_SECRET", "").strip()
    if not cid or not csec:
        raise RuntimeError("FT_CLIENT_ID / FT_CLIENT_SECRET manquants dans l'environnement.")
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": cid,
        "client_secret": csec,
        "scope": scope,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    tok = d["access_token"]
    _token_cache[scope] = (tok, now + int(d.get("expires_in", 1500)))
    return tok

def api_get(path, scope, params=None, expect_list=False):
    """GET sur l'API FT. Renvoie (status, data)."""
    url = API_BASE + path
    if params:
        clean = {k: v for k, v in params.items() if v not in (None, "")}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    token = get_token(scope)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status = r.status
            raw = r.read().decode("utf-8")
            return status, (json.loads(raw) if raw.strip() else ([] if expect_list else {}))
    except urllib.error.HTTPError as e:
        # 204 = pas de résultat (recherche) ; 206 = résultat partiel paginé → OK
        if e.code in (204,):
            return e.code, ([] if expect_list else {})
        if e.code == 206:
            raw = e.read().decode("utf-8")
            return 206, (json.loads(raw) if raw.strip() else {})
        body = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"HTTP {e.code} sur {path} — {body}")

SCOPE_OFFRES = "api_offresdemploiv2 o2dsoffre"
SCOPE_ROME = "api_rome-metiersv1 nomenclatureRome"

# ─────────────────────────────────────────────────────────────────────────────
# Logique métier des tools
# ─────────────────────────────────────────────────────────────────────────────
def _slim_offre(o):
    """Réduit une offre aux champs utiles + bien découpés (pour les listes)."""
    sal = o.get("salaire", {}) or {}
    lt = o.get("lieuTravail", {}) or {}
    ent = o.get("entreprise", {}) or {}
    return {
        "id": o.get("id"),
        "intitule": o.get("intitule"),
        "entreprise": ent.get("nom"),
        "lieu": lt.get("libelle"),
        "codePostal": lt.get("codePostal"),
        "typeContrat": o.get("typeContratLibelle") or o.get("typeContrat"),
        "alternance": o.get("alternance"),
        "salaire": sal.get("libelle"),
        "experience": o.get("experienceLibelle"),
        "qualification": o.get("qualificationLibelle"),
        "romeCode": o.get("romeCode"),
        "romeLibelle": o.get("romeLibelle"),
        "secteur": o.get("secteurActiviteLibelle"),
        "dateCreation": o.get("dateCreation"),
        "url": (o.get("origineOffre", {}) or {}).get("urlOrigine"),
        "competences": [c.get("libelle") for c in (o.get("competences") or [])],
    }

def tool_search_jobs(args):
    params = {
        "motsCles": args.get("motsCles"),
        "commune": args.get("commune"),
        "departement": args.get("departement"),
        "region": args.get("region"),
        "distance": args.get("distance"),
        "typeContrat": args.get("typeContrat"),         # ex CDI,CDD (codes)
        "experience": args.get("experience"),           # 1=moins1an 2=1-3ans 3=plus3ans
        "qualification": args.get("qualification"),     # 0=non-cadre 9=cadre
        "tempsPlein": args.get("tempsPlein"),
        "codeROME": args.get("codeROME"),
        "salaireMin": args.get("salaireMin"),
        "origineOffre": args.get("origineOffre"),
    }
    # alternance : l'API attend natureContrat E2/FS ; on expose un bool simple
    if args.get("alternance") is True:
        params["natureContrat"] = "E2"
    n = int(args.get("resultsWanted", 15))
    n = max(1, min(n, 150))
    params["range"] = f"0-{n-1}"
    status, data = api_get("/offresdemploi/v2/offres/search", SCOPE_OFFRES, params)
    resultats = data.get("resultats", []) if isinstance(data, dict) else []
    offres = [_slim_offre(o) for o in resultats]
    # agrégations de marché (gratuit, très utile)
    aggs = {}
    for f in (data.get("filtresPossibles", []) if isinstance(data, dict) else []):
        aggs[f.get("filtre")] = {v.get("valeurPossible"): v.get("nbResultats") for v in f.get("agregation", [])}
    return {"count": len(offres), "offres": offres, "agregations": aggs}

def tool_get_job(args):
    jid = args["id"]
    status, data = api_get(f"/offresdemploi/v2/offres/{jid}", SCOPE_OFFRES)
    # détail complet, on renvoie l'objet brut (déjà très structuré côté FT)
    return data

def tool_list_referentiel(args):
    ref = args["type"]  # ex: typesContrats, communes, departements, regions, secteursActivites, naturesContrats, niveauxFormations, langues, permis
    status, data = api_get(f"/offresdemploi/v2/referentiel/{ref}", SCOPE_OFFRES, expect_list=True)
    # limiter les gros référentiels (communes = 35k)
    if isinstance(data, list) and len(data) > 200:
        return {"type": ref, "total": len(data), "note": "tronqué à 200 ; affiner via une recherche", "items": data[:200]}
    return {"type": ref, "total": len(data) if isinstance(data, list) else None, "items": data}

def tool_rome_search(args):
    q = args["metier"]
    status, data = api_get("/rome-metiers/v1/metiers/metier", SCOPE_ROME,
                           {"q": q}, expect_list=True)
    items = data if isinstance(data, list) else []
    return {"count": len(items), "metiers": [{"code": m.get("code"), "libelle": m.get("libelle")} for m in items[:25]]}

def tool_rome_metier(args):
    code = args["code"]
    status, data = api_get(f"/rome-metiers/v1/metiers/metier/{code}", SCOPE_ROME)
    if not isinstance(data, dict):
        return data
    # extraire les parties les plus utiles (la fiche est énorme)
    def libs(key):
        return [x.get("libelle") for x in (data.get(key) or []) if isinstance(x, dict)]
    return {
        "code": data.get("code"),
        "libelle": data.get("libelle"),
        "definition": data.get("definition"),
        "accesEmploi": data.get("accesEmploi"),
        "appellations": libs("appellations"),
        "competencesPrincipales": libs("competencesMobiliseesPrincipales"),
        "competencesEmergentes": libs("competencesMobiliseesEmergentes"),
        "secteursActivites": libs("secteursActivites"),
        "emploiCadre": data.get("emploiCadre"),
        "transitionNumerique": data.get("transitionNumerique"),
    }

TOOLS = [
    {
        "name": "search_jobs",
        "description": "Recherche d'offres d'emploi officielles France Travail (Pôle Emploi). Renvoie les offres + des agrégations de marché (nb d'offres par contrat/expérience/qualification). Filtres : motsCles, departement (ex '75'), commune (code INSEE), region, distance (km), typeContrat (codes CDI/CDD...), experience (1/2/3), qualification (0 non-cadre / 9 cadre), codeROME, salaireMin, tempsPlein (bool), alternance (bool). resultsWanted (défaut 15, max 150).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "motsCles": {"type": "string", "description": "Mots-clés (ex 'développeur web react')"},
                "departement": {"type": "string", "description": "Code département (ex '75', '69')"},
                "commune": {"type": "string", "description": "Code INSEE commune"},
                "region": {"type": "string", "description": "Code région"},
                "distance": {"type": "integer", "description": "Rayon en km autour de la commune"},
                "typeContrat": {"type": "string", "description": "Codes séparés par virgule (CDI,CDD,MIS...)"},
                "experience": {"type": "string", "description": "1=moins d'1an, 2=1à3ans, 3=plus de 3ans"},
                "qualification": {"type": "string", "description": "0=non-cadre, 9=cadre"},
                "codeROME": {"type": "string", "description": "Code ROME du métier (ex M1805) — recherche précise"},
                "salaireMin": {"type": "number", "description": "Salaire annuel minimum en euros"},
                "tempsPlein": {"type": "boolean"},
                "alternance": {"type": "boolean", "description": "true = offres en alternance"},
                "resultsWanted": {"type": "integer", "description": "Nombre d'offres (défaut 15, max 150)"},
            },
        },
    },
    {
        "name": "get_job",
        "description": "Détail complet d'une offre France Travail par son id (30+ champs : description, salaire, compétences, entreprise, contact, lien de candidature...).",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {
        "name": "list_referentiel",
        "description": "Référentiels officiels pour affiner les recherches. type ∈ {typesContrats, naturesContrats, communes, departements, regions, secteursActivites, niveauxFormations, langues, permis, appellations}.",
        "inputSchema": {"type": "object", "properties": {"type": {"type": "string"}}, "required": ["type"]},
    },
    {
        "name": "rome_search",
        "description": "Trouve le ou les codes ROME (métiers officiels) correspondant à un intitulé. Ex 'développeur' → M1805. Utiliser le code obtenu dans search_jobs(codeROME=...) pour des résultats précis.",
        "inputSchema": {"type": "object", "properties": {"metier": {"type": "string"}}, "required": ["metier"]},
    },
    {
        "name": "rome_metier",
        "description": "Fiche métier ROME complète par code : définition, accès à l'emploi, compétences principales ET émergentes (tendances), secteurs, statut cadre.",
        "inputSchema": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
    },
]

DISPATCH = {
    "search_jobs": tool_search_jobs,
    "get_job": tool_get_job,
    "list_referentiel": tool_list_referentiel,
    "rome_search": tool_rome_search,
    "rome_metier": tool_rome_metier,
}

# ─────────────────────────────────────────────────────────────────────────────
# Boucle JSON-RPC stdio
# ─────────────────────────────────────────────────────────────────────────────
def send(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def handle(msg):
    mid = msg.get("id")
    method = msg.get("method")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "francetravail", "version": "1.0.0"},
        }}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        fn = DISPATCH.get(name)
        if not fn:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Outil inconnu: {name}"}}
        try:
            result = fn(args)
            text = json.dumps(result, ensure_ascii=False, indent=2)
            return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}]}}
        except Exception as e:
            log("ERREUR tool", name, ":", repr(e))
            return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": f"Erreur: {e}"}], "isError": True}}
    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Méthode inconnue: {method}"}}
    return None

def main():
    log("francetravail MCP démarré (stdio)")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            send(resp)

if __name__ == "__main__":
    main()
