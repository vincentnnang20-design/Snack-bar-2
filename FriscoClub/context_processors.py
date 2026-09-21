from .models import Notification


def notifications_context(request):
    """Rend le nombre de notifications non lues disponible dans tous les
    templates de l'espace personnel (Gérant / Serveurs / Caissiers), afin
    d'afficher la cloche de notification dans la sidebar/topbar.

    Les clients (interface "phone frame") ne sont jamais authentifiés en
    tant que membres du personnel : le compteur reste donc à 0 pour eux.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    if getattr(user, 'role', None) not in ('Gerant', 'Serveurs', 'Caissiers'):
        return {}

    unread_qs = Notification.objects.filter(est_lue=False).select_related(
        'Commandes_id', 'Commandes_id__numero_table'
    ).order_by('-Date_creation')

    return {
        'notifications_unread_count': unread_qs.count(),
        'notifications_recentes': unread_qs[:8],
        'is_staff_member': True,
    }
