from django.http import HttpResponse, request
from rest_framework import status, generics
from drf_spectacular.utils import extend_schema

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Produits,Utilisateurs, Tables, MouvementStock, Paiement,Commandes, LigneCommandes, Stock, Clients, PasswordResetCode, Notification
from .serializers import ProduitsSerializer, UtilisateursSerializer, TablesSerializer, MouvementStockSerializer, PaiementSerializer,CommandeReadSerializer,CommandeWriteSerializer,CommandeStatusUpdateSerializer ,LigneCommandesSerializer, StockSerializer, LoginSerializer, RegisterSerializer
from .permissions import EstGerant, EstCaissier, EstServeur, EstFournisseur, EstStaff

class DetailActionMixin:
      """Dispatches explicitly routed actions on generic detail views."""
      action_methods = {}

      def _run_action(self, request, **kwargs):
            action_name = kwargs.pop('action')
            method_name = self.action_methods.get(action_name)
            if not method_name:
                  return Response({'detail': 'Action inconnue.'}, status=status.HTTP_404_NOT_FOUND)
            return getattr(self, method_name)(request, pk=kwargs['pk'])

      def positive_quantity(self, request):
            try:
                  quantity = int(request.data.get('quantite', 0))
            except (TypeError, ValueError):
                  return None
            return quantity if quantity > 0 else None

      def get(self, request, *args, **kwargs):
            if 'action' in kwargs:
                  return self._run_action(request, **kwargs)
            return super().get(request, *args, **kwargs)

      def post(self, request, *args, **kwargs):
            if 'action' in kwargs:
                  return self._run_action(request, **kwargs)
            return Response({'detail': 'Methode non autorisee.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)




from django.db import transaction
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from .models import Produits, Stock, MouvementStock
from .serializers import ProduitsSerializer

# Liste tous les produits (GET) + en créer un nouveau (POST)
class ProduitsListCreateView(generics.ListCreateAPIView):
    queryset = Produits.objects.all()
    serializer_class = ProduitsSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_gerant') and user.is_gerant():
            return Produits.objects.all()
        return Produits.objects.filter(is_available=True)

    def perform_create(self, serializer):
        user = self.request.user
        if not (hasattr(user, 'is_gerant') and user.is_gerant()):
            raise PermissionDenied("Vous n'avez pas la permission de créer un produit.")
        # Sauvegarde du produit
        with transaction.atomic():
            nouveau_produit = serializer.save()

            # Assurer qu'une ligne de stock existe (le signal peut déjà l'avoir créée)
            stock, created = Stock.objects.get_or_create(
                Produits_id=nouveau_produit,
                defaults={'Quantité_actuel': 0, 'Seuil_alert': 5}
            )

            # Si l'appel API fournit une quantité initiale, enregistrer un mouvement d'entrée
            try:
                initial = int(self.request.data.get('initial_stock', 0))
            except (TypeError, ValueError):
                initial = 0

            if initial and initial > 0:
                mouvement = MouvementStock(Stock_id=stock, Types='Entrée', Quantité=initial, Motif='Stock initial')
                mouvement.enregistrer()


# Récupère (GET), modifie (PUT/PATCH) ou supprime (DELETE) un produit précis
class ProduitsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Produits.objects.all()
    serializer_class = ProduitsSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_gerant') and user.is_gerant():
            return Produits.objects.all()
        return Produits.objects.filter(is_available=True)

    def perform_update(self, serializer):
        user = self.request.user
        if hasattr(user, 'is_gerant') and user.is_gerant():
            serializer.save()
        else:
            raise PermissionDenied("Vous n'avez pas la permission de modifier ce produit.")

    def perform_destroy(self, instance):
        user = self.request.user
        if not (hasattr(user, 'is_gerant') and user.is_gerant()):
            raise PermissionDenied("Vous n'avez pas la permission de supprimer ce produit.")
        
        # Sécurisation des opérations de suppression logique et physique
        with transaction.atomic():
            # 1. Marquer le produit comme indisponible au lieu de le supprimer définitivement
            instance.is_available = False
            instance.save()
            
            # 2. Nettoyer le stock et ses mouvements liés
            stock = Stock.objects.filter(Produits_id=instance).first()
            if stock:
                MouvementStock.objects.filter(Stock_id=stock).delete()
                stock.delete()




class UtilisateursListCreateView(generics.ListCreateAPIView):
      queryset = Utilisateurs.objects.all()
      serializer_class = UtilisateursSerializer
      permission_classes = [IsAuthenticated]
      def get_queryset(self):
            user = self.request.user
            if user.is_gerant():
                  return Utilisateurs.objects.all()
            # elif user.is_caissier():
            #       return Utilisateurs.objects.filter(role='Caissier')
            # elif user.is_serveur():
            #       return Utilisateurs.objects.filter(role='Serveurs')
            # elif user.is_fournisseur():
            #       return Utilisateurs.objects.filter(role='Fournisseurs')
            else:
                  return Utilisateurs.objects.none()
      def perform_create(self, serializer):
            user = self.request.user
            if user.is_gerant():
                  serializer.save()
            else:
                  raise PermissionError("Vous n'avez pas la permission de créer un utilisateur.")
            


class UtilisateursDetailView(generics.RetrieveUpdateDestroyAPIView):
      queryset = Utilisateurs.objects.all()
      serializer_class = UtilisateursSerializer
      permission_classes = [IsAuthenticated]
      def get_queryset(self):
            user = self.request.user
            if user.is_gerant():
                  return Utilisateurs.objects.all()
            # elif user.is_caissier():
            #       return Utilisateurs.objects.filter(role='Caissier')
            # elif user.is_serveur():
            #       return Utilisateurs.objects.filter(role='Serveurs')
            # elif user.is_fournisseur():
            #       return Utilisateurs.objects.filter(role='Fournisseurs')
            else:
                  return Utilisateurs.objects.none()

      def perform_update(self, serializer):
            user = self.request.user
            if user.is_gerant():
                  serializer.save()
            else:
                  raise PermissionError("Vous n'avez pas la permission de modifier cet utilisateur.")

      def perform_destroy(self, instance):
            user = self.request.user
            if user.is_gerant():
                  instance.delete()
            else:
                  raise PermissionError("Vous n'avez pas la permission de supprimer cet utilisateur.")
# authentifications     
class RegisterView(generics.CreateAPIView):
      serializer_class = RegisterSerializer
      permission_classes = [AllowAny]

# Import your LoginSerializer here
# from .serializers import LoginSerializer 


# class LoginView(APIView):
#     permission_classes = [AllowAny]
#     serializer_class = LoginSerializer  # Kept so drf-spectacular picks up request body automatically

#     @extend_schema(
#         request=LoginSerializer,
#         responses={200: LoginSerializer}, # Or a custom serializer representing the user_data structure
#         summary="User Login",
#         description="Authenticates user and sets access/refresh tokens in HTTP-only cookies.",
#     )
#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']

#         # Generate JWT tokens
#         refresh = RefreshToken.for_user(user)
#         access_token = str(refresh.access_token)
#         refresh_token = str(refresh)

#         # Prepare the response payload (excluding tokens from JSON body)
#         response_data = {
#             "detail": "Login successful",
#             "user_data": {
#                 "id": user.id,
#                 "username": user.username,
#                 "role": getattr(user, 'role', None), # Safe lookup if role is dynamic
#             }
#         }

#         response = Response(response_data, status=status.HTTP_200_OK)

#         # Set Access Token Cookie (Short lived, e.g., 5-15 mins)
#         response.set_cookie(
#             key='access_token',
#             value=access_token,
#             httponly=True,       # Prevents JavaScript XSS attacks from reading token
#             secure=False,        # Set to True in Production with HTTPS
#             samesite='Lax',      # CSRF protection setting ('Lax' or 'Strict')
#             max_age=60 * 15,     # 15 minutes in seconds
#         )

#         # Set Refresh Token Cookie (Longer lived, e.g., 1-7 days)
#         response.set_cookie(
#             key='refresh_token',
#             value=refresh_token,
#             httponly=True,
#             secure=False,        # Set to True in Production with HTTPS
#             samesite='Lax',
#             max_age=60 * 60 * 24 * 7, # 7 days in seconds
#         )

#         return response

#     # user est l'utilisateur déjà trouvé et vérifié
# refresh = RefreshToken.for_user(Utilisateurs.objects.get(username=request.data['username']))





from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .serializers import LoginSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer  # Nécessaire pour drf-spectacular

    @extend_schema(
        request=LoginSerializer,
        summary="Connexion utilisateur",
        description="Authentifie l'utilisateur, renvoie les tokens JWT et configure les cookies HTTP-only.",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Récupération de l'utilisateur après validation du serializer
        user = serializer.validated_data['user']

        # Génération des tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Réponse contenant les tokens dans le JSON ET les infos utilisateur
        response_data = {
            "detail": "Connexion réussie.",
            "access": access_token,
            "refresh": refresh_token,
            "user_data": {
                "id": user.id,
                "username": user.username,
                "role": getattr(user, 'role', None),
            }
        }

        response = Response(response_data, status=status.HTTP_200_OK)

        # Configuration des cookies HTTP-Only (sécurité supplémentaire)
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,  # Mettre à True en production avec HTTPS
            samesite='Lax',
            max_age=60 * 15,  # 15 minutes
        )

        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,  # Mettre à True en production avec HTTPS
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,  # 7 jours
        )

        return response

    
class TablesListCreateView(generics.ListCreateAPIView):
      queryset = Tables.objects.all()
      serializer_class = TablesSerializer
      permission_classes = [IsAuthenticated,]
      parser_classes = [MultiPartParser, FormParser]
class TablesDetailView(generics.RetrieveUpdateDestroyAPIView):
      queryset = Tables.objects.all()
      serializer_class = TablesSerializer
      permission_classes = [IsAuthenticated]
      parser_classes = [MultiPartParser, FormParser]

class MouvementStockRetrieveView(generics.RetrieveAPIView):
      queryset = MouvementStock.objects.all()
      serializer_class = MouvementStockSerializer
      permission_classes = [IsAuthenticated]
      def get_queryset(self):
            user = self.request.user
            if user.is_gerant():
                  return MouvementStock.objects.all()
            else:
                  return MouvementStock.objects.none()
class MouvementStockListView(generics.ListAPIView):
      queryset = MouvementStock.objects.all()
      serializer_class = MouvementStockSerializer
      permission_classes = [IsAuthenticated]
      def get_queryset(self):
            user = self.request.user
            if user.is_gerant():
                  return MouvementStock.objects.all()
            else:
                  return MouvementStock.objects.none()

class PaiementListCreateView(generics.ListCreateAPIView):
      queryset = Paiement.objects.all()
      serializer_class = PaiementSerializer
      permission_classes = [IsAuthenticated]

class PaiementDetailView(generics.RetrieveUpdateDestroyAPIView):
      queryset = Paiement.objects.all()
      serializer_class = PaiementSerializer
      permission_classes = [IsAuthenticated]
      action_methods = {'valider': 'valider', 'generer-ticket': 'generer_ticket'}

      @action(detail=True, methods=['post'])
      def valider(self, request, pk=None):
            paiement = self.get_object()
            if paiement.valider():
                  return Response({'status': 'paiement validé'})
            return Response({'erreur': 'montant insuffisant'}, status=400)
      
      @action(detail=True, methods=['get'])
      def generer_ticket(self, request, pk=None):
            paiement = self.get_object()
            ticket = paiement.genererTicket()
            return Response({'ticket': ticket})

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models import Commandes
from .serializers import (
    CommandeReadSerializer, 
    CommandeWriteSerializer, 
    CommandeStatusUpdateSerializer
)


class CommandeListCreateView(generics.ListCreateAPIView):
    """
    GET /api/commandes/ : Liste les commandes
    POST /api/commandes/ : Crée une nouvelle commande
    """
    queryset = Commandes.objects.all().prefetch_related(
        'lignecommandes_set__Produits_id', 
        'paiement_set', 
        'Clients_id', 
        'numero_table'
    ).order_by('-id')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommandeWriteSerializer
        return CommandeReadSerializer

    @extend_schema(request=CommandeWriteSerializer, responses=CommandeReadSerializer)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        commande = serializer.save()

        read_serializer = CommandeReadSerializer(commande, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class CommandeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/commandes/<id>/ : Récupère une commande
    PUT /api/commandes/<id>/ : Remplace complètement la commande
    DELETE /api/commandes/<id>/ : Supprime la commande
    """
    queryset = Commandes.objects.all().prefetch_related(
        'lignecommandes_set__Produits_id', 
        'paiement_set', 
        'Clients_id', 
        'numero_table'
    )
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CommandeWriteSerializer
        return CommandeReadSerializer

    @extend_schema(request=CommandeWriteSerializer, responses=CommandeReadSerializer)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        commande = serializer.save()

        read_serializer = CommandeReadSerializer(commande, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)


class CommandeStatusUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/commandes/<id>/statut/ : Met à jour uniquement le statut
    """
    queryset = Commandes.objects.all()
    serializer_class = CommandeStatusUpdateSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['patch']
      
class LigneCommandesListCreateView(generics.ListCreateAPIView):
      queryset = LigneCommandes.objects.all()
      serializer_class = LigneCommandesSerializer
      permission_classes = [IsAuthenticated]

class LigneCommandesDetailView(generics.RetrieveAPIView):
      queryset = LigneCommandes.objects.all()
      serializer_class = LigneCommandesSerializer
      permission_classes = [IsAuthenticated]
      action_methods = {'calculer-sous-total': 'calculer_sous_total'}

      @action(detail=True, methods=['post'])
      def calculer_sous_total(self, request, pk=None):
            ligne = self.get_object()
            sous_total = ligne.calculSousTotal()
            return Response({'sous_total': sous_total})
      
from django.db import transaction
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Stock, MouvementStock
from .serializers import StockSerializer

class StockListCreateView(generics.ListCreateAPIView):
    """
    Vue pour lister les stocks existants et en créer de nouveaux.
    L'accès est restreint aux gérants.
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_gerant') and user.is_gerant():
            return Stock.objects.all()
        return Stock.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'is_gerant') and user.is_gerant():
            serializer.save()
        else:
            raise PermissionDenied("Vous n'avez pas la permission d'ajouter un stock.")


class StockUpdateDeleteView(generics.UpdateAPIView, generics.DestroyAPIView):
    """
    Vue pour modifier ou supprimer une ligne de stock.
    La suppression désactive le produit associé et nettoie les mouvements de stock.
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_gerant') and user.is_gerant():
            return Stock.objects.all()
        return Stock.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        if hasattr(user, 'is_gerant') and user.is_gerant():
            serializer.save()
        else:
            raise PermissionDenied("Vous n'avez pas la permission de modifier le stock.")

    def perform_destroy(self, instance):
        user = self.request.user
        if not (hasattr(user, 'is_gerant') and user.is_gerant()):
            raise PermissionDenied("Vous n'avez pas la permission de supprimer le stock.")

        # Utilisation d'une transaction pour garantir la cohérence des données
        with transaction.atomic():
            # 1. Rendre le produit indisponible au lieu de le supprimer
            produit = instance.Produits_id
            if produit:
                produit.is_available = False
                produit.save()

            # 2. Supprimer les mouvements de stock associés
            MouvementStock.objects.filter(Stock_id=instance).delete()

            # 3. Supprimer définitivement la ligne de stock
            instance.delete()

# class StockDetailView(generics.RetrieveUpdateDestroyAPIView):
#       queryset = Stock.objects.all()
#       serializer_class = StockSerializer
#       permission_classes = [IsAuthenticated, EstGerant]

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Produits, Stock
from .cart import Cart


def _stock_disponible(produit):
    """Retourne la quantité actuellement disponible en stock pour un produit."""
    stock = Stock.objects.filter(Produits_id=produit).first()
    return stock.Quantité_actuel if stock else 0


def _est_requete_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


@require_POST
def cart_add(request, produit_id):
    cart = Cart(request)
    produit = get_object_or_404(Produits, id=produit_id)
    quantite = int(request.POST.get('quantite', 1))

    # La quantité totale (déjà dans le panier + ajout demandé) ne doit jamais
    # dépasser la quantité réellement disponible en stock.
    deja_dans_panier = cart.cart.get(str(produit.id), {}).get('quantite', 0)
    stock_disponible = _stock_disponible(produit)

    if deja_dans_panier + quantite > stock_disponible:
        message = (
            f"Stock insuffisant pour « {produit.nom} ». "
            f"Quantité maximale disponible : {stock_disponible}."
        )
        if _est_requete_ajax(request):
            return JsonResponse(
                {'ok': False, 'message': message, 'stock_disponible': stock_disponible},
                status=400,
            )
        messages.error(request, message)
        return redirect('cart_detail')

    cart.add(produit=produit, quantite=quantite)
    return redirect('cart_detail')

def cart_remove(request, produit_id):
    cart = Cart(request)
    produit = get_object_or_404(Produits, id=produit_id)
    cart.remove(produit)
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})

 # À conserver pour vos tests Thunder Client (à retirer en prod)
