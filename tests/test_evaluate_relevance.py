import os
import sys

import pytest

if not os.getenv("TEST_PIP"):
    # add module folder to import paths for testing local src
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # reverse the order so we make sure to get the local src module
    sys.path.reverse()

from evaluate_relevance import (
    evaluate_relevance_array,
    evaluate_relevance_raw,
    evaluate_relevance_string,
    evaluate_relevances_array_to_many,
    get_path_qna,
    parse_raw_result_array,
)

# pytest code for tests/test_evaluate_relevance.py


def test_get_path_qna_no_binary(monkeypatch):
    """Test get_path_qna raises FileNotFoundError when no valid QNA binary is found."""
    monkeypatch.setattr("os.path.isfile", lambda x: False)
    monkeypatch.setattr("os.access", lambda x, y: False)
    with pytest.raises(FileNotFoundError, match="Valid QNA path not found!"):
        get_path_qna()


def test_parse_raw_result_array():
    """Test parse_raw_result_array parses raw relevance results correctly."""
    raw_result = "A: result1\nA: result2\nA: result3\n"
    expected = ["result1", "result2", "result3"]
    assert parse_raw_result_array(raw_result) == expected


def test_evaluate_relevance_string(monkeypatch):
    """Test evaluate_relevance_string returns results as a string with separators."""
    mock_results = ["result1", "result2", "result3"]
    monkeypatch.setattr(
        "evaluate_relevance.evaluate_relevance_array", lambda x, y: mock_results
    )
    relevance = "version of client"
    separator = ", "
    expected = "result1, result2, result3"
    assert evaluate_relevance_string(relevance, separator) == expected


def test_evaluate_relevance_array(monkeypatch):
    """Test evaluate_relevance_array returns results as an array."""
    mock_raw_result = "A: result1\nA: result2\nA: result3\n"
    monkeypatch.setattr(
        "evaluate_relevance.evaluate_relevance_raw", lambda x, y: mock_raw_result
    )
    relevance = "version of client"
    expected = ["result1", "result2", "result3"]
    assert evaluate_relevance_array(relevance) == expected


def test_evaluate_relevance_raw(monkeypatch):
    """Test evaluate_relevance_raw evaluates relevance and returns raw results."""
    mock_output = "A: result1\nA: result2\nTime Taken: 0:00:01\n"
    monkeypatch.setattr(
        "evaluate_relevance.evaluate_relevance_raw_file", lambda x, y: mock_output
    )
    monkeypatch.setattr(
        "evaluate_relevance.evaluate_relevance_raw_stdin", lambda x, y: mock_output
    )

    relevance = "version of client"
    assert evaluate_relevance_raw(relevance) == mock_output


def test_evaluate_relevances_array_to_many_strings():
    """Test evaluate_relevances_array_to_many which evaluates multiple relevance
    statements.
    """
    qna_path = None

    if sys.platform == "darwin":
        pytest.skip("Skipping test on macOS due to QNA binary issues.")

    try:
        qna_path = get_path_qna()
    except FileNotFoundError:
        pytest.skip("QNA binary not found, skipping test.")

    if qna_path:
        relevance_array = ['"result1"', '"result2"']
        expected = ["result1", "result2"]
        assert (
            evaluate_relevances_array_to_many(relevance_array, "string", qna_path)
            == expected
        )


def test_evaluate_relevances_array_to_many_arrays():
    """Test evaluate_relevances_array_to_many which evaluates multiple relevance
    statements.
    """
    qna_path = None

    if sys.platform == "darwin":
        pytest.skip("Skipping test on macOS due to QNA binary issues.")

    try:
        qna_path = get_path_qna()
    except FileNotFoundError:
        pytest.skip("QNA binary not found, skipping test.")

    if qna_path:
        relevance_array = ['"result1"', '"result2"']
        expected = [["result1"], ["result2"]]
        assert (
            evaluate_relevances_array_to_many(relevance_array, "array", qna_path)
            == expected
        )
