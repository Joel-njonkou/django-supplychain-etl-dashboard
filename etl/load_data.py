import os
import sys
import django
import pandas as pd
from datetime import datetime
from django.utils.timezone import make_aware # cest la fonction django pour transformer une date naive en date consciente

# Configuration du chemin relatif
current_dir = os.path.dirname(os.path.abspath(__file__)) # on recherche dans quel path se trouve load_data.py
project_root = os.path.abspath(os.path.join(current_dir, '..')) # on sort du dossier actuelle pour retrouver les modèles
if project_root not in sys.path:
    sys.path.insert(0, project_root)# on va fouiller la racine du projet

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'supplychain_core.settings') #indiquons le fichier de configuration settings 
django.setup() # initialise un env django

#importons nos modèles
from logistics.models import Entrepot, Transporteur, Commande, Expedition

def run_etl():
    csv_path = os.path.join(project_root, 'etl', 'DataCoSupplyChainDataset.csv') #importons le csv du devoir

    
    print(" 1. EXTRACTION : Lecture du fichier CSV DataCo ")
    # Lecture du fichier CSV avec l'encodage robuste
    df = pd.read_csv(csv_path, encoding='latin1')
    print(f"Nombre de lignes brutes chargées : {len(df)}")

    # NOTE : La purge (.delete()) a été supprimée ici pour sécuriser vos données !

    # 2. Préparation du cache et des listes
    entrepot_objs = {}
    transporteur_objs = {}

    commandes_batch = []
    expeditions_batch = []
    print("\n2. TRAITEMENT DES LIGNES...")

    # On utilise enumerate pour garantir un order_item_id unique pour CHAQUE ligne (1 à 180 519)
    for idx, (index, row) in enumerate(df.iterrows(), start=1):

        #  Gestion de l'Entrepôt (Département)
        dept_id = int(row['Department Id']) if pd.notna(row['Department Id']) else 0
        dept_name = str(row['Department Name']) if pd.notna(row['Department Name']) else 'Général'
        
        if dept_id not in entrepot_objs:
            entrepot, _ = Entrepot.objects.get_or_create(
                departement_id=dept_id,
                defaults={'departement_name': dept_name}
            )
            entrepot_objs[dept_id] = entrepot
        else:
            entrepot = entrepot_objs[dept_id]

        #  Gestion du Transporteur (Shipping Mode)
        shipping_mode = str(row['Shipping Mode']) if pd.notna(row['Shipping Mode']) else 'Standard Class'
        if shipping_mode not in transporteur_objs:
            transporteur, _ = Transporteur.objects.get_or_create(name=shipping_mode)
            transporteur_objs[shipping_mode] = transporteur
        else:
            transporteur = transporteur_objs[shipping_mode]

        #  Parsing des dates
        try:
            dt_order = pd.to_datetime(row['order date (DateOrders)']).to_pydatetime()
            order_date = make_aware(dt_order)
        except Exception:
            order_date = make_aware(datetime.now())

        try:
            dt_shipping = pd.to_datetime(row['shipping date (DateOrders)']).to_pydatetime()
            shipping_date = make_aware(dt_shipping)   
        except Exception:
            shipping_date = None

        #  Nom du client
        fname = str(row['Customer Fname']) if pd.notna(row['Customer Fname']) else ''
        lname = str(row['Customer Lname']) if pd.notna(row['Customer Lname']) else ''
        customer_name = f"{fname} {lname}".strip() or "Client Inconnu"

        # Création de l'objet Commande
        order_id = int(row['Order Id']) if pd.notna(row['Order Id']) else idx

        commande = Commande(
            order_id=order_id,
            order_item_id=idx,  # Clé primaire unique de la ligne (1 à 180519)
            order_date=order_date,
            order_status=str(row['Order Status']) if pd.notna(row['Order Status']) else 'COMPLETE',
            payment_type=str(row['Type']) if pd.notna(row['Type']) else 'DEBIT',

            # Client
            customer_id=int(row['Customer Id']) if pd.notna(row['Customer Id']) else 0,
            customer_name=customer_name,
            customer_segment=str(row['Customer Segment']) if pd.notna(row['Customer Segment']) else 'Consumer',
            customer_country=str(row['Customer Country']) if pd.notna(row['Customer Country']) else '',
            customer_city=str(row['Customer City']) if pd.notna(row['Customer City']) else '',

            # Destination
            market=str(row['Market']) if pd.notna(row['Market']) else 'Non spécifié',
            order_region=str(row['Order Region']) if pd.notna(row['Order Region']) else 'Non spécifiée',
            order_country=str(row['Order Country']) if pd.notna(row['Order Country']) else 'Non spécifié',
            order_city=str(row['Order City']) if pd.notna(row['Order City']) else 'Non spécifiée',
            latitude=float(row['Latitude']) if pd.notna(row['Latitude']) else 0.0,
            longitude=float(row['Longitude']) if pd.notna(row['Longitude']) else 0.0,

            # Produit
            product_card_id=int(row['Product Card Id']) if pd.notna(row['Product Card Id']) else 0,
            product_name=str(row['Product Name']) if pd.notna(row['Product Name']) else 'Inconnu',
            category_id=int(row['Category Id']) if pd.notna(row['Category Id']) else 0,
            category_name=str(row['Category Name']) if pd.notna(row['Category Name']) else 'Général',

            # Finances
            product_price=float(row['Product Price']) if pd.notna(row['Product Price']) else 0.0,
            order_item_quantity=int(row['Order Item Quantity']) if pd.notna(row['Order Item Quantity']) else 1,
            sales_before_discount=float(row['Sales']) if pd.notna(row['Sales']) else 0.0,
            discount_amount=float(row['Order Item Discount']) if pd.notna(row['Order Item Discount']) else 0.0,
            discount_rate=float(row['Order Item Discount Rate']) if pd.notna(row['Order Item Discount Rate']) else 0.0,
            sales=float(row['Order Item Total']) if pd.notna(row['Order Item Total']) else 0.0,
            benefit_per_order=float(row['Order Profit Per Order']) if pd.notna(row['Order Profit Per Order']) else 0.0,

            entrepot=entrepot
        )
        commandes_batch.append(commande)

        # f. Création de l'objet Expedition
        risk_val = row['Late_delivery_risk']
        risk = True if str(risk_val) in ['1', '1.0', 'True'] else False

        expedition = Expedition(
            commande=commande,
            shipping_date=shipping_date,
            days_for_shipping_real=int(row['Days for shipping (real)']) if pd.notna(row['Days for shipping (real)']) else 0,
            days_for_shipment_scheduled=int(row['Days for shipment (scheduled)']) if pd.notna(row['Days for shipment (scheduled)']) else 0,
            delivery_status=str(row['Delivery Status']) if pd.notna(row['Delivery Status']) else 'Shipping on time',
            late_delivery_risk=risk,
            transporteur=transporteur
        )
        expeditions_batch.append(expedition)

    # 3. Insertion en base de données par lots
    print("\n3. CHARGEMENT FINAL : Enregistrement en base de données...")
    batch_size = 5000
    for i in range(0, len(commandes_batch), batch_size):
        Commande.objects.bulk_create(commandes_batch[i:i+batch_size], ignore_conflicts=True)
        Expedition.objects.bulk_create(expeditions_batch[i:i+batch_size], ignore_conflicts=True)
        print(f"  -> Lot {i // batch_size + 1} inséré ({min(i + batch_size, len(commandes_batch))} / {len(commandes_batch)} lignes)")

    
    print(f"SUCCÈS ! {Commande.objects.count()} commandes et {Expedition.objects.count()} expéditions en base de données !")
    

if __name__ == '__main__':
    run_etl()