import json
import os
import time
from datetime import date, timedelta
from io import BytesIO

import streamlit as st
from google import genai
from google.genai import types

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


st.set_page_config(
    page_title="AI Skill Learning Hub",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# GEMINI
# ============================================================

MODEL_NAME = "gemini-3.8-flash"
FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite"
]

try:
    API_KEY = st.secrets["GEMINI_API_KEY"].strip()
    client = genai.Client(api_key=API_KEY)
    GEMINI_READY = True
except Exception:
    client = None
    GEMINI_READY = False


def temporary_error(e):
    text = str(e).upper()

    return any(
        x in text
        for x in (
            "503",
            "UNAVAILABLE",
            "429",
            "RESOURCE_EXHAUSTED",
            "TIMEOUT",
            "DEADLINE"
        )
    )


def ai_text(contents, config=None):
    if not GEMINI_READY:
        st.error(
            "Gemini is not configured. Check .streamlit/secrets.toml."
        )
        return None

    for model in [MODEL_NAME] + FALLBACK_MODELS:

        for attempt in range(3):

            try:
                args = {
                    "model": model,
                    "contents": contents
                }

                if config is not None:
                    args["config"] = config

                response = client.models.generate_content(**args)

                if response and response.text:
                    return response.text.strip()

            except Exception as e:

                if temporary_error(e):

                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue

                    break

                st.error(f"Gemini error: {e}")
                return None

    st.error(
        "Gemini is temporarily busy. Please try again in a few seconds."
    )

    return None


def ai_json(prompt):

    config = types.GenerateContentConfig(
        response_mime_type="application/json"
    )

    text = ai_text(prompt, config)

    if not text:
        return None

    text = text.strip()

    if text.startswith("```"):

        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        return None


# ============================================================
# DATABASE
# ============================================================

DATA_FILE = "users.json"


def new_skill():

    return {
        "attempts": 0,
        "correct": 0,
        "xp": 0,
        "lessons": 0,
        "builds": 0,
        "weak_areas": [],
        "recent_results": [],
        "question_history": []
    }


def new_user(name, email):

    return {
        "name": name,
        "email": email,
        "total_xp": 0,
        "streak": 0,
        "best_streak": 0,
        "last_active_date": "",
        "total_questions": 0,
        "total_correct": 0,
        "skills": {},
        "recent_activity": [],
        "badges": []
    }


def normalize_skill(data):

    if not isinstance(data, dict):
        return new_skill()

    defaults = new_skill()

    for key, value in defaults.items():

        if key not in data:
            data[key] = value

    return data


def normalize_user(user):

    if not isinstance(user, dict):
        return new_user("", "")

    defaults = new_user(
        user.get("name", ""),
        user.get("email", "")
    )

    for key, value in defaults.items():

        if key not in user:
            user[key] = value

    if not isinstance(user["skills"], dict):
        user["skills"] = {}

    for skill_name, skill_info in list(
        user["skills"].items()
    ):

        if not isinstance(skill_info, dict):
            user["skills"][skill_name] = new_skill()

        else:
            normalize_skill(skill_info)

    return user


def save_users(data):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2
        )


def load_users():

    if not os.path.exists(DATA_FILE):
        return {}

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, dict):
            return {}

        for email in list(data):
            data[email] = normalize_user(data[email])

        save_users(data)

        return data

    except (
        OSError,
        json.JSONDecodeError
    ):

        return {}


users = load_users()


# ============================================================
# SESSION STATE
# ============================================================

defaults = {

    "logged_in": False,
    "user_name": "",
    "user_email": "",

    "current_skill": "Python",
    "page": "🏠 Dashboard",

    "lesson": None,
    "lesson_topic": "",

    # Practice
    "practice_question": None,
    "practice_no": 0,
    "practice_score": 0,
    "practice_xp": 0,

    "practice_answered": False,
    "practice_selected": None,
    "practice_feedback": "",
    "practice_finished": False,

    "practice_voice_index": None,

    # Build
    "build_task": None,
    "build_evaluation": None,

    "study_plan": ""
}


