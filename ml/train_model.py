import pandas as pd
import numpy as np
import joblib
import os
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    confusion_matrix,
    accuracy_score
)
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


# ════════════════════════════════════════
#  1. CHARGEMENT DES DONNÉES
# ════════════════════════════════════════
print("📂 Chargement des données...")

df = pd.read_csv('cs-training.csv', index_col=0)
print(f"   Shape initial : {df.shape}")
print(f"   Colonnes : {list(df.columns)}")

# Aperçu
print("\n📊 Distribution de la target :")
print(df['SeriousDlqin2yrs'].value_counts())
print(f"   Taux de défaut : {df['SeriousDlqin2yrs'].mean():.2%}")


# ════════════════════════════════════════
#  2. PRÉTRAITEMENT
# ════════════════════════════════════════
print("\n🔧 Prétraitement...")

# Supprimer les doublons
df = df.drop_duplicates()
print(f"   Après suppression doublons : {df.shape}")

# Valeurs manquantes
print(f"\n   Valeurs manquantes :")
print(df.isnull().sum()[df.isnull().sum() > 0])

# Imputer MonthlyIncome par la médiane
df['MonthlyIncome'] = df['MonthlyIncome'].fillna(df['MonthlyIncome'].median())

# Imputer NumberOfDependents par 0
df['NumberOfDependents'] = df['NumberOfDependents'].fillna(0)

# Supprimer les lignes restantes avec NaN
df = df.dropna()
print(f"   Après imputation : {df.shape}")

# Supprimer les valeurs aberrantes
# age < 18 ou > 100
df = df[(df['age'] >= 18) & (df['age'] <= 100)]

# RevolvingUtilization > 1 (taux > 100%)
df = df[df['RevolvingUtilizationOfUnsecuredLines'] <= 1.5]

# MonthlyIncome > 0
df = df[df['MonthlyIncome'] > 0]

print(f"   Après nettoyage aberrants : {df.shape}")


# ════════════════════════════════════════
#  3. FEATURES — même ordre que to_ml_vector()
# ════════════════════════════════════════
feature_names = [
    'RevolvingUtilizationOfUnsecuredLines',  # revolving_utilization
    'age',                                    # age
    'NumberOfTime30-59DaysPastDueNotWorse',  # nb_30_59_days_late
    'DebtRatio',                             # debt_ratio
    'MonthlyIncome',                         # monthly_income
    'NumberOfOpenCreditLinesAndLoans',       # nb_open_credit_lines
    'NumberOfTimes90DaysLate',              # nb_90_days_late
    'NumberRealEstateLoansOrLines',          # nb_real_estate_loans
    'NumberOfTime60-89DaysPastDueNotWorse', # nb_60_89_days_late
    'NumberOfDependents',                   # nb_dependents
]

X = df[feature_names]
y = df['SeriousDlqin2yrs']

print(f"\n✅ Features sélectionnées : {len(feature_names)}")
print(f"   X shape : {X.shape}")
print(f"   y shape : {y.shape}")


# ════════════════════════════════════════
#  4. SPLIT TRAIN / TEST
# ════════════════════════════════════════
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"\n✂️  Split train/test :")
print(f"   Train : {X_train.shape[0]} exemples")
print(f"   Test  : {X_test.shape[0]} exemples")


# ════════════════════════════════════════
#  5. ENTRAÎNEMENT XGBoost
# ════════════════════════════════════════
print("\n🤖 Entraînement XGBoost...")

# Gestion du déséquilibre des classes
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
print(f"   Scale pos weight : {scale_pos_weight:.2f}")

model = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    eval_metric='auc',
    early_stopping_rounds=20,
    verbosity=0,
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=False,
)

print("   ✅ Entraînement terminé !")


# ════════════════════════════════════════
#  6. ÉVALUATION
# ════════════════════════════════════════
print("\n📈 Évaluation du modèle :")

y_pred       = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, y_pred)
auc      = roc_auc_score(y_test, y_pred_proba)

print(f"   Accuracy  : {accuracy:.4f}")
print(f"   AUC-ROC   : {auc:.4f}")
print(f"\n   Rapport de classification :")
print(classification_report(y_test, y_pred, target_names=['Non défaut', 'Défaut']))

print(f"   Matrice de confusion :")
print(confusion_matrix(y_test, y_pred))


# ════════════════════════════════════════
#  7. IMPORTANCE DES FEATURES
# ════════════════════════════════════════
print("\n🔍 Importance des features :")
importances = model.feature_importances_
for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
    bar = '█' * int(imp * 50)
    print(f"   {name:<45} {imp:.4f}  {bar}")


# ════════════════════════════════════════
#  8. SEUIL OPTIMAL
# ════════════════════════════════════════
from sklearn.metrics import precision_recall_curve, f1_score

precisions, recalls, thresholds = precision_recall_curve(y_test, y_pred_proba)
f1_scores = 2 * precisions * recalls / (precisions + recalls + 1e-8)
best_threshold = thresholds[np.argmax(f1_scores)]
print(f"\n⚙️  Seuil optimal (F1 max) : {best_threshold:.4f}")


# ════════════════════════════════════════
#  9. SAUVEGARDE
# ════════════════════════════════════════
print("\n💾 Sauvegarde du modèle...")

# Sauvegarder dans ml/
joblib.dump(model, 'xgboost_model.pkl')
print("   ✅ xgboost_model.pkl sauvegardé dans ml/")

# Copier automatiquement dans Django
django_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'credit_scoring', 'ml_model', 'xgboost_model.pkl'
)
os.makedirs(os.path.dirname(django_path), exist_ok=True)
joblib.dump(model, django_path)
print(f"   ✅ Copié dans : {django_path}")

# Sauvegarder les métadonnées
import json
metadata = {
    'feature_names':   feature_names,
    'n_features':      len(feature_names),
    'accuracy':        round(accuracy, 4),
    'auc_roc':         round(auc, 4),
    'best_threshold':  round(float(best_threshold), 4),
    'n_train':         int(X_train.shape[0]),
    'n_test':          int(X_test.shape[0]),
    'scale_pos_weight': round(float(scale_pos_weight), 2),
}
with open('model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("   ✅ model_metadata.json sauvegardé")

print("\n🎉 Pipeline terminé avec succès !")
print(f"   AUC-ROC final : {auc:.4f}")
print(f"   Seuil optimal : {best_threshold:.4f}")