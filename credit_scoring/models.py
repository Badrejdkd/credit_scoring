from django.contrib.auth.models import User
from django.db import models


class Conseiller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    agence = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.agence}"


class DossierCredit(models.Model):
    conseiller = models.ForeignKey(Conseiller, on_delete=models.CASCADE, related_name='dossiers')
    client_nom = models.CharField(max_length=100)
    client_prenom = models.CharField(max_length=100)
    revolving_utilization = models.FloatField()
    age = models.IntegerField()
    nb_30_59_days_late = models.IntegerField()
    debt_ratio = models.FloatField()
    monthly_income = models.FloatField()
    nb_open_credit_lines = models.IntegerField()
    nb_90_days_late = models.IntegerField()
    nb_real_estate_loans = models.IntegerField()
    nb_60_89_days_late = models.IntegerField()
    nb_dependents = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client_nom} {self.client_prenom}"

    def to_ml_vector(self):
        return [
            self.revolving_utilization, self.age,
            self.nb_30_59_days_late, self.debt_ratio,
            self.monthly_income, self.nb_open_credit_lines,
            self.nb_90_days_late, self.nb_real_estate_loans,
            self.nb_60_89_days_late, self.nb_dependents,
        ]


class ScoreRisque(models.Model):
    dossier = models.OneToOneField(DossierCredit, on_delete=models.CASCADE, related_name='score')
    score = models.FloatField()
    proba_defaut = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def get_niveau_risque(self):
        if self.proba_defaut < 0.2:
            return "Faible"
        elif self.proba_defaut < 0.5:
            return "Modéré"
        return "Élevé"

    def __str__(self):
        return f"Score {self.score} — {self.get_niveau_risque()}"


class ExplicationSHAP(models.Model):
    score = models.ForeignKey(ScoreRisque, on_delete=models.CASCADE, related_name='explications')
    variable = models.CharField(max_length=100)
    valeur_shap = models.FloatField()

    def __str__(self):
        return f"{self.variable} : {self.valeur_shap}"


class RapportPDF(models.Model):
    dossier = models.OneToOneField(DossierCredit, on_delete=models.CASCADE, related_name='rapport')
    fichier_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rapport — {self.dossier}"


class LogAgent(models.Model):
    dossier = models.ForeignKey(DossierCredit, on_delete=models.CASCADE, related_name='logs')
    question = models.TextField()
    reponse = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.dossier} — {self.created_at:%Y-%m-%d %H:%M}"