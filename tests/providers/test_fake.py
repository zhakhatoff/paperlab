import asyncio
import json

from paperlab.providers import FakeProvider


def run(coro):
    return asyncio.run(coro)


def test_default_echo_returns_valid_json():
    provider = FakeProvider()
    result = run(provider.complete("sys", "hello world", "m"))
    data = json.loads(result)
    assert "echo" in data
    assert data["echo"].startswith("hello world")


def test_responses_matched_by_prefix():
    provider = FakeProvider(responses={("sys_", "user_"): "matched"})
    result = run(provider.complete("sys_prompt", "user_query", "m"))
    assert result == "matched"


def test_responses_no_match_uses_default():
    provider = FakeProvider(
        responses={("other_", "other_"): "nope"},
        default="fallback",
    )
    result = run(provider.complete("sys", "user", "m"))
    assert result == "fallback"


def test_calls_accumulate_in_order():
    provider = FakeProvider()
    run(provider.complete("s1", "u1", "m1"))
    run(provider.complete("s2", "u2", "m2"))
    assert provider.calls == [("s1", "u1", "m1"), ("s2", "u2", "m2")]


def test_explicit_default_used_when_no_match():
    provider = FakeProvider(default="explicit")
    result = run(provider.complete("s", "u", "m"))
    assert result == "explicit"


def test_echo_truncated_to_80_chars():
    long_user = "x" * 100
    provider = FakeProvider()
    result = run(provider.complete("sys", long_user, "m"))
    data = json.loads(result)
    assert len(data["echo"]) <= 80
