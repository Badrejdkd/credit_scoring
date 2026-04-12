import os
from django.conf import settings
from django.utils import timezone
from .models import RapportPDF


def generer_rapport(dossier):
    """
    Génère un rapport PDF pour le dossier avec ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        raise ImportError("ReportLab non installé. Faites : pip install reportlab")

    # Dossier de sortie
    output_dir = os.path.join(settings.MEDIA_ROOT, 'rapports')
    os.makedirs(output_dir, exist_ok=True)

    filename  = f"rapport_{dossier.pk}_{dossier.client_nom}_{dossier.client_prenom}.pdf"
    filepath  = os.path.join(output_dir, filename)

    score  = getattr(dossier, 'score', None)
    shap   = score.explications.all().order_by('-valeur_shap') if score else []

    # ── Styles ──
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#b87333'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    style_subtitle = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#888888'),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    style_section = ParagraphStyle(
        'Section',
        parent=styles['Normal'],
        fontSize=13,
        textColor=colors.HexColor('#b87333'),
        fontName='Helvetica-Bold',
        spaceBefore=16,
        spaceAfter=8,
    )
    style_normal = ParagraphStyle(
        'Normal2',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4,
    )
    style_recommandation = ParagraphStyle(
        'Reco',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        leftIndent=10,
    )

    # ── Couleur risque ──
    if score:
        risque = score.get_niveau_risque()
        if risque == 'Faible':
            risque_color = colors.HexColor('#6b8e6b')
            reco_text    = "✅ Crédit recommandé. Le profil présente un faible risque de défaut."
        elif risque == 'Élevé':
            risque_color = colors.HexColor('#c27878')
            reco_text    = "❌ Crédit déconseillé. Le profil présente un risque élevé de défaut."
        else:
            risque_color = colors.HexColor('#b87333')
            reco_text    = "⚠️ Examen approfondi recommandé. Le profil présente un risque modéré."
    else:
        risque_color = colors.grey
        reco_text    = "Aucun score disponible."

    # ── Contenu ──
    story = []

    # En-tête
    story.append(Paragraph("CreditAI — Rapport de Scoring de Crédit", style_title))
    story.append(Paragraph(f"EMSI Casablanca · Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#b87333'), spaceAfter=16))

    # Infos client
    story.append(Paragraph("Informations Client", style_section))
    client_data = [
        ['Nom complet',    f'{dossier.client_nom} {dossier.client_prenom}'],
        ['Âge',            f'{dossier.age} ans'],
        ['Revenu mensuel', f'{dossier.monthly_income:,.0f} MAD'],
        ['Debt Ratio',     f'{dossier.debt_ratio:.2f}'],
        ['Revolving Util.', f'{dossier.revolving_utilization:.2f}'],
        ['Lignes de crédit', str(dossier.nb_open_credit_lines)],
        ['Prêts immobiliers', str(dossier.nb_real_estate_loans)],
        ['Personnes à charge', str(dossier.nb_dependents)],
    ]
    client_table = Table(client_data, colWidths=[6*cm, 11*cm])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f0e8')),
        ('TEXTCOLOR',  (0, 0), (0, -1), colors.HexColor('#b87333')),
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(client_table)

    # Retards
    story.append(Paragraph("Retards de Paiement", style_section))
    retards_data = [
        ['Retards 30-59 jours', str(dossier.nb_30_59_days_late)],
        ['Retards 60-89 jours', str(dossier.nb_60_89_days_late)],
        ['Retards 90+ jours',   str(dossier.nb_90_days_late)],
    ]
    retards_table = Table(retards_data, colWidths=[6*cm, 11*cm])
    retards_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f0e8')),
        ('TEXTCOLOR',  (0, 0), (0, -1), colors.HexColor('#b87333')),
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(retards_table)

    # Score
    if score:
        story.append(Paragraph("Résultat du Scoring XGBoost", style_section))
        score_data = [
            ['Score de crédit',    f'{score.score:.1f} / 100'],
            ['Probabilité défaut', f'{score.proba_defaut:.4f}'],
            ['Niveau de risque',   score.get_niveau_risque()],
        ]
        score_table = Table(score_data, colWidths=[6*cm, 11*cm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f0e8')),
            ('TEXTCOLOR',  (0, 0), (0, -1), colors.HexColor('#b87333')),
            ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR',  (1, 2), (1, 2), risque_color),
            ('FONTNAME',   (1, 2), (1, 2), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(score_table)

    # SHAP
    if shap:
        story.append(Paragraph("Facteurs d'Influence (SHAP)", style_section))
        shap_data_table = [['Variable', 'Valeur SHAP', 'Impact']]
        for e in shap:
            impact = '↑ Risque' if e.valeur_shap > 0 else '↓ Risque'
            shap_data_table.append([
                e.variable,
                f'{e.valeur_shap:+.4f}',
                impact,
            ])
        shap_table = Table(shap_data_table, colWidths=[8*cm, 4*cm, 5*cm])
        shap_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#b87333')),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(shap_table)

    # Recommandation
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dddddd'), spaceAfter=12))
    story.append(Paragraph("Recommandation", style_section))
    story.append(Paragraph(reco_text, style_recommandation))

    # Conseiller
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Rapport établi par : {dossier.conseiller.user.get_full_name()} — {dossier.conseiller.agence}",
        style_normal
    ))

    # ── Génération PDF ──
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    doc.build(story)

    # Sauvegarder en base
    rapport, _ = RapportPDF.objects.update_or_create(
        dossier=dossier,
        defaults={'fichier_path': filepath}
    )

    return rapport