# 🧠 AI Skill Learning Hub

## 1. Introduction

AI Skill Learning Hub is an AI-powered learning platform designed to provide
personalized and interactive learning for students.

The platform allows students to select a skill, learn concepts, practice
AI-generated questions, build their knowledge, and track their learning
progress.

The system uses Generative AI to create learning content and questions based
on the selected skill and the learner's performance.

---

## 2. Objective

The main objective of the AI Skill Learning Hub is to create a personalized
learning environment where students can:

- Learn different technical skills.
- Practice concepts through interactive questions.
- Receive AI-generated learning content.
- Identify weak areas from their performance.
- Get questions according to their current level.
- Track XP, accuracy, streaks and progress.
- Improve their skills through continuous practice.

---

## 3. Problem Statement

Traditional learning platforms generally provide the same content and
difficulty level to every learner.

Students have different learning speeds and different weak areas. Therefore,
a fixed learning system may not provide an effective learning experience.

The proposed AI Skill Learning Hub solves this problem by using learner
performance to provide more personalized learning and practice.

---

## 4. Proposed Solution

The proposed system combines a web-based learning interface with Generative AI.

The learner selects a skill and starts learning or practicing.

The system records performance such as:

- Correct answers
- Incorrect answers
- Accuracy
- Current level
- Weak areas
- XP
- Streak
- Learning progress

This information is used to adapt future learning and practice activities.

---

## 5. Main Features

### 👤 User Login

The platform provides a simple user interface where learners can access
their learning environment.

### 📚 Skill Selection

Students can select an available skill or enter another skill they want to
learn.

### 📖 Learn

The Learn section provides AI-generated explanations and learning material
for the selected skill.

### 📝 Adaptive Practice

The Practice section generates questions for the selected skill.

Questions can be adjusted according to the learner's performance and level.

### 🤖 Generative AI

Gemini AI is used to generate learning content, questions and challenges.

### 🎯 Performance Analysis

The system tracks the learner's answers and calculates performance such as
accuracy and weak areas.

### 📊 Progress Tracking

The platform tracks:

- XP
- Accuracy
- Streak
- Level
- Skill progress
- Practice history

### 🛠️ Build

The Build section provides activities/challenges that help learners apply
their knowledge.

### 🎤 Voice Interaction

The platform can support voice-based answering/interaction where implemented.

---

## 6. How the AI Adapts

The platform follows an adaptive learning approach.

### Step 1: Analyse Performance

The system observes the learner's previous answers and calculates performance.

### Step 2: Identify Weak Areas

Incorrect answers are used to identify concepts where the learner needs
more practice.

### Step 3: Determine Difficulty

The learner is assigned a suitable level such as:

- Beginner
- Intermediate
- Advanced

### Step 4: Generate Content

Generative AI creates learning content, questions or challenges based on
the selected skill and learning requirements.

### Step 5: Track Progress

The learner's progress is stored and displayed through XP, accuracy,
streaks and progress information.

---

## 7. AI Logic

The project uses an adaptive rule-based approach together with Generative AI.

The basic logic is:

    User selects skill
            ↓
    System checks learner level
            ↓
    AI generates learning content/questions
            ↓
    User answers
            ↓
    System evaluates performance
            ↓
    Accuracy and weak areas are updated
            ↓
    Difficulty/content is adapted
            ↓
    Progress is stored
            ↓
    Next learning activity

The Generative AI is responsible for generating dynamic learning content,
while the application logic manages performance tracking and adaptation.

---

## 8. Technologies Used

### Frontend / Web Interface

**Streamlit**

Streamlit is used to create the interactive web interface using Python.

### Programming Language

**Python**

Python is used for application logic, data processing and integration with
AI services.

### Generative AI

**Google Gemini**

Gemini is used to generate learning explanations, questions and challenges.

### Voice

**gTTS / Voice-related libraries**

Voice functionality can be used for audio-based learning or interaction.

### Deployment

**Streamlit Community Cloud**

The application is deployed as a web application so that users can access
it through a browser.

### Version Control

**GitHub**

GitHub is used to store and manage the project source code, documentation
and screenshots.

---

## 9. System Workflow

    Start
      ↓
    User Login
      ↓
    Select Skill
      ↓
    Select Learning Activity
      ↓
    Learn / Practice / Build
      ↓
    AI Generates Content
      ↓
    User Interacts With Content
      ↓
    Evaluate Performance
      ↓
    Identify Weak Areas
      ↓
    Adapt Difficulty
      ↓
    Update Progress
      ↓
    End / Continue Learning

---

## 10. Algorithm

1. Start the application.
2. Authenticate or identify the learner.
3. Allow the learner to select a skill.
4. Retrieve the learner's current level and progress.
5. Generate appropriate learning content using Generative AI.
6. Present questions or activities to the learner.
7. Record the learner's responses.
8. Evaluate the responses.
9. Calculate performance and accuracy.
10. Identify weak areas.
11. Adjust the difficulty or learning content.
12. Update XP, streak and progress.
13. Display the updated learning status.
14. Continue the learning cycle.

---

## 11. Why Generative AI is Used

Generative AI allows the platform to create new learning content dynamically.

Instead of keeping only a fixed set of questions, the system can generate
different questions, explanations and challenges based on the selected
skill.

This makes the learning experience more flexible and interactive.

---

## 12. Role of Gemini AI

Gemini AI is used as the Generative AI component of the application.

It can help generate:

- Concept explanations
- Practice questions
- Challenges
- Learning material
- Skill-based content

The application sends appropriate prompts to the Gemini model and uses the
generated response inside the learning platform.

---

## 13. Role of Streamlit

Streamlit is used to convert the Python application into an interactive
web application.

It provides:

- Buttons
- Selection boxes
- Text input
- Progress indicators
- Navigation
- Interactive learning pages
- Dashboard components

Therefore, Streamlit acts as the main interface layer of the project.

---

## 14. Project Structure

```text
AI-Skill-Learning-Platform/
│
├── app.py
│       Main application file
│
├── requirements.txt
│       Required Python libraries
│
├── README.md
│       Project documentation
│
├── screenshots/
│       Project screenshots
│
└── .streamlit/
        Application configuration