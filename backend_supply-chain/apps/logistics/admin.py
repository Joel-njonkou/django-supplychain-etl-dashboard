from django.contrib import admin
from .models import Commande, Entrepot, EtlRun, Expedition, Transporteur
from .models import LigneCommande

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ("order_id", "date_commande", "statut", "region", "nb_lignes_commande", "montant_total")
    list_filter = ("statut", "marche", "segment_client")
    search_fields = ("order_id",)

@admin.register(Expedition)
class ExpeditionAdmin(admin.ModelAdmin):
    list_display = ("commande", "transporteur", "statut_livraison", "ecart_jours", "cout_estime")
    list_filter = ("transporteur", "statut_livraison", "entrepot")
    list_select_related = ("commande", "transporteur")

admin.site.register([Transporteur, Entrepot, EtlRun])
admin.site.register(LigneCommande)
# Register your models here.
