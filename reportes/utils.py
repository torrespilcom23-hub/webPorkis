import re
import unicodedata
from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AUTOR_REPORTE = 'Granja Porkis'


def _nombre_archivo(titulo, extension):
    normalizado = unicodedata.normalize('NFKD', titulo)
    ascii_text = normalizado.encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', ascii_text).strip('_').lower()
    return f'{slug or "reporte"}.{extension}'


def exportar_pdf(titulo, encabezados, filas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        title=titulo,
        author=AUTOR_REPORTE,
        subject=titulo,
    )
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(titulo, styles['Title']))
    elements.append(Spacer(1, 12))

    if filas:
        data = [encabezados] + filas
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D5016')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph('Sin datos con los filtros aplicados.', styles['Normal']))

    def _marcar_pdf(canvas, _doc):
        canvas.setTitle(titulo)
        canvas.setAuthor(AUTOR_REPORTE)
        canvas.setSubject(titulo)

    doc.build(elements, onFirstPage=_marcar_pdf, onLaterPages=_marcar_pdf)
    buffer.seek(0)
    nombre = _nombre_archivo(titulo, 'pdf')
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre}"'
    return response


def exportar_excel(titulo, encabezados, filas):
    wb = Workbook()
    ws = wb.active
    ws.title = titulo[:31]
    ws.append(encabezados)
    for fila in filas:
        ws.append(fila)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    nombre = _nombre_archivo(titulo, 'xlsx')
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return response