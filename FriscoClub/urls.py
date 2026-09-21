from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # ---------------------------------------------------------
    # 1. FRONT-END HTML (Vues Django standard / Panier / Auth)
    # ---------------------------------------------------------
    path('', views.catalogue, name='catalogue'),
    path('login/', views.user_login_view, name='login'),
    path('logout/', views.user_logout_view, name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Panier (Session)
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:produit_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:produit_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:produit_id>/', views.cart_remove, name='cart_remove'),

    # ---------------------------------------------------------
    # 2. API REST (Django REST Framework & JWT)
    # ---------------------------------------------------------
    # Auth API & Tokens
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', views.RegisterView.as_view(), name='api-register'),
    path('api/login/', views.LoginView.as_view(), name='api-login'),

    # Produits
    path('api/produits/', views.ProduitsListCreateView.as_view(), name='produits-list'),
    path('api/produits/<int:pk>/', views.ProduitsDetailView.as_view(), name='produits-detail'),

    # Utilisateurs
    path('api/utilisateurs/', views.UtilisateursListCreateView.as_view(), name='utilisateurs-list'),
    path('api/utilisateurs/<int:pk>/', views.UtilisateursDetailView.as_view(), name='utilisateurs-detail'),

    # Tables
    path('api/tables/', views.TablesListCreateView.as_view(), name='tables-list'),
    path('api/tables/<int:pk>/', views.TablesDetailView.as_view(), name='tables-detail'),

    # Stock & Mouvements

    # API Endpoints - Gestion des Stocks
    path('api/stock/', views.StockListCreateView.as_view(), name='se'),
    path('api/stock/<int:pk>/', views.StockUpdateDeleteView.as_view(), name='stock-update-delete'),
    
    # API Endpoints - Historique des Mouvements
    path('api/mouvementstock/', views.MouvementStockListView.as_view(), name='mouvementstock-list'),
    path('api/mouvementstock/<int:pk>/', views.MouvementStockRetrieveView.as_view(), name='mouvementstock-detail'),
    
    # Vues HTML (Interface d'administration / Tableaux de bord)
    path('gestion-stock/', views.stock_list_view, name='stock_list_html'),
    path('gestion-stock/ajouter/', views.produit_create, name='produit_create'),
    path('gestion-stock/increment/<int:stock_id>/', views.stock_increment, name='stock_increment'),
    path('gestion-stock/supprimer/<int:stock_id>/', views.stock_delete, name='stock_delete'),
    path('gestion-stock/lignes/', views.lignes_commandes_view, name='lignes_commandes_html'),
    path('gestion-stock/lignes/vider/', views.lignes_commandes_clear, name='lignes_commandes_clear'),
    path('gestion-stock/mouvements/', views.mouvements_stock_view, name='mouvements_stock_html'),
    path('gestion-stock/mouvements/vider/', views.mouvements_stock_clear, name='mouvements_stock_clear'),
    path('gestion-equipe/ajouter/', views.create_team_member, name='create_team_member'),
    path('gestion-equipe/', views.user_management_view, name='user_management'),
    path('gestion-equipe/supprimer/<int:user_id>/', views.user_delete, name='user_delete'),

    # Notifications personnel (nouvelle commande passée par un client)
    path('notifications/poll/', views.notifications_poll, name='notifications_poll'),
    path('notifications/<int:notif_id>/lue/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/tout-marquer-lu/', views.notifications_mark_all_read, name='notifications_mark_all_read'),

    # path('api/stock/', views.StockListCreateView.as_view(), name='stock-list'),
    # path('api/stock/update/<int:pk>/', views.StockUpdateDeleteView.as_view(), name='stock-update'),
    # path('api/mouvementstock/', views.MouvementStockListView.as_view(), name='mouvementstock-list'),
    # path('api/mouvementstock/<int:pk>/', views.MouvementStockRetrieveView.as_view(), name='mouvementstock-detail'),
    # path('gestion-stock/', views.stock_list_view, name='stock_list_html'),
    # path('gestion-stock/ajouter/', views.produit_create, name='produit_create'),

    # Commandes
    path('api/commandes/', views.CommandeListCreateView.as_view(), name='commandes-list-create'),
    path('api/commandes/<int:pk>/', views.CommandeDetailView.as_view(), name='commandes-detail'),
    path('api/commandes/<int:pk>/statut/', views.CommandeStatusUpdateView.as_view(), name='commandes-status-update'),

    # Page d'acceuil, catalogue et checkout

    # 1. Route racine -> Page d'accueil avec la bannière Hero
    path('', views.acceuil, name='acceuil'),

    # 2. Route du catalogue -> Carte complète avec filtres et recherche
    path('catalogue/', views.catalogue, name='catalogue'),

    # 3. Validation de commande
    path('checkout/', views.checkout, name='checkout'),

    # ---------------------------------------------------------
    # 3. INTERFACE CLIENT "PHONE FRAME" (déclenchée par le QR code)
    # ---------------------------------------------------------
    path('client/', views.client_home, name='client_home'),
    path('client/catalogue/', views.client_catalogue, name='client_catalogue'),
    path('client/cart/', views.client_cart_detail, name='client_cart_detail'),
    path('client/cart/add/<int:produit_id>/', views.client_cart_add, name='client_cart_add'),
    path('client/cart/update/<int:produit_id>/', views.client_cart_update, name='client_cart_update'),
    path('client/cart/remove/<int:produit_id>/', views.client_cart_remove, name='client_cart_remove'),
    path('client/checkout/', views.client_checkout, name='client_checkout'),
]
