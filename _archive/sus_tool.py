"""
sus_tool.py — SUS (System Usability Scale) Data Collection & Analysis
======================================================================
Digunakan di halaman tab "Evaluasi" pada dashboard.
Mengimplementasikan 10-item SUS questionnaire (Brooke, 1996)
dengan interpretasi grade (Bangor et al., 2008).

Output: skor SUS per responden + mean ± SD + grade + visualisasi Plotly
"""
import pandas as pd
import numpy as np
import json, os
from config import SUS_THRESHOLDS

SUS_QUESTIONS = [
    ("Q1",  "Saya pikir saya akan sering menggunakan sistem ini",                        "positive"),
    ("Q2",  "Saya merasa sistem ini terlalu kompleks",                                    "negative"),
    ("Q3",  "Saya merasa sistem ini mudah digunakan",                                     "positive"),
    ("Q4",  "Saya pikir saya akan membutuhkan bantuan orang teknis untuk menggunakan ini","negative"),
    ("Q5",  "Saya merasa berbagai fungsi dalam sistem ini terintegrasi dengan baik",      "positive"),
    ("Q6",  "Saya merasa terlalu banyak inkonsistensi dalam sistem ini",                  "negative"),
    ("Q7",  "Saya bayangkan kebanyakan orang akan belajar sangat cepat menggunakan ini",  "positive"),
    ("Q8",  "Saya merasa sistem ini sangat berat dan tidak nyaman digunakan",             "negative"),
    ("Q9",  "Saya sangat percaya diri menggunakan sistem ini",                            "positive"),
    ("Q10", "Saya perlu belajar banyak hal sebelum bisa menggunakan sistem ini",          "negative"),
]

SUS_FILE = os.path.join(os.path.dirname(__file__), 'sus_responses.json')


def calculate_sus_score(responses: list[int]) -> float:
    """
    Hitung skor SUS dari 10 jawaban (skala Likert 1-5).
    Formula standar (Brooke, 1996):
      odd items  (positive): score - 1
      even items (negative): 5 - score
      Total * 2.5
    """
    assert len(responses) == 10, "SUS memerlukan tepat 10 respons"
    total = 0
    for i, r in enumerate(responses):
        if (i + 1) % 2 == 1:   # odd → positive
            total += r - 1
        else:                   # even → negative
            total += 5 - r
    return total * 2.5


def get_sus_grade(score: float) -> tuple[str, str]:
    for grade, (lo, hi, color) in SUS_THRESHOLDS.items():
        if lo <= score <= hi:
            return grade, color
    return "Unknown", "#888888"


def load_responses() -> list[dict]:
    if not os.path.exists(SUS_FILE):
        return []
    with open(SUS_FILE) as f:
        return json.load(f)


def save_response(name: str, role: str, responses: list[int]):
    data = load_responses()
    score = calculate_sus_score(responses)
    grade, _ = get_sus_grade(score)
    data.append({
        "id":        len(data) + 1,
        "name":      name,
        "role":      role,
        "responses": responses,
        "score":     score,
        "grade":     grade,
    })
    with open(SUS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return score, grade


def get_summary_stats() -> dict | None:
    data = load_responses()
    if not data:
        return None
    scores = [d['score'] for d in data]
    return {
        "n":       len(scores),
        "mean":    round(float(np.mean(scores)), 2),
        "std":     round(float(np.std(scores)),  2),
        "min":     round(float(np.min(scores)),  2),
        "max":     round(float(np.max(scores)),  2),
        "median":  round(float(np.median(scores)),2),
        "scores":  scores,
        "grade":   get_sus_grade(float(np.mean(scores)))[0],
    }
