import os
from flask import Blueprint, render_template, current_app, send_from_directory, abort

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/editor')
def editor():
    return render_template('editor.html')

@main_bp.route('/preview')
def preview():
    return render_template('preview.html')

@main_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
    upload_dir = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_dir, filename)

@main_bp.route('/exports/<path:filename>')
def serve_export(filename):
    export_dir = current_app.config['EXPORT_FOLDER']
    response = send_from_directory(export_dir, filename, as_attachment=True)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
