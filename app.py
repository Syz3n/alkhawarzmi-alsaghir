from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'al-khwarizmi-secret-2025'

# Add enumerate as a Jinja2 filter
app.jinja_env.globals['enumerate'] = enumerate

# ─── Game Data ────────────────────────────────────────────────────────────────

CORRECT_SENTENCES = [
    "ذهبت إلى السوق.", "قرأت الكتاب الجديد.", "كتبت الرسالة الطويلة.",
    "شربت العصير البارد.", "نظفت الغرفة جيداً.", "لعبت الكرة مع الأصدقاء.",
    "ذهبت إلى المدرسة باكراً.", "زرت صديقي المريض.", "اشتريت الفواكه الطازجة.",
    "حفظت القصيدة الجميلة.", "سافرت إلى البحر.", "رأيت المنظر الرائع.",
    "سمعت الأغنية الحزينة.", "شاهدت الفيلم الممتع.", "زرعت الأشجار الكبيرة.",
    "بنيت البيت الصغير.", "رسمت اللوحة الفنية.", "غنت الأغنية الوطنية.",
    "ركضت في الحديقة.", "سبحت في البحر.", "طرت في الطائرة.", "مشيت في المنتزه.",
    "جلست على المقعد.", "وقفت في الطابور.", "ضحكت من القلب.", "بكيت من الفرح.",
    "تحدثت بصراحة.", "سافرت بالقطار.", "عدت مسروراً.", "جئت مبكراً."
]

INCORRECT_SENTENCES = [
    "الطلاب يذهب إلى المدرسة.", "المعلمات تشرح الدرس.", "هذان الطالب مجتهد.",
    "الطالبات كتبت الواجب.", "الأولاد يلعب في الحديقة.", "رأيت المعلمون.",
    "مررت بالطلاب المجتهدون.", "هذين كتاب مفيد.", "كلمت المعلمين.",
    "سلمت على الأستاذين.", "الطالب المجتهدون.", "البنت الجميلات.",
    "هذا كتب.", "هذه أقلام.", "الطالبان المجتهد.", "كان الطلاب مجتهد.",
    "أصبح الجو جميلة.", "صار الماء باردة.", "أمسى الطالب متعبين.",
    "إن الطالب مجتهدون.", "كأن البنت جميلات.", "ليت الأولاد يلعب.",
    "أنا ذهب إلى المدرسة.", "هو أكل الطعام.", "هم كتب الواجب.",
    "اشتريت خمس كتاب.", "رأيت ثلاث بنات.", "في الفصل عشر طالب.",
    "متى أنت تذهب؟", "أين هو بيتك؟", "كيف أنت حالك؟"
]

