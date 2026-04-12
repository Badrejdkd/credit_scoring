import requests
import json


OLLAMA_MODEL = 'llama2'


def construire_contexte(dossier):
    score   = getattr(dossier, 'score', None)
    shap_qs = score.explications.all().order_by('-valeur_shap') if score else []

    contexte = f"""Tu es un expert senior en analyse de crédit bancaire au Maroc.
Tu analyses les dossiers de crédit et fournis des recommandations professionnelles.
Réponds toujours en français, de manière claire, concise et professionnelle.
Ne mentionne jamais que tu es une IA ou un modèle de langage.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOSSIER CLIENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 INFORMATIONS PERSONNELLES
- Nom complet       : {dossier.client_nom} {dossier.client_prenom}
- Âge               : {dossier.age} ans
- Revenu mensuel    : {dossier.monthly_income:,.0f} MAD

📊 INDICATEURS FINANCIERS
- Revolving Util.   : {dossier.revolving_utilization:.2f}
- Debt Ratio        : {dossier.debt_ratio:.2f}
- Lignes de crédit  : {dossier.nb_open_credit_lines}
- Prêts immobiliers : {dossier.nb_real_estate_loans}
- Personnes à charge: {dossier.nb_dependents}

⚠️ HISTORIQUE DES RETARDS
- Retards 30-59j    : {dossier.nb_30_59_days_late} fois
- Retards 60-89j    : {dossier.nb_60_89_days_late} fois
- Retards 90j+      : {dossier.nb_90_days_late} fois
"""

    if score:
        contexte += f"""
🎯 RÉSULTAT DU SCORING XGBoost
- Score de crédit   : {score.score:.1f} / 100
- Prob. de défaut   : {score.proba_defaut:.4f} ({score.proba_defaut * 100:.1f}%)
- Niveau de risque  : {score.get_niveau_risque()}
"""

    if shap_qs:
        contexte += "\n🔍 FACTEURS D'INFLUENCE (SHAP)\n"
        for e in shap_qs:
            signe  = "+" if e.valeur_shap > 0 else ""
            impact = "↑ augmente le risque" if e.valeur_shap > 0 else "↓ réduit le risque"
            contexte += f"  - {e.variable:<30} : {signe}{e.valeur_shap:.4f}  ({impact})\n"

    contexte += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Appuie-toi uniquement sur les données fournies ci-dessus.
- Sois précis, professionnel et donne des recommandations concrètes.
- Si la question est générale, donne une analyse globale du dossier.
- Maximum 4-5 phrases sauf si une explication détaillée est demandée.
- Ne répète pas les données brutes, interprète-les.
"""
    return contexte


def construire_prompt(dossier, question):
    contexte = construire_contexte(dossier)
    prompt   = f"""{contexte}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUESTION DU CONSEILLER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{question}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RÉPONSE DE L'EXPERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    return prompt


def poser_question(dossier, question):
    prompt = construire_prompt(dossier, question)

    payload = {
        'model':  OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0.3,
            'top_p':       0.9,
            'top_k':       40,
            'num_predict': 600,
            'stop':        ['━━━', 'QUESTION', 'DOSSIER'],
        }
    }

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data    = response.json()
        reponse = data.get('response', '').strip()

        if not reponse:
            return "Le modèle n'a pas retourné de réponse. Réessayez."

        return reponse

    except requests.exceptions.ConnectionError:
        return (
            "❌ Ollama n'est pas démarré.\n"
            "Ouvrez un terminal et lancez : ollama serve\n"
            "Ensuite vérifiez que le modèle est installé : ollama list"
        )

    except requests.exceptions.Timeout:
        return (
            "❌ La requête a expiré (timeout 120s).\n"
            "Le modèle est peut-être trop lourd pour votre machine.\n"
            "Essayez : ollama pull gemma:2b"
        )

    except requests.exceptions.HTTPError as e:
        return f"❌ Erreur HTTP Ollama : {e}"

    except Exception as e:
        return f"❌ Erreur inattendue : {str(e)}"


def verifier_ollama():
    try:
        response = requests.get(
            'http://localhost:11434/api/tags',
            timeout=5
        )
        response.raise_for_status()
        data    = response.json()
        modeles = [m['name'] for m in data.get('models', [])]
        return {
            'disponible': True,
            'modeles':    modeles,
            'message':    f"{len(modeles)} modèle(s) disponible(s)",
        }
    except requests.exceptions.ConnectionError:
        return {
            'disponible': False,
            'modeles':    [],
            'message':    'Ollama non démarré — lancez : ollama serve',
        }
    except Exception as e:
        return {
            'disponible': False,
            'modeles':    [],
            'message':    str(e),
        }