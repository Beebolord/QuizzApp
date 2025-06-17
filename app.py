from flask import Flask, render_template, request, session, redirect, url_for
import json
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Mapping of module names to their JSON files
MODULES = {
    'Firewall': 'Firewall.json',
    'Linux': 'Linux Part 2.json',
    'CCNA Part 1': 'ccna.json',
    'CCNA Part 2': 'ccna_2.json',
}

def load_module_quizzes(module_name):
    filepath = MODULES.get(module_name)
    if not filepath:
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['Quizzes']

@app.route('/')
def index():
    return render_template('index.html', modules=list(MODULES.keys()))

@app.route('/module/<module_name>')
def module_page(module_name):
    quizzes = load_module_quizzes(module_name)
    return render_template('module.html', module=module_name, quizzes=quizzes)

@app.route('/quiz/<module_name>/<quiz_title>/question/<int:index>', methods=['GET', 'POST'])
def question(module_name, quiz_title, index):
    session['module_name'] = module_name
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

    # First visit or new quiz
    if 'quiz_title' not in session or session.get('quiz_title') != quiz_title:
        session['quiz_title'] = quiz_title
        session['module_name'] = module_name
        session['index'] = 0
        session['score'] = 0

        # Shuffle and store questions
        shuffled = quiz['questions'][:]
        random.shuffle(shuffled)
        session['shuffled_questions'] = shuffled

    if index != session.get('index', 0):
        return redirect(url_for('question', module_name=module_name, quiz_title=quiz_title, index=session['index']))

    questions = session.get('shuffled_questions', [])
    if index >= len(questions):
        return redirect(url_for('result'))

    if request.method == 'POST':
        selected = request.form.getlist('option[]')
        print(f"✅ Selected from form: {selected}")

        current_question = questions[session['index']]
        correct_answer = current_question['correct_answer']

        # Normalize correct answers
        if isinstance(correct_answer, str):
            correct_set = set(x.strip().lower() for x in correct_answer.split(','))
        elif isinstance(correct_answer, list):
            correct_set = set(x.strip().lower() for x in correct_answer)
        else:
            correct_set = {str(correct_answer).strip().lower()}

        selected_set = set(x.strip().lower() for x in selected)

        print(f"🔍 Selected set: {selected_set}")
        print(f"✅ Correct set: {correct_set}")

        if selected_set == correct_set:
            session['score'] += 1

        session['index'] += 1

        if session['index'] >= len(questions):
            return redirect(url_for('result'))

        return redirect(url_for('question', module_name=module_name, quiz_title=quiz_title, index=session['index']))

    question_data = questions[index]
    total = len(questions)

    return render_template(
        'question.html',
        quiz_title=quiz_title,
        index=index,
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
    total = len(session.get('shuffled_questions', []))

    # Display friendly name if it's the combined quiz
    display_title = "Combined Quiz (All Questions)" if quiz_title == "__combined__" else quiz_title

    # Clear session
    session.pop('score', None)
    session.pop('quiz_title', None)
    session.pop('index', None)
    session.pop('shuffled_questions', None)

    print(f"Final score: {score} out of {total}")

    return render_template('result.html', score=score, total=total, quiz_title=display_title, module_name=module_name)

if __name__ == '__main__':
    app.run(debug=True)
