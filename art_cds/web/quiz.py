"""Quiz mode: case-based questions with cited feedback. Progress is kept in the browser only."""
from __future__ import annotations

import random

from flask import Blueprint, abort, render_template, request

from ..knowledge.quiz import QUESTIONS, QUESTIONS_BY_ID, TOPICS, by_topic

bp = Blueprint("quiz", __name__)


@bp.get("/")
def index():
    topic = request.args.get("topic") or None
    if topic and topic not in TOPICS:
        abort(404)
    questions = by_topic(topic)
    if request.args.get("shuffle"):
        questions = random.sample(questions, len(questions))
    return render_template("quiz/index.html", questions=questions, topics=TOPICS, topic=topic,
                           total=len(QUESTIONS))


@bp.get("/<qid>")
def question(qid):
    q = QUESTIONS_BY_ID.get(qid) or abort(404)
    ids = [x.id for x in QUESTIONS]
    i = ids.index(qid)
    chosen = request.args.get("a")
    chosen_index = int(chosen) if chosen is not None and chosen.isdigit() else None
    return render_template("quiz/question.html", q=q, chosen=chosen_index, number=i + 1, total=len(ids),
                           next_id=ids[i + 1] if i + 1 < len(ids) else None,
                           prev_id=ids[i - 1] if i else None)
