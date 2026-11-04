from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import Avg, Count, Q, Sum, F
from .models import Commande, Expedition, Transporteur, Entrepot
import requests 


# 1. VUES DE L'EXERCICE (Classes de base)


class TauxLivraisonATempsView(APIView):
    def get(self, request):
        total_expeditions = Expedition.objects.count()
        if total_expeditions == 0:
            return Response({"taux_livraison_a_temps": 0, "message": "Aucune expédition en base."})
      
        expeditions_a_temps = Expedition.objects.filter(late_delivery_risk=False).count()
        taux = (expeditions_a_temps / total_expeditions) * 100
      
        return Response({
            "total_expeditions": total_expeditions,
            "expeditions_a_temps": expeditions_a_temps,
            "taux_livraison_a_temps": round(taux, 2)
        })


class CoutMoyenExpeditionView(APIView):
    def get(self, request):
        resultat = Expedition.objects.aggregate(cout_moyen=Avg('commande__sales'))
        cout_moyen = resultat['cout_moyen'] or 0
      
        return Response({
            "cout_moyen_expedition": round(cout_moyen, 2)
        })


class PointsDeBlocageView(APIView):
    def get(self, request):
        blocages_par_region = (
            Expedition.objects.values('commande__order_region')
            .annotate(
                total_expeditions=Count('commande'),
                total_retards=Count('commande', filter=Q(late_delivery_risk=True))
            )
            .order_by('-total_retards')
        )
      
        return Response({
            "points_de_blocage_region": list(blocages_par_region)
        })



# 2. KPIS GLOBAUX & ANALYSE DE MARCHÉ


@api_view(['GET'])
def get_kpis_globaux(request):
    stats = Commande.objects.aggregate(
        total_expeditions=Count('order_id'),
        total_profit=Sum('benefit_per_order'),
        total_sales=Sum('sales'),
    )

    total_exp = stats['total_expeditions'] or 0
    total_profit = round(stats['total_profit'] or 0, 2)
    total_sales = stats['total_sales'] or 1.0
    profit_margin = round((total_profit / total_sales) * 100, 2)

    late_orders = Commande.objects.filter(
        expedition__days_for_shipping_real__gt=F('expedition__days_for_shipment_scheduled')
    ).aggregate(
        avg_delay=Avg(F('expedition__days_for_shipping_real') - F('expedition__days_for_shipment_scheduled'))
    )
    avg_delay_days = round(late_orders['avg_delay'] or 0, 1)

    top_markets_qs = Commande.objects.values('market').annotate(
        total=Count('order_id')
    ).order_by('-total')[:3]

    top_markets = [
        {"market": item['market'], "total": item['total']}
        for item in top_markets_qs
    ]

    return Response({
        "volume_total_expeditions": total_exp,
        "benefice_total": total_profit,
        "marge_beneficiaire_pct": profit_margin,
        "retard_moyen_jours": avg_delay_days,
        "top_marches": top_markets
    })


@api_view(['GET'])
def get_ventes_profits(request):
    selected_segment = request.GET.get('segment', None)
    selected_market = request.GET.get('market', None)

    queryset = Commande.objects.all()

    if selected_segment and selected_segment != 'ALL':
        queryset = queryset.filter(customer_segment=selected_segment)
    if selected_market and selected_market != 'ALL':
        queryset = queryset.filter(market=selected_market)

    totals = queryset.aggregate(
        total_ca=Sum('sales'),
        total_profit=Sum('benefit_per_order'),
        total_commandes=Count('order_id')
    )

    total_ca = round(totals['total_ca'] or 0, 2)
    total_profit = round(totals['total_profit'] or 0, 2)
    marge_globale = round((total_profit / total_ca * 100), 2) if total_ca > 0 else 0

    ventes_par_seg = queryset.values('customer_segment').annotate(
        ca=Sum('sales'),
        profit=Sum('benefit_per_order'),
        commandes=Count('order_id')
    ).order_by('-ca')[:5]

    data_segments = [
        {
            "segment": item['customer_segment'] or 'Autre',
            "ca": round(item['ca'] or 0, 2),
            "profit": round(item['profit'] or 0, 2),
            "marge_pct": round((item['profit'] / item['ca'] * 100), 2) if item['ca'] else 0,
            "commandes": item['commandes']
        }
        for item in ventes_par_seg
    ]

    ventes_par_prod = queryset.values('product_name').annotate(
        ca=Sum('sales'),
        profit=Sum('benefit_per_order')
    ).order_by('-ca')[:5]

    data_produits = [
        {
            "produit": item['product_name'] or 'Inconnu',
            "ca": round(item['ca'] or 0, 2),
            "profit": round(item['profit'] or 0, 2),
            "marge_pct": round((item['profit'] / item['ca'] * 100), 2) if item['ca'] else 0
        }
        for item in ventes_par_prod
    ]

    segments_list = list(Commande.objects.values_list('customer_segment', flat=True).distinct().order_by('customer_segment'))
    markets_list = list(Commande.objects.values_list('market', flat=True).distinct().order_by('market'))

    return Response({
        "total_ca": total_ca,
        "total_profit": total_profit,
        "marge_globale_pct": marge_globale,
        "total_commandes": totals['total_commandes'] or 0,
        "ventes_par_segment": data_segments,
        "ventes_par_produit": data_produits,
        "filter_options": {
            "segments": [s for s in segments_list if s],
            "markets": [m for m in markets_list if m]
        }
    })