@require_POST
def cart_update(request, produit_id):
    cart = Cart(request)
    produit = get_object_or_404(Produits, id=produit_id)
    
    # Récupération de la nouvelle quantité envoyée par le formulaire
    quantite = int(request.POST.get('quantite', 1))
    
    if quantite > 0:
        # Impossible de mettre en panier une quantité supérieure au stock disponible
        stock_disponible = _stock_disponible(produit)

        if quantite > stock_disponible:
            message = (
                f"Stock insuffisant pour « {produit.nom} ». "
                f"Quantité maximale disponible : {stock_disponible}."
            )
            if _est_requete_ajax(request):
                return JsonResponse(
                    {'ok': False, 'message': message, 'stock_disponible': stock_disponible},
                    status=400,
                )
            messages.error(request, message)
            return redirect('cart_detail')

        # Met à jour la quantité avec la nouvelle valeur (override=True)
        cart.add(produit=produit, quantite=quantite, override_quantite=True)
    else:
        # Si la quantité est 0 ou négative, on retire le produit du panier
        cart.remove(produit)

    if _est_requete_ajax(request):
        return JsonResponse({'ok': True})
    return redirect('cart_detail')




# vue de connexion et de déconnexion pour le front-end HTML

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail


def user_login_view(request):
    """Gère la connexion des utilisateurs via un formulaire HTML"""
    if request.user.is_authenticated:
        return redirect('catalogue')

    forgot_form = ForgotPasswordForm()
    verify_form = VerifyResetCodeForm()
    new_password_form = NewPasswordForm()
    reset_step = request.session.get('reset_step', 'start')

    if request.method == 'POST':
        if 'forgot_password' in request.POST:
            forgot_form = ForgotPasswordForm(request.POST)
            if forgot_form.is_valid():
                username = forgot_form.cleaned_data['username']
                user = Utilisateurs.objects.get(username__iexact=username)
                if getattr(user, 'is_gerant', False)():
                    messages.error(request, 'Les comptes administrateurs ne peuvent pas réinitialiser leur mot de passe via cette procédure.')
                    reset_step = 'start'
                    return render(request, 'auth/login.html', {
                        'forgot_form': forgot_form,
                        'verify_form': verify_form,
                        'new_password_form': new_password_form,
                        'reset_step': reset_step,
                    })
                reset_code = PasswordResetCode.generate_code(user)
                send_mail(
                    'Code de vérification FriscoClub',
                    f'Votre code de vérification est : {reset_code.code}',
                    'no-reply@friscoclub.com',
                    [user.email],
                    fail_silently=False,
                )
                request.session['reset_step'] = 'verify'
                request.session['reset_username'] = username
                request.session.modified = True
                messages.success(request, 'Un code de vérification a été envoyé à votre adresse email.')
                reset_step = 'verify'
                return render(request, 'auth/login.html', {
                    'forgot_form': forgot_form,
                    'verify_form': verify_form,
                    'new_password_form': new_password_form,
                    'reset_step': reset_step,
                })
            reset_step = 'start'

        if 'verify_code' in request.POST:
            verify_form = VerifyResetCodeForm(request.POST)
            if verify_form.is_valid():
                request.session['reset_step'] = 'new_password'
                request.session['reset_username'] = verify_form.cleaned_data['user'].username
                request.session.modified = True
                new_password_form = NewPasswordForm(initial={'username': verify_form.cleaned_data['user'].username})
                messages.success(request, 'Code validé. Vous pouvez maintenant définir un nouveau mot de passe.')
                reset_step = 'new_password'
                return render(request, 'auth/login.html', {
                    'forgot_form': forgot_form,
                    'verify_form': verify_form,
                    'new_password_form': new_password_form,
                    'reset_step': reset_step,
                })

            reset_step = 'verify'
            username_from_session = request.session.get('reset_username') or request.POST.get('username')
            if username_from_session:
                request.session['reset_username'] = username_from_session
                request.session.modified = True
            verify_form = VerifyResetCodeForm(initial={
                'username': username_from_session,
                'code': request.POST.get('code', ''),
            })
            if request.POST.get('username'):
                messages.error(request, 'Code de vérification incorrect ou expiré. Veuillez réessayer.')

        if 'new_password' in request.POST:
            data = request.POST.copy()
            reset_username = request.session.get('reset_username')
            if reset_username:
                data['username'] = reset_username
            new_password_form = NewPasswordForm(data)
            if new_password_form.is_valid():
                new_password_form.save()
                request.session.pop('reset_username', None)
                request.session.pop('reset_step', None)
                request.session.modified = True
                messages.success(request, 'Votre mot de passe a été réinitialisé avec succès.')
                return redirect('login')
            reset_step = 'new_password'

        username = request.POST.get('username')
        password = request.POST.get('password')
        if username is not None and password is not None:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenue {user.username} !")
                return redirect('catalogue')
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            
    return render(request, 'auth/login.html', {
        'forgot_form': forgot_form,
        'verify_form': verify_form,
        'new_password_form': new_password_form,
        'reset_step': reset_step,
        'reset_username': request.session.get('reset_username', ''),
    })

