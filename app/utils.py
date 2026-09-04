import os
import re
from werkzeug.utils import secure_filename

def sanitize_uppercase(text: str) -> str:
    """Normalizes identifiers, subject titles, standard codes to clean uppercase."""
    if not text:
        return ""
    return str(text).strip().upper()

def sanitize_csv_cell(value: str) -> str:
    """Neutralize formula injection characters (=, +, -, @) for safety."""
    if not value:
        return ""
    s = str(value).strip()
    if s.startswith(('=', '+', '-', '@')):
        return "'" + s
    return s

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if the uploaded file extension is in the allowed set."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_safe_filename(filename: str) -> str:
    """Generate a clean safe filename with timestamp prefix."""
    import time
    clean_name = secure_filename(filename)
    timestamp = int(time.time() * 1000)
    return f"{timestamp}_{clean_name}"

def get_active_gemini_api_key() -> str:
    """
    Retrieves the active Gemini API key from session, current_app config, 
    system environment, or reloads fresh directly from the .env file.
    """
    from pathlib import Path
    from dotenv import load_dotenv

    # 1. Check Flask session if in request context
    try:
        from flask import session
        if session.get('gemini_api_key'):
            return session['gemini_api_key'].strip()
    except Exception:
        pass

    # 2. Always reload fresh from .env file so changes take effect immediately
    try:
        base_dir = Path(__file__).resolve().parent.parent
        env_path = base_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=True)
    except Exception:
        pass

    # 3. Check environment
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    if key:
        return key

    # 4. Check Flask config
    try:
        from flask import current_app
        key = current_app.config.get('GEMINI_API_KEY', '').strip()
        if key:
            return key
    except Exception:
        pass

    return ""


def convert_pdf_to_images(pdf_path: str, output_dir: str, base_prefix: str, original_filename: str = "") -> list:
    """
    Converts each page of a PDF document into a high-resolution PNG image (200 DPI).
    Returns a list of dicts: [{'filename': ..., 'original_name': ..., 'url': ...}]
    """
    import fitz
    page_files = []
    doc = fitz.open(pdf_path)
    try:
        if doc.is_encrypted:
            raise ValueError("The uploaded PDF is password-protected. Please upload an unencrypted PDF file.")

        total_pages = len(doc)
        if total_pages == 0:
            raise ValueError("The uploaded PDF document contains no pages.")

        orig_base = original_filename or os.path.basename(pdf_path)

        for page_idx in range(total_pages):
            page = doc[page_idx]
            # 200 DPI provides crisp text, math formulas, and geometry drawings
            pix = page.get_pixmap(dpi=200)
            img_filename = f"{base_prefix}_page_{page_idx + 1}.png"
            img_target_path = os.path.join(output_dir, img_filename)
            pix.save(img_target_path)

            page_files.append({
                'filename': img_filename,
                'original_name': f"{orig_base} (Page {page_idx + 1})",
                'url': f"/uploads/{img_filename}"
            })
    finally:
        doc.close()

    return page_files
