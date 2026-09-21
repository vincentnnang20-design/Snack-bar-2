from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.utils import timezone
from decimal import Decimal
import random
import string

# Create your models here.

class Utilisateurs(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True,unique=True)
    Role_choices = [
            ("Gerant","Administrateurs"),
            ("Serveurs","Serveurs"),
            ("Caissiers","Caissiers"),
            ("Fournisseurs","Fournisseurs")
              ]
    role = models.CharField(choices = Role_choices, max_length=20, default='Gerant')
    def is_client(self):
        return self.role == 'Clients'
    def is_fournisseur(self):
        return self.role == 'Fournisseurs'
    def is_caissier(self):
        return self.role == 'Caissiers'
    def is_serveur(self):
        return self.role == 'Serveurs'
    def is_gerant(self):
        return self.role == 'Gerant'
    def __str__(self):
        return f"{self.username} ({self.role})"

class PasswordResetCode(models.Model):
    user = models.ForeignKey('Utilisateurs', on_delete=models.CASCADE, related_name='password_reset_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.used and (timezone.now() - self.created_at).seconds < 900

    @classmethod
    def generate_code(cls, user):
        code = ''.join(random.choices(string.digits, k=6))
        cls.objects.filter(user=user).delete()
        return cls.objects.create(user=user, code=code)


class Produits(models.Model):
    nom = models.CharField(max_length=25)
    image = models.ImageField(upload_to='photos/', null=True, blank=True)
    Cathegories_choices = [
            ("Alcoolisée","Alcoolisée"),
            ("Non alcoolisée","Non alcoolisée")
              ]
    Cathegories = models.CharField(choices = Cathegories_choices, max_length=20)
    Genres_choices = [
            ("Bieres","Bieres"),
            ("Whisky","Whisky"),
            ("champagnes","champagnes"),
            ("Jus naturel","Jus naturel"),
            ("Jus gazeux","Jus gazeux"),
            ("Sirop","Sirop")
              ]
    Genres = models.CharField(choices = Genres_choices, max_length=20)
    Prix_vente = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    is_available = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.nom} ({self.Genres})"
    def desactiver(self):
        self.is_available = False
        self.save()
        return True



import qrcode
from io import BytesIO
from django.db import models
from django.core.files import File

class Tables(models.Model):
    numero_table = models.CharField(max_length=50, unique=True)
    capacite = models.IntegerField(default=1)
    qrcode_image = models.ImageField(upload_to='qrcodes/', null=True, blank=True)

    class Meta:
        verbose_name = "Table"
        verbose_name_plural = "Tables"

    def __str__(self):
        return f"Table {self.numero_table}"

    def save(self, *args, **kwargs):
        # 1. Sauvegarde initiale pour générer la clé primaire (ID) si c'est une nouvelle table
        if not self.pk:
            super().save(*args, **kwargs)

        # 2. Génération automatique du QR code s'il n'existe pas encore
        if not self.qrcode_image:
            # CONFIGURATION DE L'URL CIBLE
            # Remplacez "www.friscoclub.com" par votre IP locale (ex: 192.168.1.50:8000) lors des tests
            domaine = '10.0.36.194:8000'
            qr_data = f"http://{domaine}/client/?table={self.numero_table}"

            # Construction du QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Stockage temporaire dans le buffer
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)  # Réinitialise le pointeur pour éviter un fichier vide

            # Assignation du fichier à l'ImageField sans déclencher de boucle de sauvegarde
            file_name = f"table_{self.numero_table}_qr.png"
            self.qrcode_image.save(file_name, File(buffer), save=False)

        # 3. Sauvegarde finale de l'instance avec son QR Code lié
        super().save(*args, **kwargs)

# class Tables(models.Model):
#     numero_table = models.CharField(max_length=50, unique=True)
#     capacite = models.IntegerField(default=1)
#     qrcode_image = models.ImageField(upload_to='qrcodes/', null=True, blank=True)
#     class Meta:
#         verbose_name = "Table"
#         verbose_name_plural = "Tables"

#     def __str__(self):
#         return f"Table {self.numero_table}"

#     def save(self, *args, **kwargs):
#         # Save first to ensure the object gets a primary key (id) if it's new
#         if not self.pk:
#             super().save(*args, **kwargs)

#         # Generate QR code if it hasn't been generated yet
#         if not self.qrcode_image:
#             # Data to store inside the QR code (e.g., URL or identifier)
#             qr_data = f"http://yourdomain.com/table/{self.id}/menu"

#             qr = qrcode.QRCode(
#                 version=1,
#                 error_correction=qrcode.constants.ERROR_CORRECT_L,
#                 box_size=10,
#                 border=4,
#             )
#             qr.add_data(qr_data)
#             qr.make(fit=True)

