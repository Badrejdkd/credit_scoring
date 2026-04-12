from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg
from django.http import FileResponse, Http404
import os

from .models import Conseiller, DossierCredit, ScoreRisque, ExplicationSHAP, RapportPDF, LogAgent


# ─────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────
@login_required
def dashboard(request):
    try:
        conseiller = request.user.conseiller
        dossiers = DossierCredit.objects.filter(conseiller=conseiller)
    except Conseiller.DoesNotExist:
        dossiers = DossierCredit.objects.none()

    nb_dossiers = dossiers.count()
    nb_faible   = sum(1 for d in dossiers if hasattr(d, 'score') and d.score.get_niveau_risque() == 'Faible')
    nb_modere   = sum(1 for d in dossiers if hasattr(d, 'score') and d.score.get_niveau_risque() == 'Modéré')
    nb_eleve    = sum(1 for d in dossiers if hasattr(d, 'score') and d.score.get_niveau_risque() == 'Élevé')

    scores = ScoreRisque.objects.filter(dossier__in=dossiers)
    score_moyen = round(scores.aggregate(Avg('score'))['score__avg'] or 0, 1)

    derniers_dossiers = dossiers.order_by('-created_at')[:5]
    derniers_logs     = LogAgent.objects.filter(dossier__in=dossiers).order_by('-created_at')[:5]

    return render(request, 'dashboard.html', {
        'nb_dossiers':       nb_dossiers,
        'nb_faible':         nb_faible,
        'nb_modere':         nb_modere,
        'nb_eleve':          nb_eleve,
        'score_moyen':       score_moyen,
        'derniers_dossiers': derniers_dossiers,
        'derniers_logs':     derniers_logs,
        'today':             timezone.now(),
    })


# ─────────────────────────────────────────
#  NOUVEAU DOSSIER
# ─────────────────────────────────────────
@login_required
def nouveau_dossier(request):
    try:
        conseiller = request.user.conseiller
    except Conseiller.DoesNotExist:
        messages.error(request, 'Profil conseiller introuvable.')
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            dossier = DossierCredit.objects.create(
                conseiller            = conseiller,
                client_nom            = request.POST.get('client_nom', '').strip(),
                client_prenom         = request.POST.get('client_prenom', '').strip(),
                revolving_utilization = float(request.POST.get('revolving_utilization', 0)),
                age                   = int(request.POST.get('age', 0)),
                nb_30_59_days_late    = int(request.POST.get('nb_30_59_days_late', 0)),
                debt_ratio            = float(request.POST.get('debt_ratio', 0)),
                monthly_income        = float(request.POST.get('monthly_income', 0)),
                nb_open_credit_lines  = int(request.POST.get('nb_open_credit_lines', 0)),
                nb_90_days_late       = int(request.POST.get('nb_90_days_late', 0)),
                nb_real_estate_loans  = int(request.POST.get('nb_real_estate_loans', 0)),
                nb_60_89_days_late    = int(request.POST.get('nb_60_89_days_late', 0)),
                nb_dependents         = int(request.POST.get('nb_dependents', 0)),
            )

            # Lancer le scoring ML si disponible
            try:
                from .ml_utils import scorer_dossier
                scorer_dossier(dossier)
                messages.success(request, f'Dossier créé et scoré avec succès !')
            except Exception:
                import traceback
                messages.error(request, f'ERREUR SCORING : {traceback.format_exc()}')

            messages.success(request, f'Dossier de {dossier.client_nom} créé avec succès !')
            return redirect('detail_dossier', pk=dossier.pk)

        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {e}')

    return render(request, 'nouveau_dossier.html')


# ─────────────────────────────────────────
#  HISTORIQUE
# ─────────────────────────────────────────
@login_required
def historique(request):
    try:
        conseiller = request.user.conseiller
        dossiers = DossierCredit.objects.filter(conseiller=conseiller).order_by('-created_at')
    except Conseiller.DoesNotExist:
        dossiers = DossierCredit.objects.none()

    query = request.GET.get('q', '')
    if query:
        dossiers = dossiers.filter(client_nom__icontains=query) | \
                   dossiers.filter(client_prenom__icontains=query)

    return render(request, 'historique.html', {
        'dossiers': dossiers,
        'query':    query,
    })


