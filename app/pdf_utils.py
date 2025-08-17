from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Define the PDF output directory
PDF_OUTPUT_DIR = "C:\\Users\\Aditya\\Desktop\\pdf reports"

def ensure_output_dir():
    """Ensure the PDF output directory exists."""
    if not os.path.exists(PDF_OUTPUT_DIR):
        os.makedirs(PDF_OUTPUT_DIR)
        logger.info(f"Created PDF output directory at {PDF_OUTPUT_DIR}")

def generate_unique_filename(patient_name):
    """Generate a unique filename for the PDF."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Clean patient name to be filesystem safe
    safe_name = "".join(c for c in patient_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    return f"lab_report_{safe_name}_{timestamp}.pdf"

def create_lab_report_pdf(data, patient_name, output_path=None):
    """
    Create a PDF report of lab test results.
    
    Args:
        data (list): List of test results
        patient_name (str): Name of the patient
        output_path (str, optional): Path where to save the PDF. If not provided,
                                   a unique filename will be generated in the default directory.
    
    Returns:
        str: Path to the generated PDF
    """
    try:
        # Ensure output directory exists
        ensure_output_dir()
        
        # If no output path is provided, generate one
        if not output_path:
            filename = generate_unique_filename(patient_name)
            output_path = os.path.join(PDF_OUTPUT_DIR, filename)
        else:
            # If output_path is provided, ensure it's in the PDF_OUTPUT_DIR
            filename = os.path.basename(output_path)
            output_path = os.path.join(PDF_OUTPUT_DIR, filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        elements.append(Paragraph(f"Laboratory Test Results - {patient_name}", title_style))
        elements.append(Spacer(1, 12))
        
        # Prepare table data
        table_data = [['Test Name', 'Value', 'Reference Range', 'Unit', 'Status']]
        
        for test in data:
            status = "OUT OF RANGE" if test.get("lab_test_out_of_range") else "NORMAL"
            row = [
                test.get("test_name", ""),
                test.get("test_value", ""),
                test.get("bio_reference_range", ""),
                test.get("test_unit", ""),
                status
            ]
            table_data.append(row)
        
        # Create table
        table = Table(table_data, colWidths=[2*inch, inch, 1.5*inch, inch, 1.2*inch])
        
        # Add style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        # Add conditional formatting for out-of-range values
        for row_num, row in enumerate(table_data[1:], start=1):
            if row[-1] == "OUT OF RANGE":
                style.add('TEXTCOLOR', (1, row_num), (1, row_num), colors.red)
                style.add('TEXTCOLOR', (-1, row_num), (-1, row_num), colors.red)
        
        table.setStyle(style)
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        logger.info(f"PDF report generated successfully at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise
