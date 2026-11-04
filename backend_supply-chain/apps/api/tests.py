from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.logistics.models import Commande, LigneCommande


class RegistrationTests(APITestCase):
    def setUp(self):
        self.url = reverse("auth-register")
        self.payload = {
            "username": "jules-martin",
            "email": "jules@example.com",
            "password": "Correct-Horse-438-Lime",
            "password_confirmation": "Correct-Horse-438-Lime",
        }

    def test_registration_creates_regular_user_and_returns_jwt_tokens(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        user = get_user_model().objects.get(username=self.payload["username"])
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_registration_rejects_mismatched_password_confirmation(self):
        response = self.client.post(
            self.url,
            {**self.payload, "password_confirmation": "Not-The-Same-438"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            get_user_model().objects.filter(username=self.payload["username"]).exists()
        )

    def test_registration_rejects_weak_password(self):
        response = self.client.post(
            self.url,
            {
                **self.payload,
                "password": "password",
                "password_confirmation": "password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(
            get_user_model().objects.filter(username=self.payload["username"]).exists()
        )

    def test_registration_rejects_duplicate_username(self):
        get_user_model().objects.create_user(
            username=self.payload["username"], password="Existing-Password-449!"
        )

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)


class CommandeLinesTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="analyste", password="test-password"
        )
        self.client.force_authenticate(user)

    def test_commande_detail_returns_every_order_line(self):
        commande = Commande.objects.create(
            order_id=900001,
            date_commande="2026-01-01T10:00:00Z",
            statut="COMPLETE",
            client_id=123,
            segment_client="Consumer",
            marche="Europe",
            region="Western Europe",
            pays="France",
            ville="Paris",
            nb_lignes_commande=2,
            nb_articles=3,
            montant_total="30.75",
            profit_total="8.00",
        )
        for item_id, quantity, amount, profit in (
            (5001, 1, "10.25", "3.25"),
            (5002, 2, "20.50", "4.75"),
        ):
            LigneCommande.objects.create(
                commande=commande,
                order_item_id=item_id,
                product_card_id=17,
                product_name="Produit test",
                category_name="Sport",
                quantite=quantity,
                prix_unitaire=amount,
                remise="0.00",
                taux_remise="0.000000",
                ratio_profit="0.100000",
                montant_total=amount,
                profit=profit,
            )

        response = self.client.get(f"/api/v1/commandes/{commande.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nb_lignes_commande"], 2)
        self.assertEqual(len(response.data["lignes_commande"]), 2)
        self.assertEqual(
            {line["order_item_id"] for line in response.data["lignes_commande"]},
            {5001, 5002},
        )

    def test_commande_list_includes_line_and_unit_totals(self):
        Commande.objects.create(
            order_id=900002,
            date_commande="2026-01-02T10:00:00Z",
            statut="COMPLETE",
            client_id=124,
            segment_client="Consumer",
            marche="Europe",
            region="Western Europe",
            pays="France",
            ville="Lyon",
            nb_lignes_commande=3,
            nb_articles=7,
            montant_total="70.00",
            profit_total="9.00",
        )

        response = self.client.get("/api/v1/commandes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["nb_lignes_commande"], 3)
        self.assertEqual(response.data["results"][0]["nb_articles"], 7)

    def test_commande_market_and_region_filters_match_their_own_fields(self):
        europe = Commande.objects.create(
            order_id=900003,
            date_commande="2026-01-03T10:00:00Z",
            statut="COMPLETE",
            client_id=125,
            segment_client="Consumer",
            marche="Europe",
            region="Western Europe",
            pays="France",
            ville="Paris",
            nb_lignes_commande=1,
            nb_articles=2,
            montant_total="20.00",
            profit_total="2.00",
        )
        Commande.objects.create(
            order_id=900004,
            date_commande="2026-01-04T10:00:00Z",
            statut="COMPLETE",
            client_id=126,
            segment_client="Consumer",
            marche="Europe",
            region="Northern Europe",
            pays="Sweden",
            ville="Stockholm",
            nb_lignes_commande=2,
            nb_articles=2,
            montant_total="20.00",
            profit_total="2.00",
        )

        response = self.client.get(
            "/api/v1/commandes/?marche=Europe&region=Western%20Europe"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], europe.id)

    def test_commande_filter_options_are_distinct_and_alphabetical(self):
        for offset, (region, marche) in enumerate((
            ("Western Europe", "Europe"),
            ("Africa", "Africa"),
            ("Western Europe", "Asia"),
        )):
            Commande.objects.create(
                order_id=900020 + offset,
                date_commande=f"2026-01-0{offset + 1}T10:00:00Z",
                statut="COMPLETE",
                client_id=150 + offset,
                segment_client="Consumer",
                marche=marche,
                region=region,
                pays="France",
                ville="Paris",
                nb_lignes_commande=1,
                nb_articles=1,
                montant_total="10.00",
                profit_total="1.00",
            )

        response = self.client.get("/api/v1/commandes/options/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["regions"], ["Africa", "Western Europe"])
        self.assertEqual(response.data["marches"], ["Africa", "Asia", "Europe"])

    def test_commande_list_can_sort_by_line_count_in_both_directions(self):
        for offset, line_count in enumerate((1, 3, 2)):
            Commande.objects.create(
                order_id=900010 + offset,
                date_commande=f"2026-01-0{offset + 1}T10:00:00Z",
                statut="COMPLETE",
                client_id=130 + offset,
                segment_client="Consumer",
                marche="Europe",
                region="Western Europe",
                pays="France",
                ville="Paris",
                nb_lignes_commande=line_count,
                nb_articles=line_count,
                montant_total="20.00",
                profit_total="2.00",
            )

        ascending = self.client.get(
            "/api/v1/commandes/?ordering=nb_lignes_commande,-id"
        )
        descending = self.client.get(
            "/api/v1/commandes/?ordering=-nb_lignes_commande,-id"
        )

        self.assertEqual(
            [row["nb_lignes_commande"] for row in ascending.data["results"]], [1, 2, 3]
        )
        self.assertEqual(
            [row["nb_lignes_commande"] for row in descending.data["results"]], [3, 2, 1]
        )
