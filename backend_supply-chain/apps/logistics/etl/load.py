
import pandas as pd
from django.db import transaction
from django.utils.text import slugify
from apps.logistics.models import Commande, Entrepot, Expedition, LigneCommande, Transporteur

BATCH = 2000

def _dt(x):
    return None if pd.isna(x) else x.to_pydatetime()


@transaction.atomic
def load(orders: pd.DataFrame, line_items: pd.DataFrame) -> dict:
    # Dimensions : update_or_create => relançable sans doublon
    transporteurs = {m: Transporteur.objects.update_or_create(code=slugify(m), defaults={"nom":
        m})[0]
                    for m in orders["mode_expedition"].unique()}
    entrepots = {m: Entrepot.objects.update_or_create(code=slugify(m), defaults={"nom": f"Hub{m}"})[0]
                for m in orders["marche"].unique()}
    
    commandes = [Commande(
        order_id=r.order_id, date_commande=r.date_commande.to_pydatetime(), statut=r.statut,
        client_id=r.client_id, segment_client=r.segment_client, marche=r.marche, region=r.region,
        pays=r.pays, ville=r.ville, nb_articles=r.nb_articles,
        nb_lignes_commande=r.nb_lignes_commande,
        montant_total=r.montant_total, profit_total=r.profit_total,
    ) for r in orders.itertuples(index=False)]
    
    Commande.objects.bulk_create(
        commandes, batch_size=BATCH, update_conflicts=True, unique_fields=["order_id"],
        update_fields=["date_commande", "statut", "client_id", "segment_client", "marche", "region",
                    "pays", "ville", "nb_lignes_commande", "nb_articles", "montant_total", "profit_total"])
    
    ids = dict(Commande.objects.values_list("order_id", "id"))
    expeditions = [Expedition(
        commande_id=ids[r.order_id], transporteur=transporteurs[r.mode_expedition],
        entrepot=entrepots[r.marche], date_expedition=_dt(r.date_expedition),
        delai_prevu_jours=r.delai_prevu, delai_reel_jours=r.delai_reel, ecart_jours=r.ecart_jours,
        statut_livraison=r.statut_livraison, en_retard=bool(r.en_retard), cout_estime=r.cout_estime,
    ) for r in orders.itertuples(index=False)]
    
    Expedition.objects.bulk_create(
        expeditions, batch_size=BATCH, update_conflicts=True, unique_fields=["commande"],
        update_fields=["transporteur", "entrepot", "date_expedition", "delai_prevu_jours",
                    "delai_reel_jours", "ecart_jours", "statut_livraison", "en_retard",
                        "cout_estime"])

    order_ids = [ids[order_id] for order_id in orders["order_id"].tolist()]
    LigneCommande.objects.filter(commande_id__in=order_ids).delete()
    ligne_commandes = [LigneCommande(
        commande_id=ids[r.order_id], order_item_id=r.order_item_id,
        product_card_id=r.product_card_id, product_name=r.product_name,
        category_name=r.category_name, quantite=r.quantite,
        prix_unitaire=r.prix_unitaire, remise=r.remise, taux_remise=r.taux_remise,
        ratio_profit=r.ratio_profit, montant_total=r.montant_total, profit=r.profit,
    ) for r in line_items.itertuples(index=False)]
    LigneCommande.objects.bulk_create(ligne_commandes, batch_size=BATCH)
    return {
        "commandes": len(commandes),
        "expeditions": len(expeditions),
        "lignes_commande": len(ligne_commandes),
    }
