from app.classifier import classify


def test_code_keywords_route_to_code():
    assert classify("please refactor this SQL query") == "code"
    assert classify("there is a bug in my Python function") == "code"


def test_bulk_verbs_route_to_bulk():
    assert classify("summarize this article in 3 bullets") == "bulk"
    assert classify("translate the following labels") == "bulk"


def test_reasoning_keywords_route_to_reasoning():
    assert classify("explain the trade-offs between monolith and microservices") == "reasoning"
    assert classify("what is the root cause of this issue? analyze it step by step") == "reasoning"


def test_generic_prompt_defaults_to_writing():
    assert classify("hello there") == "writing"
    assert classify("") == "writing"


def test_code_beats_reasoning_when_both_present():
    # code signal is more specific, must win
    assert classify("explain why this Python function throws an exception") == "code"
