from flask import Flask, render_template, request, session, redirect, url_for
import json
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

MODULES = {
    'CYSA': 'cysa.json',
    'Firewall': 'Firewall.json',
    'Linux': 'Linux Part 2.json',
    'CCNA Part 1': 'ccna.json',
    'CCNA Part 2': 'ccna_2.json',
    'Ethical Hacking And Countermeasure ': 'EHCM.json'
}

def load_module_quizzes(module_name):
    filepath = MODULES.get(module_name)
    if not filepath:
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    quizzes = data.get('Quizzes', [])
    # Ensure all required fields exist
    for quiz in quizzes:
        for q in quiz.get('questions', []):
            q.setdefault('answer', [])
            q.setdefault('correct_answer', '')
            q.setdefault('explanation', '')
    return quizzes

@app.route('/')
def index():
    return render_template('index.html', modules=list(MODULES.keys()))

@app.route('/module/<module_name>')
def module_page(module_name):
    quizzes = load_module_quizzes(module_name)
    return render_template('module.html', module=module_name, quizzes=quizzes)

@app.route('/quiz/<module_name>/<quiz_title>/question/<int:index>', methods=['GET', 'POST'])
def question(module_name, quiz_title, index):
    quizzes = load_module_quizzes(module_name)

    # Combined Quiz Mode
    if quiz_title == "__combined__":
        all_questions = []
        for q in quizzes:
            all_questions.extend(q.get('questions', []))
        quiz = {"quizz_title": "Combined Quiz", "questions": all_questions}
    else:
        quiz = next((q for q in quizzes if q['quizz_title'] == quiz_title), None)
        if not quiz:
            return "Quiz not found", 404

    # Initialize session
    if 'quiz_title' not in session or session.get('quiz_title') != quiz_title:
        session['quiz_title'] = quiz_title
        session['module_name'] = module_name
        session['index'] = 0
        session['score'] = 0

        # Store only shuffled **indices** to avoid large session cookie
        question_count = len(quiz['questions'])
        shuffled_indices = list(range(question_count))
        random.shuffle(shuffled_indices)
        session['shuffled_indices'] = shuffled_indices

    shuffled_indices = session['shuffled_indices']
    total = len(shuffled_indices)

    # Ensure index matches session
    if index != session.get('index', 0):
        return redirect(url_for('question', module_name=module_name, quiz_title=quiz_title, index=session['index']))

    if index >= total:
        return redirect(url_for('result'))

    current_index = shuffled_indices[index]
    question_data = quiz['questions'][current_index]

    if request.method == 'POST':
        selected = request.form.getlist('option[]')
        correct_answer = question_data['correct_answer']

        if isinstance(correct_answer, str):
            correct_set = set(x.strip().lower() for x in correct_answer.split(','))
        elif isinstance(correct_answer, list):
            correct_set = set(x.strip().lower() for x in correct_answer)
        else:
            correct_set = {str(correct_answer).strip().lower()}

        selected_set = set(x.strip().lower() for x in selected)

        if selected_set == correct_set:
            session['score'] += 1

        session['index'] += 1

        if session['index'] >= total:
            return redirect(url_for('result'))

        return redirect(url_for('question', module_name=module_name, quiz_title=quiz_title, index=session['index']))

    return render_template(
        'question.html',
        quiz_title=quiz_title,
        index=index + 1,  # 1-based display
        question=question_data,
        total=total,
        module_name=module_name,
        score=session.get('score', 0)
    )

@app.route('/result')
def result():
    score = session.get('score', 0)
    quiz_title = session.get('quiz_title', 'Unknown Quiz')
    module_name = session.get('module_name', 'default_module')
    total = len(session.get('shuffled_indices', []))

    display_title = "Combined Quiz (All Questions)" if quiz_title == "__combined__" else quiz_title

    # Clear session
    session.pop('score', None)
    session.pop('quiz_title', None)
    session.pop('index', None)
    session.pop('shuffled_indices', None)

    return render_template('result.html', score=score, total=total, quiz_title=display_title, module_name=module_name)

if __name__ == '__main__':
    app.run(debug=True)
