"""Agrégats CA / profit / analyse enrichie repris de l'ancien backend Django.

Adaptés au schéma actuel (Commande + LigneCommande + Expedition.en_retard).
N'altère pas les KPI summary / timeseries / bottlenecks existants.
"""

from django.db.models import Avg, Count, F, Q, Sum
from apps.logistics.models import Commande, Expedition, LigneCommande, Transporteur


def _is_all(value):
    return value is None or value == "" or str(value).upper() == "ALL"


def _f(x, nd=2):
    return 0.0 if x is None else round(float(x), nd)


def _marge(profit, ca):
    return round((profit / ca) * 100, 2) if ca else 0.0


def _param(params, *keys, default=None):
    for key in keys:
        if key in params and params.get(key) not in (None, ""):
            return params.get(key)
    return default


def _filter_commandes(params):
    qs = Commande.objects.all()
    segment = _param(params, "segment_client", "segment")
    marche = _param(params, "marche", "market")
    region = _param(params, "region")
    transporteur = _param(params, "transporteur")
    statut = _param(params, "statut_livraison", "delivery_status")
    date_min = _param(params, "date_min")
    date_max = _param(params, "date_max")

    if not _is_all(segment):
        qs = qs.filter(segment_client__iexact=segment)
    if not _is_all(marche):
        qs = qs.filter(marche__iexact=marche)
    if not _is_all(region):
        qs = qs.filter(region__iexact=region)
    if date_min:
        qs = qs.filter(date_commande__date__gte=date_min)
    if date_max:
        qs = qs.filter(date_commande__date__lte=date_max)
    if not _is_all(transporteur):
        qs = qs.filter(
            Q(expedition__transporteur__code=transporteur)
            | Q(expedition__transporteur__nom__iexact=transporteur)
        )
    if not _is_all(statut):
        qs = qs.filter(expedition__statut_livraison=statut)
    return qs.distinct()


def _filter_expeditions(params):
    qs = Expedition.objects.exclude(statut_livraison=Expedition.StatutLivraison.ANNULEE)
    segment = _param(params, "segment_client", "segment")
    marche = _param(params, "marche", "market")
    region = _param(params, "region")
    transporteur = _param(params, "transporteur")
    statut = _param(params, "statut_livraison", "delivery_status")
    date_min = _param(params, "date_min")
    date_max = _param(params, "date_max")

    if not _is_all(segment):
        qs = qs.filter(commande__segment_client__iexact=segment)
    if not _is_all(marche):
        qs = qs.filter(commande__marche__iexact=marche)
    if not _is_all(region):
        qs = qs.filter(commande__region__iexact=region)
    if date_min:
        qs = qs.filter(commande__date_commande__date__gte=date_min)
    if date_max:
        qs = qs.filter(commande__date_commande__date__lte=date_max)
    if not _is_all(transporteur):
        qs = qs.filter(
            Q(transporteur__code=transporteur) | Q(transporteur__nom__iexact=transporteur)
        )
    if not _is_all(statut):
        qs = qs.filter(statut_livraison=statut)
    return qs


def sales_profits(params=None):
    params = params or {}
    cmd_qs = _filter_commandes(params)

    totals = cmd_qs.aggregate(
        total_ca=Sum("montant_total"),
        total_profit=Sum("profit_total"),
        total_commandes=Count("id"),
    )
    total_ca = _f(totals["total_ca"])
    total_profit = _f(totals["total_profit"])

    ventes_par_seg = (
        cmd_qs.values("segment_client")
        .annotate(
            ca=Sum("montant_total"),
            profit=Sum("profit_total"),
            commandes=Count("id"),
        )
        .order_by("-ca")[:5]
    )
    data_segments = [
        {
            "segment": item["segment_client"] or "Autre",
            "ca": _f(item["ca"]),
            "profit": _f(item["profit"]),
            "marge_pct": _marge(_f(item["profit"]), _f(item["ca"])),
            "commandes": item["commandes"],
        }
        for item in ventes_par_seg
    ]

    lignes = LigneCommande.objects.filter(commande_id__in=cmd_qs.values("id"))
    ventes_par_prod = (
        lignes.values("product_name")
        .annotate(ca=Sum("montant_total"), profit=Sum("profit"))
        .order_by("-ca")[:5]
    )
    data_produits = [
        {
            "produit": item["product_name"] or "Inconnu",
            "ca": _f(item["ca"]),
            "profit": _f(item["profit"]),
            "marge_pct": _marge(_f(item["profit"]), _f(item["ca"])),
        }
        for item in ventes_par_prod
    ]

    top_marches = [
        {"market": item["marche"], "total": item["total"]}
        for item in (
            Commande.objects.values("marche")
            .annotate(total=Count("id"))
            .order_by("-total")[:3]
        )
        if item["marche"]
    ]

    return {
        "total_ca": total_ca,
        "total_profit": total_profit,
        "benefice_total": total_profit,
        "marge_globale_pct": _marge(total_profit, total_ca),
        "marge_beneficiaire_pct": _marge(total_profit, total_ca),
        "total_commandes": totals["total_commandes"] or 0,
        "ventes_par_segment": data_segments,
        "ventes_par_produit": data_produits,
        "top_marches": top_marches,
        "filter_options": {
            "segments": [
                s
                for s in Commande.objects.order_by("segment_client")
                .values_list("segment_client", flat=True)
                .distinct()
                if s
            ],
            "markets": [
                m
                for m in Commande.objects.order_by("marche")
                .values_list("marche", flat=True)
                .distinct()
                if m
            ],
        },
    }


