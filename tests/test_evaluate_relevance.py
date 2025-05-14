import pytest

from evaluate_relevance import (
    evaluate_relevance_array,
    evaluate_relevance_raw,
    evaluate_relevance_string,
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
        "evaluate_relevance.evaluate_relevance_array", lambda x: mock_results
    )
    relevance = "version of client"
    separator = ", "
    expected = "result1, result2, result3"
    assert evaluate_relevance_string(relevance, separator) == expected


def test_evaluate_relevance_array(monkeypatch):
    """Test evaluate_relevance_array returns results as an array."""
    mock_raw_result = "A: result1\nA: result2\nA: result3\n"
    monkeypatch.setattr(
        "evaluate_relevance.evaluate_relevance_raw", lambda x: mock_raw_result
    )
    relevance = "version of client"
    expected = ["result1", "result2", "result3"]
    assert evaluate_relevance_array(relevance) == expected


def test_evaluate_relevance_raw(monkeypatch, tmp_path):
    """Test evaluate_relevance_raw evaluates relevance and returns raw results."""
    mock_output = "A: result1\nA: result2\nTime Taken: 0:00:01\n"
    monkeypatch.setattr(
        "evaluate_relevance.evaluate_relevance_raw_file", lambda x: mock_output
    )

    relevance = "version of client"
    assert evaluate_relevance_raw(relevance) == mock_output
