from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'al-khwarizmi-secret-2025'
app.jinja_env.globals['enumerate'] = enumerate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_questions():
    with open(os.path.join(BASE_DIR, 'questions.json'), encoding='utf-8') as f:
        data = json.load(f)
    return (
        data['correct_sentences'],
        data['incorrect_sentences'],
        {int(k): v for k, v in data['questions'].items()},
        data['space_questions']
    )

CORRECT_SENTENCES, INCORRECT_SENTENCES, QUESTIONS, SPACE_QUESTIONS = load_questions()

LEADERBOARD_FILE = os.path.join(BASE_DIR, 'leaderboard.json')

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, encoding='utf-8') as f:
            return json.load(f)
    return []

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def init_session():
    if 'score'            not in session: session['score']            = 0
    if 'lives'            not in session: session['lives']            = 3
    if 'current_level'    not in session: session['current_level']    = 1
    if 'current_question' not in session: session['current_question'] = 0
    if 'levels_unlocked'  not in session: session['levels_unlocked']  = 1
    if 'feedback'         not in session: session['feedback']         = None

def get_feedback_and_clear():
    fb = session.get('feedback')
    session['feedback'] = None
    return fb

@app.route('/')
def index():
    init_session()
    return render_template('index.html',
                           score=session['score'],
                           lives=session['lives'],
                           levels_unlocked=session['levels_unlocked'],
                           feedback=get_feedback_and_clear())

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
    session['current_level']    = level
    session['current_question'] = 0
    session['lives']            = 3
    return redirect(url_for('question'))

@app.route('/question')
def question():
    init_session()
    level    = session['current_level']
    q_idx    = session['current_question']
    level_qs = QUESTIONS.get(level, [])
    if q_idx >= len(level_qs):
        return redirect(url_for('level_complete'))
    return render_template('question.html',
                           question=level_qs[q_idx],
                           q_num=q_idx + 1,
                           total=len(level_qs),
                           score=session['score'],
                           lives=session['lives'],
                           level=level,
                           feedback=get_feedback_and_clear())

@app.route('/answer', methods=['POST'])
def answer():
    level    = session.get('current_level', 1)
    q_idx    = session.get('current_question', 0)
    level_qs = QUESTIONS.get(level, [])
    if q_idx >= len(level_qs):
        return redirect(url_for('level_complete'))
    q       = level_qs[q_idx]
    correct = False
    if q['type'] == 'multiple_choice':
        correct = (int(request.form.get('option', '-1')) == q['correct'])
    elif q['type'] == 'correct_sentence':
        correct = (request.form.get('correction', '').strip() == q['correct_answer'])
    elif q['type'] == 'identify_elements':
        correct = (request.form.get('element', '') == q['elements'][q['correct']])
    if correct:
        session['score'] = session.get('score', 0) + q['points']
        session['feedback'] = {'type': 'correct',
                               'message': f"أحسنت! +{q['points']} نقطة",
                               'explanation': q['explanation']}
    else:
        session['lives'] = session.get('lives', 3) - 1
        session['feedback'] = {'type': 'wrong',
                               'message': 'إجابة خاطئة! قلب واحد مفقود',
                               'explanation': q['explanation']}
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
    return render_template('level_complete.html', level=level, score=score, has_next=(level < 3))

@app.route('/game_over')
def game_over():
    score                       = session.get('score', 0)
    session['score']            = 0
    session['lives']            = 3
    session['current_question'] = 0
    return render_template('game_over.html', score=score)

@app.route('/leaderboard')
def leaderboard():
    init_session()
    leaders = sorted(load_leaderboard(), key=lambda x: x['score'], reverse=True)
    return render_template('leaderboard.html', leaders=leaders, score=session['score'])

@app.route('/leaderboard/submit', methods=['POST'])
def leaderboard_submit():
    name  = request.form.get('name', '').strip()
    score = session.get('score', 0)
    if not name or score <= 0:
        return redirect(url_for('leaderboard'))
    leaders = load_leaderboard()
    existing = next((e for e in leaders if e['name'] == name), None)
    if existing:
        if score > existing['score']:
            existing['score'] = score
            existing['level'] = session.get('current_level', 1)
    else:
        leaders.append({'name': name, 'score': score, 'level': session.get('current_level', 1)})
    save_leaderboard(leaders)
    return redirect(url_for('leaderboard'))

@app.route('/space')
def space():
    all_qs = list(SPACE_QUESTIONS) + [q for qs in QUESTIONS.values() for q in qs]
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
        session['levels_unlocked'] = max(session.get('levels_unlocked', 1), level)
        return jsonify({'ok': True})
    if level == 0:
        session.clear()
        return jsonify({'ok': True})
    return jsonify({'ok': False})

if __name__ == '__main__':
    app.run(debug=True)
