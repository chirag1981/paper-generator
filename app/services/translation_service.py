import json
import os
import re
from typing import Dict, Any, Optional

from app.utils import get_active_gemini_api_key

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
    _USE_MODERN_GENAI = True
except ImportError:
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            import google.generativeai as genai
        HAS_GENAI = True
        _USE_MODERN_GENAI = False
    except ImportError:
        HAS_GENAI = False
        _USE_MODERN_GENAI = False

LANGUAGE_NAMES = {
    'en': 'English',
    'gu': 'Gujarati (ગુજરાતી)',
    'hi': 'Hindi (हिन्दी)'
}

def translate_paper_structure(paper_data: Dict[str, Any], target_lang: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Translates an exam paper JSON structure to the target language (en, gu, or hi).
    Uses Gemini AI if API key is provided, preserving mathematical equations, blanks, and JSON schema.
    """
    if target_lang not in ('en', 'gu', 'hi'):
        raise ValueError(f"Unsupported target language: {target_lang}. Supported: en, gu, hi")

    lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)

    key = api_key or get_active_gemini_api_key()
    if key and HAS_GENAI:
        try:
            return _translate_with_gemini(paper_data, target_lang, lang_name, key)
        except Exception as e:
            # If API fails (e.g. rate limit, invalid key), fallback to rule-based translator
            print(f"[TranslationService] Gemini translation error: {e}, falling back to basic translator.")

    return _fallback_translate(paper_data, target_lang)


def _translate_with_gemini(paper_data: Dict[str, Any], target_lang: str, lang_name: str, api_key: str) -> Dict[str, Any]:

    # Try fast flash models first
    env_model = os.environ.get('GEMINI_MODEL', '').strip()
    candidate_models = [env_model, 'gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-3.7-flash', 'gemini-flash-latest']
    seen = set()
    model_names = []
    for m in candidate_models:
        if m and m not in seen:
            seen.add(m)
            model_names.append(m)
    last_err = None

    prompt = f"""You are an expert bilingual educational exam translator specializing in Indian school curricula.
Translate all text in the following exam paper JSON into {lang_name} ({target_lang}).

CRITICAL INSTRUCTIONS:
1. Translate:
   - metadata (exam_title, standard, subject, time_limit)
   - section titles (e.g. "Q.1 (A) Fill in the blanks with suitable words from the bracket:")
   - section intro_text, options_box values, drawing_boxes
   - question texts, MCQ options, answer prefixes
   - table headers and textual table row values
2. PRESERVE STRICTLY:
   - All JSON keys and data types (arrays, objects, booleans, integers).
   - All IDs (id, section IDs).
   - Mathematical numerals, formulas, degree symbols (e.g. 90°, 360°, 180°), geometric notation (e.g. ↔XY, —AB), and numbers unless standard in the target language.
   - Blank lines (e.g. "________________").
   - Question numbering (e.g. "1.", "2.", "(i)", "(ii)", "(A)", "(B)").
3. Output MUST be ONLY valid, parsable JSON without markdown wrapping like ```json ... ```.

Input JSON:
{json.dumps(paper_data, ensure_ascii=False, indent=2)}
"""

    for m_name in model_names:
        try:
            if _USE_MODERN_GENAI:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=m_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=8192,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                    )
                )
                raw_text = (response.text or "").strip()
            else:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt)
                raw_text = (response.text or "").strip()
            
            # Strip markdown fences if present
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and "sections" in parsed:
                return parsed
        except Exception as err:
            last_err = err
            continue

    if last_err:
        raise last_err

    return paper_data


# Fallback dictionary for basic terms if no API key is set
COMMON_TRANSLATIONS = {
    'gu': {
        'Mathematics': 'ગણિત',
        'Std. 6th': 'ધોરણ ૬',
        '1st Semester Examination – 2026': 'પ્રથમ સત્ર પરીક્ષા – ૨૦૨૬',
        '2 Hours': '૨ કલાક',
        'Total Marks': 'કુલ ગુણ',
        'Marks': 'ગુણ',
        'Fill in the blanks': 'ખાલી જગ્યા પૂરો',
        'Multiple Choice Questions': 'બહુવિકલ્પી પ્રશ્નો (MCQ)',
        'True or False': 'ખરાં કે ખોટાં',
        'Answer the following': 'નીચેના પ્રશ્નોના ઉત્તર આપો',
        'True': 'સાચું',
        'False': 'ખોટું',
        'Right': 'કાટકોણ',
        'Acute': 'લઘુકોણ',
        'Obtuse': 'ગુરુકોણ',
        'Reflex': 'સરળકોણ / વિપરીત કોણ',
        'Playing': 'રમવું',
        'Reading story books': 'વાર્તાની ચોપડીઓ વાંચવી',
        'Watching TV': 'ટીવી જોવું',
        'Listening to music': 'સંગીત સાંભળવું',
        'Painting': 'ચિત્રકામ',
        'Preferred Activity': 'પસંદગીની પ્રવૃત્તિ',
        'Number of Students': 'વિદ્યાર્થીઓની સંખ્યા',
        'Five points': 'પાંચ બિંદુઓ',
        'Two lines': 'બે રેખાઓ',
        'Four rays': 'ચાર કિરણો',
        'A line segment': 'એક રેખાખંડ'
    },
    'hi': {
        'Mathematics': 'गणित',
        'Std. 6th': 'कक्षा ६',
        '1st Semester Examination – 2026': 'प्रथम सत्र परीक्षा – २०२६',
        '2 Hours': '२ घंटे',
        'Total Marks': 'कुल अंक',
        'Marks': 'अंक',
        'Fill in the blanks': 'रिक्त स्थान भरिए',
        'Multiple Choice Questions': 'बहुविकल्पीय प्रश्न (MCQ)',
        'True or False': 'सत्य या असत्य',
        'Answer the following': 'निम्नलिखित प्रश्नों के उत्तर दीजिए',
        'True': 'सत्य',
        'False': 'असत्य',
        'Right': 'समकोण',
        'Acute': 'न्यूनकोण',
        'Obtuse': 'अधिककोण',
        'Reflex': 'प्रतिवर्ती कोण',
        'Playing': 'खेलना',
        'Reading story books': 'कहानियों की किताबें पढ़ना',
        'Watching TV': 'टीवी देखना',
        'Listening to music': 'संगीत सुनना',
        'Painting': 'चित्रकला',
        'Preferred Activity': 'पसंदीदा गतिविधि',
        'Number of Students': 'छात्रों की संख्या',
        'Five points': 'पाँच बिंदु',
        'Two lines': 'दो रेखाएँ',
        'Four rays': 'चार किरणें',
        'A line segment': 'एक रेखाखंड'
    }
}

def _fallback_translate(paper_data: Dict[str, Any], target_lang: str) -> Dict[str, Any]:
    """Lightweight rule-based fallback translation when API key is not configured."""
    if target_lang == 'en':
        return paper_data # Already mostly English

    dict_map = COMMON_TRANSLATIONS.get(target_lang, {})
    new_paper = json.loads(json.dumps(paper_data)) # deep copy

    def repl(text: str) -> str:
        if not isinstance(text, str):
            return text
        res = text
        for k, v in dict_map.items():
            res = re.sub(re.escape(k), v, res, flags=re.IGNORECASE)
        return res

    if 'metadata' in new_paper:
        meta = new_paper['metadata']
        for k in ['exam_title', 'standard', 'subject', 'time_limit']:
            if k in meta and isinstance(meta[k], str):
                meta[k] = repl(meta[k])

    if 'sections' in new_paper:
        for sec in new_paper['sections']:
            if 'title' in sec:
                sec['title'] = repl(sec['title'])
            if 'marks' in sec:
                sec['marks'] = repl(sec['marks'])
            if 'intro_text' in sec:
                sec['intro_text'] = repl(sec['intro_text'])
            if 'options_box' in sec:
                sec['options_box'] = repl(sec['options_box'])
            if 'drawing_boxes' in sec and isinstance(sec['drawing_boxes'], list):
                sec['drawing_boxes'] = [repl(b) for b in sec['drawing_boxes']]
            
            if 'questions' in sec:
                for q in sec['questions']:
                    if 'text' in q:
                        q['text'] = repl(q['text'])
                    if 'options' in q and isinstance(q['options'], list):
                        q['options'] = [repl(opt) for opt in q['options']]
                    if 'answer_prefix' in q:
                        q['answer_prefix'] = repl(q['answer_prefix'])

            if 'table_data' in sec and isinstance(sec['table_data'], dict):
                tbl = sec['table_data']
                if 'headers' in tbl and isinstance(tbl['headers'], list):
                    tbl['headers'] = [repl(h) for h in tbl['headers']]
                if 'rows' in tbl and isinstance(tbl['rows'], list):
                    tbl['rows'] = [[repl(cell) for cell in r] for r in tbl['rows']]

    return new_paper
