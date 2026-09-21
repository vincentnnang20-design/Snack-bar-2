from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

from .models import Produits, Stock, PasswordResetCode, MouvementStock, Commandes, LigneCommandes, Tables


class StockListViewTest(TestCase):
    def test_stock_page_lists_existing_stock(self):
        user = get_user_model().objects.create_user(
            username='gerant',
            password='secret123',
            role='Gerant',
        )

        produit = Produits.objects.create(
            nom='Coca-Cola',
            Cathegories='Non alcoolisée',
            Genres='Jus gazeux',
            Prix_vente=1000,
        )
        stock = Stock.objects.get(Produits_id=produit)
        stock.Quantité_actuel = 24
        stock.Seuil_alert = 5
        stock.save()

        self.client.force_login(user)
        response = self.client.get(reverse('stock_list_html'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('stocks', response.context)
        self.assertIn(stock, response.context['stocks'])
        self.assertContains(response, 'Coca-Cola')
        self.assertContains(response, '24')
        self.assertContains(response, '5')

    def test_stock_movements_page_displays_for_manager(self):
        user = get_user_model().objects.create_user(
            username='gerant-mouvements', password='secret123', role='Gerant'
        )
        produit = Produits.objects.create(
            nom='Jus orange',
            Cathegories=Produits.Cathegories_choices[1][0],
            Genres=Produits.Genres_choices[3][0],
            Prix_vente=1000,
        )
        stock = Stock.objects.get(Produits_id=produit)
        MouvementStock.objects.create(Stock_id=stock, Types='Entrée', Quantité=10)

        self.client.force_login(user)
        response = self.client.get(reverse('mouvements_stock_html'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jus orange')
        self.assertContains(response, "Vider l'historique")


class PublicStockVisibilityTest(TestCase):
    def setUp(self):
        self.produit = Produits.objects.create(
            nom='Produit en rupture',
            Cathegories=Produits.Cathegories_choices[0][0],
            Genres=Produits.Genres_choices[0][0],
            Prix_vente=1500,
        )
        self.stock = Stock.objects.get(Produits_id=self.produit)

    def test_out_of_stock_product_is_hidden_publicly_but_visible_to_manager(self):
        # The automatic stock row starts at zero: it must not be public.
        self.produit.refresh_from_db()
        self.assertFalse(self.produit.is_available)
        self.assertNotContains(self.client.get(reverse('catalogue')), self.produit.nom)
        self.assertNotContains(self.client.get(reverse('acceuil')), self.produit.nom)

        manager = get_user_model().objects.create_user(
            username='stock-manager', password='secret123', role='Gerant'
        )
        self.client.force_login(manager)
        self.assertContains(self.client.get(reverse('stock_list_html')), self.produit.nom)

    def test_product_reappears_when_stock_is_replenished(self):
        self.stock.Quantité_actuel = 6
        self.stock.save()
        self.produit.refresh_from_db()

        self.assertTrue(self.produit.is_available)
        self.assertContains(self.client.get(reverse('catalogue')), self.produit.nom)
        self.assertContains(self.client.get(reverse('acceuil')), self.produit.nom)


class CommandLineHistoryTest(TestCase):
    def test_manager_can_clear_order_line_history(self):
        manager = get_user_model().objects.create_user(
            username='manager-lignes', password='secret123', role='Gerant'
        )
        # bulk_create bypasses the QR-code generation hook, which saves a new
        # table twice and is unrelated to this history-cleanup scenario.
        Tables.objects.bulk_create([Tables(numero_table='T-TEST')])
        table = Tables.objects.get(numero_table='T-TEST')
        produit = Produits.objects.create(
            nom='Produit commande',
            Cathegories=Produits.Cathegories_choices[0][0],
            Genres=Produits.Genres_choices[0][0],
            Prix_vente=1200,
        )
        commande = Commandes.objects.create(numero_table=table, Montant_Total=1200)
        LigneCommandes.objects.create(
            Commandes_id=commande, Produits_id=produit, Quantité=1, Prix_unitaire=1200
        )

        self.client.force_login(manager)
        response = self.client.post(reverse('lignes_commandes_clear'))

        self.assertRedirects(response, reverse('lignes_commandes_html'))
        self.assertFalse(LigneCommandes.objects.exists())
        commande.refresh_from_db()
        self.assertEqual(commande.Montant_Total, 0)


class TeamMemberCreationViewTest(TestCase):
    def test_admin_can_create_team_member_with_hashed_password(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            password='secret123',
            role='Gerant',
        )

        self.client.force_login(admin)
        response = self.client.post(reverse('create_team_member'), {
            'username': 'caissier1',
            'email': 'caissier@example.com',
            'password': 'Azerty123!',
            'password_confirm': 'Azerty123!',
            'role': 'Caissiers',
            'phone': '0123456789',
        })

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username='caissier1')
        self.assertEqual(user.role, 'Caissiers')
        self.assertTrue(user.check_password('Azerty123!'))
        self.assertTrue(self.client.login(username='caissier1', password='Azerty123!'))


class PasswordRecoveryTest(TestCase):
    def test_authenticated_user_is_redirected_from_login_page(self):
        user = get_user_model().objects.create_user(
            username='employee',
            password='oldpass123',
            role='Caissiers',
        )

        self.client.force_login(user)
        response = self.client.get(reverse('login'))

        self.assertRedirects(response, reverse('catalogue'))

    def test_admin_cannot_use_forgot_password_flow(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='oldpass123',
            role='Gerant',
        )

        response = self.client.post(reverse('login'), {'forgot_password': '1', 'username': 'admin'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, 'Les comptes administrateurs ne peuvent pas')

    def test_forgot_password_sends_code_and_allows_reset(self):
        user = get_user_model().objects.create_user(
            username='employee',
            email='employee@example.com',
            password='oldpass123',
            role='Caissiers',
        )

        response = self.client.post(reverse('login'), {'forgot_password': '1', 'username': 'employee'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        reset_code = PasswordResetCode.objects.get(user=user)
        response = self.client.post(reverse('login'), {'verify_code': '1', 'username': 'employee', 'code': reset_code.code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get('reset_username'), 'employee')

        response = self.client.post(reverse('login'), {
            'new_password': '1',
            'username': 'employee',
            'password': 'newpass123!',
            'password_confirm': 'newpass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.get(username='employee').check_password('newpass123!'))
