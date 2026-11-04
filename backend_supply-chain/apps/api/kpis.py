
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from rest_framework.exceptions import ValidationError
from apps.logistics.models import Expedition
from .filters import ExpeditionFilter

TRUNC = {"day": TruncDay, "week": TruncWeek, "month": TruncMonth}
GROUPS = {"region": ["commande__region"], "transporteur": ["transporteur__nom"],
        "region_transporteur": ["commande__region", "transporteur__nom"]}
AGG = dict(volume=Count("id"), retards=Count("id", filter=Q(en_retard=True)),
            cout_moyen=Avg("cout_estime"), retard_moyen=Avg("ecart_jours", filter=Q(en_retard=True)))

def base_queryset(params=None):
    qs = Expedition.objects.exclude(statut_livraison=Expedition.StatutLivraison.ANNULEE)
    fs = ExpeditionFilter(params or {}, queryset=qs)
    if not fs.is_valid():
        raise ValidationError(fs.errors)
    return fs.qs

def _f(x, nd=2):
    return None if x is None else round(float(x), nd)

def _rates(row):
    v, r = row["volume"], row["retards"]
    return {"volume": v, "retards": r, "taux_retard": round(r / v, 4) if v else None,
            "taux_livraison_a_temps": round((v - r) / v, 4) if v else None,
            "retard_moyen_jours": _f(row["retard_moyen"]), "cout_moyen": _f(row["cout_moyen"])}
        
def summary(qs):
    return _rates(qs.aggregate(**AGG))

def timeseries(qs, granularity="week"):
    if granularity not in TRUNC:
        raise ValidationError({"granularity": "day, week ou month"})
    rows = (qs.annotate(periode=TRUNC[granularity]("commande__date_commande"))
            .values("periode").annotate(**AGG).order_by("periode"))
    return [{"periode": r["periode"].date(), **_rates(r)} for r in rows]

def bottlenecks(qs, by="region_transporteur", min_volume=100, limit=10):
    if by not in GROUPS:
        raise ValidationError({"by": "region, transporteur ou region_transporteur"})
    fields = GROUPS[by]
    rows = (qs.values(*fields).annotate(**AGG)
            .filter(volume__gte=min_volume)
            .order_by("-retards")[:limit])
    out = []
    for r in rows:
        item = {"region": r.get("commande__region"), "transporteur": r.get("transporteur__nom"),
            **_rates(r)}
        out.append({k: v for k, v in item.items() if v is not None or k not in ("region", "transporteur")})
    return out
            