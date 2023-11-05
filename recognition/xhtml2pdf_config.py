from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from xhtml2pdf import pisa
from django.conf import settings
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def configure_fonts():
    font_path = f"{settings.BASE_DIR}/NotoSansSC-VariableFont_wght.ttf"
    pdfmetrics.registerFont(TTFont('NotoSansSC-VariableFont_wght', font_path))
    pisa.registerFont(TTFont('NotoSansSC-VariableFont_wght', font_path))


configure_fonts()
