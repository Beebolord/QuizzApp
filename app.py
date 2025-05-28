from flask import Flask, render_template, request, session, redirect, url_for
import json
import random


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # set a secure secret key for sessions

def load_quizzes():
    with open('Firewall.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['Quizzes']

@app.route('/')
def index():
    quizzes = load_quizzes()
    return render_template('index.html', quizzes=quizzes)

@app.route('/quiz/<quiz_title>/question/<int:index>', methods=['GET', 'POST'])
def question(quiz_title, index):
    quizzes = load_quizzes()
    # Find the selected quiz by title
    quiz = next((q for q in quizzes if q['quizz_title'] == quiz_title), None)
    if quiz is None:
        return "Quiz not found", 404

    if 'quiz_title' not in session or session.get('quiz_title') != quiz_title:
        # New quiz session start
        session['quiz_title'] = quiz_title
        session['index'] = 0
        session['score'] = 0

    if request.method == 'POST':
        selected_answer = request.form.get('option')
        current_question = quiz['questions'][session['index']]
        correct_answer = current_question['correct_answer']

        if selected_answer == correct_answer:
            session['score'] += 1

        session['index'] += 1

        if session['index'] >= len(quiz['questions']):
            return redirect(url_for('result'))

        return redirect(url_for('question', quiz_title=quiz_title, index=session['index']))

    # GET method - show current question
    question_data = quiz['questions'][index]

    total = len(quiz['questions']) if quiz else 0
    return render_template('question.html', quiz_title=quiz_title, index=index, question=question_data, total=total)

@app.route('/result')
def result():
    score = session.get('score', 0)
    quiz_title = session.get('quiz_title', 'Unknown Quiz')
    quizzes = load_quizzes()
    quiz = next((q for q in quizzes if q['quizz_title'] == quiz_title), None)
    total = len(quiz['questions']) if quiz else 0
    # Clear session after showing result
    session.clear()
    return render_template('result.html', score=score, total=total, quiz_title=quiz_title)

@app.route('/next', methods=['POST'])
def next_question():
    session['question_index'] = session.get('question_index', 0) + 1
    return redirect(request.referrer or url_for('home'))

@app.route('/previous', methods=['POST'])
def previous_question():
    session['question_index'] = max(session.get('question_index', 0) - 1, 0)
    return redirect(request.referrer or url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
