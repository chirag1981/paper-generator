import os
import json
import time
from flask import Blueprint, request, jsonify, current_app, send_from_directory, session
from werkzeug.utils import secure_filename
from app.utils import allowed_file, get_safe_filename, sanitize_uppercase, get_active_gemini_api_key, convert_pdf_to_images
from app.services.ocr_service import get_sample_std6_maths_paper, extract_paper_from_images
from app.services.translation_service import translate_paper_structure, LANGUAGE_NAMES
from app.services.docx_generator import build_docx_paper
from app.services.pdf_generator import convert_docx_to_pdf

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/upload', methods=['POST'])
def upload_images():
    """Handles multi-image and PDF document uploads from the dropzone."""
    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    files = request.files.getlist('files') or [request.files['file']]
    uploaded_files = []
    allowed_exts = current_app.config['ALLOWED_EXTENSIONS']
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    for f in files:
        if f and allowed_file(f.filename, allowed_exts):
            safe_name = get_safe_filename(f.filename)
            target_path = os.path.join(upload_dir, safe_name)
            f.save(target_path)

            ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
            if ext == 'pdf':
                try:
                    pdf_base = safe_name.rsplit('.', 1)[0]
                    page_images = convert_pdf_to_images(
                        pdf_path=target_path,
                        output_dir=upload_dir,
                        base_prefix=pdf_base,
                        original_filename=f.filename
                    )
                    uploaded_files.extend(page_images)
                except Exception as e:
                    return jsonify({'success': False, 'error': f'Failed to process PDF document: {str(e)}'}), 400
            else:
                uploaded_files.append({
                    'filename': safe_name,
                    'original_name': f.filename,
                    'url': f'/uploads/{safe_name}'
                })

    if not uploaded_files:
        return jsonify({'success': False, 'error': 'No valid image or PDF files found'}), 400

    return jsonify({
        'success': True,
        'message': f'Successfully uploaded and processed {len(uploaded_files)} page(s)',
        'files': uploaded_files
    })


