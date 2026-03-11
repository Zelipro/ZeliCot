"""
Save.py — Utilitaires de génération et d'export de rapports pour ZeliCot.

Fonctions publiques :
    get_available_renderers()                    -> list[{id, label}]
    get_available_save_locations(page)           -> list[{path, label}]
    generer_rapport(...)                         -> str (chemin du fichier généré)
    generer_rapport_stat_personne(...)           -> str (chemin du fichier généré)
"""

import os
import time as _time


# ---------------------------------------------------------------------------
# Détection des moteurs disponibles
# ---------------------------------------------------------------------------

def _has_reportlab() -> bool:
    try:
        import reportlab  # noqa: F401
        return True
    except ImportError:
        return False


def _has_fpdf() -> bool:
    try:
        import fpdf  # noqa: F401
        return True
    except ImportError:
        return False


def get_available_renderers():
    """Retourne la liste des moteurs de rendu disponibles sur la machine."""
    renderers = [{"id": "html", "label": "HTML"}]
    if _has_reportlab():
        renderers.append({"id": "reportlab", "label": "ReportLab (PDF)"})
    if _has_fpdf():
        renderers.append({"id": "fpdf", "label": "FPDF (PDF)"})
    return renderers


def get_available_save_locations(page=None):
    """Retourne les dossiers de sauvegarde disponibles sur la machine."""
    home = os.path.expanduser("~")
    candidates = [
        {"path": home,                                      "label": "Dossier personnel (~)"},
        {"path": os.path.join(home, "Documents"),           "label": "Documents"},
        {"path": os.path.join(home, "Téléchargements"),     "label": "Téléchargements"},
        {"path": os.path.join(home, "Downloads"),           "label": "Downloads"},
        {"path": os.path.join(home, "Bureau"),              "label": "Bureau"},
        {"path": os.path.join(home, "Desktop"),             "label": "Desktop"},
    ]
    locations = [c for c in candidates if os.path.isdir(c["path"])]
    if not locations:
        locations = [{"path": home, "label": "Dossier personnel (~)"}]
    return locations


# ---------------------------------------------------------------------------
# Styles HTML communs
# ---------------------------------------------------------------------------

_HTML_STYLE = """
<style>
  body  { font-family: Arial, sans-serif; margin: 40px; color: #1C2233; }
  h1    { color: #2D7D4D; border-bottom: 2px solid #2D7D4D; padding-bottom: 6px; }
  h2    { color: #1F5A35; margin-top: 28px; }
  table { border-collapse: collapse; width: 100%; margin-top: 12px; }
  th    { background: #2D7D4D; color: white; padding: 10px; text-align: left; }
  td    { padding: 9px 10px; border-bottom: 1px solid #E2E5EC; }
  tr:hover td { background: #F7FAF8; }
  .total  { font-weight: bold; color: #2D7D4D; font-size: 15px; margin-top: 16px; }
  .footer { margin-top: 40px; font-size: 12px; color: #6B7280; }
</style>
"""


# ---------------------------------------------------------------------------
# HTML — Rapport de cotisation
# ---------------------------------------------------------------------------

def _html_rapport(cotisation_name: str, cotisants) -> str:
    rows = ""
    total = 0.0
    for idx, (name, prix, date) in enumerate(cotisants, 1):
        prix_f = float(prix)
        total += prix_f
        rows += f"<tr><td>{idx}</td><td>{name}</td><td>{prix_f:.2f}</td><td>{date}</td></tr>\n"

    now = _time.strftime("%d/%m/%Y à %H:%M:%S")
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Rapport - {cotisation_name}</title>{_HTML_STYLE}</head>
<body>
<h1>Rapport de cotisation</h1>
<h2>Motif : {cotisation_name}</h2>
<table>
  <thead><tr><th>#</th><th>Nom</th><th>Montant</th><th>Date</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
<p class="total">Total : {total:.2f}</p>
<p class="footer">Généré le {now}</p>
</body></html>"""


# ---------------------------------------------------------------------------
# HTML — Statistique personne
# ---------------------------------------------------------------------------

def _html_stat_personne(person_name: str, stats, total_fois: int, total_montant: float) -> str:
    rows = ""
    for idx, s in enumerate(stats, 1):
        rows += (
            f"<tr><td>{idx}</td><td>{s['cotisation']}</td>"
            f"<td>{s['fois']}</td><td>{s['montant']:.2f}</td></tr>\n"
        )
    now = _time.strftime("%d/%m/%Y à %H:%M:%S")
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Statistique - {person_name}</title>{_HTML_STYLE}</head>
<body>
<h1>Statistique personnelle</h1>
<h2>Personne : {person_name}</h2>
<table>
  <thead><tr><th>#</th><th>Cotisation</th><th>Nombre de fois</th><th>Montant</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
<p class="total">Total cotisations : {total_fois} | Total payé : {total_montant:.2f}</p>
<p class="footer">Généré le {now}</p>
</body></html>"""