for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


def current_user():

    email = st.session_state.user_email

    if email not in users:

        users[email] = new_user(
            st.session_state.user_name,
            email
        )

    users[email] = normalize_user(
        users[email]
    )

    save_users(users)

    return users[email]


def skill_data(skill):

    user = current_user()

    if skill not in user["skills"]:

        user["skills"][skill] = new_skill()

    user["skills"][skill] = normalize_skill(
        user["skills"][skill]
    )

    save_users(users)

    return user["skills"][skill]


# ============================================================
# ADAPTIVE ENGINE
# ============================================================

def accuracy(skill):

    data = skill_data(skill)

    if data["attempts"] == 0:
        return 0.0

    return round(
        data["correct"] /
        data["attempts"] *
        100,
        1
    )


def recent_accuracy(skill):

    results = skill_data(skill)["recent_results"]

    if not results:
        return 0.0

    return round(
        sum(results) /
        len(results) *
        100,
        1
    )


def level(skill):

    data = skill_data(skill)

    if data["attempts"] < 3:
        return "Beginner"

    score = (
        accuracy(skill) * 0.4
        +
        recent_accuracy(skill) * 0.6
    )

    if score < 45:
        return "Beginner"

    if score < 75:
        return "Intermediate"

    return "Advanced"


def weak_area(skill):

    areas = skill_data(skill).get(
        "weak_areas",
        []
    )

    if not areas:
        return "general fundamentals"

    counts = {}

    for area in areas:
        counts[area] = counts.get(
            area,
            0
        ) + 1

    return max(
        counts,
        key=counts.get
    )


def update_streak():

    user = current_user()

    today = date.today()
    today_string = str(today)

    if user.get("last_active_date") == today_string:
        return

    last = user.get(
        "last_active_date",
        ""
    )

    if last:

        try:

            previous = date.fromisoformat(last)

            if today - previous == timedelta(days=1):
                user["streak"] += 1
            else:
                user["streak"] = 1

        except ValueError:
            user["streak"] = 1

    else:
        user["streak"] = 1

    user["best_streak"] = max(
        user["best_streak"],
        user["streak"]
    )

    user["last_active_date"] = today_string

    save_users(users)


def add_xp(amount, reason):

    user = current_user()

    user["total_xp"] += amount

    user["recent_activity"].insert(
        0,
        {
            "date": str(date.today()),
            "reason": reason,
            "xp": amount
        }
    )

    user["recent_activity"] = (
        user["recent_activity"][:10]
    )

    badges = set(
        user.get("badges", [])
    )

    if user["total_xp"] >= 100:
        badges.add("100 XP")

    if user["total_xp"] >= 500:
        badges.add("500 XP")

    if user["total_questions"] >= 10:
        badges.add("10 Questions")

    if user["total_questions"] >= 50:
        badges.add("50 Questions")

    if user["best_streak"] >= 3:
        badges.add("3 Day Streak")

    if user["best_streak"] >= 7:
        badges.add("7 Day Streak")

    user["badges"] = sorted(badges)

    save_users(users)


# ============================================================
# AI FEATURES
# ============================================================

def generate_lesson(skill, topic):

    prompt = f"""
You are an expert AI tutor.

Create a simple personalized lesson
for a college student.

Skill: {skill}

Topic: {topic}

Level: {level(skill)}

Weak area: {weak_area(skill)}

Return ONLY JSON:

{{
"title":"Lesson title",
"explanation":"Clear explanation",
"example":"Practical example",
"key_points":["Point 1","Point 2","Point 3"],
"common_mistake":"One common mistake",
"quick_question":"One short question"
}}
"""

    return ai_json(prompt)


