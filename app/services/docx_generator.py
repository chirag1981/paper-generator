import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from app.services.geometry_drawer import generate_zigzag_diagram, generate_lines_rays_diagram, generate_pictograph_chart

import re

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=35, bottom=35, left=60, right=60):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color='cbd5e1', sz='4', val='single'):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def set_all_cell_borders(table, color='000000', sz='4', val='single'):
    """Sets complete box borders (including left and right outer borders) for grid tables."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

# Project Standard Word Document Font Sizes
DOCX_HEADING_FONT_SIZE = Pt(12)
DOCX_BODY_FONT_SIZE = Pt(12)

def create_omml_fraction(num: str, den: str, font_name: str = 'Cambria Math', is_bold: bool = False, font_size = DOCX_BODY_FONT_SIZE) -> str:
    """Generates an XML snippet for a native Microsoft Word stacked vertical fraction with font size scaling."""
    bold_xml = '<w:b/>' if is_bold else ''
    sz_pt = font_size.pt if hasattr(font_size, 'pt') else 12
    sz_val = int(sz_pt * 2)
    sz_xml = f'<w:sz w:val="{sz_val}"/><w:szCs w:val="{sz_val}"/>'
    return (
        f'<m:oMath {nsdecls("m")} {nsdecls("w")}>'
        f'<m:f>'
        f'<m:fPr><m:type m:val="bar"/></m:fPr>'
        f'<m:num><m:r><w:rPr>{bold_xml}{sz_xml}<w:rFonts w:ascii="{font_name}" w:hAnsi="{font_name}"/></w:rPr><m:t>{num}</m:t></m:r></m:num>'
        f'<m:den><m:r><w:rPr>{bold_xml}{sz_xml}<w:rFonts w:ascii="{font_name}" w:hAnsi="{font_name}"/></w:rPr><m:t>{den}</m:t></m:r></m:den>'
        f'</m:f>'
        f'</m:oMath>'
    )

def add_formatted_math_text(paragraph, text: str, font_name: str = 'Nirmala UI', font_size = DOCX_BODY_FONT_SIZE, is_bold: bool = False, color: RGBColor = RGBColor(15, 23, 42)):
    """
    Parses text and inserts regular text runs and native Word OMML equations for stacked fractions.
    """
    if not text:
        return

    frac_pattern = re.compile(r'(\\frac\{([^}]+)\}\{([^}]+)\}|(?<![/\d])(\d+)/(\d+)(?![/\d]))')
    last_idx = 0

    for match in frac_pattern.finditer(text):
        start, end = match.span()
        if start > last_idx:
            prefix = text[last_idx:start]
            r = paragraph.add_run(prefix)
            set_run_font(r, font_name)
            r.font.size = font_size
            r.font.bold = is_bold
            r.font.color.rgb = color

        if match.group(1) and match.group(1).startswith('\\frac'):
            num, den = match.group(2), match.group(3)
        else:
            num, den = match.group(4), match.group(5)

        omml_xml = create_omml_fraction(num, den, font_name='Cambria Math', is_bold=is_bold, font_size=font_size)
        paragraph._p.append(parse_xml(omml_xml))
        last_idx = end

    if last_idx < len(text):
        suffix = text[last_idx:]
        r = paragraph.add_run(suffix)
        set_run_font(r, font_name)
        r.font.size = font_size
        r.font.bold = is_bold
        r.font.color.rgb = color

def extract_question_summary(paper_data: dict) -> tuple:
    """
    Extracts dynamic list of questions and their allocated marks:
    [{'name': 'Q-1', 'marks': 13}, {'name': 'Q-2', 'marks': 12}, ...]
    and computes the total marks.
    If custom_marks_table is defined in paper_data, uses it directly.
    """
    custom_table = paper_data.get('custom_marks_table')
    if isinstance(custom_table, list) and len(custom_table) > 0:
        q_list = []
        for item in custom_table:
            q_name = str(item.get('name', 'Q')).strip()
            try:
                q_marks = int(item.get('marks', 0))
            except (ValueError, TypeError):
                q_marks = 0
            q_list.append({'name': q_name, 'marks': q_marks})
        calc_total = sum(i['marks'] for i in q_list)
        return q_list, calc_total

    sections = paper_data.get('sections', [])
    if not sections:
        return ([{'name': 'Q-1', 'marks': 0}], 0)

    indic_to_eng = str.maketrans('૦૧૨૩૪૫૬૭૮૯०१२३४५६७८९', '01234567890123456789')
    q_dict = {}

    for idx, sec in enumerate(sections, 1):
        title = sec.get('title', '').strip()
        sec_id = str(sec.get('id', '')).lower()
        marks_str = str(sec.get('marks', '0')).translate(indic_to_eng)
        m_nums = re.findall(r'\d+', marks_str)
        marks_val = int(m_nums[0]) if m_nums else 0

        clean_title = title.translate(indic_to_eng)
        match = re.search(r'(?:Q|Que|Question|Sec|Section|પ્ર|પ્રશ્ન|प्रश्न)[\.\s\-:_]*(\d+)', clean_title, re.IGNORECASE)
        if match:
            q_key = f"Q-{match.group(1)}"
        else:
            lead_digit = re.search(r'^[\s\-:_]*(\d+)', clean_title)
            if lead_digit:
                q_key = f"Q-{lead_digit.group(1)}"
            else:
                id_match = re.search(r'(?:sec|q)[\-_]*(\d+)', sec_id)
                q_key = f"Q-{id_match.group(1)}" if id_match else f"Q-{idx}"

        if q_key not in q_dict:
            q_dict[q_key] = 0
        q_dict[q_key] += marks_val

    q_list = [{'name': k, 'marks': v} for k, v in q_dict.items()]
    if not q_list:
        q_list = [{'name': 'Q-1', 'marks': 18}, {'name': 'Q-2', 'marks': 17}, {'name': 'Q-3', 'marks': 25}]

    calc_total = sum(item['marks'] for item in q_list)
    meta_total = str(paper_data.get('metadata', {}).get('total_marks', '')).translate(indic_to_eng)
    meta_nums = re.findall(r'\d+', meta_total)
    total_val = int(meta_nums[0]) if meta_nums else calc_total

    return q_list, total_val

def set_run_font(run, font_name='Nirmala UI'):
    """Sets ASCII, High-ANSI, and Complex Script (Indic) fonts for clean rendering."""
    run.font.name = font_name
    rPr = run._r.get_or_add_rPr()
    rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="{font_name}" w:hAnsi="{font_name}" w:cs="{font_name}"/>')
    rPr.append(rFonts)

def build_docx_paper(paper_data: dict, output_path: str, temp_dir: str = None) -> str:
    """Builds an exact, beautifully formatted 4-page exam document with multilingual font support."""
    if not temp_dir:
        temp_dir = os.path.dirname(output_path) or '.'
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    doc = docx.Document()

    # Set default style font with Indic script fallback
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Nirmala UI'
    font.size = DOCX_BODY_FONT_SIZE
    font.color.rgb = RGBColor(15, 23, 42)

    # Set Margins
    for section in doc.sections:
        section.top_margin = Inches(0.4)
        section.bottom_margin = Inches(0.4)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)

    PRIMARY_COLOR = RGBColor(15, 23, 42)
    MUTED_COLOR = RGBColor(71, 85, 105)

    meta = paper_data.get('metadata', {})
    exam_title = (meta.get('exam_title') or 'Examination Paper').strip()
    standard = (meta.get('standard') or '').strip()
    subject = (meta.get('subject') or '').strip()
    total_marks = str(meta.get('total_marks') or '').strip()
    date_val = meta.get('date', '')
    day_val = meta.get('day', '')
    roll_no_val = meta.get('roll_no', '')

    # Extract dynamic question marks summary
    q_summary, calc_total = extract_question_summary(paper_data)
    if not total_marks and calc_total > 0:
        total_marks = str(calc_total)

    # ==================== HEADER ====================
    # 1. Exam Title (Centered, Bold)
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    run_title = title_p.add_run(exam_title)
    set_run_font(run_title, 'Nirmala UI')
    run_title.font.size = Pt(15)
    run_title.font.bold = True
    run_title.font.color.rgb = PRIMARY_COLOR

    # Add blue horizontal border below title
    pPr = title_p._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="8" w:space="4" w:color="0284c7"/></w:pBdr>')
    pPr.append(pBdr)

    # 2. Subject (Centered, Bold - Heading size 12)
    if subject:
        subj_p = doc.add_paragraph()
        subj_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subj_p.paragraph_format.space_before = Pt(3)
        subj_p.paragraph_format.space_after = Pt(1)
        prefix = 'Subject: ' if not any(subject.lower().startswith(p) for p in ['subject', 'વિષય', 'विषय']) else ''
        run_subj = subj_p.add_run(f'{prefix}{subject}')
        set_run_font(run_subj, 'Nirmala UI')
        run_subj.font.size = Pt(12)
        run_subj.font.bold = True
        run_subj.font.color.rgb = PRIMARY_COLOR

    # 3. Standard (Centered, Bold - Heading size 12)
    if standard:
        std_p = doc.add_paragraph()
        std_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        std_p.paragraph_format.space_before = Pt(0)
        std_p.paragraph_format.space_after = Pt(3)
        run_std = std_p.add_run(f'{standard}')
        set_run_font(run_std, 'Nirmala UI')
        run_std.font.size = Pt(12)
        run_std.font.bold = True
        run_std.font.color.rgb = PRIMARY_COLOR

    # 4. Date, Day (Left) & Marks, Roll No (Right)
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.LEFT
    meta_table.autofit = False
    meta_col_widths = [Inches(4.4), Inches(2.8)]
    for idx, col in enumerate(meta_table.columns):
        col.width = meta_col_widths[idx]
    for row in meta_table.rows:
        for idx, cell in enumerate(row.cells):
            cell.width = meta_col_widths[idx]
            set_cell_margins(cell, top=15, bottom=15, left=10, right=10)

    # Date / Marks
    m_r1c1 = meta_table.rows[0].cells[0].paragraphs[0]
    m_r1c1.paragraph_format.space_after = Pt(0)
    r = m_r1c1.add_run('Date: ')
    r.font.bold = True; r.font.size = DOCX_BODY_FONT_SIZE; set_run_font(r, 'Nirmala UI')
    r_d = m_r1c1.add_run(date_val if date_val else '____________')
    r_d.font.size = DOCX_BODY_FONT_SIZE; set_run_font(r_d, 'Nirmala UI')

    m_r1c2 = meta_table.rows[0].cells[1].paragraphs[0]
    m_r1c2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    m_r1c2.paragraph_format.space_after = Pt(0)
    r = m_r1c2.add_run('Marks: ')
    r.font.bold = True; r.font.size = DOCX_BODY_FONT_SIZE; set_run_font(r, 'Nirmala UI')
    r_m = m_r1c2.add_run(str(total_marks))
    r_m.font.bold = True; r_m.font.size = DOCX_BODY_FONT_SIZE; set_run_font(r_m, 'Nirmala UI')

    # Day / Roll No
    m_r2c1 = meta_table.rows[1].cells[0].paragraphs[0]
    m_r2c1.paragraph_format.space_after = Pt(0)
    r = m_r2c1.add_run('Day: ')
    r.font.bold = True; r.font.size = DOCX_BODY_FONT_SIZE; set_run_font(r, 'Nirmala UI')
    r_dy = m_r2c1.add_run(day_val if day_val else '____________')
    r_dy.font.size = DOCX_BODY_FONT_SIZE; set_run_font(r_dy, 'Nirmala UI')

    m_r2c2 = meta_table.rows[1].cells[1].paragraphs[0]
    m_r2c2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    m_r2c2.paragraph_format.space_after = Pt(0)
    r = m_r2c2.add_run('Roll No: ')
    r.font.bold = True; r.font.size = DOCX_BODY_FONT_SIZE; set_run_font(r, 'Nirmala UI')
    r_rn = m_r2c2.add_run(roll_no_val if roll_no_val else '____________')
    r_rn.font.size = DOCX_BODY_FONT_SIZE; set_run_font(r_rn, 'Nirmala UI')

    # Make meta_table borders none
    tblPr_meta = meta_table._tbl.tblPr
    borders_none = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="none"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr_meta.append(borders_none)

    # 5. Merged Assessment & Signatures Layout Table (Optional)
    if paper_data.get('show_marks_table', True) is not False and not paper_data.get('hide_marks_table', False):
        num_q_cols = len(q_summary)
        total_cols = num_q_cols + 5  # Question, Q-1..Q-N, Total, Blank, Sig Label, Sig Box
        
        assessment_table = doc.add_table(rows=3, cols=total_cols)
        assessment_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        assessment_table.autofit = False
        set_all_cell_borders(assessment_table, color='000000', sz='4')

        col_w_question = Inches(1.05)
        col_w_total = Inches(0.6)
        col_w_blank = Inches(0.35)
        col_w_sig_lbl = Inches(1.1)
        col_w_sig_box = Inches(1.25)
        
        fixed_width = 1.05 + 0.6 + 0.35 + 1.1 + 1.25  # 4.35 inches
        avail_for_q = max(0.45 * num_q_cols, 7.2 - fixed_width)
        col_w_q = Inches(avail_for_q / max(1, num_q_cols))

        col_widths = [col_w_question] + [col_w_q] * num_q_cols + [col_w_total, col_w_blank, col_w_sig_lbl, col_w_sig_box]

        for idx, col in enumerate(assessment_table.columns):
            col.width = col_widths[idx]

        for r_idx in range(3):
            for c_idx in range(total_cols):
                cell = assessment_table.rows[r_idx].cells[c_idx]
                cell.width = col_widths[c_idx]
                set_cell_margins(cell, top=35, bottom=35, left=35, right=35)

        blank_col_idx = num_q_cols + 2
        sig_lbl_col_idx = num_q_cols + 3
        sig_box_col_idx = num_q_cols + 4
        total_col_idx = num_q_cols + 1

        # Merge the blank column vertically across rows 0, 1, 2
        merged_blank_cell = assessment_table.rows[0].cells[blank_col_idx].merge(assessment_table.rows[2].cells[blank_col_idx])
        merged_blank_cell.width = col_w_blank
        set_cell_margins(merged_blank_cell, top=35, bottom=35, left=15, right=15)

        # Row 0: "Question", Questions, "Total", [Blank], "Teacher's Sign", [Sig Box]
        p0 = assessment_table.rows[0].cells[0].paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        r = p0.add_run('Question')
        r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

        for i, q_item in enumerate(q_summary):
            p = assessment_table.rows[0].cells[i+1].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(q_item['name'])
            r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

        p_tot_hdr = assessment_table.rows[0].cells[total_col_idx].paragraphs[0]
        p_tot_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_tot_hdr.paragraph_format.space_after = Pt(0)
        r = p_tot_hdr.add_run('Total')
        r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

        p_sig0 = assessment_table.rows[0].cells[sig_lbl_col_idx].paragraphs[0]
        p_sig0.paragraph_format.space_after = Pt(0)
        r = p_sig0.add_run("Teacher's Sign")
        r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

        # Row 1: "Obtain Marks", blanks, blanks, [Blank], "Supe. Sign", [Sig Box]
        p1 = assessment_table.rows[1].cells[0].paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r = p1.add_run('Obtain Marks')
        r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

        p_sig1 = assessment_table.rows[1].cells[sig_lbl_col_idx].paragraphs[0]
        p_sig1.paragraph_format.space_after = Pt(0)
        r = p_sig1.add_run("Supe. Sign")
        r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

        # Row 2: "Marks", values, total, [Blank], "Rechk. Sign", [Sig Box]
        p2 = assessment_table.rows[2].cells[0].paragraphs[0]
        p2.paragraph_format.space_after = Pt(0)
        r = p2.add_run('Marks')
        r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

        for i, q_item in enumerate(q_summary):
            p = assessment_table.rows[2].cells[i+1].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(q_item['marks']))
            r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

        p_tot_val = assessment_table.rows[2].cells[total_col_idx].paragraphs[0]
        p_tot_val.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_tot_val.paragraph_format.space_after = Pt(0)
        r = p_tot_val.add_run(str(total_marks))
        r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

        p_sig2 = assessment_table.rows[2].cells[sig_lbl_col_idx].paragraphs[0]
        p_sig2.paragraph_format.space_after = Pt(0)
        r = p_sig2.add_run("Rechk. Sign")
        r.font.bold = True; r.font.size = Pt(10); set_run_font(r, 'Nirmala UI')

    def add_section_heading(title_text, marks_text):
        tbl = doc.add_table(rows=1, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
        tbl.autofit = False
        tbl.columns[0].width = Inches(5.8)
        tbl.columns[1].width = Inches(1.4)
        tbl.rows[0].cells[0].width = Inches(5.8)
        tbl.rows[0].cells[1].width = Inches(1.4)
        
        # Borderless clean exam header
        tblPr = tbl._tbl.tblPr
        tblPr.append(parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="none"/>'
            f'<w:bottom w:val="none"/>'
            f'<w:left w:val="none"/>'
            f'<w:right w:val="none"/>'
            f'<w:insideH w:val="none"/>'
            f'<w:insideV w:val="none"/>'
            f'</w:tblBorders>'
        ))

        for c in tbl.rows[0].cells:
            set_cell_margins(c, top=8, bottom=8, left=15, right=15)

        p0 = tbl.rows[0].cells[0].paragraphs[0]
        p0.paragraph_format.space_before = Pt(3)
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.add_run(title_text)
        set_run_font(r0, 'Nirmala UI')
        r0.font.size = Pt(12)
        r0.font.bold = True
        r0.font.color.rgb = PRIMARY_COLOR

        p1 = tbl.rows[0].cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1.paragraph_format.space_before = Pt(3)
        p1.paragraph_format.space_after = Pt(1)
        
        clean_marks = marks_text
        if clean_marks:
            clean_marks = clean_marks.strip('[]')
            if not clean_marks.startswith('('):
                clean_marks = f'({clean_marks})'

        r1 = p1.add_run(clean_marks)
        set_run_font(r1, 'Nirmala UI')
        r1.font.size = Pt(12)
        r1.font.bold = True
        r1.font.color.rgb = PRIMARY_COLOR

    sections = paper_data.get('sections', [])
    for s_idx, sec in enumerate(sections):
        if sec.get('page_break_before', False) and s_idx > 0:
            doc.add_page_break()

        title = sec.get('title', f'Section {s_idx+1}')
        marks = sec.get('marks', '')
        add_section_heading(title, marks)

        if sec.get('options_box'):
            opt_tbl = doc.add_table(rows=1, cols=1)
            opt_tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
            opt_tbl.autofit = False
            opt_tbl.columns[0].width = Inches(7.2)
            opt_cell = opt_tbl.rows[0].cells[0]
            opt_cell.width = Inches(7.2)
            set_cell_background(opt_cell, 'f1f5f9')
            set_cell_margins(opt_cell, top=50, bottom=50, left=80, right=80)
            opt_p = opt_cell.paragraphs[0]
            opt_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            opt_p.paragraph_format.space_after = Pt(0)
            r_opt = opt_p.add_run(sec['options_box'])
            set_run_font(r_opt, 'Nirmala UI')
            r_opt.font.size = DOCX_BODY_FONT_SIZE
            r_opt.font.bold = True
            r_opt.font.color.rgb = RGBColor(30, 41, 59)

            tblPr = opt_tbl._tbl.tblPr
            borders = parse_xml(
                f'<w:tblBorders {nsdecls("w")}>'
                f'<w:top w:val="dashed" w:sz="4" w:space="0" w:color="64748b"/>'
                f'<w:bottom w:val="dashed" w:sz="4" w:space="0" w:color="64748b"/>'
                f'<w:left w:val="dashed" w:sz="4" w:space="0" w:color="64748b"/>'
                f'<w:right w:val="dashed" w:sz="4" w:space="0" w:color="64748b"/>'
                f'</w:tblBorders>'
            )
            tblPr.append(borders)

        if sec.get('intro_text'):
            p_in = doc.add_paragraph()
            p_in.paragraph_format.space_before = Pt(2)
            p_in.paragraph_format.space_after = Pt(2)
            add_formatted_math_text(p_in, sec['intro_text'], font_size=DOCX_BODY_FONT_SIZE)

        questions = sec.get('questions', [])
        q_type = sec.get('type', 'general')
        diag_type = sec.get('diagram_type')
        is_side_by_side = bool(diag_type and len(questions) > 0 and sec.get('diagram_layout') != 'stacked')

        if is_side_by_side:
            # Generate diagram image
            diag_img_path = None
            if diag_type == 'geometry_lines':
                diag_img_path = os.path.join(temp_dir, 'sec_geometry_lines.png')
                generate_lines_rays_diagram(diag_img_path)
                diag_w = Inches(2.7)
            elif diag_type == 'zigzag':
                diag_img_path = os.path.join(temp_dir, 'sec_zigzag.png')
                generate_zigzag_diagram(diag_img_path)
                diag_w = Inches(2.2)
            elif diag_type == 'pictograph':
                diag_img_path = os.path.join(temp_dir, 'sec_pictograph.png')
                generate_pictograph_chart(diag_img_path)
                diag_w = Inches(2.9)
            else:
                diag_w = Inches(2.7)

            # 2-column borderless table: Options Left (4.3 in), Diagram Right (2.9 in)
            sbs_tbl = doc.add_table(rows=1, cols=2)
            sbs_tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
            sbs_tbl.autofit = False
            sbs_tbl.columns[0].width = Inches(4.3)
            sbs_tbl.columns[1].width = Inches(2.9)
            sbs_tbl.rows[0].cells[0].width = Inches(4.3)
            sbs_tbl.rows[0].cells[1].width = Inches(2.9)

            tblPr_sbs = sbs_tbl._tbl.tblPr
            tblPr_sbs.append(parse_xml(
                f'<w:tblBorders {nsdecls("w")}>'
                f'<w:top w:val="none"/>'
                f'<w:bottom w:val="none"/>'
                f'<w:left w:val="none"/>'
                f'<w:right w:val="none"/>'
                f'<w:insideH w:val="none"/>'
                f'<w:insideV w:val="none"/>'
                f'</w:tblBorders>'
            ))

            cell_opts = sbs_tbl.rows[0].cells[0]
            cell_diag = sbs_tbl.rows[0].cells[1]
            set_cell_margins(cell_opts, top=10, bottom=10, left=5, right=15)
            set_cell_margins(cell_diag, top=10, bottom=10, left=10, right=5)

            # Left Cell: Options / Questions vertically
            for q_idx, q in enumerate(questions):
                p_q = cell_opts.paragraphs[0] if q_idx == 0 else cell_opts.add_paragraph()
                p_q.paragraph_format.space_before = Pt(2)
                p_q.paragraph_format.space_after = Pt(2.5)
                p_q.paragraph_format.line_spacing = 1.15
                add_formatted_math_text(p_q, q.get('text', ''), font_size=DOCX_BODY_FONT_SIZE, is_bold=q.get('is_bold', False))
                if q.get('answer_lines'):
                    for line_idx in range(q.get('answer_lines', 1)):
                        p_ans = cell_opts.add_paragraph()
                        p_ans.paragraph_format.space_before = Pt(1)
                        p_ans.paragraph_format.space_after = Pt(2)
                        p_ans_r = p_ans.add_run('_________________________________________')
                        set_run_font(p_ans_r, 'Nirmala UI')
                        p_ans_r.font.size = Pt(9.5)
                        p_ans_r.font.color.rgb = RGBColor(100, 116, 139)

            # Right Cell: Diagram picture
            if diag_img_path and os.path.exists(diag_img_path):
                p_diag = cell_diag.paragraphs[0]
                p_diag.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_diag.paragraph_format.space_before = Pt(0)
                p_diag.paragraph_format.space_after = Pt(0)
                p_diag.add_run().add_picture(diag_img_path, width=diag_w)
        else:
            if sec.get('diagram_type') == 'pictograph':
                pic_path = os.path.join(temp_dir, 'sec_pictograph.png')
                generate_pictograph_chart(pic_path)
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_after = Pt(1)
                p_img.paragraph_format.space_before = Pt(0)
                p_img.add_run().add_picture(pic_path, width=Inches(3.4))
            elif sec.get('diagram_type') == 'geometry_lines':
                geom_path = os.path.join(temp_dir, 'sec_geometry_lines.png')
                generate_lines_rays_diagram(geom_path)
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_after = Pt(1)
                p_img.paragraph_format.space_before = Pt(0)
                p_img.add_run().add_picture(geom_path, width=Inches(2.8))
            elif sec.get('diagram_type') == 'zigzag':
                zig_path = os.path.join(temp_dir, 'sec_zigzag.png')
                generate_zigzag_diagram(zig_path)
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_after = Pt(1)
                p_img.paragraph_format.space_before = Pt(0)
                p_img.add_run().add_picture(zig_path, width=Inches(1.8))

        if sec.get('table_data'):
            tbl_info = sec['table_data']
            headers = tbl_info.get('headers', [])
            rows = tbl_info.get('rows', [])
            if headers and rows:
                t = doc.add_table(rows=len(rows)+1, cols=len(headers))
                t.alignment = WD_TABLE_ALIGNMENT.LEFT
                t.autofit = False
                set_all_cell_borders(t, color='000000', sz='4')

                col_w = Inches(7.2 / len(headers))
                for col in t.columns:
                    col.width = col_w
                for h_i, h in enumerate(headers):
                    cell = t.rows[0].cells[h_i]
                    cell.width = col_w
                    set_cell_background(cell, 'f1f5f9')
                    set_cell_margins(cell, top=45, bottom=45, left=40, right=40)
                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_after = Pt(0)
                    add_formatted_math_text(p, h, font_size=DOCX_BODY_FONT_SIZE, is_bold=True)

                for r_i, r_data in enumerate(rows, start=1):
                    for c_i in range(len(headers)):
                        val = r_data[c_i] if c_i < len(r_data) else ''
                        cell = t.rows[r_i].cells[c_i]
                        cell.width = col_w
                        set_cell_margins(cell, top=35, bottom=35, left=40, right=40)
                        p = cell.paragraphs[0]
                        p.paragraph_format.space_after = Pt(0)
                        if c_i == 1:
                            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        else:
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        add_formatted_math_text(p, str(val), font_size=DOCX_BODY_FONT_SIZE)

        render_general_questions = not is_side_by_side
        if render_general_questions:
            # Check if questions in this section should be rendered horizontally across columns
            is_horizontal_subquestions = (
                q_type != 'mcq' and 
                len(questions) in [2, 3, 4] and 
                all(re.match(r'^[a-d]\)', q.get('text', '').strip()) or len(q.get('text', '')) < 45 for q in questions) and
                not any(q.get('answer_lines') for q in questions)
            )

            if is_horizontal_subquestions and len(questions) > 1:
                # Render sub-questions side-by-side in a borderless table
                sub_tbl = doc.add_table(rows=1, cols=len(questions))
                sub_tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
                sub_tbl.autofit = False
                tblPr_sub = sub_tbl._tbl.tblPr
                tblPr_sub.append(parse_xml(
                    f'<w:tblBorders {nsdecls("w")}>'
                    f'<w:top w:val="none"/>'
                    f'<w:bottom w:val="none"/>'
                    f'<w:left w:val="none"/>'
                    f'<w:right w:val="none"/>'
                    f'<w:insideH w:val="none"/>'
                    f'<w:insideV w:val="none"/>'
                    f'</w:tblBorders>'
                ))

                col_width = Inches(7.2 / len(questions))
                for col in sub_tbl.columns:
                    col.width = col_width
                for q_idx, q in enumerate(questions):
                    cell = sub_tbl.rows[0].cells[q_idx]
                    cell.width = col_width
                    set_cell_margins(cell, top=15, bottom=20, left=15, right=15)
                    p_sub = cell.paragraphs[0]
                    p_sub.paragraph_format.space_before = Pt(2)
                    p_sub.paragraph_format.space_after = Pt(2)
                    add_formatted_math_text(p_sub, q.get('text', ''), font_size=DOCX_BODY_FONT_SIZE, is_bold=q.get('is_bold', True))
                render_general_questions = False

        if render_general_questions:
            for q_idx, q in enumerate(questions):
                q_text = q.get('text', '')
                
                if q_type == 'mcq':
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(5.5) if q_idx > 0 else Pt(3)
                    p.paragraph_format.space_after = Pt(1.5)
                    p.paragraph_format.line_spacing = 1.15
                    add_formatted_math_text(p, q_text, font_size=DOCX_BODY_FONT_SIZE, is_bold=True)

                    opts = q.get('options', [])
                    if opts:
                        t_opt = doc.add_table(rows=1, cols=len(opts))
                        t_opt.alignment = WD_TABLE_ALIGNMENT.LEFT
                        t_opt.autofit = False
                        tblPr_opt = t_opt._tbl.tblPr
                        tblPr_opt.append(parse_xml(
                            f'<w:tblBorders {nsdecls("w")}>'
                            f'<w:top w:val="none"/>'
                            f'<w:bottom w:val="none"/>'
                            f'<w:left w:val="none"/>'
                            f'<w:right w:val="none"/>'
                            f'<w:insideH w:val="none"/>'
                            f'<w:insideV w:val="none"/>'
                            f'</w:tblBorders>'
                        ))

                        col_w_opt = Inches(7.2 / len(opts))
                        for col in t_opt.columns:
                            col.width = col_w_opt
                        for i, opt in enumerate(opts):
                            c = t_opt.rows[0].cells[i]
                            c.width = col_w_opt
                            set_cell_margins(c, top=25, bottom=40, left=15, right=15)
                            p_opt = c.paragraphs[0]
                            p_opt.paragraph_format.space_after = Pt(0)
                            add_formatted_math_text(p_opt, opt, font_size=DOCX_BODY_FONT_SIZE)
                elif q_type == 'true_false':
                    tbl_tf = doc.add_table(rows=1, cols=2)
                    tbl_tf.alignment = WD_TABLE_ALIGNMENT.LEFT
                    tbl_tf.autofit = False
                    tbl_tf.columns[0].width = Inches(6.0)
                    tbl_tf.columns[1].width = Inches(1.2)
                    tbl_tf.rows[0].cells[0].width = Inches(6.0)
                    tbl_tf.rows[0].cells[1].width = Inches(1.2)
                    
                    tblPr_tf = tbl_tf._tbl.tblPr
                    tblPr_tf.append(parse_xml(
                        f'<w:tblBorders {nsdecls("w")}>'
                        f'<w:top w:val="none"/>'
                        f'<w:bottom w:val="none"/>'
                        f'<w:left w:val="none"/>'
                        f'<w:right w:val="none"/>'
                        f'<w:insideH w:val="none"/>'
                        f'<w:insideV w:val="none"/>'
                        f'</w:tblBorders>'
                    ))

                    set_cell_margins(tbl_tf.rows[0].cells[0], top=28, bottom=28, left=10, right=10)
                    set_cell_margins(tbl_tf.rows[0].cells[1], top=28, bottom=28, left=10, right=10)
                    
                    p0 = tbl_tf.rows[0].cells[0].paragraphs[0]
                    p0.paragraph_format.space_before = Pt(2)
                    p0.paragraph_format.space_after = Pt(2)
                    p0.paragraph_format.line_spacing = 1.15
                    add_formatted_math_text(p0, q_text, font_size=DOCX_BODY_FONT_SIZE)

                    p1 = tbl_tf.rows[0].cells[1].paragraphs[0]
                    p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    p1.paragraph_format.space_before = Pt(2)
                    p1.paragraph_format.space_after = Pt(2)
                    r1 = p1.add_run('[                  ]')
                    set_run_font(r1, 'Nirmala UI')
                    r1.font.size = DOCX_BODY_FONT_SIZE; r1.font.bold = True
                    r1.font.color.rgb = PRIMARY_COLOR
                elif q_type == 'fill_in_blanks':
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(3.5) if q_idx > 0 else Pt(2)
                    p.paragraph_format.space_after = Pt(3.5)
                    p.paragraph_format.line_spacing = 1.2
                    add_formatted_math_text(p, q_text, font_size=DOCX_BODY_FONT_SIZE)
                else:
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(7) if q_idx > 0 else Pt(2.5)
                    p.paragraph_format.space_after = Pt(2.5)
                    p.paragraph_format.line_spacing = 1.2
                    add_formatted_math_text(p, q_text, font_size=DOCX_BODY_FONT_SIZE, is_bold=q.get('is_bold', False))

                    if q.get('diagram_type') == 'zigzag':
                        zig_path = os.path.join(temp_dir, 'inline_zigzag.png')
                        generate_zigzag_diagram(zig_path)
                        p_zig = doc.add_paragraph()
                        p_zig.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_zig.paragraph_format.space_before = Pt(2)
                        p_zig.paragraph_format.space_after = Pt(2)
                        p_zig.add_run().add_picture(zig_path, width=Inches(1.8))
                    elif q.get('diagram_type') == 'geometry_lines':
                        geom_path = os.path.join(temp_dir, 'inline_geom.png')
                        generate_lines_rays_diagram(geom_path)
                        p_geom = doc.add_paragraph()
                        p_geom.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_geom.paragraph_format.space_before = Pt(2)
                        p_geom.paragraph_format.space_after = Pt(2)
                        p_geom.add_run().add_picture(geom_path, width=Inches(2.8))
                    elif q.get('diagram_type') == 'pictograph':
                        pic_path = os.path.join(temp_dir, 'inline_pic.png')
                        generate_pictograph_chart(pic_path)
                        p_pic = doc.add_paragraph()
                        p_pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_pic.paragraph_format.space_before = Pt(2)
                        p_pic.paragraph_format.space_after = Pt(2)
                        p_pic.add_run().add_picture(pic_path, width=Inches(3.0))

                    if q.get('supercell_cells'):
                        cells_data = q['supercell_cells']
                        tbl_sc = doc.add_table(rows=1, cols=len(cells_data))
                        tbl_sc.alignment = WD_TABLE_ALIGNMENT.LEFT
                        tbl_sc.autofit = False
                        set_table_borders(tbl_sc, color='334155', sz='6')
                        col_w_sc = Inches(7.2 / len(cells_data))
                        for col in tbl_sc.columns:
                            col.width = col_w_sc
                        for i, val in enumerate(cells_data):
                            cell = tbl_sc.rows[0].cells[i]
                            cell.width = col_w_sc
                            set_cell_background(cell, 'f8fafc')
                            set_cell_margins(cell, top=20, bottom=20, left=10, right=10)
                            p = cell.paragraphs[0]
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            p.paragraph_format.space_after = Pt(0)
                            r = p.add_run(str(val))
                            set_run_font(r, 'Nirmala UI')
                            r.font.size = DOCX_BODY_FONT_SIZE; r.font.bold = True
                            r.font.color.rgb = PRIMARY_COLOR

                    if q.get('answer_lines'):
                        total_lines = q.get('answer_lines', 1)
                        for line_idx in range(total_lines):
                            p_ans = doc.add_paragraph()
                            p_ans.paragraph_format.space_before = Pt(2)
                            p_ans.paragraph_format.space_after = Pt(7) if line_idx == total_lines - 1 else Pt(3)
                            prefix = q.get('answer_prefix', 'Ans: ') if line_idx == 0 else '          '
                            r_pfx = p_ans.add_run(prefix)
                            set_run_font(r_pfx, 'Nirmala UI')
                            r_pfx.font.size = DOCX_BODY_FONT_SIZE
                            r_pfx.font.bold = True if line_idx == 0 else False
                            r_pfx.font.color.rgb = PRIMARY_COLOR
                            
                            r_line = p_ans.add_run('____________________________________________________________________')
                            set_run_font(r_line, 'Nirmala UI')
                            r_line.font.size = Pt(9.5)
                            r_line.font.color.rgb = RGBColor(100, 116, 139)

            if sec.get('drawing_boxes'):
                raw_boxes = sec['drawing_boxes']
                boxes = [b for b in raw_boxes if not any(k in str(b).lower() for k in ["figure showing", "geometric figure", "points l, m, p", "points o, c, a"])]
                if boxes:
                    tbl_box = doc.add_table(rows=1, cols=len(boxes))
                    tbl_box.alignment = WD_TABLE_ALIGNMENT.LEFT
                    tbl_box.autofit = False
                    set_table_borders(tbl_box, color='94a3b8', sz='4', val='dashed')
                    box_margin_vert = 400 if len(boxes) <= 3 else 460
                    col_w_box = Inches(7.2 / len(boxes))
                    for col in tbl_box.columns:
                        col.width = col_w_box
                    for i, label in enumerate(boxes):
                        c = tbl_box.rows[0].cells[i]
                        c.width = col_w_box
                        set_cell_background(c, 'ffffff')
                        set_cell_margins(c, top=box_margin_vert, bottom=box_margin_vert, left=20, right=20)
                        p = c.paragraphs[0]
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        r = p.add_run(label)
                        set_run_font(r, 'Nirmala UI')
                        r.font.size = DOCX_BODY_FONT_SIZE; r.font.bold = True
                        r.font.color.rgb = PRIMARY_COLOR

    doc.save(output_path)
    return output_path

