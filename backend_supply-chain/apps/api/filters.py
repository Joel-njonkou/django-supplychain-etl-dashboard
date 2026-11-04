
import django_filters as df
from apps.logistics.models import Commande, Expedition

class ExpeditionFilter(df.FilterSet):
    date_min = df.DateFilter(field_name="commande__date_commande", lookup_expr="date__gte")
    date_max = df.DateFilter(field_name="commande__date_commande", lookup_expr="date__lte")
    region = df.CharFilter(field_name="commande__region", lookup_expr="iexact")
    marche = df.CharFilter(field_name="commande__marche", lookup_expr="iexact")
    transporteur = df.CharFilter(field_name="transporteur__code")
    entrepot = df.CharFilter(field_name="entrepot__code")
    statut_livraison = df.MultipleChoiceFilter(choices=Expedition.StatutLivraison.choices)
    class Meta:
        model = Expedition
        fields = []
        
class CommandeFilter(df.FilterSet):
    date_min = df.DateFilter(field_name="date_commande", lookup_expr="date__gte")
    date_max = df.DateFilter(field_name="date_commande", lookup_expr="date__lte")
    region = df.CharFilter(lookup_expr="iexact")
    marche = df.CharFilter(lookup_expr="iexact")
    class Meta:
        model = Commande
        fields = ["statut", "segment_client", "region", "marche"]