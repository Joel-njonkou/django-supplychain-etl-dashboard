from django.urls import path
from .views import (
    TauxLivraisonATempsView,
    CoutMoyenExpeditionView,
    PointsDeBlocageView,
    get_kpis_globaux,
    get_ventes_profits,
    get_vouses_globales_enrichies,
    AgentChatView,
)

urlpatterns = [
    path('taux-livraison/', TauxLivraisonATempsView.as_view(), name='taux-livraison'),
    path('cout-moyen/', CoutMoyenExpeditionView.as_view(), name='cout-moyen'),
    path('points-de-blocage/', PointsDeBlocageView.as_view(), name='points-de-blocage'),
    path('kpis-globaux/', get_kpis_globaux, name='kpis-globaux'),
    path('ventes-profits/', get_ventes_profits, name='ventes-profits'),
    path('vouses-globales-enrichies/', get_vouses_globales_enrichies, name='vouses-globales-enrichies'),
    path('agent-chat/', AgentChatView.as_view(), name='agent-chat'),
]