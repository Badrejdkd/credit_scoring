# credit_scoring
# 🏦 CreditAI — Système Intelligent de Scoring de Risque de Crédit

> Plateforme web IA pour l'analyse et la prise de décision en matière de crédit bancaire.
> PFA 4ème année — EMSI Casablanca · Filière IA & Data Science

---

## 📋 Description

Face au constat que les décisions de crédit dans le secteur bancaire marocain reposent encore sur des critères manuels et peu explicables, **CreditAI** est une plateforme web intelligente qui combine :

- 🎯 **Scoring ML** avec XGBoost pour prédire le risque de défaut
- 🔍 **Explicabilité SHAP** pour comprendre chaque décision variable par variable
- 🤖 **Agent LLM + RAG** pour répondre aux questions en langage naturel sur les dossiers
- 📄 **Rapports PDF** générés automatiquement avec score, SHAP et analyse IA
- 📊 **Dashboard BI** interactif avec KPIs du portefeuille crédit

---

## 🚀 Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 🔐 Authentification | Login / Register sécurisé par conseiller |
| 📁 Soumission dossier | Formulaire avec 11 variables financières |
| 🎯 Scoring automatique | Modèle XGBoost + probabilité de défaut |
| 🔍 Explication SHAP | Graphique waterfall par variable |
| 🤖 Chatbot LLM | Agent conversationnel avec RAG (ChromaDB) |
| 📄 Export PDF | Rapport complet score + SHAP + analyse LLM |
| 📊 Dashboard KPI | Distribution des scores, taux de défaut |
| 📂 Historique | Consultation des dossiers analysés |

---

## 🛠️ Stack Technique
Backend        →  Python 3.11 · Django 6 · SQL Server
Machine Learning → XGBoost · Scikit-learn · SHAP · MLflow
LLM / RAG      →  LangChain · LangGraph · Gemini API · ChromaDB
Frontend       →  Django Templates · Bootstrap 5 · Chart.js
Export         →  ReportLab
Base de données → Microsoft SQL Server (mssql-django)
Outils         →  VSCode · Git · Jupyter Notebook

---

## ⚙️ Installation

### 1. Cloner le projet
```bash
git clone https://github.com/votre-repo/creditai.git
cd creditai
```

### 2. Créer l'environnement virtuel
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Créer la base de données dans SQL Server
```sql
CREATE DATABASE pfa_project;
```

### 5. Configurer `settings.py`
```python
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'pfa_project',
        'HOST': 'VOTRE_HOST\\SQLEXPRESS',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'trusted_connection': 'yes',
        },
    }
}
```

### 6. Appliquer les migrations
```bash
python manage.py makemigrations credit_scoring
python manage.py migrate
```

### 7. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 8. Lancer le serveur
```bash
python manage.py runserver
```

Ouvrir : **http://127.0.0.1:8000**

---

## 📦 Requirements
django
mssql-django
pyodbc
scikit-learn
xgboost
shap
mlflow
langchain
langgraph
langchain-google-genai
chromadb
reportlab
pillow
python-decouple

---

## 🗄️ Modèle de données
Conseiller ──< DossierCredit ──1── ScoreRisque ──< ExplicationSHAP
│
├──0/1── RapportPDF
└──────< LogAgent

| Modèle | Description |
|---|---|
| `Conseiller` | Lié à User Django, avec agence |
| `DossierCredit` | 11 variables financières du client |
| `ScoreRisque` | Score + probabilité de défaut |
| `ExplicationSHAP` | Valeur SHAP par variable |
| `RapportPDF` | Chemin vers le PDF généré |
| `LogAgent` | Historique des échanges LLM |

---


## 🏫 Contexte académique

- **Établissement** : EMSI Casablanca
- **Filière** : Intelligence Artificielle & Data Science
- **Niveau** : 4ème année — Projet de Fin d'Année (PFA)
- **Durée** : 7 semaines
- **Année** : 2025–2026
---

## 📄 Licence

Projet académique — EMSI Casablanca. Usage éducatif uniquement.