def generate_question(skill):

    data = skill_data(skill)

    history = "\n".join(
        data["question_history"][-10:]
    )

    if not history:
        history = "None"

    prompt = f"""
You are an adaptive AI tutor.

Generate ONE fresh MCQ.

Skill: {skill}

Level: {level(skill)}

Weak area: {weak_area(skill)}

Previous questions to avoid:
{history}

Return ONLY JSON:

{{
"question":"Question",
"options":["A","B","C","D"],
"correct_index":0,
"concept":"Concept",
"explanation":"Short explanation"
}}

Rules:

1. options must contain exactly 4 answers.
2. correct_index must be 0, 1, 2 or 3.
3. Only one option must be correct.
4. Do not repeat previous questions.
5. Keep the question appropriate for the current level.
"""

    question = ai_json(prompt)

    if not isinstance(question, dict):
        return None

    if not question.get("question"):
        return None

    if not isinstance(
        question.get("options"),
        list
    ):
        return None

    if len(question["options"]) != 4:
        return None

    if question.get("correct_index") not in (
        0,
        1,
        2,
        3
    ):
        return None

    return question


def generate_build(skill):

    prompt = f"""
You are an AI project mentor.

Create a small practical build challenge.

Skill: {skill}

Level: {level(skill)}

Weak area: {weak_area(skill)}

Return ONLY JSON:

{{
"title":"Challenge title",
"description":"Challenge description",
"requirements":["Requirement 1","Requirement 2","Requirement 3"],
"hint":"Helpful hint",
"expected_output":"Expected output"
}}
"""

    return ai_json(prompt)


def evaluate_build(
    skill,
    task,
    answer
):

    prompt = f"""
You are an AI coding mentor.

Evaluate this student solution.

Skill: {skill}

Challenge:
{json.dumps(task, indent=2)}

Student solution:
{answer}

Return ONLY JSON:

{{
"score":0,
"strengths":["Strength"],
"improvements":["Improvement"],
"feedback":"Overall feedback",
"next_step":"Recommended next step"
}}

Score must be from 0 to 100.
"""

    result = ai_json(prompt)

    if not isinstance(result, dict):
        return None

    try:

        result["score"] = max(
            0,
            min(
                100,
                int(result.get("score", 0))
            )
        )

    except (
        ValueError,
        TypeError
    ):

        result["score"] = 0

    return result


def transcribe_audio(audio):

    try:

        mime = getattr(
            audio,
            "type",
            None
        ) or "audio/wav"

        return ai_text(
            [
                "Transcribe this student's spoken answer. "
                "Return only the spoken answer.",

                types.Part.from_bytes(
                    data=audio.getvalue(),
                    mime_type=mime
                )
            ]
        )

    except Exception as e:

        st.error(
            f"Voice error: {e}"
        )

        return None


def voice_index(text, options):

    if not text:
        return None

    text = text.lower().strip()

    mapping = {

        "a": 0,
        "option a": 0,
        "first": 0,
        "first option": 0,

        "b": 1,
        "option b": 1,
        "second": 1,
        "second option": 1,

        "c": 2,
        "option c": 2,
        "third": 2,
        "third option": 2,

        "d": 3,
        "option d": 3,
        "fourth": 3,
        "fourth option": 3
    }

    if text in mapping:
        return mapping[text]

    for i, option in enumerate(options):

        if text == str(option).lower().strip():
            return i

    return None


def speak(text):

    if not GTTS_AVAILABLE:
        return None

    try:

        audio = BytesIO()

        gTTS(
            text=text,
            lang="en"
        ).write_to_fp(audio)

        return audio.getvalue()

    except Exception:
        return None


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.logged_in:

    st.title("🧠 AI Skill Learning Hub")

    st.subheader(
        "Learn • Practice • Build • Improve"
    )

    st.write(
        "An adaptive AI-powered learning platform for students."
    )

    st.divider()

    name = st.text_input(
        "Enter your name"
    )

    email = st.text_input(
        "Enter your email"
    )

    if st.button(
        "🚀 Start Learning",
        use_container_width=True
    ):

        if not name.strip() or not email.strip():

            st.warning(
                "Please enter your name and email."
            )

        else:

            email = email.strip().lower()

            if email not in users:

                users[email] = new_user(
                    name.strip(),
                    email
                )

            else:

                users[email] = normalize_user(
                    users[email]
                )

                users[email]["name"] = name.strip()

            save_users(users)

            st.session_state.logged_in = True
            st.session_state.user_name = (
                users[email]["name"]
            )
            st.session_state.user_email = email

            st.rerun()

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