QUESTIONS = {
    1: [
        {"id": 1, "type": "multiple_choice", "points": 10,
         "question": "ما الفاعل في الجملة: 'قرأ الطالبُ الكتابَ'؟",
         "sentence": "قرأ الطالبُ الكتابَ", "correct": 0,
         "options": ["الطالبُ", "الكتابَ", "قرأ", "المدرسة"],
         "explanation": "الفاعل هو الطالبُ لأنه من قام بفعل القراءة وهو مرفوع بالضمة",
         "hint": "الفاعل هو من قام بالفعل"},
        {"id": 2, "type": "multiple_choice", "points": 10,
         "question": "ما المفعول به في الجملة: 'كتبتِ التلميذةُ الدرسَ'؟",
         "sentence": "كتبتِ التلميذةُ الدرسَ", "correct": 1,
         "options": ["التلميذةُ", "الدرسَ", "كتبتِ", "القلم"],
         "explanation": "المفعول به هو الدرسَ لأنه من وقع عليه فعل الكتابة وهو منصوب بالفتحة",
         "hint": "المفعول به هو ما وقع عليه الفعل"},
        {"id": 3, "type": "correct_sentence", "points": 15,
         "question": "صحح الجملة التالية: 'ذهبتُ إلى المدرسةِ صباحاً'",
         "sentence": "ذهبتُ إلى المدرسةِ صباحاً", "correct_answer": "الجملة صحيحة",
         "explanation": "الجملة صحيحة إعرابياً",
         "hint": "راجع الضمائر المتصلة"},
        {"id": 4, "type": "multiple_choice", "points": 10,
         "question": "ما نوع الكلمة 'مدرسة' في: 'ذهبت إلى المدرسةِ'؟",
         "sentence": "ذهبت إلى المدرسةِ", "correct": 0,
         "options": ["اسم مجرور", "فعل ماض", "فاعل", "مفعول به"],
         "explanation": "المدرسةِ: اسم مجرور بـ'إلى' وعلامة جره الكسرة",
         "hint": "الاسم بعد حرف الجر يكون مجروراً"},
        {"id": 5, "type": "identify_elements", "points": 12,
         "question": "حدد نوع الكلمة الملونة: <الطالبُ> مجتهد",
         "sentence": "الطالبُ مجتهد", "correct": 0,
         "elements": ["مبتدأ", "خبر", "فاعل", "مفعول به"],
         "explanation": "الطالبُ: مبتدأ مرفوع بالضمة, مجتهد: خبر مرفوع بالضمة",
         "hint": "المبتدأ هو الذي نبدأ به الجملة الاسمية"},
        {"id": 6, "type": "multiple_choice", "points": 10,
         "question": "ما إعراب 'الكتابُ' في: 'الكتابُ مفيدٌ'؟",
         "sentence": "الكتابُ مفيدٌ", "correct": 0,
         "options": ["مبتدأ مرفوع", "خبر مرفوع", "فاعل مرفوع", "اسم مجرور"],
         "explanation": "الكتابُ: مبتدأ مرفوع بالضمة، مفيدٌ: خبر مرفوع بالضمة",
         "hint": "الجملة الاسمية تبدأ بمبتدأ"},
        {"id": 7, "type": "correct_sentence", "points": 15,
         "question": "صحح الجملة: 'الطالبان مجتهدين'",
         "sentence": "الطالبان مجتهدين", "correct_answer": "الطالبان مجتهدان",
         "explanation": "الصحيح: الطالبان مجتهدان - لأن المثنى يرفع بالألف",
         "hint": "المثنى يرفع بالألف وينصب ويجر بالياء"},
        {"id": 8, "type": "multiple_choice", "points": 10,
         "question": "ما ضمير المتكلم في: 'أنا طالبٌ'؟",
         "sentence": "أنا طالبٌ", "correct": 0,
         "options": ["أنا", "طالبٌ", "ضمير مستتر", "لا يوجد"],
         "explanation": "أنا: ضمير رفع منفصل في محل رفع مبتدأ",
         "hint": "الضمائر أنواع: منفصلة ومتصلة"},
        {"id": 9, "type": "identify_elements", "points": 12,
         "question": "ما إعراب 'التلميذاتُ' في: 'حضرت التلميذاتُ'؟",
         "sentence": "حضرت التلميذاتُ", "correct": 0,
         "elements": ["فاعل مرفوع", "مفعول به منصوب", "خبر مرفوع", "اسم مجرور"],
         "explanation": "التلميذاتُ: فاعل مرفوع بالضمة لأنه جمع مؤنث سالم",
         "hint": "الفاعل يرفع بعد الفعل"},
        {"id": 10, "type": "multiple_choice", "points": 12,
         "question": "ما نوع 'لا' في: 'لا تأكلْ بسرعة'؟",
         "sentence": "لا تأكلْ بسرعة", "correct": 0,
         "options": ["ناهية", "نافية", "عاطفة", "استفهامية"],
         "explanation": "لا: حرف نهي وجزم، والفعل بعدها مجزوم",
         "hint": "لا الناهية تطلب الكف عن الفعل"},
        {"id": 11, "type": "correct_sentence", "points": 15,
         "question": "صحح الجملة: رجعوا المسافرون",
         "sentence": "رجعوا المسافرون", "correct_answer": "رجع المسافرون",
         "explanation": "الصحيح: رجع المسافرون - لأن الفعل يطابق الفاعل في العدد",
         "hint": "الفعل يطابق الفاعل تذكيراً وتأنيثاً"},
        {"id": 12, "type": "multiple_choice", "points": 12,
         "question": "ما إعراب 'محمودٌ' في: 'محمودٌ خلقه'؟",
         "sentence": "محمودٌ خلقه", "correct": 0,
         "options": ["مبتدأ مرفوع", "خبر مرفوع", "فاعل مرفوع", "صفة مرفوعة"],
         "explanation": "محمودٌ: مبتدأ مرفوع بالضمة، خلقه: مبتدأ ثان مرفوع",
         "hint": "الجملة الاسمية قد تتعدد مكوناتها"},
        {"id": 13, "type": "identify_elements", "points": 10,
         "question": "حدد الفعل في: 'الطلاب يدرسون بجد'",
         "sentence": "الطلاب يدرسون بجد", "correct": 0,
         "elements": ["يدرسون", "الطلاب", "بجد", "يجتهدون"],
         "explanation": "يدرسون: فعل مضارع مرفوع بثبوت النون",
         "hint": "الفعل هو الكلمة التي تدل على حدث"},
        {"id": 14, "type": "multiple_choice", "points": 10,
         "question": "ما نوع الجملة: 'الجوُ جميلٌ'؟",
         "sentence": "الجوُ جميلٌ", "correct": 0,
         "options": ["اسمية", "فعلية", "شبه جملة", "ظرفية"],
         "explanation": "جملة اسمية لأنها تبدأ باسم (المبتدأ)",
         "hint": "الجملة الاسمية تبدأ باسم"},
        {"id": 15, "type": "correct_sentence", "points": 15,
         "question": "صحح الجملة: هذا الكتب مفيدة",
         "sentence": "هذا الكتب مفيدة", "correct_answer": "هذه الكتب مفيدة",
         "explanation": "الصحيح: هذه الكتب مفيدة - لأن 'هذه' للجمع",
         "hint": "أسماء الإشارة تختلف حسب العدد"},
    ],
    2: [
        {"id": 16, "type": "multiple_choice", "points": 15,
         "question": "ما إعراب 'كان' في الجملة: 'كان الجوُ جميلاً'؟",
         "sentence": "كان الجوُ جميلاً", "correct": 0,
         "options": ["فعل ماض ناقص", "فعل ماض تام", "اسم", "حرف"],
         "explanation": "كان: فعل ماض ناقص يرفع المبتدأ وينصب الخبر",
         "hint": "كان وأخواتها أفعال ناقصة"},
        {"id": 17, "type": "multiple_choice", "points": 15,
         "question": "ما خبر 'إن' في: 'إن العلمَ نافعٌ'؟",
         "sentence": "إن العلمَ نافعٌ", "correct": 1,
         "options": ["العلمَ", "نافعٌ", "إن", "مفيد"],
         "explanation": "نافعٌ: خبر إن مرفوع بالضمة, العلمَ: اسم إن منصوب بالفتحة",
         "hint": "إن وأخواتها تنصب المبتدأ وترفع الخبر"},
        {"id": 18, "type": "identify_elements", "points": 18,
         "question": "حدد أنواع كان وأخواتها في الجمل التالية",
         "sentence": "كان الطالب مجتهداً - صار الجو بارداً - أصبحت مهذبة", "correct": 0,
         "elements": ["كان ناقصة", "صار تامة", "أصبح ناقصة", "كان تامة"],
         "explanation": "كلها أفعال ناقصة: كان، صار، أصبح",
         "hint": "أخوات كان: صار، أصبح، أمسى، ظل، بات، ليس"},
        {"id": 19, "type": "correct_sentence", "points": 18,
         "question": "صحح الجملة: 'إن الطلاب مجتهدون'",
         "sentence": "إن الطلاب مجتهدون", "correct_answer": "إن الطلاب مجتهدون",
         "explanation": "الجملة صحيحة: إن حرف نصب، الطلاب اسم إن منصوب، مجتهدون خبر إن مرفوع",
         "hint": "إن تنصب المبتدأ وترفع الخبر"},
        {"id": 20, "type": "multiple_choice", "points": 15,
         "question": "ما إعراب 'كأن' في: 'كأن النجمَ الماس'؟",
         "sentence": "كأن النجمَ الماس", "correct": 1,
         "options": ["فعل ماض ناقص", "حرف تشبيه", "اسم", "فعل أمر"],
         "explanation": "كأن: حرف تشبيه ونصب",
         "hint": "أحرف التشبيه: كأن، كأنما، كما، مثل"},
        {"id": 21, "type": "identify_elements", "points": 18,
         "question": "حدد المفعول المطلق في الجملة",
         "sentence": "ضحك الطفل ضحكاً طويلاً", "correct": 0,
         "elements": ["ضحكاً", "الطفل", "طويلاً", "ضحك"],
         "explanation": "ضحكاً: مفعول مطلق منصوب بالفتحة",
         "hint": "المفعول المطلق يؤكد الفعل أو يبين نوعه"},
        {"id": 22, "type": "multiple_choice", "points": 18,
         "question": "ما نوع المفعول في: 'سار الجندي سيراً سريعاً'؟",
         "sentence": "سار الجندي سيراً سريعاً", "correct": 0,
         "options": ["مفعول مطلق", "مفعول به", "مفعول لأجله", "مفعول معه"],
         "explanation": "سيراً: مفعول مطلق منصوب بالفتحة لتأكيد الفعل",
         "hint": "المفعول المطلق يؤكد الفعل أو يبين نوعه أو عدده"},
        {"id": 23, "type": "correct_sentence", "points": 18,
         "question": "صحح الجملة: ساعدت الاخوه بعضهم",
         "sentence": "ساعدت الاخوه بعضهم", "correct_answer": "ساعد الإخوة بعضهم",
         "explanation": "الصحيح: ساعد الإخوة بعضهم - الفعل يطابق الفاعل",
         "hint": "جمع التكسير يعامل معاملة المفرد"},
        {"id": 24, "type": "multiple_choice", "points": 16,
         "question": "ما إعراب 'أف' في: 'أفٍ من الكسل'؟",
         "sentence": "أفٍ من الكسل", "correct": 0,
         "options": ["اسم فعل مضارع", "اسم فعل ماض", "حرف", "فعل أمر"],
         "explanation": "أفٍ: اسم فعل مضارع بمعنى (أتضجر)",
         "hint": "أسماء الأفعال: أف، هيا، صه، إيه"},
        {"id": 25, "type": "identify_elements", "points": 18,
         "question": "حدد المفعول لأجله في الجملة",
         "sentence": "اجتهد طلباً للنجاح", "correct": 0,
         "elements": ["طلباً", "اجتهد", "للنجاح", "النجاح"],
         "explanation": "طلباً: مفعول لأجله منصوب بالفتحة",
         "hint": "المفعول لأجله يبين سبب الفعل"},
    ],
    3: [
        {"id": 31, "type": "multiple_choice", "points": 20,
         "question": "ما نوع الأسلوب في: 'واللهِ لأجتهدنَّ'؟",
         "sentence": "واللهِ لأجتهدنَّ", "correct": 0,
         "options": ["قسم", "تعجب", "مدح", "نداء"],
         "explanation": "أسلوب قسم: القسم بالواو، واللام لام التوكيد، والنون نون التوكيد",
         "hint": "أدوات القسم: الواو، الباء، التاء"},
        {"id": 32, "type": "identify_elements", "points": 22,
         "question": "حدد نوع 'ما' في: 'ما أجملَ الربيعَ'",
         "sentence": "ما أجملَ الربيعَ", "correct": 0,
         "elements": ["تعجبية", "نافية", "موصولة", "استفهامية"],
         "explanation": "ما: تعجبية، وأجملَ: فعل ماضٍ جاء على صيغة التعجب",
         "hint": "صيغ التعجب: ما أفعلَه، وأفعِل به"},
        {"id": 33, "type": "correct_sentence", "points": 22,
         "question": "صحح الجملة: 'يا رجل أقبل'",
         "sentence": "يا رجل أقبل", "correct_answer": "يا رجلُ أقبل",
         "explanation": "الصحيح: يا رجلُ أقبل - المنادى المفرد العلم مرفوع",
         "hint": "المنادى المفرد العلم مبني على الضم"},
        {"id": 34, "type": "multiple_choice", "points": 20,
         "question": "ما إعراب 'الذي' في: 'جاء الذي اجتهد'؟",
         "sentence": "جاء الذي اجتهد", "correct": 0,
         "options": ["اسم موصول", "اسم إشارة", "ضمير", "اسم استفهام"],
         "explanation": "الذي: اسم موصول مبني على السكون في محل رفع فاعل",
         "hint": "الأسماء الموصولة: الذي، التي، اللذان، اللتان، الذين، اللواتي"},
        {"id": 35, "type": "identify_elements", "points": 22,
         "question": "حدد الحال في الجملة",
         "sentence": "جاء الولد راكضاً", "correct": 0,
         "elements": ["راكضاً", "جاء", "الولد", "راكض"],
         "explanation": "راكضاً: حال منصوب بالفتحة",
         "hint": "الحال يبين هيئة صاحبها"},
    ]
}