# ---------------------------------------------------------------------------
# ReportLab — Rapport de cotisation
# ---------------------------------------------------------------------------

def _pdf_reportlab_rapport(cotisation_name: str, cotisants, dest_path: str):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate(dest_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Rapport de cotisation — {cotisation_name}", styles["Title"]))
    story.append(Spacer(1, 12))

    data = [["#", "Nom", "Montant", "Date"]]
    total = 0.0
    for idx, (name, prix, date) in enumerate(cotisants, 1):
        prix_f = float(prix)
        total += prix_f
        data.append([str(idx), name, f"{prix_f:.2f}", date or ""])
    data.append(["", "TOTAL", f"{total:.2f}", ""])

    table = Table(data, colWidths=[30, 200, 80, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0),  (-1, 0),  colors.HexColor("#2D7D4D")),
        ("TEXTCOLOR",      (0, 0),  (-1, 0),  colors.white),
        ("FONTNAME",       (0, 0),  (-1, 0),  "Helvetica-Bold"),
        ("GRID",           (0, 0),  (-1, -1), 0.5, colors.HexColor("#C9D1DC")),
        ("BACKGROUND",     (0, -1), (-1, -1), colors.HexColor("#E8F5E9")),
        ("FONTNAME",       (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1),  (-1, -2), [colors.white, colors.HexColor("#F7FAF8")]),
        ("ALIGN",          (2, 0),  (2, -1),  "RIGHT"),
        ("ALIGN",          (0, 0),  (0, -1),  "CENTER"),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Généré le {_time.strftime('%d/%m/%Y à %H:%M:%S')}",
        styles["Normal"],
    ))
    doc.build(story)


# ---------------------------------------------------------------------------
# ReportLab — Statistique personne
# ---------------------------------------------------------------------------

def _pdf_reportlab_stat(
    person_name: str, stats, total_fois: int, total_montant: float, dest_path: str
):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate(dest_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Statistique — {person_name}", styles["Title"]))
    story.append(Spacer(1, 12))

    data = [["#", "Cotisation", "Nombre de fois", "Montant"]]
    for idx, s in enumerate(stats, 1):
        data.append([str(idx), s["cotisation"], str(s["fois"]), f"{s['montant']:.2f}"])
    data.append(["", "TOTAL", str(total_fois), f"{total_montant:.2f}"])

    table = Table(data, colWidths=[30, 220, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0),  (-1, 0),  colors.HexColor("#2D7D4D")),
        ("TEXTCOLOR",      (0, 0),  (-1, 0),  colors.white),
        ("FONTNAME",       (0, 0),  (-1, 0),  "Helvetica-Bold"),
        ("GRID",           (0, 0),  (-1, -1), 0.5, colors.HexColor("#C9D1DC")),
        ("BACKGROUND",     (0, -1), (-1, -1), colors.HexColor("#E8F5E9")),
        ("FONTNAME",       (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1),  (-1, -2), [colors.white, colors.HexColor("#F7FAF8")]),
        ("ALIGN",          (0, 0),  (0, -1),  "CENTER"),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Généré le {_time.strftime('%d/%m/%Y à %H:%M:%S')}",
        styles["Normal"],
    ))
    doc.build(story)


# ---------------------------------------------------------------------------
# FPDF — Rapport de cotisation
# ---------------------------------------------------------------------------

def _pdf_fpdf_rapport(cotisation_name: str, cotisants, dest_path: str):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(45, 125, 77)
    pdf.cell(0, 12, f"Rapport — {cotisation_name}", ln=True)

    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(45, 125, 77)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 8, "#",       fill=True, border=1)
    pdf.cell(80, 8, "Nom",     fill=True, border=1)
    pdf.cell(30, 8, "Montant", fill=True, border=1)
    pdf.cell(60, 8, "Date",    fill=True, border=1, ln=True)

    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(28, 34, 51)
    total = 0.0
    for idx, (name, prix, date) in enumerate(cotisants, 1):
        prix_f = float(prix)
        total += prix_f
        fill = idx % 2 == 0
        pdf.set_fill_color(247, 250, 248) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 7, str(idx),        border=1, fill=fill)
        pdf.cell(80, 7, str(name),       border=1, fill=fill)
        pdf.cell(30, 7, f"{prix_f:.2f}", border=1, fill=fill)
        pdf.cell(60, 7, str(date or ""), border=1, fill=fill, ln=True)

    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(232, 245, 233)
    pdf.cell(10, 8, "",             fill=True, border=1)
    pdf.cell(80, 8, "TOTAL",        fill=True, border=1)
    pdf.cell(30, 8, f"{total:.2f}", fill=True, border=1)
    pdf.cell(60, 8, "",             fill=True, border=1, ln=True)

    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(107, 114, 128)
    pdf.ln(8)
    pdf.cell(0, 6, f"Généré le {_time.strftime('%d/%m/%Y à %H:%M:%S')}")
    pdf.output(dest_path)


