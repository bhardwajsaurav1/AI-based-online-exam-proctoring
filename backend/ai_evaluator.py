"""
AI Subjective Question Evaluator & Grading Engine.
Author: Sole Contributor / Creator

Evaluates candidate written answers using Google Gemini 2.5 Flash API
with intelligent semantic fallback.
"""

import os
import re
import json
import config

NON_ANSWER_PATTERNS = [
    r"^(i\s+)?(do\s*not|don'?t)\s+know",
    r"^idk",
    r"^(no\s+idea|not\s+sure|na|n/a|none|nil|skip|\.)$",
    r"^[a-zA-Z\s]{0,10}$"
]

def is_non_answer(text):
    cleaned = (text or "").strip().lower()
    if len(cleaned) < 8:
        return True
    for pattern in NON_ANSWER_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return True
    return False

def evaluate_subjective_answer(question_text, rubric, student_answer, max_marks=5.0):
    """
    Evaluates a candidate's descriptive written answer.
    """
    cleaned_answer = (student_answer or "").strip()
    max_marks = float(max_marks)

    # Detect blank or dismissive answers
    if not cleaned_answer or is_non_answer(cleaned_answer):
        return {
            "awarded_marks": 0.0,
            "max_marks": max_marks,
            "percentage": 0.0,
            "feedback": "No substantive technical explanation was provided for this question."
        }

    # 1. Evaluate using Google Gemini API if configured
    gemini_result = _evaluate_with_gemini(question_text, rubric, cleaned_answer, max_marks)
    if gemini_result is not None:
        return gemini_result

    # 2. Heuristic Semantic Fallback
    return _evaluate_with_heuristics(question_text, rubric, cleaned_answer, max_marks)


def _evaluate_with_gemini(question_text, rubric, student_answer, max_marks):
    api_key = getattr(config, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        rubric_str = rubric if isinstance(rubric, str) else "; ".join(rubric)

        prompt = (
            f"You are an academic examiner grading a student's answer to a technical question.\n\n"
            f"QUESTION: {question_text}\n"
            f"EXPECTED CONCEPTS / RUBRIC: {rubric_str}\n"
            f"MAX MARKS: {max_marks}\n\n"
            f"STUDENT ANSWER:\n\"\"\"\n{student_answer}\n\"\"\"\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Grade objectively based on technical correctness and conceptual coverage.\n"
            f"2. If the student answer is irrelevant, gibberish, or incorrect, award 0 marks.\n"
            f"3. Return ONLY a JSON object: {{\"awarded_marks\": float, \"feedback\": \"Concise 1-2 sentence assessment.\"}}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )

        data = json.loads(response.text)
        awarded = float(data.get("awarded_marks", 0.0))
        awarded = max(0.0, min(max_marks, round(awarded, 1)))

        return {
            "awarded_marks": awarded,
            "max_marks": max_marks,
            "percentage": round((awarded / max_marks) * 100, 1),
            "feedback": data.get("feedback", "Evaluation completed.")
        }
    except Exception as e:
        print(f"[INFO] Gemini subjective evaluation unavailable ({e}), using semantic fallback.")
        return None


def _evaluate_with_heuristics(question_text, rubric, student_answer, max_marks):
    words = re.findall(r'\b[a-zA-Z0-9_-]+\b', student_answer.lower())
    word_count = len(words)

    rubric_text = rubric if isinstance(rubric, str) else " ".join(rubric)
    rubric_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', rubric_text.lower()))
    stopwords = {"which", "their", "there", "about", "would", "these", "other", "after", "where", "should", "could", "first", "system", "because", "using"}
    keywords = [k for k in rubric_keywords if k not in stopwords]

    if not keywords:
        matched_ratio = min(1.0, word_count / 30.0)
    else:
        matched = [k for k in keywords if k in student_answer.lower()]
        matched_ratio = len(matched) / len(keywords)

    if matched_ratio == 0:
        return {
            "awarded_marks": 0.0,
            "max_marks": max_marks,
            "percentage": 0.0,
            "feedback": "Answer did not cover the essential technical concepts required in the question."
        }

    length_factor = min(1.0, word_count / 30.0)
    score_ratio = (0.7 * matched_ratio) + (0.3 * length_factor)
    awarded_marks = round(max(0.5, min(max_marks, score_ratio * max_marks)), 1)
    percentage = round((awarded_marks / max_marks) * 100, 1)

    if percentage >= 75:
        feedback = "Comprehensive answer covering the primary technical mechanisms and concepts."
    elif percentage >= 50:
        feedback = "Good response with relevant conceptual coverage, though some technical details were omitted."
    else:
        feedback = "Basic response; partially addressed the question but requires more depth."

    return {
        "awarded_marks": awarded_marks,
        "max_marks": max_marks,
        "percentage": percentage,
        "feedback": feedback
    }