# ─────────────────────────────────────────
#  DETAIL DOSSIER
# ─────────────────────────────────────────
@login_required
def detail_dossier(request, pk):
    try:
        conseiller = request.user.conseiller
    except Conseiller.DoesNotExist:
        return redirect('dashboard')

    dossier = get_object_or_404(DossierCredit, pk=pk, conseiller=conseiller)
    score   = getattr(dossier, 'score', None)
    shap    = score.explications.all().order_by('-valeur_shap') if score else []
    logs    = dossier.logs.order_by('-created_at')

    dossier_data = [
        ('Nom complet',           f'{dossier.client_nom} {dossier.client_prenom}'),
        ('Âge',                   f'{dossier.age} ans'),
        ('Revenu mensuel',        f'{dossier.monthly_income:,.0f} MAD'),
        ('Revolving Utilization', f'{dossier.revolving_utilization:.2f}'),
        ('Debt Ratio',            f'{dossier.debt_ratio:.2f}'),
        ('Lignes de crédit',      dossier.nb_open_credit_lines),
        ('Prêts immobiliers',     dossier.nb_real_estate_loans),
        ('Personnes à charge',    dossier.nb_dependents),
        ('Retards 30-59j',        dossier.nb_30_59_days_late),
        ('Retards 60-89j',        dossier.nb_60_89_days_late),
        ('Retards 90j+',          dossier.nb_90_days_late),
        ('Date création',         dossier.created_at.strftime('%d/%m/%Y %H:%M')),
    ]

    return render(request, 'detail_dossier.html', {
        'dossier':      dossier,
        'score':        score,
        'shap':         shap,
        'logs':         logs,
        'dossier_data': dossier_data,
    })


# ─────────────────────────────────────────
#  SUPPRIMER DOSSIER
# ─────────────────────────────────────────
@login_required
def supprimer_dossier(request, pk):
    try:
        conseiller = request.user.conseiller
    except Conseiller.DoesNotExist:
        return redirect('dashboard')

    dossier = get_object_or_404(DossierCredit, pk=pk, conseiller=conseiller)
    if request.method == 'POST':
        dossier.delete()
        messages.success(request, 'Dossier supprimé avec succès.')
        return redirect('historique')

    return render(request, 'confirmer_suppression.html', {'dossier': dossier})


# ─────────────────────────────────────────
#  SHAP & EXPLICATION
# ─────────────────────────────────────────


@login_required
def shap_liste(request):
    try:
        conseiller = request.user.conseiller
        dossiers = DossierCredit.objects.filter(
            conseiller=conseiller
        ).exclude(score=None).order_by('-created_at')
    except Conseiller.DoesNotExist:
        dossiers = DossierCredit.objects.none()

    return render(request, 'shap_liste.html', {'dossiers': dossiers})


@login_required
def chatbot_liste(request):
    try:
        conseiller = request.user.conseiller
        dossiers = DossierCredit.objects.filter(
            conseiller=conseiller
        ).order_by('-created_at')
    except Conseiller.DoesNotExist:
        dossiers = DossierCredit.objects.none()

    return render(request, 'chatbot_liste.html', {'dossiers': dossiers})


@login_required
def rapport_liste(request):
    try:
        conseiller = request.user.conseiller
        dossiers = DossierCredit.objects.filter(
            conseiller=conseiller
        ).order_by('-created_at')
    except Conseiller.DoesNotExist:
        dossiers = DossierCredit.objects.none()

    return render(request, 'rapport_liste.html', {'dossiers': dossiers})


