
from decimal import Decimal


COLUMNS = {
    "Order Id": "order_id",
    "order date (DateOrders)": "date_commande",
    "shipping date (DateOrders)": "date_expedition",
    "Order Status": "statut",
    "Customer Id": "client_id",
    "Customer Segment": "segment_client",
    "Market": "marche",
    "Order Region": "region",
    "Order Country": "pays",
    "Order City": "ville",
    "Order Item Id": "order_item_id",
    "Product Card Id": "product_card_id",
    "Product Name": "product_name",
    "Category Name": "category_name",
    "Order Item Quantity": "quantite",
    "Order Item Product Price": "prix_unitaire",
    "Order Item Discount": "remise",
    "Order Item Discount Rate": "taux_remise",
    "Order Item Profit Ratio": "ratio_profit",
    "Order Item Total": "montant_ligne",
    "Order Profit Per Order": "profit_ligne",
    "Shipping Mode": "mode_expedition",
    "Days for shipping (real)": "delai_reel",
    "Days for shipment (scheduled)": "delai_prevu",
    "Delivery Status": "statut_livraison_source",
    "Late_delivery_risk": "late_flag_source",
}

DATE_FORMAT = "%m/%d/%Y %H:%M"

STATUT_LIVRAISON = {
    "Late delivery": "en_retard",
    "Advance shipping": "en_avance",
    "Shipping on time": "a_temps",
    "Shipping canceled": "annulee",
}

# Grille de coût ESTIMÉ (le jeu n'a pas de coût de transport) — à documenter dans le README
TARIF_MODE = {"Same Day": 18.0, "First Class": 12.0, "Second Class": 8.0, "Standard Class": 5.0}

COUT_PAR_ARTICLE = 0.35

PENALITE_JOUR_RETARD = 2.50

REQUIRED = ["order_id", "order_item_id", "product_card_id", "date_commande", "statut",
            "client_id", "marche", "region", "quantite", "montant_ligne", "profit_ligne",
            "mode_expedition", "delai_reel", "delai_prevu", "statut_livraison_source"]


