# ExamPaperAI – Comprehensive Business Logic, Rules & Architecture Specifications

This document is the single source of truth for all business logic, design rules, data schemas, auto-healing heuristics, layout engines, and document formatting constraints implemented across **ExamPaperAI**.

---

## 1. Core Architecture & System Overview

ExamPaperAI transforms raw handwritten or printed exam question papers (in English, Gujarati, or Hindi) into high-fidelity editable structures, pixel-perfect printable web previews, and professionally formatted Microsoft Word (`.docx`) and PDF documents.

### Key Technology Stack:
- **Backend**: Python 3.11+ / Flask application with modular blueprint architecture (`routes/api.py`, `routes/main.py`).
- **AI Vision OCR**: Google Gemini Vision API via Multimodal GenAI SDK (`gemini-3.8-flash`, `gemini-3.6-flash`, etc.).
- **DOCX Compilation**: `python-docx` coupled with native Office Math Markup Language (OMML) for stacked fractions.
- **PDF Generation**: Native Microsoft Word COM automation (`docx2pdf`) with cross-platform fallback (`libreoffice`).
- **Frontend Workspace**: Dual-pane editor with an HTML5 pan-and-zoom inspection viewer (`viewer.js`), live reactive form cards (`editor.js`), and synchronous A4 print engine (`preview.html`).

---

## 2. Examination Paper Schema Specification

Every exam paper is stored and manipulated as a JSON object adhering to this canonical structure:

```json
{
  "metadata": {
    "exam_title": "1st Semester Examination – 2026",
    "standard": "Std. 6th",
    "subject": "Mathematics",
    "total_marks": "60",
    "time_limit": "2 Hours",
    "date": "",
    "day": "",
    "roll_no": ""
  },
  "sections": [
    {
      "id": "sec_1a",
      "title": "Q-1 (A) Choose the correct answer",
      "marks": "(5)",
      "type": "mcq | fill_in_blanks | true_false | general | table",
      "options_box": "[ optional bracketed word bank ]",
      "drawing_boxes": ["(1) 40°", "(2) 75°"],
      "page_break_before": false,
      "intro_text": "In the given figure name the following:",
      "diagram_type": "zigzag | geometry_lines | pictograph | clock_blank | clock | cylinder | pyramid | sphere | circle | cone | cube",
      "diagram_layout": "side_by_side | stacked",
      "options_layout": "vertical | two_columns | horizontal",
      "subquestions_layout": "vertical | two_columns | horizontal",
      "table_data": {
        "headers": ["S.No", "Item", "CP (₹)", "SP (₹)", "Profit", "Loss"],
        "rows": [["A", "Ice-cream", "5", "10", "", ""]]
      },
      "questions": [
        {
          "text": "1) 3/4 + 7/4 = ______",
          "options": ["(a) 10/4", "(b) 10/8", "(c) 2/6", "(d) 10/6"],
          "diagram_type": "zigzag | geometry_lines | pictograph | clock_blank | clock | cylinder | pyramid | sphere | circle | cone | cube",
          "options_layout": "vertical | two_columns | horizontal",
          "is_bold": true,
          "answer_lines": 2,
          "answer_prefix": "Ans: ",
          "supercell_cells": ["6828", "670", "9435"]
        }
      ]
    }
  ],
  "custom_marks_table": []
}
```

---

## 3. Layout Hierarchy & Layout Rules

ExamPaperAI supports three primary option/sub-question layouts:
1. **Vertical (Stacked - 1 per line)**:
   - **Default layout throughout the application**.
   - Each answer option `(a)`, `(b)`, `(c)`, `(d)` or sub-question is rendered on its own line with 0.4-inch indentation.
   - Ideal for lengthier options, fractions, formulas, and complex expressions.
2. **2 Columns (Side-by-Side / 2x2 Grid)**:
   - Options are split evenly across 2 columns: column 1 contains `(a)` & `(c)`, column 2 contains `(b)` & `(d)`.
3. **Horizontal (1 Row - Side-by-side across page)**:
   - Options are laid out side-by-side across the entire width of the page in equal fractions (e.g. 4 columns for 4 choices).

### Layout Inheritance & Resolution Precedence:
```
Question 'options_layout' (if set)
  └── Section 'options_layout' / 'subquestions_layout' (if set)
        └── System Default: 'vertical' (Stacked - 1 per line)
```

---

## 4. OCR Ingestion & Auto-Healing Rules (`ocr_service.py`)

When handwritten or printed exam papers are scanned via Google Gemini Vision, the raw extracted content is automatically sanitized and normalized through `sanitize_and_fix_paper_diagrams()`:

### Rule 4.1: Fallback Model Cascade
- Tries models in descending order: `gemini-3.8-flash` $\rightarrow$ `gemini-3.6-flash` $\rightarrow$ `gemini-3.7-flash` $\rightarrow$ `gemini-flash-latest`.
- If no Gemini API key is configured or all requests fail, gracefully serves the pre-loaded 60-mark Class 6 Mathematics exam paper structure.