@login_required
def shap_explication(request, pk):
    try:
        conseiller = request.user.conseiller
    except Conseiller.DoesNotExist:
        return redirect('dashboard')

    dossier = get_object_or_404(DossierCredit, pk=pk, conseiller=conseiller)
    score   = getattr(dossier, 'score', None)
    shap    = score.explications.all().order_by('-valeur_shap') if score else []

    # Calcul pour barres visuelles
    shap_data = []
    if shap:
        max_val = max(abs(e.valeur_shap) for e in shap) or 1
        for e in shap:
            pct = round((abs(e.valeur_shap) / max_val) * 100)
            shap_data.append({
                'variable':    e.variable,
                'valeur_shap': e.valeur_shap,
                'pct':         pct,
                'positif':     e.valeur_shap > 0,
            })

    return render(request, 'shap_explication.html', {
        'dossier':   dossier,
        'score':     score,
        'shap_data': shap_data,
    })


# ─────────────────────────────────────────
#  CHATBOT LLM
# ─────────────────────────────────────────
@login_required
def chatbot(request, pk):
    try:
        conseiller = request.user.conseiller
    except Conseiller.DoesNotExist:
        return redirect('dashboard')

    dossier = get_object_or_404(DossierCredit, pk=pk, conseiller=conseiller)
    score   = getattr(dossier, 'score', None)
    logs    = dossier.logs.order_by('created_at')
    reponse = None

    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        if question:
            try:
                from .llm_utils import poser_question
                reponse = poser_question(dossier, question)
            except Exception as e:
                reponse = f"Erreur LLM : {e}"

            LogAgent.objects.create(
                dossier=dossier,
                question=question,
                reponse=reponse,
            )
            return redirect('chatbot', pk=pk)

    return render(request, 'chatbot.html', {
        'dossier': dossier,
        'score':   score,
        'logs':    logs,
    })


# ─────────────────────────────────────────
#  RAPPORT PDF
# ─────────────────────────────────────────
@login_required
def rapport_pdf(request, pk):
    try:
        conseiller = request.user.conseiller
    except Conseiller.DoesNotExist:
        return redirect('dashboard')

    dossier = get_object_or_404(DossierCredit, pk=pk, conseiller=conseiller)
    score   = getattr(dossier, 'score', None)
    rapport = getattr(dossier, 'rapport', None)

    if request.method == 'POST':
        try:
            from .pdf_utils import generer_rapport
            rapport = generer_rapport(dossier)
            messages.success(request, 'Rapport PDF généré avec succès !')
        except Exception as e:
            messages.error(request, f'Erreur génération PDF : {e}')
        return redirect('rapport_pdf', pk=pk)

    return render(request, 'rapport_pdf.html', {
        'dossier': dossier,
        'score':   score,
        'rapport': rapport,
    })


@login_required
def telecharger_pdf(request, pk):
    try:
        conseiller = request.user.conseiller
    except Conseiller.DoesNotExist:
        return redirect('dashboard')

    dossier = get_object_or_404(DossierCredit, pk=pk, conseiller=conseiller)
    rapport = getattr(dossier, 'rapport', None)

    if not rapport or not os.path.exists(rapport.fichier_path):
        raise Http404("Rapport introuvable.")

    return FileResponse(
        open(rapport.fichier_path, 'rb'),
        as_attachment=True,
        filename=f'rapport_{dossier.client_nom}_{dossier.client_prenom}.pdf'
    )


# ─────────────────────────────────────────
#  LOGIN / REGISTER / LOGOUT
# ─────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        user = authenticate(request,
            username=request.POST.get('username'),
            password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Identifiants incorrects.')
    return render(request, 'login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        prenom    = request.POST.get('prenom', '').strip()
        nom       = request.POST.get('nom', '').strip()
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        agence    = request.POST.get('agence', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not all([prenom, nom, username, email, agence, password1, password2]):
            messages.error(request, 'Tous les champs sont obligatoires.')
        elif password1 != password2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        elif len(password1) < 8:
            messages.error(request, 'Mot de passe trop court (8 caractères min).')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Nom d\'utilisateur déjà pris.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email déjà utilisé.')
        else:
            user = User.objects.create_user(
                username=username, email=email,
                password=password1, first_name=prenom, last_name=nom)
            Conseiller.objects.create(user=user, agence=agence)
            messages.success(request, 'Compte créé ! Connectez-vous.')
            return redirect('login')

    return render(request, 'register.html')


def logout_view(request):
    logout(request)
    return redirect('login')