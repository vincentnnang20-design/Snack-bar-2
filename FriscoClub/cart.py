# gerer le panier d'achat pour le site FriscoClub
from decimal import Decimal
from .models import Produits  

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, produit, quantite=1, override_quantite=False):
        produit_id = str(produit.id)
        if produit_id not in self.cart:
            self.cart[produit_id] = {
                'quantite': 0,
                'prix': str(produit.Prix_vente)
            }
        
        if override_quantite:
            self.cart[produit_id]['quantite'] = quantite
        else:
            self.cart[produit_id]['quantite'] += quantite
            
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, produit):
        produit_id = str(produit.id)
        if produit_id in self.cart:
            del self.cart[produit_id]
            self.save()

    def __iter__(self):
        produit_ids = self.cart.keys()
        produits = Produits.objects.filter(id__in=produit_ids)
        cart = self.cart.copy()

        for produit in produits:
            cart[str(produit.id)]['produit'] = produit

        for item in cart.values():
            item['prix'] = Decimal(item['prix'])
            item['total_prix'] = item['prix'] * item['quantite']
            yield item

    def __len__(self):
        return sum(item['quantite'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['prix']) * item['quantite'] for item in self.cart.values())

    def clear(self):
        del self.session['cart']
        self.save()
    