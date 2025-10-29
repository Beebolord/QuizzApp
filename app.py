from flask import Flask, render_template, request, session, redirect, url_for
import json
import glob
import random
from openai import OpenAI
import os

app = Flask(__name__)
key = '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'
client = OpenAI(api_key=key)

MODULES = {
    'Ethical Hacking And Countermeasure ': 'EHCM.json',
    'CYSA': 'cysa.json',
    'Firewall': 'Firewall.json',
    'Linux': 'Linux Part 2.json',
    'CCNA Part 1': 'ccna.json',
    'CCNA Part 2': 'ccna_2.json',
}
def get_all_modules():
    """
    Scan /quizz for *.json and group into modules.
    Handles BOTH formats:
      A) {"Quizzes": [ {...}, {...} ]}
      B) {"quizz_title": "...", "questions": [...]}
    Module name is derived from quizz_title up to the first dot, or the full title if no dot.
    """
    modules = {}
    for path in glob.glob("quizz/*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # New format: single quiz
            if "quizz_title" in data and "questions" in data:
                quizzes = [data]
            # Old format: bundled quizzes
            elif "Quizzes" in data and isinstance(data["Quizzes"], list):
                quizzes = data["Quizzes"]
            else:
                continue  # skip unknown format

            for q in quizzes:
                title = q.get("quizz_title", "Untitled Quiz")
                # Module name: before first '.' if present, else the whole title
                dot = title.find(".")
                module_name = title[:dot].strip() if dot != -1 else title.strip()
                modules.setdefault(module_name, []).append(q)

        except Exception as e:
            print(f"[get_all_modules] error reading {path}: {e}")

    return modules

def load_module_quizzes(module_name: str):
    """Return a list of quiz dicts for a given module name."""
    modules = get_all_modules()
    return modules.get(module_name, [])
@app.route('/')
def index():
    modules = get_all_modules()
    return render_template('index.html', modules=list(modules.keys()))

@app.route('/module/<module_name>')
def module_page(module_name):
    modules = get_all_modules()
    quizzes = modules.get(module_name, [])
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
    total = len(session.get('shuffled_indices', []))

    display_title = "Combined Quiz (All Questions)" if quiz_title == "__combined__" else quiz_title

    # Clear session
    session.pop('score', None)
    session.pop('quiz_title', None)
    session.pop('index', None)
    session.pop('shuffled_indices', None)

    return render_template('result.html', score=score, total=total, quiz_title=display_title, module_name=module_name)



@app.route("/add_quiz", methods=["GET", "POST"])
def add_quiz():
    if request.method == "POST":
        quiz_title = request.form.get("quiz_title", "").strip() or "Untitled Quiz"
        questions = request.form.get("questions", "").strip()
        answers = request.form.get("answers", "").strip()

        if not questions or not answers:
            return render_template(
                "add_quiz.html",
                quiz_title=quiz_title,
                raw_text=questions,
                json_output="⚠️ Please enter both questions and answers before sending.",
            )

        # Build the prompt for GPT
        prompt = f"""
        Format the following questions and answers into a JSON quiz object that follows this structure:
        {{
          "quizz_title": "{quiz_title}",
          "questions": [
            {{
              "question": "...",
              "answer": ["...","...","..."],
              "correct_answer": "...",
              "explanation": "..."
            }}
          ]
        }}

        Requirements:
        - Return ONLY valid JSON (no markdown, code fences, or text outside it).
        - Include all questions and answers.
        - Combine multiple correct answers in 'correct_answer' separated by spaces.
        - Write short, clear explanations for each question.

        Questions:
        {questions}

        Answers:
        {answers}
        """

        # Send to OpenAI
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that formats quizzes into clean JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            formatted_output = response.choices[0].message.content.strip()

            # Try parsing to ensure it's valid JSON
            try:
                quiz_data = json.loads(formatted_output)
            except json.JSONDecodeError:
                # Try to recover if the model returns wrapped JSON (e.g. ```json ... ```)
                formatted_output = formatted_output.strip("` \n")
                start = formatted_output.find("{")
                end = formatted_output.rfind("}") + 1
                quiz_data = json.loads(formatted_output[start:end])

            # Save to /quizz folder
            os.makedirs("quizz", exist_ok=True)
            safe_title = "".join(c for c in quiz_title if c.isalnum() or c in (" ", "_", "-")).strip()
            filename = f"quizz/{safe_title or 'Untitled_Quiz'}.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(quiz_data, f, indent=4, ensure_ascii=False)

            save_message = f"✅ Saved quiz to: {filename}"

        except Exception as e:
            formatted_output = f"⚠️ Error: {str(e)}"
            save_message = ""

        return render_template(
            "add_quiz.html",
            quiz_title=quiz_title,
            raw_text=questions,
            json_output=f"{formatted_output}\n\n{save_message}\n\n"
                        f'<a href="/module/{quiz_title}" '
                        f'style="display:inline-block;margin-top:15px;'
                        f'background-color:#007bff;color:white;'
                        f'padding:10px 20px;border-radius:6px;text-decoration:none;">'
                        f'Take Quiz</a>'
        )

    # GET request
    return render_template("add_quiz.html", quiz_title="", raw_text="", json_output="")
if __name__ == '__main__':
    app.run(debug=True)