def enriched(params=None):
    params = params or {}
    cmd_qs = _filter_commandes(params)
    exp_qs = _filter_expeditions(params)

    totaux_cmd = cmd_qs.aggregate(
        total_ca=Sum("montant_total"),
        total_profit=Sum("profit_total"),
        total_commandes=Count("id"),
    )
    total_remises = _f(
        LigneCommande.objects.filter(commande_id__in=cmd_qs.values("id")).aggregate(
            total=Sum("remise")
        )["total"]
    )
    total_ca = _f(totaux_cmd["total_ca"])
    total_profit = _f(totaux_cmd["total_profit"])

    total_exp = exp_qs.count()
    retards_count = exp_qs.filter(en_retard=True).count()
    taux_retard = round((retards_count / total_exp) * 100, 2) if total_exp else 0.0
    taux_a_temps = round(100 - taux_retard, 2) if total_exp else 0.0

    fiabilite_transporteurs = list(
        exp_qs.values(nom_transporteur=F("transporteur__nom"))
        .annotate(
            total_expeditions=Count("id"),
            retards=Count("id", filter=Q(en_retard=True)),
            delai_moyen_reel=Avg("delai_reel_jours"),
            delai_moyen_prevu=Avg("delai_prevu_jours"),
        )
        .order_by("-total_expeditions")
    )
    for row in fiabilite_transporteurs:
        row["delai_moyen_reel"] = _f(row["delai_moyen_reel"], 1)
        row["delai_moyen_prevu"] = _f(row["delai_moyen_prevu"], 1)

    blocages_regionaux = list(
        exp_qs.values(region=F("commande__region"), pays=F("commande__pays"))
        .annotate(
            total_commandes=Count("id"),
            nb_retards=Count("id", filter=Q(en_retard=True)),
            ca_affecte=Sum("commande__montant_total"),
        )
        .order_by("-nb_retards")[:10]
    )
    for row in blocages_regionaux:
        row["ca_affecte"] = _f(row["ca_affecte"])

    categories_stats = list(
        LigneCommande.objects.filter(commande_id__in=cmd_qs.values("id"))
        .values("category_name")
        .annotate(
            ca=Sum("montant_total"),
            profit=Sum("profit"),
            volume=Count("id"),
        )
        .order_by("-ca")[:5]
    )
    for row in categories_stats:
        row["ca"] = _f(row["ca"])
        row["profit"] = _f(row["profit"])
        if not row["category_name"]:
            row["category_name"] = "Inconnu"

    return {
        "kpis": {
            "total_ca": total_ca,
            "total_profit": total_profit,
            "benefice_total": total_profit,
            "total_remises": total_remises,
            "marge_globale_pct": _marge(total_profit, total_ca),
            "marge_beneficiaire_pct": _marge(total_profit, total_ca),
            "total_commandes": totaux_cmd["total_commandes"] or 0,
            "taux_a_temps_pct": taux_a_temps,
            "taux_retard_pct": taux_retard,
            "top_marches": [
                {"market": item["marche"], "total": item["total"]}
                for item in (
                    cmd_qs.values("marche")
                    .annotate(total=Count("id"))
                    .order_by("-total")[:3]
                )
                if item["marche"]
            ],
        },
        "fiabilite_transporteurs": fiabilite_transporteurs,
        "blocages_regionaux": blocages_regionaux,
        "categories_stats": categories_stats,
        "filters": {
            "markets": [
                m
                for m in Commande.objects.order_by("marche")
                .values_list("marche", flat=True)
                .distinct()
                if m
            ],
            "segments": [
                s
                for s in Commande.objects.order_by("segment_client")
                .values_list("segment_client", flat=True)
                .distinct()
                if s
            ],
            "transporteurs": list(
                Transporteur.objects.order_by("nom").values_list("nom", flat=True)
            ),
            "delivery_status": [
                s
                for s in Expedition.objects.order_by("statut_livraison")
                .values_list("statut_livraison", flat=True)
                .distinct()
                if s
            ],
        },
    }
