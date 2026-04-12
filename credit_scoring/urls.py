from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('',             views.login_view,     name='login'),
    path('register/',    views.register_view,  name='register'),
    path('logout/',      views.logout_view,    name='logout'),

    # Dashboard
    path('dashboard/',   views.dashboard,      name='dashboard'),

    # Dossiers
    path('dossier/nouveau/',            views.nouveau_dossier,   name='nouveau_dossier'),
    path('dossier/historique/',         views.historique,        name='historique'),
    path('dossier/<int:pk>/',           views.detail_dossier,    name='detail_dossier'),
    path('dossier/<int:pk>/supprimer/', views.supprimer_dossier, name='supprimer_dossier'),

    # Pages liste (sidebar)
    path('dossier/shap/',               views.shap_liste,        name='shap_liste'),
    path('dossier/chatbot/',            views.chatbot_liste,     name='chatbot_liste'),
    path('dossier/rapport/',            views.rapport_liste,     name='rapport_liste'),

    # Pages détail avec pk
    path('dossier/shap/<int:pk>/',        views.shap_explication, name='shap_explication'),
    path('dossier/chatbot/<int:pk>/',     views.chatbot,          name='chatbot'),
    path('dossier/rapport/<int:pk>/',     views.rapport_pdf,      name='rapport_pdf'),
    path('dossier/telecharger/<int:pk>/', views.telecharger_pdf,  name='telecharger_pdf'),
]