
import pandas as pd
import pytest
from pathlib import Path
from apps.logistics.etl.extract import extract
from apps.logistics.etl.transform import transform

SAMPLE = Path(__file__).resolve().parents[4] / "data" / "samples" / "mini.csv"

@pytest.fixture(scope="module")
def result():
    return transform(extract(SAMPLE))

def test_une_ligne_par_commande(result):
    orders, _, _, _ = result
    assert orders["order_id"].is_unique

def test_aggregation_conserve_et_somme_toutes_les_lignes():
    raw = extract(SAMPLE).iloc[[0]].copy()
    second = raw.copy()
    second["order_item_id"] = int(raw.iloc[0]["order_item_id"]) + 10000000
    raw.loc[:, "order_id"] = 999999
    second.loc[:, "order_id"] = 999999
    raw.loc[:, "quantite"] = 1
    second.loc[:, "quantite"] = 2
    raw.loc[:, "montant_ligne"] = 10.25
    second.loc[:, "montant_ligne"] = 20.50
    raw.loc[:, "profit_ligne"] = 3.25
    second.loc[:, "profit_ligne"] = 4.75

    orders, lines, rejects, stats = transform(pd.concat([raw, second], ignore_index=True))

    assert rejects.empty
    assert len(orders) == 1
    assert orders.iloc[0]["nb_lignes_commande"] == 2
    assert orders.iloc[0]["nb_articles"] == 3
    assert orders.iloc[0]["montant_total"] == 30.75
    assert orders.iloc[0]["profit_total"] == 8.00
    assert len(lines) == stats["order_lines_out"] == 2
    
def test_les_lignes_invalides_sont_rejetees_avec_motif(result):
    _, _, rejects, stats = result
    assert stats["rows_rejected"] == len(rejects) >= 1
    assert rejects["motif"].str.len().min() > 0
    
def test_ecart_et_retard_coherents(result):
    orders, _, _, stats = result
    assert (orders["ecart_jours"] == orders["delai_reel"] - orders["delai_prevu"]).all()
    assert stats["incoherences_retard"] == 0
    
def test_cout_estime_positif(result):
    orders, _, _, _ = result
    assert (orders["cout_estime"] > 0).all()
    
@pytest.mark.django_db
def test_chargement_idempotent(result):
    from apps.logistics.etl.load import load
    from apps.logistics.models import Commande, Expedition, LigneCommande
    orders, lines, _, _ = result
    load(orders, lines)
    n1 = (Commande.objects.count(), Expedition.objects.count(), LigneCommande.objects.count())
    load(orders, lines)
    assert (Commande.objects.count(), Expedition.objects.count(), LigneCommande.objects.count()) == n1

@pytest.mark.django_db
def test_chargement_partiel_ne_supprime_pas_les_lignes_des_autres_commandes(result):
    from apps.logistics.etl.load import load
    from apps.logistics.models import LigneCommande
    orders, lines, _, _ = result
    load(orders, lines)
    untouched_order_id = int(orders.iloc[-1]["order_id"])
    partial_order = orders.iloc[[0]]
    partial_lines = lines[lines["order_id"] == partial_order.iloc[0]["order_id"]]

    load(partial_order, partial_lines)

    assert LigneCommande.objects.filter(commande__order_id=untouched_order_id).exists()
