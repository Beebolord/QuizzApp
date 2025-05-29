from flask import Flask, render_template, request, session, redirect, url_for
import json
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Mapping of module names to their JSON files
MODULES = {
    'Firewall': 'Firewall.json',
    'Linux': 'Linux Part 2.json'
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
    quiz = next((q for q in quizzes if q['quizz_title'] == quiz_title), None)
    if not quiz:
        return "Quiz not found", 404

    if 'quiz_title' not in session or session.get('quiz_title') != quiz_title:
        session['quiz_title'] = quiz_title
        session['module'] = module_name
        session['index'] = 0
        session['score'] = 0

    if request.method == 'POST':
        selected = request.form.getlist('option[]')  # ✅ handles checkboxes
        current_question = quiz['questions'][session['index']]
        correct_answer = current_question['correct_answer']

        # Normalize both selected and correct to sets of strings
        if isinstance(correct_answer, str):
            correct_set = set([x.strip() for x in correct_answer.split(',')])
        elif isinstance(correct_answer, list):
            correct_set = set([x.strip() for x in correct_answer])
        else:
            correct_set = set([str(correct_answer)])

        selected_set = set([x.strip() for x in selected])

        if selected_set == correct_set:
            session['score'] += 1

        session['index'] += 1
        if session['index'] >= len(quiz['questions']):
            return redirect(url_for('result'))

        return redirect(url_for('question', module_name=module_name, quiz_title=quiz_title, index=session['index']))
    question_data = quiz['questions'][index]
    total = len(quiz['questions']) if quiz else 0
    return render_template(
        'question.html',
        quiz_title=quiz_title,
        index=index,
        question=question_data,
        total=total,
        module_name=module_name  # Make sure you pass this so templates can use it
    )
@app.route('/result')
def result():
    score = session.get('score', 0)
    quiz_title = session.get('quiz_title', 'Unknown Quiz')
    module_name = session.get('module_name', 'default_module')

    quizzes = load_module_quizzes(module_name)
    quiz = next((q for q in quizzes if q['quizz_title'] == quiz_title), None)
    total = len(quiz['questions']) if quiz else 0

    # Clear session except for module name
    session.pop('score', None)
    session.pop('quiz_title', None)
    session.pop('index', None)

    return render_template('result.html', score=score, total=total, quiz_title=quiz_title, module_name=module_name)

if __name__ == '__main__':
    app.run(debug=True)
