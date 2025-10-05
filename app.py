"""
Learning Buddy Agent - Core logic (OpenAI only)

This module exposes the required functions:
  - generate_explanation(topic)
  - generate_quiz(topic)
  - check_answers(user_answers, correct_answers)

It uses the OpenAI Chat Completions API via the official SDK (>=1.0).
Configuration is read from environment variables (optionally via .env):
  - OPENAI_API_KEY (required)
  - OPENAI_MODEL (default: gpt-4o-mini)
"""

import json
import os
import re
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables from .env if present
load_dotenv()


def _call_openai_chat(messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 500) -> str:
    """Call OpenAI chat completions and return the assistant content text."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Please add it to your .env or environment.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()  # type: ignore[attr-defined]


def generate_explanation(topic: str) -> str:
    """Generate a short, beginner-friendly explanation for a topic using OpenAI."""
    topic = topic.strip()
    system = (
        "You are a friendly teacher. Explain complex ideas simply using clear, "
        "concise language and, when helpful, a concrete example. Keep it under 120 words."
    )
    prompt = (
        "Write a short, easy-to-understand explanation of the following topic. "
        "Avoid jargon; if necessary, define it briefly."
        f"\n\nTopic: {topic}\n\nExplanation:"
    )
    return _call_openai_chat([
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ])


def _parse_quiz_json(text: str) -> List[Dict[str, str]]:
    """Parse quiz JSON robustly; return list of {question, answer} dicts."""
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "questions" in data and isinstance(data["questions"], list):
            items = data["questions"]
        elif isinstance(data, list):
            items = data
        else:
            return []

        normalized: List[Dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            q = str(item.get("question", "")).strip()
            a = str(item.get("answer", "")).strip()
            if q and a:
                normalized.append({"question": q, "answer": a})
        return normalized
    except Exception:
        return []


def generate_quiz(topic: str, num_questions: int = 4) -> List[Dict[str, str]]:
    """Generate a short quiz (3–5 questions) with correct answers using OpenAI."""
    topic = topic.strip()
    n = max(3, min(5, int(num_questions)))
    system = "You are a helpful quiz generator. Create concise questions testing core understanding."
    prompt = (
        "Create a short quiz about the topic. Return JSON with keys: questions -> list of "
        "objects each with 'question' and 'answer'. Keep questions short and clear."
        f"\n\nTopic: {topic}\nNumber of questions: {n}\n\nJSON only:"
    )
    raw = _call_openai_chat([
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ])
    items = _parse_quiz_json(raw)
    return items


def _normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[\W_]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def check_answers(user_answers: List[str], correct_answers: List[str]) -> Tuple[int, List[str]]:
    """Compare user answers to correct answers and produce score + feedback."""
    total = min(len(user_answers), len(correct_answers))
    score = 0
    feedback: List[str] = []

    for i in range(total):
        user = _normalize_text(user_answers[i])
        correct = _normalize_text(correct_answers[i])
        is_correct = user == correct or (user and user in correct) or (correct and correct in user)
        if is_correct:
            score += 1
            feedback.append("Correct!")
        else:
            feedback.append(f"Not quite. Expected: {correct_answers[i]}")

    return score, feedback



