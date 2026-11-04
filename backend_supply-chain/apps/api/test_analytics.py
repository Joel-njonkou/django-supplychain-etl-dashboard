from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.logistics.models import (
    Commande,
    Entrepot,
    Expedition,
    LigneCommande,
    Transporteur,
)


def _make_order(
    *,
    order_id,
    segment="Consumer",
    marche="Europe",
    region="Western Europe",
    pays="France",
    montant="100.00",
    profit="20.00",
    product="Produit A",
    category="Sport",
    remise="5.00",
    transporteur=None,
    entrepot=None,
    en_retard=False,
    statut_livraison="a_temps",
):
    commande = Commande.objects.create(
        order_id=order_id,
        date_commande="2026-01-01T10:00:00Z",
        statut="COMPLETE",
        client_id=order_id,
        segment_client=segment,
        marche=marche,
        region=region,
        pays=pays,
        ville="Paris",
        nb_lignes_commande=1,
        nb_articles=1,
        montant_total=montant,
        profit_total=profit,
    )
    LigneCommande.objects.create(
        commande=commande,
        order_item_id=order_id * 10,
        product_card_id=1,
        product_name=product,
        category_name=category,
        quantite=1,
        prix_unitaire=montant,
        remise=remise,
        taux_remise="0.050000",
        ratio_profit="0.200000",
        montant_total=montant,
        profit=profit,
    )
    Expedition.objects.create(
        commande=commande,
        transporteur=transporteur,
        entrepot=entrepot,
        delai_prevu_jours=2,
        delai_reel_jours=4 if en_retard else 2,
        ecart_jours=2 if en_retard else 0,
        statut_livraison=statut_livraison,
        en_retard=en_retard,
        cout_estime="12.50",
    )
    return commande


class AnalyticsEndpointsTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="analyste-bi", password="test-password"
        )
        self.client.force_authenticate(user)
        self.transporteur = Transporteur.objects.create(code="std", nom="Standard Class")
        self.entrepot = Entrepot.objects.create(code="hub-eu", nom="HubEurope")
        _make_order(
            order_id=1,
            segment="Consumer",
            marche="Europe",
            montant="100.00",
            profit="20.00",
            product="Produit A",
            category="Sport",
            transporteur=self.transporteur,
            entrepot=self.entrepot,
            en_retard=False,
        )
        _make_order(
            order_id=2,
            segment="Corporate",
            marche="Europe",
            montant="50.00",
            profit="5.00",
            product="Produit B",
            category="Electronics",
            transporteur=self.transporteur,
            entrepot=self.entrepot,
            en_retard=True,
            statut_livraison="en_retard",
        )
        _make_order(
            order_id=3,
            segment="Consumer",
            marche="Africa",
            region="West Africa",
            pays="Senegal",
            montant="25.00",
            profit="4.00",
            product="Produit A",
            category="Sport",
            transporteur=self.transporteur,
            entrepot=self.entrepot,
            en_retard=True,
            statut_livraison="en_retard",
        )

    def test_sales_profits_totals_and_filters(self):
        response = self.client.get("/api/v1/kpis/sales-profits/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_ca"], 175.0)
        self.assertEqual(response.data["total_profit"], 29.0)
        self.assertEqual(response.data["benefice_total"], 29.0)
        self.assertEqual(response.data["marge_globale_pct"], 16.57)
        self.assertEqual(response.data["total_commandes"], 3)
        self.assertTrue(response.data["ventes_par_segment"])
        self.assertTrue(response.data["ventes_par_produit"])
        self.assertIn("Consumer", response.data["filter_options"]["segments"])

        filtered = self.client.get("/api/v1/kpis/sales-profits/?segment=Corporate")
        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered.data["total_ca"], 50.0)
        self.assertEqual(filtered.data["total_commandes"], 1)

        by_market = self.client.get("/api/v1/kpis/sales-profits/?market=Africa")
        self.assertEqual(by_market.status_code, status.HTTP_200_OK)
        self.assertEqual(by_market.data["total_ca"], 25.0)

    def test_enriched_kpis_and_breakdowns(self):
        response = self.client.get("/api/v1/kpis/enriched/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        kpis = response.data["kpis"]
        self.assertEqual(kpis["total_ca"], 175.0)
        self.assertEqual(kpis["total_profit"], 29.0)
        self.assertEqual(kpis["total_remises"], 15.0)
        self.assertEqual(kpis["total_commandes"], 3)
        self.assertEqual(kpis["taux_retard_pct"], 66.67)
        self.assertEqual(kpis["taux_a_temps_pct"], 33.33)
        self.assertTrue(response.data["fiabilite_transporteurs"])
        self.assertTrue(response.data["blocages_regionaux"])
        self.assertTrue(response.data["categories_stats"])
        self.assertIn("Europe", response.data["filters"]["markets"])
        self.assertIn("Standard Class", response.data["filters"]["transporteurs"])

        filtered = self.client.get(
            "/api/v1/kpis/enriched/?marche=Europe&segment_client=Consumer"
        )
        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered.data["kpis"]["total_ca"], 100.0)
        self.assertEqual(filtered.data["kpis"]["taux_retard_pct"], 0.0)
