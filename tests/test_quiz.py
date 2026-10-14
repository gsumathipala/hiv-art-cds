"""Step 10: quiz mode."""
import pytest

from art_cds.knowledge.quiz import QUESTIONS, TOPICS
from art_cds.knowledge.cases import CASES_BY_KEY


def test_questions_are_well_formed():
    ids = [q.id for q in QUESTIONS]
    assert len(ids) == len(set(ids))
    for q in QUESTIONS:
        assert q.topic in TOPICS
        assert len(q.options) >= 3 and 0 <= q.answer < len(q.options)
        assert len(q.explanation) > 80 and q.refs
        assert not q.case or q.case in CASES_BY_KEY


@pytest.mark.parametrize("q", QUESTIONS, ids=lambda q: q.id)
def test_each_question_page_renders_and_marks_the_answer(client, q):
    html = client.get(f"/quiz/{q.id}?a={q.answer}").get_data(as_text=True)
    assert "Correct." in html and q.explanation[:40] in html
    wrong = (q.answer + 1) % len(q.options)
    assert "Not quite" in client.get(f"/quiz/{q.id}?a={wrong}").get_data(as_text=True)


def test_index_and_topic_filter(client):
    assert client.get("/quiz/").status_code == 200
    assert client.get("/quiz/?topic=Resistance").status_code == 200
    assert client.get("/quiz/?topic=Nonsense").status_code == 404
    assert client.get("/quiz/nope").status_code == 404
