
from django.db.models import Avg, Count, Q
from apps.api import kpis

def _pct(x):
    return round(100 * x, 1)
def _rows(qs, fields):
    return list(qs.values(*fields).annotate(
        volume=Count("id"), retards=Count("id", filter=Q(en_retard=True)),
        prevu=Avg("delai_prevu_jours"), reel=Avg("delai_reel_jours"), cout=Avg("cout_estime")))
    
def _eta2(rows, p0, n):
    # Part de la variance du retard (variable 0/1) expliquée par le regroupement : 0 = aucune, 1 = totale
    total = p0 * (1 - p0)
    if total == 0:
        return 0.0
    between = sum((r["volume"] / n) * ((r["retards"] / r["volume"]) - p0) ** 2 for r in rows if
        r["volume"])
    return between / total

def analyse_bottlenecks(params=None, min_volume=100, top=5):
    qs = kpis.base_queryset(params)
    n = qs.count()
    if n == 0:
        return None
    late = qs.filter(en_retard=True).count()
    p0 = late / n
    modes = _rows(qs, ["transporteur__nom"])
    regions = _rows(qs, ["commande__region"])
    cells = [c for c in _rows(qs, ["commande__region", "transporteur__nom"]) if c["volume"] >=
        min_volume]
    mode_rate = {m["transporteur__nom"]: m["retards"] / m["volume"] for m in modes}
    items = []
    for c in cells:
        taux = c["retards"] / c["volume"]
        items.append({
            "region": c["commande__region"], "transporteur": c["transporteur__nom"],
            "volume": c["volume"], "retards": c["retards"], "taux_retard_pct": _pct(taux),
            "retards_en_exces": round(c["retards"] - p0 * c["volume"]),          # vs taux global
            "ecart_au_mode_points": _pct(taux - mode_rate[c["transporteur__nom"]]),   # effet région, mode neutralisé
            "cout_estime_moyen": round(float(c["cout"]), 2),
        })
    par_volume = sorted(items, key=lambda i: i["retards"], reverse=True)[:top]
    par_exces = sorted(items, key=lambda i: i["retards_en_exces"], reverse=True)[:top]
    mode_info = [{"transporteur": m["transporteur__nom"], "volume": m["volume"],
                  "taux_retard_pct": _pct(m["retards"] / m["volume"]),
                  "delai_prevu_moyen_jours": round(float(m["prevu"]), 2),
                  "delai_reel_moyen_jours": round(float(m["reel"]), 2),
                  "ecart_planification_jours": round(float(m["reel"] - m["prevu"]), 2)}
                 for m in sorted(modes, key=lambda m: -m["retards"] / m["volume"])]
    eta_mode, eta_region = _eta2(modes, p0, n), _eta2(regions, p0, n)
    ev = {
        "global": {"volume": n, "retards": late, "taux_retard_pct": _pct(p0)},
        "classement_par_volume_de_retards": par_volume,
        "classement_par_retards_en_exces": par_exces,
        "modes": mode_info,
        "part_variabilite_expliquee_pct": {"transporteur": _pct(eta_mode), "region":
            _pct(eta_region)},
        "note_cout": "cout_estime_moyen est une ESTIMATION qui inclut une pénalité de retard : "
                     "la corrélation coût/retard est vraie par construction.",
    }
    ev["constats"] = _constats(ev, eta_mode, eta_region)
    return ev

def _constats(ev, eta_mode, eta_region):
    out = []
    if eta_mode >= 0.05 and eta_mode >= 3 * max(eta_region, 0.001):
        out.append({"id": "STRUCTUREL_MODE",
                    "texte": "Le retard dépend surtout du mode d'expédition, très peu de la région "
                            f"({_pct(eta_mode)} % de la variabilité contre {_pct(eta_region)} %)."})
    for m in ev["modes"]:
        if m["taux_retard_pct"] >= 70 and m["ecart_planification_jours"] >= 0.5:
            out.append({"id": "PROMESSE_IRREALISTE", "texte": f"{m['transporteur']} : {m['taux_retard_pct']} % de retard, délai prévu "
                                f"{m['delai_prevu_moyen_jours']} j contre {m['delai_reel_moyen_jours']} j réels."})
    vol = {(i["region"], i["transporteur"]) for i in ev["classement_par_volume_de_retards"]}
    exc = {(i["region"], i["transporteur"]) for i in ev["classement_par_retards_en_exces"]}
    if vol != exc:
        out.append({"id": "EFFET_VOLUME",
                    "texte": "Le classement par nombre de retards est dominé par les gros volumes ;"
                            "le classement par retards en excès désigne d'autres couples."})
    return out