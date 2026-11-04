
from rest_framework import viewsets
from rest_framework.decorators import action
from apps.logistics.models import Commande, Entrepot, EtlRun, Expedition, Transporteur
from . import serializers as sz
from .filters import CommandeFilter, ExpeditionFilter
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from . import analytics, kpis

class TransporteurViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transporteur.objects.all()
    serializer_class = sz.TransporteurSerializer
    pagination_class = None
    
class EntrepotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Entrepot.objects.all()
    serializer_class = sz.EntrepotSerializer
    pagination_class = None 
    
class CommandeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Commande.objects.select_related("expedition__transporteur", "expedition__entrepot")
    filterset_class = CommandeFilter
    ordering_fields = ["date_commande", "montant_total", "order_id", "nb_lignes_commande", "id"]
    ordering = ["-date_commande", "-id"]                      # ordre stable => pagination fiable

    @action(detail=False, methods=["get"])
    def options(self, request):
        regions = Commande.objects.order_by().values_list("region", flat=True).distinct()
        marches = Commande.objects.order_by().values_list("marche", flat=True).distinct()
        return Response({
            "regions": sorted(regions, key=str.casefold),
            "marches": sorted(marches, key=str.casefold),
        })

    def get_serializer_class(self):
        return sz.CommandeDetailSerializer if self.action == "retrieve" else sz.CommandeSerializer

class ExpeditionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Expedition.objects.select_related("commande", "transporteur", "entrepot")
    serializer_class = sz.ExpeditionSerializer
    filterset_class = ExpeditionFilter
    ordering_fields = ["ecart_jours", "cout_estime", "commande__date_commande"]
    ordering = ["-commande__date_commande", "-id"]

class EtlRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EtlRun.objects.all()
    serializer_class = sz.EtlRunSerializer
    

class KpiSummaryView(APIView):
    @extend_schema(parameters=[ExpeditionFilter], responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(kpis.summary(kpis.base_queryset(request.query_params)))
    
class KpiTimeseriesView(APIView):
    @extend_schema(parameters=[ExpeditionFilter, OpenApiParameter("granularity", str,
        description="day|week|month")],
                    responses=OpenApiTypes.OBJECT)
    def get(self, request):
        qs = kpis.base_queryset(request.query_params)
        return Response(kpis.timeseries(qs, request.query_params.get("granularity", "week")))
    
class KpiBottlenecksView(APIView):
    @extend_schema(parameters=[ExpeditionFilter, OpenApiParameter("by", str),
        OpenApiParameter("limit", int),
                                OpenApiParameter("min_volume", int)], responses=OpenApiTypes.OBJECT)
    def get(self, request):
        q = request.query_params
        qs = kpis.base_queryset(q)
        by = q.get("by", "region_transporteur")
        limit = min(int(q.get("limit", 10)), 100)
        min_volume = int(q.get("min_volume", settings.BOTTLENECK_MIN_VOLUME))
        return Response(kpis.bottlenecks(qs, by, min_volume, limit))


class KpiSalesProfitsView(APIView):
    """CA, profit, marge, tops segments/produits (équivalent ancien /api/ventes-profits/)."""

    @extend_schema(
        parameters=[
            OpenApiParameter("segment_client", str, description="ou alias segment"),
            OpenApiParameter("marche", str, description="ou alias market"),
            OpenApiParameter("region", str),
            OpenApiParameter("transporteur", str),
            OpenApiParameter("statut_livraison", str, description="ou alias delivery_status"),
            OpenApiParameter("date_min", OpenApiTypes.DATE),
            OpenApiParameter("date_max", OpenApiTypes.DATE),
        ],
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        return Response(analytics.sales_profits(request.query_params))


class KpiEnrichedView(APIView):
    """Analyse globale enrichie (équivalent ancien /api/vueses-globales-enrichies/)."""

    @extend_schema(
        parameters=[
            OpenApiParameter("segment_client", str, description="ou alias segment"),
            OpenApiParameter("marche", str, description="ou alias market"),
            OpenApiParameter("region", str),
            OpenApiParameter("transporteur", str),
            OpenApiParameter("statut_livraison", str, description="ou alias delivery_status"),
            OpenApiParameter("date_min", OpenApiTypes.DATE),
            OpenApiParameter("date_max", OpenApiTypes.DATE),
        ],
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        return Response(analytics.enriched(request.query_params))
