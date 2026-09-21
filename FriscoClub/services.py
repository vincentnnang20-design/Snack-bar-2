from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Stock, LigneCommandes, MouvementStock

@transaction.atomic
def ajouter_ligne_commande(commande, produit, quantite, prix_unitaire):
    if quantite <= 0:
        raise ValidationError({"quantite": "La quantite doit etre strictement positive."})
    if commande.statut != 'brouillon':
        raise ValidationError({"detail": "Cette commande ne peut plus etre modifiee."})
    try:
        stock = Stock.objects.select_for_update().get(Produits_id=produit)
    except Stock.DoesNotExist:
        raise ValidationError({"detail": "Aucun stock n'est configure pour ce produit."})

    if stock.Quantité_actuel < quantite:
        raise ValidationError({"detail": "Stock insuffisant."})

    ligne = LigneCommandes.objects.create(
        Commandes_id=commande,
        Produits_id=produit,
        Quantité=quantite,
        Prix_unitaire=produit.Prix_vente,
    )

    stock.Quantité_actuel -= quantite
    stock.save()

    MouvementStock.objects.create(
        Stock_id=stock,
        Types="Sortie",
        Quantité=quantite,
    )

    return ligne
