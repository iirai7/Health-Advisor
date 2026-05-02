from app.services.llm_client import chat_completion
from app.utils.stage_definitions import MedicalStageDefinitions
import json
import logging
import re

logger = logging.getLogger(__name__)

# Emergency keywords — fast pre-screen before any LLM call
_EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "cannot breathe", "shortness of breath",
    "heart attack", "stroke", "unconscious", "unresponsive", "severe bleeding",
    "suicide", "overdose", "seizure", "paralysis", "vision loss",
    "ألم في الصدر", "لا أستطيع التنفس", "نوبة قلبية", "سكتة دماغية",
    "فقدان الوعي", "نزيف حاد", "انتحار", "جرعة زائدة", "تشنج", "شلل"
]

EMERGENCY_NUMBER = "997"


# =============================================================
# LANGUAGE DETECTION
# =============================================================

def _detect_language(text: str, fallback: str = 'en') -> str:
    arabic_chars = set('ابجدهوزحطيكلمنسعفصقرشتثخذضظغأةئؤبآىءيهو٠١٢٣٤٥٦٧٨٩')
    has_arabic = bool(set(text) & arabic_chars)
    has_latin = bool(re.search(r'[a-zA-Z]', text))
    if has_arabic:
        return 'ar'
    if has_latin:
        return 'en'
    return fallback  # pure numbers/symbols → preserve session language


# =============================================================
# JSON PARSE HELPER
# =============================================================

def _parse_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON from LLM output."""
    try:
        cleaned = raw.strip()
        cleaned = re.sub(r'^```json\s*', '', cleaned)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'```$', '', cleaned).strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError) as e:
        # Fallback 1: find first {...} JSON block in the string
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Fallback 2: extract longest string value from known response keys
        string_values = re.findall(
            r'"(?:bot_response|response|message|text)"\s*:\s*"((?:[^"\\]|\\.)*)"',
            raw, re.DOTALL
        )
        if string_values:
            best = max(string_values, key=len)
            if len(best) > 20:
                logger.warning(f"JSON parse failed — recovered via key regex. Raw[:200]: {raw[:200]}")
                return {'bot_response': best.replace('\\n', '\n').replace('\\"', '"')}

        # Fallback 3: strip JSON syntax and use raw text directly
        plain = re.sub(r'[{}\[\]":]', '', raw).strip()
        if len(plain) > 20:
            logger.warning(f"JSON parse failed — using stripped raw text. Raw[:200]: {raw[:200]}")
            return {'bot_response': plain}

        logger.error(f"Failed to parse JSON from LLM response: {e}\nRaw: {raw}")
        return {}


# =============================================================
# GATHERING — STAGE-SPECIFIC EXTRACTION
# =============================================================

def run_gathering_stage(stage_num: int, user_message: str, language: str = 'en') -> dict:
    """
    Call the LLM to extract structured data for the given gathering stage
    from the user's message.

    Returns:
        dict: {
            'is_valid'    (bool): True if extraction succeeded,
            'extracted'   (dict): Field values (keys match user_medical_history columns),
            'bot_response'(str):  Acknowledgement or clarification request,
        }
        On failure returns {'is_valid': False, 'extracted': {}, 'bot_response': ''}
    """
    stage_info = MedicalStageDefinitions.get_gathering_stage_info(stage_num)
    if not stage_info:
        return {'is_valid': False, 'extracted': {}, 'bot_response': ''}

    lang_label = 'Arabic' if language == 'ar' else 'English'

    system_prompt = f"""You are a medical data extraction assistant. You MUST respond in {lang_label} only.

CURRENT TASK: Extract '{stage_info['name']}' from the patient's message.
WHAT TO EXTRACT: {stage_info['extract_instruction']}

RULES:
- If the user says "skip", "none", "لا شيء", "تخطي", or similar, accept it: set is_valid=true with null values.
- If information is unclear or missing, set is_valid=false and ask for clarification in bot_response.
- RESPOND ONLY WITH VALID JSON — no extra text, no markdown, no explanation.

JSON FORMAT:
{{
  "is_valid": true or false,
  "extracted": {{ <field_name>: <value or null>, ... }},
  "bot_response": "Warm brief acknowledgement (if valid) or polite clarification request (if invalid). In {lang_label}."
}}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    raw = chat_completion(messages, temperature=0.2, max_tokens=400)
    if not raw:
        return {'is_valid': False, 'extracted': {}, 'bot_response': ''}

    parsed = _parse_json(raw)
    if not parsed:
        return {'is_valid': False, 'extracted': {}, 'bot_response': ''}

    return {
        'is_valid': bool(parsed.get('is_valid', False)),
        'extracted': parsed.get('extracted', {}),
        'bot_response': parsed.get('bot_response', ''),
    }


