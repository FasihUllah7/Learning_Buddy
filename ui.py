"""
Learning Buddy Agent - Streamlit UI

Run:
  streamlit run ui.py

Requires environment variables (or .env):
  - OPENAI_API_KEY
  - OPENAI_MODEL (optional; default gpt-4o-mini)
"""

import os
import streamlit as st
from dotenv import load_dotenv

from app import generate_explanation, generate_quiz, check_answers


load_dotenv()

st.set_page_config(page_title="Learning Buddy Agent", page_icon="📘", layout="centered")

st.title("📘 Learning Buddy Agent")
st.write(
    "Enter a topic to get a short explanation and a quick quiz. "
    "Answer the questions and submit to see your score and feedback."
)

if "quiz" not in st.session_state:
    st.session_state.quiz = []
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "explanation" not in st.session_state:
    st.session_state.explanation = ""
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "score" not in st.session_state:
    st.session_state.score = None
if "feedback" not in st.session_state:
    st.session_state.feedback = []


def reset_quiz_state() -> None:
    st.session_state.quiz = []
    st.session_state.user_answers = []
    st.session_state.score = None
    st.session_state.feedback = []


topic_input = st.text_input("Topic", placeholder="e.g., Neural networks, Photosynthesis, Pythagorean theorem")

col_generate, col_clear = st.columns([2, 1])
with col_generate:
    generate_clicked = st.button("Generate Lesson + Quiz", type="primary")
with col_clear:
    if st.button("Clear"):
        st.session_state.topic = ""
        st.session_state.explanation = ""
        reset_quiz_state()
        st.experimental_rerun()

if generate_clicked and topic_input.strip():
    reset_quiz_state()
    with st.spinner("Generating explanation and quiz via OpenAI..."):
        st.session_state.topic = topic_input.strip()
        st.session_state.explanation = generate_explanation(st.session_state.topic)
        st.session_state.quiz = generate_quiz(st.session_state.topic)
        st.session_state.user_answers = ["" for _ in st.session_state.quiz]


if st.session_state.explanation:
    st.subheader("Explanation")
    st.write(st.session_state.explanation)

if st.session_state.quiz:
    st.subheader("Quiz")
    st.caption("Answer briefly. Spelling variations are okay; we check approximately.")

    for idx, qa in enumerate(st.session_state.quiz):
        st.markdown(f"**Q{idx + 1}. {qa['question']}**")
        st.session_state.user_answers[idx] = st.text_input(
            f"Your answer to Q{idx + 1}",
            value=st.session_state.user_answers[idx],
            key=f"ans_{idx}",
        )

    if st.button("Submit Answers", type="primary"):
        correct_answers = [qa["answer"] for qa in st.session_state.quiz]
        score, feedback = check_answers(st.session_state.user_answers, correct_answers)
        st.session_state.score = score
        st.session_state.feedback = feedback

if st.session_state.score is not None:
    total = len(st.session_state.quiz)
    st.subheader("Results")
    st.success(f"Score: {st.session_state.score} / {total}")

    for idx, fb in enumerate(st.session_state.feedback):
        st.markdown(f"**Q{idx + 1}:** {fb}")