def user_logout_view(request):
    """Déconnexion de l'utilisateur"""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('login')

# vu du stock pour le front-end HTML
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Stock

@login_required
def stock_list_view(request):
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')

    stocks = Stock.objects.select_related('Produits_id').order_by('Produits_id__nom')
    return render(request, 'stock/stock_list.html', {'stocks': stocks})


@login_required
def stock_increment(request, stock_id):
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')

    if request.method == 'POST':
        try:
            qte = int(request.POST.get('quantite', 0))
        except (TypeError, ValueError):
            qte = 0
        stock = get_object_or_404(Stock, id=stock_id)
        if qte > 0:
            mv = MouvementStock(Stock_id=stock, Types='Entrée', Quantité=qte, Motif='Ajustement gérant')
            mv.enregistrer()
    return redirect('stock_list_html')


@login_required
def stock_delete(request, stock_id):
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')

    stock = get_object_or_404(Stock, id=stock_id)
    with transaction.atomic():
        produit = stock.Produits_id
        if produit:
            produit.is_available = False
            produit.save(update_fields=['is_available'])
        MouvementStock.objects.filter(Stock_id=stock).delete()
        stock.delete()
    return redirect('stock_list_html')


@login_required
def lignes_commandes_view(request):
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')
    lignes = LigneCommandes.objects.select_related('Commandes_id', 'Produits_id').order_by('-id')
    return render(request, 'stock/lignes_commandes.html', {'lignes': lignes})