@api_bp.route('/scan-ocr', methods=['POST'])
def scan_ocr():
    """Extracts structured questions from uploaded images using Multilingual Gemini OCR."""
    try:
        req_data = request.get_json() or {}
        filenames = req_data.get('filenames', [])
        language_hint = req_data.get('language', 'auto')
        custom_key = req_data.get('api_key') or get_active_gemini_api_key()

        if not custom_key:
            return jsonify({
                'success': False,
                'error': 'Gemini API Key not found. Please click the "🔑 AI Key" button in the toolbar to enter your Google Gemini API key or save GEMINI_API_KEY in .env.'
            }), 400

        upload_dir = current_app.config['UPLOAD_FOLDER']
        
        # If no specific files passed, look for all available images in upload folder
        if not filenames:
            filenames = [f for f in os.listdir(upload_dir) if allowed_file(f, current_app.config['ALLOWED_EXTENSIONS'])]

        if not filenames:
            return jsonify({'success': False, 'error': 'No images uploaded to scan'}), 400

        image_paths = [os.path.join(upload_dir, f) for f in filenames if os.path.exists(os.path.join(upload_dir, f))]
        
        if not image_paths:
            return jsonify({'success': False, 'error': 'Image files not found on server'}), 404

        extracted_paper = extract_paper_from_images(
            image_paths=image_paths,
            language_hint=language_hint,
            api_key=custom_key
        )

        return jsonify({
            'success': True,
            'paper': extracted_paper,
            'message': f'Successfully digitized {len(image_paths)} page(s) with AI OCR!'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/translate-paper', methods=['POST'])
def translate_paper():
    """Translates paper structure between English, Gujarati, and Hindi."""
    try:
        req_data = request.get_json() or {}
        paper = req_data.get('paper')
        target_lang = req_data.get('target_lang', 'gu')
        custom_key = req_data.get('api_key') or get_active_gemini_api_key()

        if not paper:
            return jsonify({'success': False, 'error': 'Paper data is required for translation'}), 400

        translated = translate_paper_structure(
            paper_data=paper,
            target_lang=target_lang,
            api_key=custom_key
        )

        lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        return jsonify({
            'success': True,
            'paper': translated,
            'target_lang': target_lang,
            'message': f'Paper successfully converted to {lang_name}!'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/config-status', methods=['GET'])
def get_config_status():
    """Returns AI configuration status (e.g. if API key is active)."""
    key = get_active_gemini_api_key()
    return jsonify({
        'success': True,
        'has_gemini_key': bool(key)
    })


@api_bp.route('/save-api-key', methods=['POST'])
def save_api_key():
    """Saves Gemini API key to active session and runtime config."""
    try:
        req_data = request.get_json() or {}
        key = req_data.get('api_key', '').strip()
        if not key:
            return jsonify({'success': False, 'error': 'API key cannot be empty'}), 400

        session['gemini_api_key'] = key
        current_app.config['GEMINI_API_KEY'] = key
        os.environ['GEMINI_API_KEY'] = key

        return jsonify({
            'success': True,
            'message': 'Gemini API Key saved successfully!'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/sample-paper', methods=['GET'])
def get_sample_paper():
    """Returns the default preloaded 6th Grade Maths 1st Semester exam structure."""
    data = get_sample_std6_maths_paper()
    return jsonify({'success': True, 'paper': data})


@api_bp.route('/download-direct/<file_type>', methods=['GET'])
def download_direct(file_type):
    """Direct one-click GET download for default Std 6 Maths exam paper."""
    export_dir = current_app.config['EXPORT_FOLDER']
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(export_dir, exist_ok=True)
    paper_data = get_sample_std6_maths_paper()
    
    if file_type == 'pdf':
        docx_path = os.path.join(export_dir, 'Std_6_Maths_1st_Semester_Exam.docx')
        pdf_path = os.path.join(export_dir, 'Std_6_Maths_1st_Semester_Exam.pdf')
        try:
            convert_docx_to_pdf(docx_path, pdf_path)
        except Exception as err:
            current_app.logger.warning(f"Sample PDF conversion error: {err}")
        if os.path.exists(pdf_path):
            return send_from_directory(export_dir, 'Std_6_Maths_1st_Semester_Exam.pdf', as_attachment=True)
        return send_from_directory(export_dir, 'Std_6_Maths_1st_Semester_Exam.docx', as_attachment=True)
    else:
        docx_path = os.path.join(export_dir, 'Std_6_Maths_1st_Semester_Exam.docx')
        build_docx_paper(paper_data, docx_path, temp_dir=upload_dir)
        return send_from_directory(export_dir, 'Std_6_Maths_1st_Semester_Exam.docx', as_attachment=True)


@api_bp.route('/generate-docx', methods=['POST'])
def generate_docx():
    """Builds a formatted Word document (.docx) from current paper JSON."""
    try:
        req_data = request.get_json()
        if not req_data or 'paper' not in req_data:
            return jsonify({'success': False, 'error': 'Invalid request payload'}), 400

        paper_data = req_data['paper']
        export_dir = current_app.config['EXPORT_FOLDER']
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(export_dir, exist_ok=True)

        meta = paper_data.get('metadata', {})
        std = secure_filename(meta.get('standard', 'Std6')).replace(' ', '_') or 'Std6'
        sub = secure_filename(meta.get('subject', 'Maths')).replace(' ', '_') or 'Paper'
        filename = f"{std}_{sub}_Exam_{int(time.time())}.docx"
        out_path = os.path.join(export_dir, filename)

        build_docx_paper(paper_data, out_path, temp_dir=upload_dir)

        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/exports/{filename}',
            'message': 'Word document generated successfully!'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """Builds a formatted Word document and converts it to PDF."""
    try:
        req_data = request.get_json()
        if not req_data or 'paper' not in req_data:
            return jsonify({'success': False, 'error': 'Invalid request payload'}), 400

        paper_data = req_data['paper']
        export_dir = current_app.config['EXPORT_FOLDER']
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(export_dir, exist_ok=True)

        meta = paper_data.get('metadata', {})
        std = secure_filename(meta.get('standard', 'Std6')).replace(' ', '_') or 'Std6'
        sub = secure_filename(meta.get('subject', 'Maths')).replace(' ', '_') or 'Paper'
        ts = int(time.time())
        docx_filename = f"{std}_{sub}_Exam_{ts}.docx"
        pdf_filename = f"{std}_{sub}_Exam_{ts}.pdf"
        
        docx_path = os.path.join(export_dir, docx_filename)
        pdf_path = os.path.join(export_dir, pdf_filename)

        build_docx_paper(paper_data, docx_path, temp_dir=upload_dir)
        convert_docx_to_pdf(docx_path, pdf_path)

        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            return jsonify({
                'success': True,
                'filename': pdf_filename,
                'download_url': f'/exports/{pdf_filename}',
                'docx_url': f'/exports/{docx_filename}',
                'message': 'PDF generated successfully!'
            })
        else:
            return jsonify({
                'success': True,
                'filename': docx_filename,
                'download_url': f'/exports/{docx_filename}',
                'message': 'Generated DOCX'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
