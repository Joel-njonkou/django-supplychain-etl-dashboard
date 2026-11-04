
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .auth import RegistrationView
from . import views as v
from apps.agent.views import BottleneckExplainView, ChatView


router = DefaultRouter()
router.register("transporteurs", v.TransporteurViewSet)
router.register("entrepots", v.EntrepotViewSet)
router.register("commandes", v.CommandeViewSet)
router.register("expeditions", v.ExpeditionViewSet)
router.register("etl/runs", v.EtlRunViewSet)

urlpatterns = [
    path("auth/register/", RegistrationView.as_view(), name="auth-register"),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("kpis/summary/", v.KpiSummaryView.as_view()),
    path("kpis/timeseries/", v.KpiTimeseriesView.as_view()),
    path("kpis/bottlenecks/", v.KpiBottlenecksView.as_view()),
    path("", include(router.urls)),
    path("agent/bottlenecks/explain/", BottleneckExplainView.as_view(), name="agent-bottleneck-explain"),
    path("agent/chat/", ChatView.as_view(), name="agent-chat"),
]