LEADERBOARD = [
    {"name": "عبدالعزيز", "score": 150, "level": 3},
    {"name": "سيف", "score": 120, "level": 2},
    {"name": "محمد", "score": 90, "level": 2},
    {"name": "سالم", "score": 60, "level": 1},
]

# ─── Session Helpers ───────────────────────────────────────────────────────────

def init_session():
    if 'score' not in session:
        session['score'] = 0
    if 'lives' not in session:
        session['lives'] = 3
    if 'current_level' not in session:
        session['current_level'] = 1
    if 'current_question' not in session:
        session['current_question'] = 0
    if 'levels_unlocked' not in session:
        session['levels_unlocked'] = 1
    if 'feedback' not in session:
        session['feedback'] = None

def get_feedback_and_clear():
    fb = session.get('feedback')
    session['feedback'] = None
    return fb

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    init_session()
    feedback = get_feedback_and_clear()
    return render_template('index.html',
                           score=session['score'],
                           lives=session['lives'],
                           levels_unlocked=session['levels_unlocked'],
                           feedback=feedback)

@app.route('/levels')
def levels():
    init_session()
    return render_template('levels.html',
                           levels_unlocked=session['levels_unlocked'],
                           score=session['score'],
                           lives=session['lives'])

@app.route('/start_level/<int:level>')
def start_level(level):
    if level > session.get('levels_unlocked', 1):
        return redirect(url_for('levels'))
    session['current_level'] = level
    session['current_question'] = 0
    session['lives'] = 3
    return redirect(url_for('question'))