#             img = qr.make_image(fill_color="black", back_color="white")

#             # Store the image in a BytesIO buffer
#             buffer = BytesIO()
#             img.save(buffer, format='PNG')

#             # Assign file to ImageField without triggering infinite save loop
#             file_name = f"table_{self.numero_table}_qr.png"
#             self.qrcode_image.save(file_name, File(buffer), save=False)

#         super().save(*args, **kwargs)




class Clients(models.Model):
    nom_client = models.CharField(max_length=25)
    numero_telephone = models.CharField(max_length=20, blank=True, null=True)
    def __str__(self):
        return f"{self.nom_client} (Client)"

class Commandes(models.Model):
    # id= models.UUIDField(primary_key=True)
    numero_table = models.ForeignKey(Tables,on_delete=models.CASCADE)
    # Serveurs_id = models.ForeignKey(Utilisateurs,on_delete=models.CASCADE,related_name='commande_serveur', null=True, blank=True)
    Clients_id = models.ForeignKey(Clients,on_delete=models.CASCADE,related_name='commande_client', null=True, blank=True)
    Date_Creation = models.DateTimeField(auto_now_add=True)
    nature_choices = [
        ("à emporter","à emporter"),
        ("consommer sur place","consommer sur place")
    ]
    nature =  models.CharField(choices = nature_choices, max_length=20, default="consommer sur place")
    Montant_Total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    statut = models.CharField(max_length=12, default='en cours', choices=[('en cours', 'en cours'), ('validee', 'Validee')])

    # --- Mode de paiement choisi par le client au moment de la commande ---
    Mode_paiement_choices = [
        ("numerique", "Paiement numérique (Orange Money / Mobile Money)"),
        ("espece", "Paiement en espèces (au comptoir)"),
    ]
    mode_paiement = models.CharField(
        max_length=15, choices=Mode_paiement_choices, blank=True, null=True
    )
    Operateur_paiement_choices = [
        ("Orange", "Orange Money"),
        ("MTN", "MTN Mobile Money"),
    ]
    operateur_paiement = models.CharField(
        max_length=10, choices=Operateur_paiement_choices, blank=True, null=True
    )
    numero_paiement = models.CharField(max_length=20, blank=True, null=True)

    Statut_paiement_choices = [
        ("a_payer_comptoir", "À payer au comptoir"),
        ("en_attente_confirmation", "En attente de confirmation"),
        ("payee", "Payée"),
    ]
    statut_paiement = models.CharField(
        max_length=25, choices=Statut_paiement_choices, default="a_payer_comptoir"
    )

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"

    #calculer le total de la commande.
    def calculTotal(self):
        total = sum(ligne.Sous_Total for ligne in self.lignecommandes_set.all())
        self.Montant_Total = total
        self.save()
        return total
    
    #valide la commande.
    def valide(self):
        self.calculTotal()
        self.statut = 'validee'
        self.save(update_fields=['statut'])
        return True
    
    #annule la commande.
    def annuler(self):
        if self.statut == 'annulee':
            return False
        for ligne in self.lignecommandes_set.all():
            stock = Stock.objects.filter(Produits_id=ligne.Produits_id).first()
            if stock:
                stock.incrementer(ligne.Quantité)
        self.statut = 'annulee'
        self.save(update_fields=['statut'])
        return True


class LigneCommandes(models.Model):
    Commandes_id = models.ForeignKey(Commandes,on_delete=models.CASCADE)
    Produits_id = models.ForeignKey(Produits,on_delete=models.CASCADE)
    Quantité = models.IntegerField(default=1)
    Prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    Sous_Total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"

    #calcule du sousTotal
    def save(self, *args, **kwargs):
        self.Sous_Total = self.Quantité * self.Prix_unitaire
        super().save(*args, **kwargs)
        #mettre a jour le total de la commande associer
        self.Commandes_id.calculTotal()

    def calculSousTotal(self):
        self.save()
        return self.Sous_Total

class Stock(models.Model):
    Produits_id = models.ForeignKey(Produits,on_delete=models.CASCADE)
    Quantité_actuel = models.IntegerField(default=1)
    Seuil_alert = models.IntegerField(default=5)
    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"

    def save(self, *args, **kwargs):
        """Synchronise la disponibilité publique avec la quantité réellement en stock."""
        super().save(*args, **kwargs)
        Produits.objects.filter(pk=self.Produits_id_id).update(
            is_available=self.Quantité_actuel > 0
        )

    def decrementer(self,qte):
        if qte <= 0:
            raise ValueError('La quantite doit etre strictement positive.')
        self.Quantité_actuel -= qte
        self.save()
        self.verifierAlert()
    def incrementer(self,qte):
            if qte <= 0:
                raise ValueError('La quantite doit etre strictement positive.')
            self.Quantité_actuel += qte
            self.save()
    def verifierAlert(self):
            return self.Quantité_actuel <= self.Seuil_alert

class MouvementStock(models.Model):
    Stock_id = models.ForeignKey(Stock,on_delete=models.CASCADE)
    Types_choices = [
            ("Entrée","Entrée"),
            ("Sortie","Sortie")
              ]
    Types = models.CharField(choices = Types_choices, max_length=20)
    Quantité = models.IntegerField(default=0)
    Date = models.DateTimeField(auto_now=True)
    Motif = models.CharField(max_length=25, blank=True, default="")
    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"

    def enregistrer(self):
        self.save()
        stock = self.Stock_id
        if self.Types == 'Entrée':
            stock.incrementer(self.Quantité)
        elif self.Types == 'Sortie':
            stock.decrementer(self.Quantité)
        # Mettre à jour la disponibilité du produit lié :
        try:
            produit = stock.Produits_id
            produit.is_available = stock.Quantité_actuel > 0
            produit.save(update_fields=['is_available'])
        except Exception:
            pass
        return True


class Paiement(models.Model):
    Commandes_id = models.ForeignKey(Commandes,on_delete=models.CASCADE)
    Caissiers_id = models.ForeignKey(Utilisateurs,on_delete=models.CASCADE)
    Montant = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    Modes_choices = [
            ("MTN","MTN MoMo"),
            ("Orange","Orange Money"),
            ("Espèces","Espèces")
              ]
    modes = models.CharField(choices = Modes_choices, max_length=20)
    Date = models.DateTimeField(auto_now=True)
    def valider(self):
        commande = self.Commandes_id
        commande.calculTotal()
        if self.Montant >= commande.Montant_Total:
            return True
        return False
    def genererTicket(self):
        lignes = self.Commandes_id.lignecommandes_set.all()
        ticket = f"--- Ticket Commande #{self.Commandes_id.numero} ---\n"
        for ligne in lignes:
            ticket += f"{ligne.Produits_id.nom} x{ligne.Quantité}: {ligne.Sous_Total} FCFA\n"
        ticket += f"Total: {self.Commandes_id.Montant_Total} FCFA\n"
        ticket += f"Payé ({self.modes}) : {self.Montant} FCFA\n"
        return ticket

class Notification(models.Model):
    """Notification affichée côté personnel (Gérant / Serveurs / Caissiers)
    lorsqu'un client valide une commande depuis l'interface "phone frame".
    """
    Commandes_id = models.ForeignKey(
        Commandes, on_delete=models.CASCADE, related_name='notifications'
    )
    titre = models.CharField(max_length=100, default="Nouvelle commande")
    message = models.TextField()
    est_lue = models.BooleanField(default=False)
    Date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-Date_creation']

    def __str__(self):
        return f"{self.titre} — Commande #{self.Commandes_id_id}"

    def marquer_comme_lue(self):
        if not self.est_lue:
            self.est_lue = True
            self.save(update_fields=['est_lue'])
        return True

    @classmethod
    def creer_pour_commande(cls, commande):
        """Construit et enregistre la notification envoyée au personnel
        juste après la validation d'une commande côté client, avec le
        détail complet de la commande (table, articles, montant, paiement).
        """
        lignes = commande.lignecommandes_set.select_related('Produits_id').all()
        detail_articles = ", ".join(
            f"{ligne.Produits_id.nom} x{ligne.Quantité}" for ligne in lignes
        ) or "Aucun article"

        mode_paiement_label = dict(Commandes.Mode_paiement_choices).get(
            commande.mode_paiement, "Non renseigné"
        )
        if commande.mode_paiement == "numerique" and commande.operateur_paiement:
            operateur_label = dict(Commandes.Operateur_paiement_choices).get(
                commande.operateur_paiement, commande.operateur_paiement
            )
            mode_paiement_label = f"{mode_paiement_label} — {operateur_label} ({commande.numero_paiement or 'N/A'})"

        message = (
            f"Table {commande.numero_table.numero_table} — {commande.nature}. "
            f"Articles : {detail_articles}. "
            f"Total : {commande.Montant_Total} FCFA. "
            f"Paiement : {mode_paiement_label}."
        )

        return cls.objects.create(
            Commandes_id=commande,
            titre=f"Nouvelle commande #{commande.id}",
            message=message,
        )


from django.db.models.signals import post_save
from django.dispatch import receiver

# Ce code s'exécute automatiquement quand un nouveau produit est créé
@receiver(post_save, sender=Produits)
def creer_stock_automatique(sender, instance, created, **kwargs):
    if created:
        Stock.objects.get_or_create(
            Produits_id=instance,
            defaults={'Quantité_actuel': 0, 'Seuil_alert': 5}
        )
