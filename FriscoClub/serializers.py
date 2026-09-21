from http import client

from rest_framework import serializers
from django.contrib.auth import authenticate
from .services import ajouter_ligne_commande
from .models import Produits, Utilisateurs, Tables, MouvementStock, Paiement, Commandes, LigneCommandes, Stock
from django.db import transaction, DatabaseError
# from .models import Produits, Stock, MouvementStock


class ProduitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produits
        fields = '__all__'

    def validate_Prix_vente(self, value):
        if value < 0:
            raise serializers.ValidationError("Le prix de vente ne peut pas être négatif.")
        return value

    def create(self, validated_data):
        try:
            with transaction.atomic():
                # 1. Create the product
                product = Produits.objects.create(**validated_data)

                # 2. Create associated stock
                stock = Stock.objects.create(Produits_id=product)

                # 3. Create initial stock movement
                MouvementStock.objects.create(
                    Stock_id=stock,
                    Types="Entrée",
                    Quantité=1
                )

                return product

        except DatabaseError as e:
            # Catch database-level issues (e.g., integrity errors, connection loss)
            raise serializers.ValidationError({
                "detail": "Une erreur s'est produite lors de la création du produit et de son stock.",
                "error": str(e)
            })
        except Exception as e:
            # Catch any unexpected Python runtime errors
            raise serializers.ValidationError({
                "detail": "Échec de l'opération.",
                "error": str(e)
            })


class UtilisateursSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = Utilisateurs
        fields = ['username', 'phone', 'role','password']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'detail': 'Le mot de passe sont obligatoires.'})
        return Utilisateurs.objects.create_user(password=password, **validated_data)


# class LoginSerializer(serializers.Serializer):
#     username = serializers.CharField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, data):
#         user = authenticate(username=data['username'], password=data['password'])
#         if not user:
#             raise serializers.ValidationError("Identifiants invalides")
#         data['user'] = user
#         return data


from rest_framework import serializers
from django.contrib.auth import authenticate


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        error_messages={"blank": "Le nom d'utilisateur est requis."}
    )
    password = serializers.CharField(
        write_only=True,
        error_messages={"blank": "Le mot de passe est requis."}
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # Authentification auprès du backend Django
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    {"detail": "Nom d'utilisateur ou mot de passe incorrect."}
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    {"detail": "Ce compte utilisateur a été désactivé."}
                )
        else:
            raise serializers.ValidationError(
                {"detail": "Veuillez fournir le nom d'utilisateur et le mot de passe."}
            )

        # Attache l'instance utilisateur pour qu'elle soit accessible via serializer.validated_data['user']
        attrs['user'] = user
        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = Utilisateurs
        fields =['username', 'password']
    def create(self, validated_data):
        # cree l'utilisateur et hache automatiquement le mot de passe
        return Utilisateurs.objects.create_user(role='Gerant', **validated_data)

class TablesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tables
        fields = '__all__'

class MouvementStockSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source='Stock_id.Produits_id.nom', read_only=True)
    class Meta:
        model = MouvementStock
        fields = '__all__'


class PaiementSerializer(serializers.ModelSerializer):
    commande_numero = serializers.CharField(source='Commandes_id.numero', read_only=True)
    commande_total = serializers.FloatField(source='Commandes_id.Montant_Total', read_only=True)
    caissier_nom = serializers.CharField(source='Caissiers_id.username', read_only=True)
    class Meta:
        model = Paiement
        fields = '__all__'

class LigneCommandesSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source='Produits_id.nom', read_only=True)
    produit_prix = serializers.FloatField(source='Produits_id.Prix_vente', read_only=True)
    class Meta:
        model = LigneCommandes
        fields = '__all__'

    def create(self, validated_data):
        commande = validated_data["Commandes_id"]
        produit = validated_data["Produits_id"]
        quantite = validated_data["Quantité"]
        prix_unitaire = produit.Prix_vente

        return ajouter_ligne_commande(
            commande,
            produit,
            quantite,
            prix_unitaire
    )


from rest_framework import serializers
from django.db import transaction
from .models import Commandes, Clients, Tables, Produits, LigneCommandes, Paiement


# --- 1. SERIALIZERS DE LECTURE (GET / LIST / RETRIEVE) ---

class LigneProduitReadSerializer(serializers.ModelSerializer):
    id_produit = serializers.IntegerField(source='Produits_id.id')
    name_produit = serializers.CharField(source='Produits_id.nom')
    categorie = serializers.CharField(source='Produits_id.categorie.nom', default=None)
    genre = serializers.CharField(source='Produits_id.genre', default=None)
    quantité = serializers.IntegerField(source='Quantité')
    prix_unitaire = serializers.DecimalField(source='Produits_id.Prix_vente', max_digits=10, decimal_places=2)
    sous_total = serializers.SerializerMethodField()

    class Meta:
        model = LigneCommandes
        fields = ['id_produit', 'name_produit', 'categorie', 'genre', 'quantité', 'prix_unitaire', 'sous_total']

    def get_sous_total(self, obj):
        if hasattr(obj, 'Sous_Total'):
            return obj.Sous_Total
        return obj.Quantité * obj.Produits_id.Prix_vente


class CommandeReadSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField()
    numero_table = serializers.IntegerField(source='numero_table.numero_table')
    produit = LigneProduitReadSerializer(source='lignecommandes_set', many=True)
    date_commande = serializers.DateTimeField(source='created_at')
    montant_total = serializers.DecimalField(source='Montant_Total', max_digits=12, decimal_places=2)
    mode_paiement = serializers.SerializerMethodField()

    class Meta:
        model = Commandes
        fields = ['id', 'client', 'numero_table', 'produit', 'date_commande', 'montant_total', 'mode_paiement', 'statut']

    def get_client(self, obj):
        if obj.Clients_id:
            return {
                "client_name": obj.Clients_id.nom,
                "phone_number": getattr(obj.Clients_id, 'telephone', None)
            }
        return None

    def get_mode_paiement(self, obj):
        paiement = obj.paiement_set.last()
        return paiement.modes if paiement else None


# --- 2. SERIALIZERS D'ÉCRITURE (POST / PUT) ---

class ItemWriteSerializer(serializers.Serializer):
    id_produit = serializers.IntegerField()
    quantité = serializers.IntegerField(min_value=1)


class CommandeWriteSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(write_only=True)
    numero_table = serializers.IntegerField(write_only=True)
    mode_paiement = serializers.ChoiceField(choices=Paiement.Modes_choices, write_only=True)
    items = ItemWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Commandes
        fields = ['client_name', 'phone_number', 'numero_table', 'items', 'mode_paiement']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        client_name = validated_data.pop('client_name')
        phone_number = validated_data.pop('phone_number')
        num_table = validated_data.pop('numero_table')
        mode_p = validated_data.pop('mode_paiement')

        with transaction.atomic():
            client, _ = Clients.objects.get_or_create(
                telephone=phone_number,
                defaults={'nom': client_name}
            )

            table = Tables.objects.filter(numero_table=num_table).first()
            if not table:
                raise serializers.ValidationError({"numero_table": f"Table {num_table} introuvable."})

            commande = Commandes.objects.create(
                Clients_id=client,
                numero_table=table
            )

            total = 0
            for item in items_data:
                produit = Produits.objects.filter(id=item['id_produit']).first()
                if not produit:
                    raise serializers.ValidationError({"items": f"Produit ID {item['id_produit']} introuvable."})

                LigneCommandes.objects.create(
                    Commande_id=commande,
                    Produits_id=produit,
                    Quantité=item['quantité']
                )
                total += produit.Prix_vente * item['quantité']

            commande.Montant_Total = total
            commande.save()

            request = self.context.get('request')
            caissier = request.user if request and request.user.is_authenticated else None

            Paiement.objects.create(
                Commandes_id=commande,
                Caissiers_id=caissier,
                Montant=total,
                modes=mode_p
            )

            return commande

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        client_name = validated_data.pop('client_name', None)
        phone_number = validated_data.pop('phone_number', None)
        num_table = validated_data.pop('numero_table', None)
        mode_p = validated_data.pop('mode_paiement', None)

        with transaction.atomic():
            if client_name or phone_number:
                if instance.Clients_id:
                    if client_name: instance.Clients_id.nom = client_name
                    if phone_number: instance.Clients_id.telephone = phone_number
                    instance.Clients_id.save()

            if num_table:
                table = Tables.objects.filter(numero_table=num_table).first()
                if not table:
                    raise serializers.ValidationError({"numero_table": f"Table {num_table} introuvable."})
                instance.numero_table = table

            if mode_p:
                paiement = instance.paiement_set.last()
                if paiement:
                    paiement.modes = mode_p
                    paiement.save()

            if items_data is not None:
                instance.lignecommandes_set.all().delete()
                total = 0
                for item in items_data:
                    produit = Produits.objects.filter(id=item['id_produit']).first()
                    if not produit:
                        raise serializers.ValidationError({"items": f"Produit ID {item['id_produit']} introuvable."})
                    
                    LigneCommandes.objects.create(
                        Commande_id=instance,
                        Produits_id=produit,
                        Quantité=item['quantité']
                    )
                    total += produit.Prix_vente * item['quantité']
                
                instance.Montant_Total = total

            instance.save()
            return instance


# --- 3. SERIALIZER DE MISE À JOUR DU STATUT (PATCH) ---

class CommandeStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commandes
        fields = ['id', 'statut']


class StockSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source='Produits_id.nom', read_only=True)

    class Meta:
        model = Stock
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            # Retrieve the new stock quantity if provided in validated_data
            new_quantity = validated_data.get('quantity', instance.Quantité_actuel)
            old_quantity = instance.Quantité_actuel

            # Calculate difference to log stock movement if quantity changed
            quantity_diff = new_quantity - old_quantity

            # Perform the update on Stock fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Record stock movement automatically if stock quantity changed
            if quantity_diff != 0:
                movement_type = "Entrée" if quantity_diff > 0 else "Sortie"
                MouvementStock.objects.create(
                    Stock_id=instance,
                    Types=movement_type,
                    Quantité=abs(quantity_diff)
                )

            return instance