@login_required
@require_POST
def lignes_commandes_clear(request):
    """Supprime l'historique des lignes et remet les totaux concernés à zéro."""
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')

    with transaction.atomic():
        commande_ids = list(LigneCommandes.objects.values_list('Commandes_id_id', flat=True).distinct())
        deleted_count, _ = LigneCommandes.objects.all().delete()
        if commande_ids:
            Commandes.objects.filter(id__in=commande_ids).update(Montant_Total=0)

    if deleted_count:
        messages.success(request, f'{deleted_count} ligne(s) de commande ont été supprimée(s).')
    else:
        messages.info(request, "L'historique des lignes de commande est déjà vide.")
    return redirect('lignes_commandes_html')


@login_required
def mouvements_stock_view(request):
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')
    mouvements = MouvementStock.objects.select_related('Stock_id__Produits_id').order_by('-Date')
    return render(request, 'stock/mouvements_stock.html', {'mouvements': mouvements})


@login_required
@require_POST
def mouvements_stock_clear(request):
    """Supprime l'historique des mouvements sans modifier les quantités en stock."""
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')

    deleted_count, _ = MouvementStock.objects.all().delete()
    if deleted_count:
        messages.success(request, f'{deleted_count} mouvement(s) de stock ont été supprimé(s).')
    else:
        messages.info(request, "L'historique des mouvements est déjà vide.")
    return redirect('mouvements_stock_html')


