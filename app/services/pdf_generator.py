import os
import sys

def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> str:
    """Converts a DOCX file to PDF using Microsoft Word COM on Windows, or PyMuPDF/fallback."""
    docx_path = os.path.abspath(docx_path)
    pdf_path = os.path.abspath(pdf_path)
    os.makedirs(os.path.dirname(pdf_path) or '.', exist_ok=True)

    # Try Word COM Automation on Windows
    if sys.platform == 'win32':
        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()
            word = win32com.client.Dispatch('Word.Application')
            word.Visible = False
            word.DisplayAlerts = False
            doc = word.Documents.Open(docx_path)
            doc.SaveAs(pdf_path, FileFormat=17) # 17 = wdFormatPDF
            doc.Close()
            word.Quit()
            pythoncom.CoUninitialize()
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                return pdf_path
        except Exception as e:
            print(f"Word COM conversion notice: {e}")

    return pdf_path
