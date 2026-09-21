from django.contrib import admin
from FriscoClub.models import (Commandes,Utilisateurs,Produits,
                               Stock,MouvementStock,Tables, Paiement,LigneCommandes)

# Register your models here.

@admin.register(Utilisateurs)
class UtilisateursAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    search_fields = ('username',)
    ordering = ('username',)
@admin.register(Commandes)
class CommandesAdmin(admin.ModelAdmin):
    list_display = ('numero_table', 'Clients_id', 'Date_Creation', 'Montant_Total', 'statut')
    list_filter = ('statut', 'Date_Creation')
    search_fields = ('numero_table',)
    ordering = ('Date_Creation',)
@admin.register(Produits)
class ProduitsAdmin(admin.ModelAdmin):
    list_display = ('nom', 'Cathegories', 'Genres', 'Prix_vente')
    list_filter = ('Cathegories', 'Genres')
    search_fields = ('nom',)
    ordering = ('nom',)
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('Produits_id', 'Quantité_actuel', 'Seuil_alert')
    list_filter = ('Seuil_alert',)
    search_fields = ('Produits_id',)
    ordering = ('Produits_id',)
@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('Stock_id', 'Types', 'Quantité', 'Date', 'Motif')
    list_filter = ('Types', 'Date')
    search_fields = ('Motif',)
    ordering = ('Date',)
@admin.register(Tables)
class TablesAdmin(admin.ModelAdmin):
    list_display = ('numero_table', 'qrcode_image', 'capacite')
    list_filter = ('capacite',)
    search_fields = ('numero_table',)
    ordering = ('numero_table',)
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('Commandes_id','Montant', 'Date')
    list_filter = ('Date',)
    search_fields = ('Commandes_id',)
    ordering = ('Date',)
@admin.register(LigneCommandes)
class LigneCommandesAdmin(admin.ModelAdmin):
    list_display = ('Commandes_id', 'Produits_id', 'Quantité', 'Prix_unitaire', 'Sous_Total')
    list_filter = ('Commandes_id',)
    search_fields = ('Produits_id',)
    ordering = ('Commandes_id',)