@app.route('/question')
def question():
    init_session()
    level = session['current_level']
    q_idx = session['current_question']
    level_qs = QUESTIONS.get(level, [])

    if q_idx >= len(level_qs):
        return redirect(url_for('level_complete'))

    q = level_qs[q_idx]
    feedback = get_feedback_and_clear()
    return render_template('question.html',
                           question=q,
                           q_num=q_idx + 1,
                           total=len(level_qs),
                           score=session['score'],
                           lives=session['lives'],
                           level=level,
                           feedback=feedback)

@app.route('/answer', methods=['POST'])
def answer():
    level = session.get('current_level', 1)
    q_idx = session.get('current_question', 0)
    level_qs = QUESTIONS.get(level, [])

    if q_idx >= len(level_qs):
        return redirect(url_for('level_complete'))

    q = level_qs[q_idx]
    correct = False

    if q['type'] == 'multiple_choice':
        chosen = request.form.get('option', '-1')
        correct = (int(chosen) == q['correct'])

    elif q['type'] == 'correct_sentence':
        user_ans = request.form.get('correction', '').strip()
        correct = (user_ans.lower() == q['correct_answer'].lower())

    elif q['type'] == 'identify_elements':
        chosen = request.form.get('element', '')
        correct_ans = q['elements'][q['correct']]
        correct = (chosen == correct_ans)

    if correct:
        session['score'] = session.get('score', 0) + q['points']
        session['feedback'] = {
            'type': 'correct',
            'message': f"🎉 أحسنت! +{q['points']} نقطة",
            'explanation': q['explanation']
        }
        session['current_question'] = q_idx + 1
    else:
        session['lives'] = session.get('lives', 3) - 1
        session['feedback'] = {
            'type': 'wrong',
            'message': '❌ إجابة خاطئة! قلب واحد مفقود',
            'explanation': q['explanation']
        }
        if session['lives'] <= 0:
            return redirect(url_for('game_over'))
        session['current_question'] = q_idx + 1

    return redirect(url_for('question'))