#vue d'acceuil pour le front-end HTML

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Produits, Tables, Clients, Commandes, LigneCommandes
from .cart import Cart
from .models import MouvementStock
from django.contrib import messages
from django.contrib.auth import get_user_model



def acceuil(request):
    """Page d'accueil : Vitrine avec les 4 nouveautés et les catégories"""
    # La vitrine ne propose que les produits réellement commandables. Le stock
    # reste toutefois visible dans l'espace de gestion afin d'être réapprovisionné.
    nouveautes = Produits.objects.filter(
        is_available=True,
        stock__Quantité_actuel__gt=0,
    ).distinct().order_by('-id')[:4]
    categories = [choice[1] for choice in Produits.Cathegories_choices]
    
    return render(request, 'acceuil.html', {
        'nouveautes': nouveautes,
        'categories': categories
    })


def catalogue(request):
    """Affiche les produits commandables avec recherche, filtres et pagination."""
    produits_list = Produits.objects.filter(
        is_available=True,
        stock__Quantité_actuel__gt=0,
    ).distinct().order_by('nom', 'id')

    # Récupération des filtres depuis l'URL (GET)
    query = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('categorie', '')
    genre_filter = request.GET.get('genre', '')

    # Application de la recherche textuelle
    if query:
        produits_list = produits_list.filter(Q(nom__icontains=query))
    
    # Application des filtres par catégorie et genre
    if cat_filter:
        produits_list = produits_list.filter(Cathegories=cat_filter)

    if genre_filter:
        produits_list = produits_list.filter(Genres=genre_filter)

    # Pagination : 8 produits par page
    paginator = Paginator(produits_list, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'cat_filter': cat_filter,
        'genre_filter': genre_filter,
        'categories': Produits.Cathegories_choices,
        'genres': Produits.Genres_choices,
        'pagination_pages': paginator.get_elided_page_range(number=page_obj.number, on_each_side=1, on_ends=1),
        'pagination_query': request.GET.copy(),
    }
    context['pagination_query'].pop('page', None)
    context['pagination_query'] = context['pagination_query'].urlencode()
    return render(request, 'catalogue.html', context)


