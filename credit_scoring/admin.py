from django.contrib import admin
from .models import *

admin.site.register(Conseiller)
admin.site.register(DossierCredit)
admin.site.register(ScoreRisque)
admin.site.register(ExplicationSHAP)
admin.site.register(RapportPDF)
admin.site.register(LogAgent)