# 3. ENDPOINT ENRICHI MULTI-FILTRES 

@api_view(['GET'])
def get_vouses_globales_enrichies(request):
    market = request.GET.get('market', 'ALL')
    transporteur_name = request.GET.get('transporteur', 'ALL')
    segment = request.GET.get('segment', 'ALL')
    delivery_status = request.GET.get('delivery_status', 'ALL')

    cmd_qs = Commande.objects.all()
    exp_qs = Expedition.objects.all()

    if market != 'ALL':
        cmd_qs = cmd_qs.filter(market=market)
        exp_qs = exp_qs.filter(commande__market=market)
   
    if segment != 'ALL':
        cmd_qs = cmd_qs.filter(customer_segment=segment)
        exp_qs = exp_qs.filter(commande__customer_segment=segment)

    if transporteur_name != 'ALL':
        exp_qs = exp_qs.filter(transporteur__name=transporteur_name)
        cmd_qs = cmd_qs.filter(expedition__transporteur__name=transporteur_name)

    if delivery_status != 'ALL':
        exp_qs = exp_qs.filter(delivery_status=delivery_status)
        cmd_qs = cmd_qs.filter(expedition__delivery_status=delivery_status)

    totaux_cmd = cmd_qs.aggregate(
        total_ca=Sum('sales'),
        total_profit=Sum('benefit_per_order'),
        total_remises=Sum('discount_amount'),
        total_commandes=Count('order_id')
    )

    total_ca = round(totaux_cmd['total_ca'] or 0, 2)
    total_profit = round(totaux_cmd['total_profit'] or 0, 2)
    total_remises = round(totaux_cmd['total_remises'] or 0, 2)
    marge_globale = round((total_profit / total_ca * 100), 2) if total_ca > 0 else 0

    total_exp = exp_qs.count()
    retards_count = exp_qs.filter(late_delivery_risk=True).count()
    taux_retard = round((retards_count / total_exp * 100), 2) if total_exp > 0 else 0
    taux_a_temps = round(100 - taux_retard, 2)

    fiabilite_transporteurs = list(
        exp_qs.values(nom_transporteur=F('transporteur__name'))
        .annotate(
            total_expeditions=Count('commande_id'),
            retards=Count('commande_id', filter=Q(late_delivery_risk=True)),
            delai_moyen_reel=Avg('days_for_shipping_real'),
            delai_moyen_prevu=Avg('days_for_shipment_scheduled')
        )
        .order_by('-total_expeditions')
    )

    blocages_regionaux = list(
        exp_qs.values(region=F('commande__order_region'), pays=F('commande__order_country'))
        .annotate(
            total_commandes=Count('commande_id'),
            nb_retards=Count('commande_id', filter=Q(late_delivery_risk=True)),
            ca_affecte=Sum('commande__sales')
        )
        .order_by('-nb_retards')[:10]
    )

    categories_stats = list(
        cmd_qs.values('category_name')
        .annotate(
            ca=Sum('sales'),
            profit=Sum('benefit_per_order'),
            volume=Count('order_id')
        )
        .order_by('-ca')[:5]
    )

    markets_list = list(Commande.objects.values_list('market', flat=True).distinct().order_by('market'))
    segments_list = list(Commande.objects.values_list('customer_segment', flat=True).distinct().order_by('customer_segment'))
    transporteurs_list = list(Transporteur.objects.values_list('name', flat=True).distinct().order_by('name'))
    statuts_livraison = list(Expedition.objects.values_list('delivery_status', flat=True).distinct().order_by('delivery_status'))

    return Response({
        "kpis": {
            "total_ca": total_ca,
            "total_profit": total_profit,
            "total_remises": total_remises,
            "marge_globale_pct": marge_globale,
            "total_commandes": totaux_cmd['total_commandes'],
            "taux_a_temps_pct": taux_a_temps,
            "taux_retard_pct": taux_retard,
        },
        "fiabilite_transporteurs": fiabilite_transporteurs,
        "blocages_regionaux": blocages_regionaux,
        "categories_stats": categories_stats,
        "filters": {
            "markets": markets_list,
            "segments": segments_list,
            "transporteurs": transporteurs_list,
            "delivery_status": statuts_livraison
        }
    })


class AgentChatView(APIView):
    
    #Gère un fil de conversation unique et centralisé pour l'agent IA.
    
    def post(self, request):
        # Récupération des données envoyées par le front (valeur du KPI, question, etc.)
        user_message = request.data.get("message", "")
        metric_context = request.data.get("context", {}) # Ex: { "transporteur": "A", "retard": 34.5 }

        # Construction du prompt dynamique basé sur les données réelles
        prompt = f"""
        En tant qu'analyste Data Science et Supply Chain, analyse les données suivantes issues du tableau de bord :
        Contexte de la métrique : {metric_context}
        Question ou action de l'utilisateur : {user_message}

        Fournis une explication analytique précise, factuelle et orientée solution en français.
        """

        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "qwen2.5:1.5b",
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=180)
            if response.status_code == 200:
                ai_response = response.json().get("response", "Réponse vide.")
                return Response({"status": "success", "response": ai_response})
            else:
                return Response({"status": "error", "message": "Erreur du modèle local."}, status=500)
        except requests.exceptions.ConnectionError:
            return Response({"status": "error", "message": "Ollama ne répond pas."}, status=503)