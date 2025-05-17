
from fpdf import FPDF
from io import BytesIO
# Export to Excel
def export_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# Export to PDF
def export_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    for i, row in df.iterrows():
        pdf.multi_cell(0, 10, f"{i+1}. {row['log']}\nSummary: {row['summary']}\nCategory: {row['category']}\n", border=1)
    
    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin-1')  # Get PDF as bytes
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output
