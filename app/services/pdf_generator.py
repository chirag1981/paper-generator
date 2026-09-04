import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)

def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> str:
    """
    Converts a DOCX file to PDF using Microsoft Word COM on Windows, or LibreOffice (soffice) as cross-platform fallback.
    Raises FileNotFoundError or RuntimeError on failure.
    """
    docx_path = os.path.abspath(docx_path)
    pdf_path = os.path.abspath(pdf_path)
    out_dir = os.path.dirname(pdf_path) or '.'
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Input DOCX file not found: {docx_path}")

    # 1. Attempt Word COM Automation on Windows
    if sys.platform == 'win32':
        if _convert_via_word_com(docx_path, pdf_path):
            return pdf_path
        logger.info("Word COM conversion failed or unavailable; attempting LibreOffice (soffice) fallback.")

    # 2. Cross-platform / fallback conversion via LibreOffice (soffice)
    _convert_via_soffice(docx_path, out_dir)
    
    # LibreOffice saves as <base_name>.pdf in out_dir
    base_name = os.path.splitext(os.path.basename(docx_path))[0]
    produced_pdf = os.path.join(out_dir, f"{base_name}.pdf")
    
    if os.path.exists(produced_pdf) and produced_pdf != pdf_path:
        try:
            os.replace(produced_pdf, pdf_path)
        except Exception as e:
            logger.warning(f"Failed to rename produced PDF from {produced_pdf} to {pdf_path}: {e}")
            if os.path.exists(produced_pdf) and not os.path.exists(pdf_path):
                pdf_path = produced_pdf

    if not (os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0):
        raise RuntimeError(f"PDF conversion failed: output file '{pdf_path}' was not created or is empty.")

    return pdf_path


def _convert_via_word_com(docx_path: str, pdf_path: str) -> bool:
    """Converts DOCX to PDF using Word COM automation with strict resource cleanup."""
    word = None
    doc = None
    pythoncom = None
    try:
        import win32com.client
        import pythoncom
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        word.DisplayAlerts = False
        doc = word.Documents.Open(docx_path)
        doc.SaveAs(pdf_path, FileFormat=17)  # 17 = wdFormatPDF
        return os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0
    except Exception as e:
        logger.warning(f"Word COM conversion encountered an error: {e}")
        return False
    finally:
        if doc is not None:
            try:
                doc.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        if pythoncom is not None:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass


def _convert_via_soffice(docx_path: str, out_dir: str):
    """Converts DOCX to PDF using headless LibreOffice."""
    soffice_cmd = 'soffice'
    if sys.platform == 'win32':
        import shutil
        if not shutil.which('soffice'):
            for candidate in [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
            ]:
                if os.path.exists(candidate):
                    soffice_cmd = candidate
                    break

    try:
        subprocess.run(
            [soffice_cmd, '--headless', '--convert-to', 'pdf', '--outdir', out_dir, docx_path],
            check=True,
            timeout=120,
            capture_output=True
        )
    except FileNotFoundError:
        logger.error("LibreOffice ('soffice') executable is not installed or not found on PATH.")
        raise
    except Exception as e:
        logger.exception(f"Exception during soffice headless execution: {e}")
        raise
