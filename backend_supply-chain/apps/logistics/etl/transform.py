
import pandas as pd
from .config import (DATE_FORMAT, STATUT_LIVRAISON, TARIF_MODE, COUT_PAR_ARTICLE,
                    PENALITE_JOUR_RETARD, REQUIRED)


TEXT_COLS = ["statut", "segment_client", "marche", "region", "pays", "ville",
            "product_name", "category_name", "mode_expedition", "statut_livraison_source"]
NUM_COLS = ["order_id", "order_item_id", "product_card_id", "client_id", "quantite",
            "prix_unitaire", "remise", "taux_remise", "ratio_profit", "montant_ligne",
            "profit_ligne", "delai_reel", "delai_prevu"]

def transform(raw: pd.DataFrame):
    stats = {"rows_in": len(raw)}
    df = raw.copy()
    
    # 1) Typage
    for c in ("date_commande", "date_expedition"):
        df[c] = pd.to_datetime(df[c], format=DATE_FORMAT, errors="coerce", utc=True)
    for c in NUM_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in TEXT_COLS:
        df[c] = df[c].astype("string").str.strip()
    df["ville"] = df["ville"].fillna("")
    
    # 2) Validation ligne à ligne : on REJETTE (avec motif) au lieu de planter ou de deviner
    actual_retard = df["delai_reel"] > df["delai_prevu"]
    checks = pd.concat({
        "champ_obligatoire_manquant": df[REQUIRED].isna().any(axis=1),
        "delai_negatif": (df["delai_reel"] < 0) | (df["delai_prevu"] < 0),
        "quantite_invalide": df["quantite"] <= 0,
        "mode_inconnu": ~df["mode_expedition"].isin(list(TARIF_MODE)),
        "statut_livraison_inconnu": ~df["statut_livraison_source"].isin(list(STATUT_LIVRAISON)),
        "statut_livraison_incoherent": (
            (df["statut_livraison_source"] == "Late delivery") & ~actual_retard
        ) | (
            (df["statut_livraison_source"] == "Advance shipping") & actual_retard
        ) | (
            (df["statut_livraison_source"] == "Shipping on time") & (df["delai_reel"] != df["delai_prevu"])
        ) | (
            (df["statut_livraison_source"] == "Shipping canceled") & actual_retard
        ),
    }, axis=1)
    bad = checks.any(axis=1)
    motif = (checks[bad].apply(lambda r: ",".join(r.index[r]), axis=1)
            if bad.any() else pd.Series(dtype="string"))
    rejects = df[bad].assign(motif=motif)
    df = df[~bad]
    stats["rows_rejected"] = int(bad.sum())
    
    # 3) Doublons stricts
    before = len(df)
    df = df.drop_duplicates()
    stats["duplicates_dropped"] = before - len(df)

    duplicate_item_ids = df["order_item_id"].duplicated(keep=False)
    if duplicate_item_ids.any():
        duplicate_lines = df[duplicate_item_ids].assign(motif="order_item_id_duplique")
        rejects = pd.concat([rejects, duplicate_lines], ignore_index=True)
        df = df[~duplicate_item_ids]
        stats["rows_rejected"] += len(duplicate_lines)
    
    # 4) Cohérence intra-commande : mode, délais et statut doivent être uniques par commande
    nun = df.groupby("order_id")[["mode_expedition", "delai_reel", "delai_prevu", "statut_livraison_source"]].nunique()
    stats["commandes_incoherentes"] = int((nun > 1).any(axis=1).sum())
    
    # 5) Agrégation : lignes d'articles vers une ligne par commande
    first = ["date_commande", "date_expedition", "statut", "client_id", "segment_client", "marche",
            "region", "pays", "ville", "mode_expedition", "delai_reel", "delai_prevu",
            "statut_livraison_source"]
    agg = {c: "first" for c in first}
    agg.update(quantite="sum", montant_ligne="sum", profit_ligne="sum")
    orders = df.sort_values("order_id").groupby("order_id", as_index=False).agg(agg)
    orders = orders.rename(columns={"quantite": "nb_articles", "montant_ligne": "montant_total",
                                   "profit_ligne": "profit_total"})
    line_counts = df.groupby("order_id").size()
    orders["nb_lignes_commande"] = orders["order_id"].map(line_counts).astype("int64")
    for c in ("order_id", "client_id", "nb_lignes_commande", "nb_articles", "delai_reel", "delai_prevu"):
        orders[c] = orders[c].astype("int64")

    line_items = df[["order_item_id", "order_id", "product_card_id", "product_name", "category_name",
                     "quantite", "prix_unitaire", "remise", "taux_remise", "ratio_profit",
                     "montant_ligne", "profit_ligne"]].copy()
    line_items = line_items.rename(columns={"montant_ligne": "montant_total", "profit_ligne": "profit"})
    for column in ("order_item_id", "order_id", "product_card_id", "quantite"):
        line_items[column] = line_items[column].astype("int64")
    for column in ("prix_unitaire", "remise", "montant_total", "profit"):
        line_items[column] = line_items[column].round(2)
    for column in ("taux_remise", "ratio_profit"):
        line_items[column] = line_items[column].round(6)
    
    # 6) Champs dérivés
    orders["ecart_jours"] = orders["delai_reel"] - orders["delai_prevu"]
    orders["statut_livraison"] = orders["statut_livraison_source"].map(STATUT_LIVRAISON)
    orders["en_retard"] = orders["statut_livraison"].eq("en_retard")
    retard = orders["ecart_jours"].clip(lower=0)
    orders["cout_estime"] = (orders["mode_expedition"].map(TARIF_MODE)
                            + COUT_PAR_ARTICLE * orders["nb_articles"]
                            + PENALITE_JOUR_RETARD * retard).round(2)
    orders["montant_total"] = orders["montant_total"].round(2)
    orders["profit_total"] = orders["profit_total"].round(2)
    
    # 7) Contrôle de concordance : "en retard" (statut source) vs délai réel > prévu
    actives = orders["statut_livraison"] != "annulee"
    stats["incoherences_retard"] = int(((orders["en_retard"] != (orders["ecart_jours"] > 0)) &
        actives).sum())
    stats["orders_out"] = len(orders)
    stats["order_lines_out"] = len(line_items)
    return orders, line_items, rejects, stats