def checkout(request):
    """Page de validation finale de la commande"""
    cart = Cart(request)
    tables = Tables.objects.all()
    
    if request.method == 'POST':
        # Vérification finale du stock avant de valider la commande : la quantité
        # demandée pour chaque produit du panier ne doit pas dépasser le stock
        # réellement disponible (protège aussi contre une rupture de stock
        # survenue entre l'ajout au panier et la validation de la commande).
        indisponibilites = []
        for item in cart:
            stock_disponible = _stock_disponible(item['produit'])
            if item['quantite'] > stock_disponible:
                indisponibilites.append(
                    f"{item['produit'].nom} (demandé : {item['quantite']}, "
                    f"disponible : {stock_disponible})"
                )

        if indisponibilites:
            messages.error(
                request,
                "Stock insuffisant pour valider la commande. "
                "Quantité maximale disponible dépassée pour : "
                + "; ".join(indisponibilites)
            )
            return redirect('cart_detail')

        table_id = request.POST.get('table_id')
        nature = request.POST.get('nature')
        nom_client = request.POST.get('nom_client')
        
        # Création du client si fourni
        client = None
        if nom_client:
            client = Clients.objects.create(nom_client=nom_client)
            
        table = get_object_or_404(Tables, id=table_id)
        
        # Création de la commande
        commande = Commandes.objects.create(
            numero_table=table,
            Clients_id=client,
            nature=nature,
            Montant_Total=cart.get_total_price()
        )
        
        # Enregistrement des lignes de commande
        for item in cart:
            LigneCommandes.objects.create(
                Commandes_id=commande,
                Produits_id=item['produit'],
                Quantité=item['quantite'],
                Prix_unitaire=item['prix']
            )
            # Mettre à jour le stock : créer un mouvement de sortie pour chaque ligne
            try:
                stock = Stock.objects.filter(Produits_id=item['produit']).first()
                if stock:
                    mv = MouvementStock(Stock_id=stock, Types='Sortie', Quantité=item['quantite'], Motif=f'Commande #{commande.id}')
                    mv.enregistrer()
            except Exception:
                pass
            
        cart.clear() # Vider le panier
        return render(request, 'cart/success.html', {'commande': commande})

    return render(request, 'cart/checkout.html', {'cart': cart, 'tables': tables})


# incrementer le stock d'un produit spécifique via une vue HTML et creer un nouveau produit

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Produits
from .forms import ProduitForm, TeamMemberForm, PasswordResetForm, ForgotPasswordForm, VerifyResetCodeForm, NewPasswordForm

@login_required
def produit_create(request):
    """Permet au gérant de créer un nouveau produit"""
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')

    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save()

            # Si le gérant a fourni une quantité initiale, l'enregistrer
            try:
                initial = int(request.POST.get('initial_stock', 0))
            except (TypeError, ValueError):
                initial = 0

            stock, created = Stock.objects.get_or_create(Produits_id=produit, defaults={'Quantité_actuel': 0, 'Seuil_alert': 5})
            if initial and initial > 0:
                mv = MouvementStock(Stock_id=stock, Types='Entrée', Quantité=initial, Motif='Stock initial')
                mv.enregistrer()

            return redirect('stock_list_html')
    else:
        form = ProduitForm()

    return render(request, 'stock/produit_form.html', {'form': form})


@login_required
def create_team_member(request):
    """Permet au gérant d’enregistrer un membre de l’équipe et de réinitialiser un mot de passe."""
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')

    team_form = TeamMemberForm()
    reset_form = PasswordResetForm()

    if request.method == 'POST':
        if 'reset_password' in request.POST or 'new_password' in request.POST:
            reset_form = PasswordResetForm(request.POST)
            if reset_form.is_valid():
                reset_form.save()
                messages.success(request, 'Le mot de passe a été réinitialisé avec succès.')
                return redirect('create_team_member')
        elif 'username' in request.POST and 'password' in request.POST and 'password_confirm' in request.POST and 'role' in request.POST:
            team_form = TeamMemberForm(request.POST)
            if team_form.is_valid():
                team_form.save()
                messages.success(request, 'Le membre de l’équipe a été créé avec succès.')
                return redirect('create_team_member')

    return render(request, 'auth/create_team_member.html', {
        'team_form': team_form,
        'reset_form': reset_form,
    })


@login_required
def user_management_view(request):
    """Vue réservée au gérant pour lister tous les utilisateurs et leurs informations."""
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')

    users = Utilisateurs.objects.all().order_by('username')
    return render(request, 'auth/user_management.html', {'users': users})