### Rule 4.2: Figure & Diagram Promotion (No Text Placeholders)
- **Zigzag Line Figures**: If student questions reference points `L, M, P, Q, R` or marked points on a polyline, assigns `diagram_type: "zigzag"` and renders the vector diagram.
- **Geometry Lines & Rays**: If questions reference intersecting lines `G-A-C-E`, ray `AB`, line `FD`, or points `O, C, A, F, B, D`, assigns `diagram_type: "geometry_lines"`.
- **Pictographs**: If text references girl students or pictographs, assigns `diagram_type: "pictograph"`.
- **Geometric Shapes**: Replaces placeholders like `[Cylinder shape]`, `[Pyramid shape]`, `[Circle/Sphere shape]`, `[Cone]`, `[Cube]` with proper shape types (`cylinder`, `pyramid`, `sphere`, `circle`, `cone`, `cube`) and generates clean blank answer lines (`(1) = _________________________`).

### Rule 4.3: Clock and Time Questions
- Detects analog clock questions ("Draw hands to show correct times", "quarter to 2", etc.).
- Converts misplaced descriptive drawing boxes into questions with `diagram_type: "clock_blank"`.
- Sets `subquestions_layout: "horizontal"` specifically for clock sections so clock faces display side-by-side.

### Rule 4.4: Section Marks Auto-Healing
- If section marks are missing, blank, `0`, or `[0]`, automatically sets marks equal to question count (e.g. `[5]`), preventing understated total marks.

### Rule 4.5: Answer Prefix Cleanup
- Automatically strips boilerplate prefixes like `"Ans:"`, `"Ans."`, `"Answer:"` from questions to keep clean layout.

### Rule 4.6: Default Layout Assignment
- Every generated section is automatically assigned `options_layout: "vertical"` and `subquestions_layout: "vertical"` unless explicitly set or detected as a clock section.

---

## 5. Document Compilation Rules (`docx_generator.py`)

### Rule 5.1: Typography & Font Standards
- Primary Font: **Nirmala UI** across all headings, questions, tables, and runs.
- Guarantees flawless Unicode rendering for Indic scripts (Gujarati and Devanagari/Hindi) without font substitution or glyph clipping.
- Body Font Size: **11.0 pt**; Section Title Size: **12.5 pt**; Exam Header Size: **15.0 pt**.
- Line spacing: **1.15x** (`DOCX_LINE_SPACING`).

### Rule 5.2: Stacked Vertical Fractions via Word OMML
- Text containing fractions matching `\b\d+/\d+\b` (e.g. `3/4`, `7/4`, `5071/1000`) is parsed into Word Office Math Markup Language (`w:oMath` with `<m:f>` fraction elements).
- Rendered as true typographic vertical stacked fractions rather than linear slash characters.

### Rule 5.3: Table & Layout Pagination Guardrails
- All layout tables are configured with `prevent_row_split(table)` (`w:cantSplit`) so questions or options never get sliced across page breaks.
- Multi-row tables include `w:tblHeader` on the first row to repeat header rows if spanning pages.
- Zero-border layout tables (`set_no_borders()`) are used for side-by-side sections and headers.

### Rule 5.4: MCQ Options Formatting
- **Vertical**: Each option rendered in its own paragraph with `0.4"` indent, `Pt(3)` spacing after, and `keep_with_next=True` on options to prevent orphan choices.
- **Two Columns**: Rendered as a 2-column borderless table with `Inches(3.6)` per column.
- **Horizontal**: Rendered as a single-row table with `N` columns distributed equally across `PAGE_CONTENT_WIDTH_INCHES` (7.2 inches).

---

## 6. Frontend State & Synchronization Rules (`editor.js`)

### Rule 6.1: Dual-Layer Persistence
- **Client Cache**: All changes sync immediately to browser `localStorage` (`current_paper`).
- **Server Cache**: On changes, state is sent asynchronously via `navigator.sendBeacon('/api/current-paper')` and cached to `uploads/last_paper.json`.
- When the user returns or refreshes the page, the most up-to-date state is restored automatically.

### Rule 6.2: Upload & Reset Isolation
- When new documents are uploaded via `/api/upload`, previous paper structures and cached questions are cleanly cleared to prevent questions from leaking across different exams.
- The `/api/reset` endpoint deletes temporary uploads from disk and clears session tokens.

### Rule 6.3: Live Math Fraction Rendering
- Real-time regex parser converts `(\d+)/(\d+)` into stacked HTML fraction blocks (`<span class="fraction"><span class="numerator">...</span><span class="denominator">...</span></span>`) in the live preview card.

---

## 7. Multilingual Translation Rules (`translation_service.py`)

- Translates between **English**, **Gujarati (ગુજરાતી)**, and **Hindi (हिन्दी)**.
- **Preserved Invariants**:
  - Formulas, mathematical fractions (`3/4`), numbers, currencies (`₹`), and equations.
  - Marks allocations (e.g. `(5)`, `[4]`, `Marks`).
  - Diagram types (`diagram_type`), layouts, table structures, and internal IDs.
  - Student drawing boxes and blank fill lines (`____________`).
- Uses targeted Gemini instructions with low temperature (0.1) to guarantee faithful translations without hallucinations.

---

## 8. Verification & Test Suite

The rules and logic are backed by automated unit tests in `tests/`:
- `tests/test_default_layout.py`:
  - Verifies that raw papers without layout directives default to `vertical` stacked in `sanitize_and_fix_paper_diagrams()` and `get_sample_std6_maths_paper()`.
  - Verifies that `.docx` compilation renders MCQ options as stacked paragraphs rather than horizontal tables.
- `tests/test_shape_export.py`:
  - Verifies that 2D/3D shape diagrams (`cylinder`, `pyramid`, `circle`) are converted into embedded document graphics and formatted tables.