# ---------------------------------------------------------------------------
# FPDF — Statistique personne
# ---------------------------------------------------------------------------

def _pdf_fpdf_stat(
    person_name: str, stats, total_fois: int, total_montant: float, dest_path: str
):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(45, 125, 77)
    pdf.cell(0, 12, f"Statistique — {person_name}", ln=True)

    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(45, 125, 77)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 8, "#",          fill=True, border=1)
    pdf.cell(90, 8, "Cotisation", fill=True, border=1)
    pdf.cell(40, 8, "Nb de fois", fill=True, border=1)
    pdf.cell(40, 8, "Montant",    fill=True, border=1, ln=True)

    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(28, 34, 51)
    for idx, s in enumerate(stats, 1):
        fill = idx % 2 == 0
        pdf.set_fill_color(247, 250, 248) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 7, str(idx),                border=1, fill=fill)
        pdf.cell(90, 7, str(s["cotisation"]),     border=1, fill=fill)
        pdf.cell(40, 7, str(s["fois"]),           border=1, fill=fill)
        pdf.cell(40, 7, f"{s['montant']:.2f}",   border=1, fill=fill, ln=True)

    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(232, 245, 233)
    pdf.cell(10, 8, "",                     fill=True, border=1)
    pdf.cell(90, 8, "TOTAL",               fill=True, border=1)
    pdf.cell(40, 8, str(total_fois),       fill=True, border=1)
    pdf.cell(40, 8, f"{total_montant:.2f}", fill=True, border=1, ln=True)

    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(107, 114, 128)
    pdf.ln(8)
    pdf.cell(0, 6, f"Généré le {_time.strftime('%d/%m/%Y à %H:%M:%S')}")
    pdf.output(dest_path)


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

def generer_rapport(
    page,
    cotisation_name: str,
    cotisants,
    destination_dir: str,
    renderer: str,
) -> str:
    """
    Génère un rapport de cotisation dans un sous-dossier portant le nom de la cotisation.
    cotisants : liste de tuples (name, prix, date).
    Retourne le chemin complet du fichier généré.
    """
    safe_name = cotisation_name.replace("/", "_").replace("\\", "_")
    timestamp = _time.strftime("%Y%m%d_%H%M%S")

    # Créer le sous-dossier <destination_dir>/<nom_cotisation>/
    folder = os.path.join(destination_dir, safe_name)
    os.makedirs(folder, exist_ok=True)

    if renderer == "html":
        filename = f"rapport_{safe_name}_{timestamp}.html"
        dest_path = os.path.join(folder, filename)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(_html_rapport(cotisation_name, cotisants))

    elif renderer == "reportlab":
        filename = f"rapport_{safe_name}_{timestamp}.pdf"
        dest_path = os.path.join(folder, filename)
        _pdf_reportlab_rapport(cotisation_name, cotisants, dest_path)

    elif renderer == "fpdf":
        filename = f"rapport_{safe_name}_{timestamp}.pdf"
        dest_path = os.path.join(folder, filename)
        _pdf_fpdf_rapport(cotisation_name, cotisants, dest_path)

    else:
        raise ValueError(f"Moteur de rendu inconnu : {renderer!r}")

    return dest_path


def generer_rapport_stat_personne(
    page,
    person_name: str,
    stats,
    total_fois: int,
    total_montant: float,
    destination_dir: str,
    renderer: str,
) -> str:
    """
    Génère un rapport de statistique dans un sous-dossier portant le nom de la personne.
    stats : liste de dicts {'cotisation': str, 'fois': int, 'montant': float}.
    Retourne le chemin complet du fichier généré.
    """
    safe_name = person_name.replace("/", "_").replace("\\", "_")
    timestamp = _time.strftime("%Y%m%d_%H%M%S")

    # Créer le sous-dossier <destination_dir>/<nom_personne>/
    folder = os.path.join(destination_dir, safe_name)
    os.makedirs(folder, exist_ok=True)

    if renderer == "html":
        filename = f"stat_{safe_name}_{timestamp}.html"
        dest_path = os.path.join(folder, filename)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(_html_stat_personne(person_name, stats, total_fois, total_montant))

    elif renderer == "reportlab":
        filename = f"stat_{safe_name}_{timestamp}.pdf"
        dest_path = os.path.join(folder, filename)
        _pdf_reportlab_stat(person_name, stats, total_fois, total_montant, dest_path)

    elif renderer == "fpdf":
        filename = f"stat_{safe_name}_{timestamp}.pdf"
        dest_path = os.path.join(folder, filename)
        _pdf_fpdf_stat(person_name, stats, total_fois, total_montant, dest_path)

    else:
        raise ValueError(f"Moteur de rendu inconnu : {renderer!r}")

    return dest_path