@login_required
def user_delete(request, user_id):
    if not getattr(request.user, 'is_gerant', False):
        return redirect('acceuil')
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect('user_management')
        user.delete()
        messages.success(request, 'Utilisateur supprimé.')
        return redirect('user_management')
    return render(request, 'auth/user_delete_confirm.html', {'user_obj': user})


# =====================================================================
# INTERFACE CLIENT — "PHONE FRAME"
# ---------------------------------------------------------------------
# Ensemble de vues dédiées à l'expérience mobile déclenchée par le scan
# du QR code posé sur chaque table. Elles réutilisent la même logique
# métier (panier de session, stock, commandes) que le site principal,
# mais sont rendues dans un gabarit compact façon smartphone, avec des
# rangées de produits en défilement horizontal (accueil, catalogue et
# disponibilité du stock).
# =====================================================================

def _sync_client_table(request):
    """Mémorise en session la table scannée (paramètre ?table= du QR code)."""
    numero_table = request.GET.get('table')
    if numero_table:
        table = Tables.objects.filter(numero_table=numero_table).first()
        if table:
            request.session['numero_table_client'] = table.numero_table
            request.session['client_table_id'] = table.id
    return request.session.get('numero_table_client')


def _client_cart_count(request):
    return len(Cart(request))


def client_home(request):
    """Écran d'accueil de l'interface client (phone frame)."""
    numero_table = _sync_client_table(request)

    nouveautes = Produits.objects.filter(
        is_available=True,
        stock__Quantité_actuel__gt=0,
    ).distinct().order_by('-id')[:10]

    categories = [choice[1] for choice in Produits.Cathegories_choices]

    return render(request, 'clients/accueil.html', {
        'nouveautes': nouveautes,
        'categories': categories,
        'numero_table_client': numero_table,
        'cart_count': _client_cart_count(request),
    })


def client_catalogue(request):
    """Carte / menu du client, organisée en rangées défilables horizontalement."""
    numero_table = _sync_client_table(request)

    produits_list = Produits.objects.filter(
        is_available=True,
        stock__Quantité_actuel__gt=0,
    ).distinct().order_by('nom', 'id')

    query = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('categorie', '')
    genre_filter = request.GET.get('genre', '')

    if query:
        produits_list = produits_list.filter(Q(nom__icontains=query))
    if cat_filter:
        produits_list = produits_list.filter(Cathegories=cat_filter)
    if genre_filter:
        produits_list = produits_list.filter(Genres=genre_filter)

    # Regroupement par genre pour obtenir des rangées "à la Netflix",
    # chacune défilant horizontalement. Si l'utilisateur filtre déjà par
    # genre, une seule rangée est affichée.
    genres_choices = Produits.Genres_choices
    rows = []
    for code, label in genres_choices:
        if genre_filter and genre_filter != code:
            continue
        produits_du_genre = [p for p in produits_list if p.Genres == code]
        if produits_du_genre:
            rows.append({'label': label, 'code': code, 'produits': produits_du_genre})

    context = {
        'rows': rows,
        'query': query,
        'cat_filter': cat_filter,
        'genre_filter': genre_filter,
        'categories': Produits.Cathegories_choices,
        'genres': genres_choices,
        'numero_table_client': numero_table,
        'cart_count': _client_cart_count(request),
        'has_results': any(row['produits'] for row in rows),
    }
    return render(request, 'clients/catalogue.html', context)


def client_cart_detail(request):
    numero_table = _sync_client_table(request)
    cart = Cart(request)
    return render(request, 'clients/cart.html', {
        'cart': cart,
        'numero_table_client': numero_table,
        'cart_count': _client_cart_count(request),
    })


@require_POST
def client_cart_add(request, produit_id):
    cart = Cart(request)
    produit = get_object_or_404(Produits, id=produit_id)
    quantite = int(request.POST.get('quantite', 1))

    deja_dans_panier = cart.cart.get(str(produit.id), {}).get('quantite', 0)
    stock_disponible = _stock_disponible(produit)

    if deja_dans_panier + quantite > stock_disponible:
        message = (
            f"Stock insuffisant pour « {produit.nom} ». "
            f"Quantité maximale disponible : {stock_disponible}."
        )
        if _est_requete_ajax(request):
            return JsonResponse(
                {'ok': False, 'message': message, 'stock_disponible': stock_disponible},
                status=400,
            )
        messages.error(request, message)
        return redirect('client_cart_detail')

    cart.add(produit=produit, quantite=quantite)

    if _est_requete_ajax(request):
        return JsonResponse({'ok': True, 'cart_count': _client_cart_count(request)})
    return redirect(request.POST.get('next') or 'client_cart_detail')


@require_POST
def client_cart_update(request, produit_id):
    cart = Cart(request)
    produit = get_object_or_404(Produits, id=produit_id)
    quantite = int(request.POST.get('quantite', 1))

    if quantite > 0:
        stock_disponible = _stock_disponible(produit)
        if quantite > stock_disponible:
            message = (
                f"Stock insuffisant pour « {produit.nom} ». "
                f"Quantité maximale disponible : {stock_disponible}."
            )
            if _est_requete_ajax(request):
                return JsonResponse(
                    {'ok': False, 'message': message, 'stock_disponible': stock_disponible},
                    status=400,
                )
            messages.error(request, message)
            return redirect('client_cart_detail')
        cart.add(produit=produit, quantite=quantite, override_quantite=True)
    else:
        cart.remove(produit)

    if _est_requete_ajax(request):
        return JsonResponse({'ok': True, 'cart_count': _client_cart_count(request)})
    return redirect('client_cart_detail')


