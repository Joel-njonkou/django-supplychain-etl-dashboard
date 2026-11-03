
from rest_framework import serializers
from apps.logistics.models import Commande, Entrepot, EtlRun, Expedition, Transporteur
from apps.logistics.models import LigneCommande


class TransporteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transporteur
        fields = ["id", "code", "nom"]
class EntrepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrepot
        fields = ["id", "code", "nom"]
class ExpeditionSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="commande.order_id", read_only=True)
    region = serializers.CharField(source="commande.region", read_only=True)
    date_commande = serializers.DateTimeField(source="commande.date_commande", read_only=True)
    transporteur = TransporteurSerializer(read_only=True)
    entrepot = EntrepotSerializer(read_only=True)
    class Meta:
        model = Expedition
        fields = ["id", "order_id", "region", "date_commande", "transporteur", "entrepot", "date_expedition", "delai_prevu_jours", 
                    "delai_reel_jours", "ecart_jours", "statut_livraison", "en_retard", "cout_estime"]

class CommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = ["id", "order_id", "date_commande", "statut", "segment_client", "marche", "region",
                "pays", "ville", "nb_lignes_commande", "nb_articles", "montant_total", "profit_total"]

class LigneCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneCommande
        fields = ["order_item_id", "product_card_id", "product_name", "category_name", "quantite",
                  "prix_unitaire", "remise", "taux_remise", "ratio_profit", "montant_total", "profit"]

class CommandeDetailSerializer(CommandeSerializer):
    expedition = ExpeditionSerializer(read_only=True)
    lignes_commande = LigneCommandeSerializer(many=True, read_only=True)
    class Meta(CommandeSerializer.Meta):
        fields = CommandeSerializer.Meta.fields + ["expedition", "lignes_commande"]
class EtlRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtlRun
        fields = "__all__"