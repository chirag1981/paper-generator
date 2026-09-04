# ExamPaperAI – Multilingual Exam Paper Digitizer & Document Builder

> **Short Description**: AI-powered multilingual exam paper digitizer, OCR scanner, and document builder for Gujarati, Hindi, and English with dynamic multi-column options layout, Microsoft Word (`.docx`), and PDF exports.

An interactive, modern Flask web application designed for educators, schools, and publishers to upload photos or multi-page PDFs of handwritten exam drafts, math question papers, and worksheets in **Gujarati (ગુજરાતી), Hindi (हिन्दी), and English**. Edit questions in a split-screen live workspace, convert languages seamlessly, configure custom question option layouts, and export publication-ready Microsoft Word (`.docx`) and high-resolution PDF documents.

---

## ✨ Key Features

- **Multilingual Handwriting OCR (Gemini Vision AI via `google-genai`)**:
  - Scans single/multi-page image scans (`.png`, `.jpg`, `.jpeg`) and multi-page PDF documents.
  - Recognizes Gujarati (ગુજરાતી), Hindi (हिन्दी), and English handwriting with complex Indic typography.
  - Automatically structures sections, marks, question types, MCQ options, fill-in-the-blanks, tables, and math equations.
- **Dynamic Option Layouts (Horizontal, 2-Column Side-by-Side, Vertical Stacked)**:
  - Configure how multiple-choice options are presented:
    - **Horizontal (1 Row)**: Space-saving single-line display `(A) ... (B) ... (C) ... (D) ...`
    - **2 Columns (Side-by-Side)**: Balanced two-column grid `(A) ... (B) ... / (C) ... (D) ...`
    - **Vertical (Stacked)**: Classic one-per-line list for lengthier answer options.
  - Layouts are honored synchronously across the Live Interactive Editor, Printable Preview, Word (`.docx`), and PDF outputs.
- **1-Click Automatic Language Conversion**:
  - Instantly translate exam papers between **English ↔ Gujarati ↔ Hindi** with full preservation of formatting, numbers, sub-parts, and blanks.
- **Split-Screen Interactive Workspace**:
  - **Left Pane**: Zoomable, panable image viewer for inspecting original handwriting.
  - **Right Pane**: Structured, editable question cards with live state synchronization.
- **Customizable Assessment Grid**:
  - Optional student assessment table (`Question No. | 1 | 2 | 3 | Total | Marks Obtained`) with 1-click toggle to include or remove as needed.
- **Print-Ready Indic Document Engine**:
  - **Microsoft Word (`.docx`)**: Clean, standardized typography using `Nirmala UI` (12pt), consistent paragraph spacing, right-aligned section marks, custom school headers, and table styling.
  - **High-Resolution PDF Generation**: Dual-engine support via local Microsoft Word COM automation with automatic process cleanup, falling back to cross-platform headless LibreOffice.
- **Embedded Diagram & Geometry Generator**:
  - Line transversal diagrams, polyline graphs (`L-M-P-Q-R`), ray intersections, and pictographs.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.11+**
- (Optional for PDF generation) **Microsoft Word** on Windows or **LibreOffice** (`soffice`)
- (Optional for PDF upload conversion) **Poppler** (`pdftoppm`)

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/chirag1981/paper-generator.git
cd paper-generator
pip install -r requirements.txt
```

### 3. Environment Setup
Copy the `.env.example` file to `.env`:
```bash
copy .env.example .env
```

Set your Gemini API Key in `.env` (or configure it dynamically via the **"AI Key"** modal in the web app):
```env
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_SECRET_KEY=your_random_secret_key
FLASK_ENV=development
```

### 4. Run the Application
```bash
python run.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## 📁 Project Structure

```
paper-generator/
├── app/
│   ├── config.py                 # Hierarchical environment configurations
│   ├── routes/
│   │   ├── main.py               # Blueprint for web pages (Upload, Editor, Preview)
│   │   └── api.py                # REST API (Upload, OCR, Translation & Export endpoints)
│   ├── services/
│   │   ├── docx_generator.py     # Microsoft Word builder with Indic font & layout engines
│   │   ├── pdf_generator.py      # PDF conversion engine (Word COM + LibreOffice fallback)
│   │   ├── geometry_drawer.py    # Diagram & Pictograph generator
│   │   ├── ocr_service.py        # Gemini Multimodal OCR scanner (google-genai SDK)
│   │   └── translation_service.py# English ↔ Gujarati ↔ Hindi translation pipeline
│   └── utils.py                  # Normalization, sanitization & CSV helpers
├── templates/
│   ├── base.html                 # Core layout with modern styling
│   ├── index.html                # Drag-and-drop file uploader with PDF & multi-image support
│   ├── editor.html               # Dual-pane workspace with live layout controls & OCR tools
│   └── preview.html              # Synchronous printable preview with direct export
├── static/
│   ├── css/                      # tokens.css & main.css design system
│   └── js/                       # uploader.js, editor.js, viewer.js
├── uploads/                      # Uploaded source images & temporary PDF pages
├── exports/                      # Generated DOCX and PDF files
├── .env.example                  # Environment variable reference
├── .gitignore                    # Version control exclusion rules
├── requirements.txt              # Production dependencies
└── run.py                        # Application entry point
```

---

## 📄 License
This project is licensed under the MIT License.
