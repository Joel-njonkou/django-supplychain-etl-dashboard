
from datetime import date
from apps.api import kpis
from .analysis import analyse_bottlenecks

class ToolError(Exception):
    pass
FILTERS = {
    "date_min": {"type": ["string", "null"], "description": "Date minimale YYYY-MM-DD"},
    "date_max": {"type": ["string", "null"], "description": "Date maximale YYYY-MM-DD"},
    "region": {"type": ["string", "null"], "description": "Région exacte, ex. Western Europe"},
    "transporteur": {"type": ["string", "null"], "enum": [
        "standard-class", "second-class", "first-class", "same-day", None]},
}

def _fn(name, desc, extra=None, required=None):
    props = {**FILTERS, **(extra or {})}
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props, "required": required or [],
                        "additionalProperties": False}}}
TOOLS = [
    _fn("kpi_summary", "KPI globaux : volume, retards, taux de retard, taux de livraison à temps, "
                        "retard moyen (jours), coût estimé moyen. Filtres optionnels."),
    _fn("timeseries", "Évolution des KPI dans le temps.",
        {"granularity": {"type": ["string", "null"], "enum": ["day", "week", "month", None]}}),
    _fn("bottlenecks", "Classement des points de blocage par nombre de retards (volume minimum appliqué).",
        {"by": {"type": ["string", "null"], "enum": [
            "region", "transporteur", "region_transporteur", None]},
        "limit": {"type": ["integer", "null"], "minimum": 1, "maximum": 20}}),
    _fn("analyse_goulots", "Analyse complète : retards en excès, part de variabilité expliquée par mode et par "
                            "région, écart de planification, constats. À privilégier pour « pourquoi » ou « où »."),
]

ALLOWED = {t["function"]["name"]: set(t["function"]["parameters"]["properties"]) for t in TOOLS}

def _clean(args):
    out = {}
    for k in ("date_min", "date_max"):
        if args.get(k):
            try:
                date.fromisoformat(str(args[k]))
            except ValueError:
                raise ToolError(f"{k} doit être au format YYYY-MM-DD")
            out[k] = str(args[k])
    for k in ("region", "transporteur"):
        if args.get(k):
            out[k] = str(args[k])[:60]
    return out

def execute_tool(name, args):
    if name not in ALLOWED:
        raise ToolError(f"outil inconnu : {name}")
    if not isinstance(args, dict):
        raise ToolError("arguments invalides")
    inconnus = set(args) - ALLOWED[name]
    if inconnus:
        raise ToolError(f"paramètres non autorisés : {sorted(inconnus)}")
    f = _clean(args)
    qs = kpis.base_queryset(f)
    if name == "kpi_summary":
        return kpis.summary(qs)
    if name == "timeseries":
        g = args.get("granularity") or "week"
        if g not in ("day", "week", "month"):
            raise ToolError("granularity invalide")
        return kpis.timeseries(qs, g)[-60:]     # borne la taille du résultat
    if name == "bottlenecks":
        by = args.get("by") or "region_transporteur"
        limit = max(1, min(int(args.get("limit") or 8), 20))
        return kpis.bottlenecks(qs, by, 100, limit)
    
    return analyse_bottlenecks(f) or {"erreur": "aucune donnée pour ces filtres"}