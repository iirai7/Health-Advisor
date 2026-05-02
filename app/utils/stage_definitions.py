class MedicalStageDefinitions:
    """
    Defines all stages for the gathering and diagnosis phases.
    Gathering: 9 stages (collecting medical history, one category at a time)
    Diagnosis:  6 stages (symptom assessment, one question at a time)
    """

    TOTAL_GATHERING_STAGES = 9
    TOTAL_DIAGNOSIS_STAGES = 6

    # ------------------------------------------------------------------ #
    # GATHERING STAGES                                                     #
    # ------------------------------------------------------------------ #
    GATHERING_STAGES = {
        1: {
            'name': 'Date of Birth',
            'db_fields': ['date_of_birth'],
            'question_en': "Let's begin your medical intake. What is your date of birth? (e.g. 1990-05-15 or 'May 15, 1990')",
            'question_ar': "لنبدأ استيفاء بياناتك الطبية. ما هو تاريخ ميلادك؟ (مثال: 1990-05-15 أو '15 مايو 1990')",
            'extract_instruction': 'Extract date_of_birth as a YYYY-MM-DD string, or null if not provided.',
        },
        2: {
            'name': 'Gender & Blood Type',
            'db_fields': ['gender', 'blood_type'],
            'question_en': "What is your gender? And do you know your blood type?",
            'question_ar': "ما هو جنسك؟ وهل تعرف فصيلة دمك؟",
            'extract_instruction': (
                'Extract gender (one of: male, female, prefer_not_to_say, or null) '
                'and blood_type (one of: A+, A-, B+, B-, AB+, AB-, O+, O-, unknown, or null).'
            ),
        },
        3: {
            'name': 'Height & Weight',
            'db_fields': ['height_cm', 'weight_kg'],
            'question_en': "What is your height (in cm) and weight (in kg)?",
            'question_ar': "ما هو طولك (بالسنتيمتر) ووزنك (بالكيلوغرام)؟",
            'extract_instruction': 'Extract height_cm as a number or null, and weight_kg as a number or null.',
        },
        4: {
            'name': 'Primary Care Physician',
            'db_fields': ['pcp_name', 'pcp_phone', 'pcp_hospital'],
            'question_en': "Do you have a primary care physician? If yes, share their name, phone, and hospital. (Say 'skip' if not applicable.)",
            'question_ar': "هل لديك طبيب رعاية أولية؟ إذا نعم، اذكر اسمه ورقم هاتفه ومستشفاه. (قل 'تخطي' إذا لم ينطبق عليك.)",
            'extract_instruction': 'Extract pcp_name (string or null), pcp_phone (string or null), pcp_hospital (string or null).',
        },
        5: {
            'name': 'Surgical History',
            'db_fields': ['surgical_history', 'hospitalization_history'],
            'question_en': "Have you had any past surgeries or hospitalisations? Describe briefly, or say 'none'.",
            'question_ar': "هل أجريت عمليات جراحية أو دخلت المستشفى سابقاً؟ صفها باختصار، أو قل 'لا شيء'.",
            'extract_instruction': 'Extract surgical_history (descriptive string or null) and hospitalization_history (descriptive string or null).',
        },
        6: {
            'name': 'Current Medications',
            'db_fields': ['current_medications'],
            'question_en': "Are you currently taking any medications? List them, or say 'none'.",
            'question_ar': "هل تتناول حالياً أي أدوية؟ اذكرها، أو قل 'لا شيء'.",
            'extract_instruction': 'Extract current_medications as a descriptive string or null.',
        },
        7: {
            'name': 'Allergies',
            'db_fields': ['drug_allergies', 'food_allergies', 'other_allergies'],
            'question_en': "Do you have any allergies? (drug, food, or other). Say 'none' if not applicable.",
            'question_ar': "هل لديك أي حساسية؟ (أدوية، أطعمة، أو غيرها). قل 'لا شيء' إذا لم ينطبق عليك.",
            'extract_instruction': 'Extract drug_allergies (string or null), food_allergies (string or null), other_allergies (string or null).',
        },
        8: {
            'name': 'Lifestyle',
            'db_fields': ['smoking_status', 'alcohol_use', 'exercise_frequency'],
            'question_en': "Tell me about your lifestyle: Do you smoke? Drink alcohol? How often do you exercise?",
            'question_ar': "أخبرني عن نمط حياتك: هل تدخن؟ هل تتناول الكحول؟ كم مرة تمارس الرياضة؟",
            'extract_instruction': (
                'Extract smoking_status (one of: never, former, current, or null), '
                'alcohol_use (one of: none, occasional, regular, or null), '
                'exercise_frequency (one of: none, light, moderate, heavy, or null).'
            ),
        },
        9: {
            'name': 'Family History & Additional Notes',
            'db_fields': ['family_history', 'additional_notes'],
            'question_en': "Any significant family medical history (e.g. heart disease, diabetes)? Anything else important to add about your health?",
            'question_ar': "هل لديك تاريخ عائلي طبي مهم (مثل أمراض القلب والسكري)؟ هل هناك أي شيء آخر مهم بشأن صحتك؟",
            'extract_instruction': 'Extract family_history (descriptive string or null) and additional_notes (descriptive string or null).',
        },
    }

    # ------------------------------------------------------------------ #
    # DIAGNOSIS STAGES                                                     #
    # ------------------------------------------------------------------ #
    DIAGNOSIS_STAGES = {
        1: {
            'name': 'Symptom Description',
            'question_en': "I'm ready to help assess your symptoms. What are you experiencing today?",
            'question_ar': "أنا مستعد لمساعدتك في تقييم أعراضك. ماذا تشعر اليوم؟",
        },
        2: {
            'name': 'Duration',
            'question_en': "How long have you been experiencing these symptoms?",
            'question_ar': "منذ متى وأنت تعاني من هذه الأعراض؟",
        },
        3: {
            'name': 'Severity',
            'question_en': "On a scale of 1 to 10, how severe are your symptoms? (1 = very mild, 10 = extremely severe)",
            'question_ar': "على مقياس من 1 إلى 10، كيف تقيّم شدة أعراضك؟ (1 = خفيف جداً، 10 = شديد للغاية)",
        },
        4: {
            'name': 'Associated Symptoms',
            'question_en': "Are you experiencing any other symptoms alongside this? (e.g. fever, nausea, headache, fatigue)",
            'question_ar': "هل تعاني من أعراض أخرى مصاحبة؟ (مثل: حمى، غثيان، صداع، إرهاق)",
        },
        5: {
            'name': 'Triggers & Context',
            'question_en': "Have you noticed any events, foods, activities, or factors that seem to trigger or worsen your symptoms?",
            'question_ar': "هل لاحظت أي أحداث أو أطعمة أو أنشطة أو عوامل تبدو أنها تثير أعراضك أو تزيدها سوءاً؟",
        },
        6: {
            'name': 'Assessment',
            'question_en': None,  # AI generates the assessment — no hardcoded question
            'question_ar': None,
        },
    }

    # ------------------------------------------------------------------ #
    # HELPERS                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_gathering_question(stage_num: int, language: str = 'en') -> str:
        stage = MedicalStageDefinitions.GATHERING_STAGES.get(stage_num, {})
        return stage.get('question_ar' if language == 'ar' else 'question_en', '')

    @staticmethod
    def get_diagnosis_question(stage_num: int, language: str = 'en') -> str:
        stage = MedicalStageDefinitions.DIAGNOSIS_STAGES.get(stage_num, {})
        return stage.get('question_ar' if language == 'ar' else 'question_en', '')

    @staticmethod
    def get_gathering_stage_info(stage_num: int) -> dict:
        return MedicalStageDefinitions.GATHERING_STAGES.get(stage_num, {})

    @staticmethod
    def is_gathering_complete(stage_num: int) -> bool:
        return stage_num > MedicalStageDefinitions.TOTAL_GATHERING_STAGES

    @staticmethod
    def is_diagnosis_assessment_stage(stage_num: int) -> bool:
        return stage_num == MedicalStageDefinitions.TOTAL_DIAGNOSIS_STAGES

    @staticmethod
    def detect_language(text: str) -> str:
        arabic_chars = set('ابجدهوزحطيكلمنسعفصقرشتثخذضظغأةئؤبآىءيهو')
        return 'ar' if set(text) & arabic_chars else 'en'