def client_cart_remove(request, produit_id):
    cart = Cart(request)
    produit = get_object_or_404(Produits, id=produit_id)
    cart.remove(produit)
    return redirect('client_cart_detail')


@login_required
def notifications_poll(request):
    """Endpoint AJAX interrogé périodiquement par la sidebar du personnel
    pour savoir si une nouvelle commande vient d'être passée par un client.
    """
    if getattr(request.user, 'role', None) not in ('Gerant', 'Serveurs', 'Caissiers'):
        return JsonResponse({'ok': False}, status=403)

    notifs = Notification.objects.filter(est_lue=False).select_related(
        'Commandes_id', 'Commandes_id__numero_table'
    ).order_by('-Date_creation')[:8]

    data = [{
        'id': n.id,
        'titre': n.titre,
        'message': n.message,
        'date': n.Date_creation.strftime('%d/%m %H:%M'),
        'commande_id': n.Commandes_id_id,
    } for n in notifs]

    return JsonResponse({
        'ok': True,
        'count': Notification.objects.filter(est_lue=False).count(),
        'notifications': data,
    })


@login_required
@require_POST
def notification_mark_read(request, notif_id):
    if getattr(request.user, 'role', None) not in ('Gerant', 'Serveurs', 'Caissiers'):
        return JsonResponse({'ok': False}, status=403)
    notif = get_object_or_404(Notification, id=notif_id)
    notif.marquer_comme_lue()
    return JsonResponse({'ok': True, 'count': Notification.objects.filter(est_lue=False).count()})


@login_required
@require_POST
def notifications_mark_all_read(request):
    if getattr(request.user, 'role', None) not in ('Gerant', 'Serveurs', 'Caissiers'):
        return JsonResponse({'ok': False}, status=403)
    Notification.objects.filter(est_lue=False).update(est_lue=True)
    return JsonResponse({'ok': True, 'count': 0})


def client_checkout(request):
    """Validation de commande depuis l'interface client (table pré-remplie)."""
    numero_table = _sync_client_table(request)
    cart = Cart(request)
    table = None
    table_id = request.session.get('client_table_id')
    if table_id:
        table = Tables.objects.filter(id=table_id).first()

    if request.method == 'POST':
        indisponibilites = []
        for item in cart:
            stock_disponible = _stock_disponible(item['produit'])
            if item['quantite'] > stock_disponible:
                indisponibilites.append(
                    f"{item['produit'].nom} (demandé : {item['quantite']}, "
                    f"disponible : {stock_disponible})"
                )

        if indisponibilites:
            messages.error(
                request,
                "Stock insuffisant pour valider la commande. "
                "Quantité maximale disponible dépassée pour : "
                + "; ".join(indisponibilites)
            )
            return redirect('client_cart_detail')

        # --- Mode de paiement choisi par le client ---
        mode_paiement = request.POST.get('mode_paiement')
        operateur_paiement = request.POST.get('operateur_paiement', '').strip()
        numero_paiement = request.POST.get('numero_paiement', '').strip()

        if mode_paiement not in dict(Commandes.Mode_paiement_choices):
            messages.error(request, "Veuillez choisir un mode de paiement valide.")
            return redirect('client_checkout')

        if mode_paiement == 'numerique' and not numero_paiement:
            messages.error(
                request,
                "Veuillez indiquer le numéro à utiliser pour le paiement numérique "
                "(Orange Money / Mobile Money)."
            )
            return redirect('client_checkout')

        if mode_paiement == 'espece':
            operateur_paiement = ''
            numero_paiement = ''
            statut_paiement = 'a_payer_comptoir'
        else:
            statut_paiement = 'en_attente_confirmation'

        table = get_object_or_404(Tables, id=request.POST.get('table_id') or table_id)
        nature = request.POST.get('nature', 'consommer sur place')
        nom_client = request.POST.get('nom_client')

        client = None
        if nom_client:
            client = Clients.objects.create(nom_client=nom_client)

        commande = Commandes.objects.create(
            numero_table=table,
            Clients_id=client,
            nature=nature,
            Montant_Total=cart.get_total_price(),
            mode_paiement=mode_paiement,
            operateur_paiement=operateur_paiement or None,
            numero_paiement=numero_paiement or None,
            statut_paiement=statut_paiement,
        )

        for item in cart:
            LigneCommandes.objects.create(
                Commandes_id=commande,
                Produits_id=item['produit'],
                Quantité=item['quantite'],
                Prix_unitaire=item['prix']
            )
            try:
                stock = Stock.objects.filter(Produits_id=item['produit']).first()
                if stock:
                    mv = MouvementStock(Stock_id=stock, Types='Sortie', Quantité=item['quantite'], Motif=f'Commande #{commande.id}')
                    mv.enregistrer()
            except Exception:
                pass

        # --- Notification du personnel : une commande vient d'être passée ---
        try:
            Notification.creer_pour_commande(commande)
        except Exception:
            pass

        cart.clear()
        return render(request, 'clients/success.html', {
            'commande': commande,
            'numero_table_client': numero_table,
        })

    return render(request, 'clients/checkout.html', {
        'cart': cart,
        'table': table,
        'tables': Tables.objects.all(),
        'numero_table_client': numero_table,
        'cart_count': _client_cart_count(request),
    })
