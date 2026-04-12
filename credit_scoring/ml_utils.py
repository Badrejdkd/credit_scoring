import numpy as np
import joblib
import os
from django.conf import settings
from .models import ScoreRisque, ExplicationSHAP


def scorer_dossier(dossier):
    """
    Charge le modèle XGBoost et score le dossier.
    Crée ou met à jour ScoreRisque + ExplicationSHAP.
    """

    # ── 1. Charger le modèle ──
    model_path = os.path.join(
        settings.BASE_DIR,
        'credit_scoring',
        'ml_model',
        'xgboost_model.pkl'
    )

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Modèle introuvable : {model_path}"
        )

    model = joblib.load(model_path)

    # ── 2. Vecteur de features ──
    X = np.array([dossier.to_ml_vector()])

    # ── 3. Prédiction ──
    proba_defaut = float(model.predict_proba(X)[0][1])
    score        = round((1 - proba_defaut) * 100, 2)

    # ── 4. Sauvegarder le score ──
    score_obj, _ = ScoreRisque.objects.update_or_create(
        dossier=dossier,
        defaults={
            'score':        score,
            'proba_defaut': proba_defaut,
        }
    )

    # ── 5. Explications SHAP ──
    try:
        import shap

        explainer   = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        if isinstance(shap_values, list):
            vals = shap_values[1][0]
        else:
            vals = shap_values[0]

        feature_names = [
            'revolving_utilization',
            'age',
            'nb_30_59_days_late',
            'debt_ratio',
            'monthly_income',
            'nb_open_credit_lines',
            'nb_90_days_late',
            'nb_real_estate_loans',
            'nb_60_89_days_late',
            'nb_dependents',
        ]

        score_obj.explications.all().delete()

        for name, val in zip(feature_names, vals):
            ExplicationSHAP.objects.create(
                score=score_obj,
                variable=name,
                valeur_shap=float(val),
            )

    except Exception as e:
        print(f"SHAP non disponible : {e}")

    return score_obj