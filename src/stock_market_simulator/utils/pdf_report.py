import os
import glob
from fpdf import FPDF


def create_pdf_report(out_dir):
    """Generate a PDF summary inside *out_dir*.

    The function reads ``config.txt`` and ``report.txt`` from the directory and
    appends all ``*.png`` plots. The resulting file is saved as ``report.pdf``.
    """
    config_path = os.path.join(out_dir, "config.txt")
    report_path = os.path.join(out_dir, "report.txt")
    pdf_path = os.path.join(out_dir, "report.pdf")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    if os.path.exists(config_path):
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        with open(config_path, "r") as cfg:
            for line in cfg:
                pdf.multi_cell(0, 10, line.rstrip())

    if os.path.exists(report_path):
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        with open(report_path, "r") as rep:
            for line in rep:
                pdf.multi_cell(0, 10, line.rstrip())

    for img_path in sorted(glob.glob(os.path.join(out_dir, "*.png"))):
        pdf.add_page()
        # Leave a small margin around the image
        pdf.image(img_path, x=10, y=10, w=pdf.w - 20)

    pdf.output(pdf_path)
    return pdf_path