user = current_user()

skills = [

    "Python",
    "SQL",
    "Machine Learning",
    "Data Science",
    "Data Analytics",
    "Artificial Intelligence",
    "Generative AI",
    "Deep Learning",
    "Java",
    "C",
    "C++",
    "JavaScript",
    "HTML/CSS",
    "React",
    "Node.js",
    "MongoDB",
    "DBMS",
    "Cybersecurity",
    "Cloud Computing",
    "Git & GitHub",
    "Networking",
    "Operating Systems",
    "Aptitude",
    "English Communication",
    "Interview Preparation"
]


with st.sidebar:

    st.title("🧠 AI Skill Hub")

    st.write(
        f"Welcome, **{user['name']}**"
    )

    selected_skill = st.selectbox(
        "🎯 Select Skill",
        skills,
        index=(
            skills.index(
                st.session_state.current_skill
            )
            if st.session_state.current_skill in skills
            else 0
        )
    )

    st.session_state.current_skill = selected_skill

    custom_skill = st.text_input(
        "Or enter another skill"
    )

    if custom_skill.strip():
        st.session_state.current_skill = (
            custom_skill.strip()
        )

    st.divider()

    pages = [
        "🏠 Dashboard",
        "🎓 Learn",
        "🧠 Practice",
        "💻 Build",
        "📊 My Progress"
    ]

    st.session_state.page = st.radio(
        "Navigation",
        pages,
        index=pages.index(
            st.session_state.page
        )
    )

    st.divider()

    if st.button(
        "🔄 Reset Practice",
        use_container_width=True
    ):

        st.session_state.practice_question = None
        st.session_state.practice_no = 0
        st.session_state.practice_score = 0
        st.session_state.practice_xp = 0

        st.session_state.practice_answered = False
        st.session_state.practice_selected = None
        st.session_state.practice_feedback = ""
        st.session_state.practice_finished = False
        st.session_state.practice_voice_index = None

        st.rerun()

    if st.button(
        "🚪 Sign Out",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.rerun()


skill = st.session_state.current_skill


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "🏠 Dashboard":

    st.title("🧠 AI Skill Learning Hub")

    st.subheader(
        f"Welcome back, {user['name']}!"
    )

    st.write(
        "Your AI tutor adapts learning content to your performance."
    )

    st.divider()

    a, b, c, d = st.columns(4)

    a.metric(
        "⭐ Total XP",
        user["total_xp"]
    )

    b.metric(
        "🔥 Streak",
        f"{user['streak']} days"
    )

    c.metric(
        "🎯 Accuracy",
        f"{accuracy(skill)}%"
    )

    d.metric(
        "📈 Level",
        level(skill)
    )

    st.divider()

    x, y, z = st.columns(3)

    x.info(
        f"Current skill\n\n**{skill}**"
    )

    y.info(
        f"Current level\n\n**{level(skill)}**"
    )

    z.info(
        f"Weak area\n\n**{weak_area(skill)}**"
    )

    st.divider()

    st.subheader(
        "How the AI adapts"
    )

    st.write(
        """
**1. Analyse performance** — accuracy and recent answers are tracked.

**2. Identify weak areas** — incorrect answers are linked to concepts.

**3. Adapt difficulty** — the system selects Beginner, Intermediate or Advanced.

**4. Generate content** — Gemini creates lessons, questions and challenges.

**5. Track progress** — XP, streaks, badges and skill progress are saved.
"""
    )

    st.success(
        "Choose Learn, Practice or Build from the sidebar."
    )


# ============================================================
# LEARN
# ============================================================

elif st.session_state.page == "🎓 Learn":

    st.title("🎓 AI Learn")

    st.write(
        f"Learn **{skill}** with an AI tutor."
    )

    topic = st.text_input(
        "What do you want to learn?",
        placeholder="Example: SQL joins"
    )

    if st.button(
        "✨ Generate AI Lesson",
        use_container_width=True
    ):

        if not topic.strip():

            st.warning(
                "Please enter a topic."
            )

        else:

            with st.spinner(
                "🤖 AI tutor is preparing your lesson..."
            ):

                result = generate_lesson(
                    skill,
                    topic.strip()
                )

            if result:

                st.session_state.lesson = result
                st.session_state.lesson_topic = (
                    topic.strip()
                )

                skill_data(skill)["lessons"] += 1

                add_xp(
                    10,
                    f"Lesson: {topic.strip()}"
                )

                st.rerun()

    lesson = st.session_state.lesson

    if lesson:

        st.divider()

        st.header(
            lesson.get(
                "title",
                "AI Lesson"
            )
        )

        st.write(
            lesson.get(
                "explanation",
                ""
            )
        )

        st.subheader("💡 Example")

        st.info(
            lesson.get(
                "example",
                ""
            )
        )

        st.subheader("📌 Key Points")

        for point in lesson.get(
            "key_points",
            []
        ):

            st.write(
                f"• {point}"
            )

        st.subheader(
            "⚠️ Common Mistake"
        )

        st.warning(
            lesson.get(
                "common_mistake",
                ""
            )
        )

        st.subheader(
            "🧠 Quick Check"
        )

        st.write(
            lesson.get(
                "quick_question",
                ""
            )
        )

        answer = st.text_input(
            "Your answer",
            key="lesson_answer"
        )

        if st.button(
            "Check Answer"
        ):

            feedback = ai_text(
                f"""
You are an AI tutor.

Question:
{lesson.get("quick_question", "")}

Student answer:
{answer}

Give short friendly feedback and explain briefly.
"""
            )

            if feedback:
                st.info(feedback)


# ============================================================
# PRACTICE
# ============================================================

# ============================================================
# PRACTICE
# ============================================================

elif st.session_state.page == "🧠 Practice":

    st.title("🧠 Adaptive Practice")

    st.write(
        f"Skill: **{skill}** | "
        f"Level: **{level(skill)}** | "
        f"Weak area: **{weak_area(skill)}**"
    )

    st.info(
        "The AI uses your performance to adapt future questions."
    )

    # --------------------------------------------------------
    # FINISHED
    # --------------------------------------------------------

    if st.session_state.practice_finished:

        st.success(
            f"Practice complete! "
            f"Score: {st.session_state.practice_score}/5"
        )

        st.metric(
            "Session XP",
            st.session_state.practice_xp
        )

        if st.button(
            "🔄 Start New Practice",
            use_container_width=True
        ):
            st.session_state.practice_question = None
            st.session_state.practice_no = 0
            st.session_state.practice_score = 0
            st.session_state.practice_xp = 0
            st.session_state.practice_answered = False
            st.session_state.practice_selected = None
            st.session_state.practice_feedback = ""
            st.session_state.practice_finished = False
            st.session_state.practice_voice_index = None

            st.rerun()

    else:

        # ----------------------------------------------------
        # GENERATE QUESTION
        # ----------------------------------------------------

        if st.session_state.practice_question is None:

            with st.spinner(
                "🤖 Generating a personalized question..."
            ):
                question = generate_question(skill)

            if question:
                st.session_state.practice_question = question

            else:
                st.warning(
                    "The AI could not create a question. "
                    "Please try again."
                )

        question = st.session_state.practice_question

        if question:

            question_number = (
                st.session_state.practice_no + 1
            )

            st.subheader(
                f"Question {question_number} of 5"
            )

            st.write(
                question["question"]
            )

            # ------------------------------------------------
            # ANSWER SELECTION
            # ------------------------------------------------

            if not st.session_state.practice_answered:

                selected = st.selectbox(
                    "Choose your answer:",
                    question["options"],
                    index=None,
                    placeholder="Select an option...",
                    key=f"answer_{question_number}"
                )

                # ------------------------------------------------
                # VOICE ANSWER
                # ------------------------------------------------

                audio = st.audio_input(
                    "🎤 Or record your answer",
                    key=f"audio_{question_number}"
                )

                if audio:

                    if st.button(
                        "🎤 Convert Voice Answer",
                        key=f"voice_{question_number}"
                    ):

                        with st.spinner(
                            "🎤 Converting your answer..."
                        ):
                            transcript = transcribe_audio(audio)

                        if transcript:

                            st.info(
                                f"You said: {transcript}"
                            )

                            index = voice_index(
                                transcript,
                                question["options"]
                            )

                            if index is not None:

                                st.session_state.practice_voice_index = index

                                st.success(
                                    f"Voice answer detected: "
                                    f"Option {chr(65 + index)}"
                                )

                            else:

                                st.warning(
                                    "Please say A, B, C, D, "
                                    "or the exact option text."
                                )

                # ------------------------------------------------
                # SUBMIT ANSWER
                # ------------------------------------------------

                if st.button(
                    "✅ Submit Answer",
                    use_container_width=True
                ):

                    # Use voice answer if available
                    if (
                        st.session_state.practice_voice_index
                        is not None
                    ):

                        selected_index = (
                            st.session_state.practice_voice_index
                        )

                    elif selected is not None:

                        selected_index = (
                            question["options"].index(selected)
                        )

                    else:

                        st.warning(
                            "⚠️ Please select an option first."
                        )
                        st.stop()

                    correct_index = question["correct_index"]

                    is_correct = (
                        selected_index == correct_index
                    )

                    # Save answer state
                    st.session_state.practice_answered = True
                    st.session_state.practice_selected = selected_index

                    # ------------------------------------------------
                    # CREATE FEEDBACK
                    # ------------------------------------------------

                    selected_letter = chr(
                        65 + selected_index
                    )

                    correct_letter = chr(
                        65 + correct_index
                    )

                    correct_answer = question["options"][
                        correct_index
                    ]

                    explanation = question.get(
                        "explanation",
                        "This is the correct answer based on the concept."
                    )

                    if is_correct:

                        st.session_state.practice_feedback = (
                            f"Option {selected_letter} is correct!\n\n"
                            f"Why: {explanation}"
                        )

                        st.session_state.practice_score += 1
                        st.session_state.practice_xp += 20

                    else:

                        st.session_state.practice_feedback = (
                            f"Option {selected_letter} is wrong.\n\n"
                            f"Option {correct_letter} is correct.\n\n"
                            f"Correct answer: {correct_answer}\n\n"
                            f"Why: {explanation}"
                        )

                    # ------------------------------------------------
                    # UPDATE SKILL DATA
                    # ------------------------------------------------

                    data = skill_data(skill)

                    data["attempts"] += 1

                    data["correct"] += int(
                        is_correct
                    )

                    data["recent_results"].append(
                        int(is_correct)
                    )

                    data["recent_results"] = (
                        data["recent_results"][-10:]
                    )

                    if not is_correct:

                        data["weak_areas"].append(
                            question.get(
                                "concept",
                                "general"
                            )
                        )

                        data["weak_areas"] = (
                            data["weak_areas"][-20:]
                        )

                    data["question_history"].append(
                        question["question"]
                    )

                    data["question_history"] = (
                        data["question_history"][-30:]
                    )

                    # ------------------------------------------------
                    # UPDATE USER DATA
                    # ------------------------------------------------

                    user = current_user()

                    user["total_questions"] += 1

                    user["total_correct"] += int(
                        is_correct
                    )

                    update_streak()

                    save_users(users)

            # --------------------------------------------------------
            # RESULT — ONLY AFTER SUBMIT
            # --------------------------------------------------------

            if st.session_state.practice_answered:

                selected_index = (
                    st.session_state.practice_selected
                )

                correct_index = question["correct_index"]

                selected_letter = chr(
                    65 + selected_index
                )

                correct_letter = chr(
                    65 + correct_index
                )

                correct_answer = question["options"][
                    correct_index
                ]

                explanation = question.get(
                    "explanation",
                    "This option matches the concept being tested."
                )

                st.divider()

                # ------------------------------------------------
                # CORRECT ANSWER
                # ------------------------------------------------

                if selected_index == correct_index:

                    st.success(
                        f"✅ Option {selected_letter} is correct!"
                    )

                    st.markdown(
                        f"### 💡 Why?\n{explanation}"
                    )

                # ------------------------------------------------
                # WRONG ANSWER
                # ------------------------------------------------

                else:

                    st.error(
                        f"❌ Option {selected_letter} is wrong."
                    )

                    st.success(
                        f"✅ Option {correct_letter} is correct!"
                    )

                    st.markdown(
                        f"**Correct answer:** "
                        f"Option {correct_letter} — "
                        f"{correct_answer}"
                    )

                    st.markdown(
                        f"### 💡 Why is Option {correct_letter} correct?\n"
                        f"{explanation}"
                    )

                # ------------------------------------------------
                # LISTEN TO FEEDBACK
                # ------------------------------------------------

                if st.button(
                    "🔊 Listen to Feedback",
                    key=f"listen_{question_number}"
                ):

                    audio_bytes = speak(
                        st.session_state.practice_feedback
                    )

                    if audio_bytes:

                        st.audio(
                            audio_bytes,
                            format="audio/mp3"
                        )

                    else:

                        st.info(
                            "Text-to-speech is unavailable."
                        )

                # ------------------------------------------------
                # NEXT QUESTION
                # ------------------------------------------------

                if question_number < 5:

                    if st.button(
                        "➡️ Next Question",
                        use_container_width=True
                    ):

                        st.session_state.practice_no += 1
                        st.session_state.practice_question = None
                        st.session_state.practice_answered = False
                        st.session_state.practice_selected = None
                        st.session_state.practice_feedback = ""
                        st.session_state.practice_voice_index = None

                        st.rerun()

                # ------------------------------------------------
                # FINISH PRACTICE
                # ------------------------------------------------

                else:

                    if st.button(
                        "🏁 Finish Practice",
                        use_container_width=True
                    ):

                        add_xp(
                            st.session_state.practice_xp,
                            f"{skill} practice session"
                        )

                        st.session_state.practice_finished = True

                        save_users(users)

                        st.rerun()


# ============================================================
# BUILD
# ============================================================

elif st.session_state.page == "💻 Build":

    st.title("💻 AI Build Challenge")

    st.write(
        f"Build a practical challenge using **{skill}**."
    )

    if st.button(
        "🚀 Generate Build Challenge",
        use_container_width=True
    ):

        with st.spinner(
            "🤖 AI mentor is creating a challenge..."
        ):

            task = generate_build(skill)

        if task:

            st.session_state.build_task = task

            st.session_state.build_evaluation = None

            st.rerun()

    task = st.session_state.build_task

    if task:

        st.divider()

        st.header(
            task.get(
                "title",
                "Build Challenge"
            )
        )

        st.write(
            task.get(
                "description",
                ""
            )
        )

        st.subheader(
            "📋 Requirements"
        )

        for requirement in task.get(
            "requirements",
            []
        ):

            st.write(
                f"• {requirement}"
            )

        st.subheader(
            "💡 Hint"
        )

        st.info(
            task.get(
                "hint",
                ""
            )
        )

        st.subheader(
            "Expected Output"
        )

        st.write(
            task.get(
                "expected_output",
                ""
            )
        )

        answer = st.text_area(
            "Paste or write your solution here",
            height=250
        )

        if st.button(
            "🤖 Evaluate My Solution",
            use_container_width=True
        ):

            if not answer.strip():

                st.warning(
                    "Please enter your solution first."
                )

            else:

                with st.spinner(
                    "🤖 AI is evaluating your solution..."
                ):

                    result = evaluate_build(
                        skill,
                        task,
                        answer
                    )

                if result:

                    st.session_state.build_evaluation = result

                    skill_data(skill)["builds"] += 1

                    add_xp(
                        25,
                        f"Build: {task.get('title', '')}"
                    )

                    st.rerun()

    evaluation = st.session_state.build_evaluation

    if evaluation:

        st.divider()

        st.subheader(
            "📊 AI Evaluation"
        )

        st.metric(
            "Score",
            f"{evaluation.get('score', 0)}/100"
        )

        st.subheader(
            "💪 Strengths"
        )

        for item in evaluation.get(
            "strengths",
            []
        ):

            st.write(
                f"• {item}"
            )

        st.subheader(
            "🔧 Improvements"
        )

        for item in evaluation.get(
            "improvements",
            []
        ):

            st.write(
                f"• {item}"
            )

        st.subheader(
            "🤖 AI Feedback"
        )

        st.info(
            evaluation.get(
                "feedback",
                ""
            )
        )

        st.subheader(
            "➡️ Next Step"
        )

        st.success(
            evaluation.get(
                "next_step",
                ""
            )
        )


# ============================================================
# PROGRESS
# ============================================================

elif st.session_state.page == "📊 My Progress":

    st.title("📊 My Progress")

    user = current_user()

    if "skills" not in user:
        user["skills"] = {}
        save_users(users)

    total = user["total_questions"]

    overall = (
        round(
            user["total_correct"] /
            total *
            100,
            1
        )
        if total
        else 0.0
    )

    a, b, c, d = st.columns(4)

    a.metric(
        "⭐ XP",
        user["total_xp"]
    )

    b.metric(
        "📝 Questions",
        total
    )

    c.metric(
        "🎯 Accuracy",
        f"{overall}%"
    )

    d.metric(
        "🔥 Best Streak",
        f"{user['best_streak']} days"
    )

    st.divider()

    st.subheader(
        "🎯 Skill Progress"
    )

    if user.get("skills"):

        for name, data in user.get(
            "skills",
            {}
        ).items():

            normalize_skill(data)

            acc = (
                data["correct"] /
                data["attempts"]
                if data["attempts"]
                else 0
            )

            st.write(
                f"**{name}**"
            )

            st.progress(
                min(
                    max(
                        acc,
                        0.0
                    ),
                    1.0
                )
            )

            st.caption(
                f"Level: {level(name)} | "
                f"Accuracy: {acc * 100:.1f}% | "
                f"Lessons: {data['lessons']} | "
                f"Builds: {data['builds']}"
            )

    else:

        st.info(
            "Start learning to see your progress."
        )

    st.divider()

    st.subheader(
        "🏅 Badges"
    )

    if user.get("badges"):

        for badge in user["badges"]:

            st.success(
                f"🏆 {badge}"
            )

    else:

        st.info(
            "Complete activities to unlock badges."
        )

    st.divider()

    st.subheader(
        "⚠️ Weak Areas"
    )

    found = False

    for name, data in user.get(
        "skills",
        {}
    ).items():

        areas = data.get(
            "weak_areas",
            []
        )

        if areas:

            found = True

            unique_areas = list(
                dict.fromkeys(areas)
            )

            st.write(
                f"**{name}:** "
                + ", ".join(
                    unique_areas[:5]
                )
            )

    if not found:

        st.success(
            "No major weak areas detected yet."
        )

    st.divider()

    st.subheader(
        "📅 Recent Activity"
    )

    if user.get("recent_activity"):

        for item in user["recent_activity"]:

            st.write(
                f"**{item['date']}** — "
                f"{item['reason']} "
                f"(+{item['xp']} XP)"
            )

    else:

        st.info(
            "Your activity will appear here."
        )

    st.divider()

    st.subheader(
        "🤖 AI Study Recommendation"
    )

    if st.button(
        "Generate My 7-Day Study Plan",
        use_container_width=True
    ):

        prompt = f"""
Create a practical 7-day study plan
for a college student.

Skill: {skill}

Level: {level(skill)}

Weak area: {weak_area(skill)}

Accuracy: {accuracy(skill)}%

Give Day 1 through Day 7
with short tasks.
"""

        with st.spinner(
            "🤖 Creating your study plan..."
        ):

            plan = ai_text(prompt)

        if plan:
            st.session_state.study_plan = plan

    if st.session_state.study_plan:

        st.info(
            st.session_state.study_plan
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🧠 AI Skill Learning Hub | "
    "Adaptive Learning • Gemini AI • Voice • Progress Tracking"
)
