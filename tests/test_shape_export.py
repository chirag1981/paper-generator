import os
import docx
import pytest
from app.services.docx_generator import build_docx_paper

def test_shape_questions_in_docx(tmp_path):
    paper_data = {
        'metadata': {
            'title': 'Mathematics Exam',
            'standard': 'Std6',
            'subject': 'Maths',
            'total_marks': '3'
        },
        'sections': [
            {
                'id': 'sec_shapes',
                'title': 'Q-3 (C) Name the following shapes',
                'type': 'fill_in_blanks',
                'subquestions_layout': 'vertical',
                'marks': '[3]',
                'questions': [
                    {'diagram_type': 'cylinder', 'text': '(1) = ____________'},
                    {'diagram_type': 'pyramid', 'text': '(2) = ____________'},
                    {'diagram_type': 'circle', 'text': '(3) = ____________'}
                ]
            }
        ]
    }

    out_docx = str(tmp_path / "test_paper.docx")
    build_docx_paper(paper_data, out_docx, temp_dir=str(tmp_path))

    assert os.path.exists(out_docx)
    doc = docx.Document(out_docx)

    # Verify tables with pictures exist
    shape_tables = []
    for table in doc.tables:
        xml = table._tbl.xml
        if 'pic:pic' in xml or 'w:drawing' in xml:
            shape_tables.append(table)

    assert len(shape_tables) == 3, f"Expected 3 shape tables, got {len(shape_tables)}"
