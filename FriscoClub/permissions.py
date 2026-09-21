from rest_framework.permissions import BasePermission

class EstGerant(BasePermission):
    """Autorise uniquement les administrateurs/gerants"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_gerant()
    
class EstCaissier(BasePermission):
    """Autorise uniquement les caissiers et gerants"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_caissier() or request.user.is_gerant()
        )
    
class EstServeur(BasePermission):
    """Autorise uniquement les serveurs et gerants"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_serveur() or request.user.is_gerant()
        )
    
class EstFournisseur(BasePermission):
    """Autorise uniquement les fournisseurs et gerants"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_fournisseur() or request.user.is_gerant()
        )

class EstStaff(BasePermission):
    """Autorise tout le personnel(pas les clients)"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role != 'Clients'