@app.route('/level_complete')
def level_complete():
    level = session.get('current_level', 1)
    score = session.get('score', 0)

    if level >= session.get('levels_unlocked', 1):
        session['levels_unlocked'] = min(level + 1, 3)

    return render_template('level_complete.html',
                           level=level,
                           score=score,
                           has_next=(level < 3))

@app.route('/game_over')
def game_over():
    score = session.get('score', 0)
    session['score'] = 0
    session['lives'] = 3
    session['current_question'] = 0
    return render_template('game_over.html', score=score)

@app.route('/leaderboard')
def leaderboard():
    init_session()
    leaders = sorted(LEADERBOARD + [{"name": "أنت", "score": session['score'], "level": session['current_level']}],
                     key=lambda x: x['score'], reverse=True)
    return render_template('leaderboard.html', leaders=leaders, score=session['score'])

@app.route('/space')
def space():
    # Flatten all questions from all levels into one list for the shooter quiz
    all_qs = []
    for level_qs in QUESTIONS.values():
        all_qs.extend(level_qs)
    return render_template('space.html',
                           correct_sentences=json.dumps(CORRECT_SENTENCES, ensure_ascii=False),
                           incorrect_sentences=json.dumps(INCORRECT_SENTENCES, ensure_ascii=False),
                           all_questions=json.dumps(all_qs, ensure_ascii=False))

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

@app.route('/cheat/<int:level>')
def cheat(level):
    if level in (2, 3):
        current = session.get('levels_unlocked', 1)
        session['levels_unlocked'] = max(current, level)
        return jsonify({'ok': True})
    if level == 0:
        session.clear()
        return jsonify({'ok': True})
    return jsonify({'ok': False})

if __name__ == '__main__':
    app.run(debug=True)