# =============================================================
# DIAGNOSIS — STAGE-SPECIFIC HANDLING
# =============================================================

def run_diagnosis_stage(
    stage_num: int,
    user_message: str,
    language: str,
    symptom_context: str = '',
    medical_history: dict = None,
    conditions: list = None,
) -> dict:
    """
    Handle one turn of the diagnosis flow.

    Stages 1–5: Acknowledge the user's answer briefly (JSON).
    Stage 6:    Generate a full assessment (JSON with is_emergency flag).

    Returns:
        dict: {
            'bot_response' (str):  Reply text,
            'is_emergency' (bool): True only on immediately life-threatening signals,
        }
    """
    lang_label = 'Arabic' if language == 'ar' else 'English'

    # --- Stages 1–5: brief acknowledgement only ---
    if stage_num < MedicalStageDefinitions.TOTAL_DIAGNOSIS_STAGES:
        system_prompt = f"""You are a compassionate medical assistant. You MUST respond in {lang_label} only.

The patient has answered one of your intake questions. Acknowledge their response briefly and warmly (1–2 sentences max).
Do NOT ask another question — the next question will be sent separately.
Do NOT provide any diagnosis or medical advice at this stage.

RESPOND ONLY WITH VALID JSON:
{{
  "bot_response": "Brief warm acknowledgement in {lang_label}."
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        raw = chat_completion(messages, temperature=0.3, max_tokens=200)
        parsed = _parse_json(raw) if raw else {}
        return {
            'bot_response': parsed.get('bot_response', ''),
            'is_emergency': False,
        }

    # --- Stage 6: full assessment ---
    history_text = _format_history(medical_history or {}, conditions or [])

    system_prompt = f"""You are a knowledgeable medical diagnostic assistant. You MUST respond in {lang_label} only.

PATIENT MEDICAL HISTORY:
{history_text}

SYMPTOM CONSULTATION SUMMARY:
{symptom_context}

Based on the above, provide a structured assessment in {lang_label}.

RESPOND ONLY WITH VALID JSON:
{{
  "is_emergency": false,
  "summary": "Brief summary of reported symptoms in {lang_label}",
  "possible_causes": "Potential conditions in {lang_label}",
  "next_steps": "Recommended actions and advice in {lang_label}"
}}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Please provide the assessment based on the consultation above."},
    ]

    raw = chat_completion(messages, temperature=0.3, max_tokens=700)
    parsed = _parse_json(raw) if raw else {}

    return {
        'bot_response': parsed.get('bot_response', ''),
        'summary': parsed.get('summary', ''),
        'possible_causes': parsed.get('possible_causes', ''),
        'next_steps': parsed.get('next_steps', ''),
        'is_emergency': bool(parsed.get('is_emergency', False)),
    }


# =============================================================
# CONTEXT FORMATTERS
# =============================================================

def _format_history(history: dict, conditions: list) -> str:
    if not history:
        return "No medical history on file."

    conditions_str = ", ".join(
        c.get('name_en', '') for c in conditions
    ) if conditions else "None reported"

    return (
        f"- DOB: {history.get('date_of_birth', 'N/A')}\n"
        f"- Gender: {history.get('gender', 'N/A')}\n"
        f"- Blood Type: {history.get('blood_type', 'N/A')}\n"
        f"- Height: {history.get('height_cm', 'N/A')} cm | Weight: {history.get('weight_kg', 'N/A')} kg\n"
        f"- Chronic Conditions: {conditions_str}\n"
        f"- Current Medications: {history.get('current_medications') or 'None'}\n"
        f"- Drug Allergies: {history.get('drug_allergies') or 'None'}\n"
        f"- Food Allergies: {history.get('food_allergies') or 'None'}\n"
        f"- Surgical History: {history.get('surgical_history') or 'None'}\n"
        f"- Smoking: {history.get('smoking_status', 'N/A')} | "
        f"Alcohol: {history.get('alcohol_use', 'N/A')} | "
        f"Exercise: {history.get('exercise_frequency', 'N/A')}\n"
        f"- Family History: {history.get('family_history') or 'None'}\n"
        f"- Additional Notes: {history.get('additional_notes') or 'None'}"
    )


# =============================================================
# EMERGENCY PRE-SCREEN
# =============================================================

def quick_emergency_check(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _EMERGENCY_KEYWORDS)