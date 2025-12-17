#!/usr/local/python
#
# Related:
#  - https://git.psu.edu/sysman/besengine/blob/master/Code/BESRelevanceProvider.py
"""
Created by James Stewart (@JGStew) on 2020-02-26.

Copyright (c) 2020, James Stewart

This will evaluate relevance using the QNA executable.
It can be used to evaluate relevance strings or files containing relevance strings.

Must be run as root or with sudo on MacOS.

There are 4 ways to return the relevance evaluation results
  - Raw String output from QNA
    - evaluate_relevance_raw_stdin()
  - Single String with separator between plural results (newline by default)
    - evaluate_relevance_string()
  - Array of Strings for plural results
    - evaluate_relevance_array()
  - (TODO) Hash with array of strings for results, plus timing info, return type info

Example usage:
    python evaluate_relevance.py "version of client"
    python evaluate_relevance.py "Q: version of client"
    python evaluate_relevance.py relevance_tmp.txt
    python evaluate_relevance.py
"""
from __future__ import absolute_import

import datetime
import os
import re
import subprocess
import sys
import time

DEFAULT_INPUT_FILE = "relevance_tmp.txt"
FILE_WRITE_OUTPUT = False


def get_path_qna():
    """Find path for the QNA binary."""
    test_file_paths = [
        "/usr/local/bin/qna",
        "/Library/BESAgent/BESAgent.app/Contents/MacOS/QnA",
        "/opt/BESClient/bin/qna",
        "C:/Program Files (x86)/BigFix Enterprise/BES Client/qna.exe",
        "qna",
        "qna.exe",
    ]

    for file_path in test_file_paths:
        # test if path exists and is executable:
        #   - https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
            # return first valid path
            # print(file_path)
            return file_path

    raise FileNotFoundError("Valid QNA path not found!")


def parse_raw_result_array(result):
    """Parse a raw relevance result into an array
    Args:

        result (str): raw relevance result string
    Returns:
        list: array of relevance results
    """
    # split the result string into an array using regex
    results_array_raw = re.split(r"\r\n|\r|\n", result)
    results_array = []
    for result_raw in results_array_raw:
        if result_raw.startswith("Q: A: "):
            results_array.append(result_raw.split("Q: A: ", 1)[1])
        if result_raw.startswith("A: "):
            results_array.append(result_raw.split("A: ", 1)[1])
    return results_array


def evaluate_relevance_string(relevance, separator="\n", path_qna=None):
    """Get string with newlines from relevance results
    Args:

        relevance (str): relevance statement string
        separator (str): separator for multiple results
    """
    return separator.join(evaluate_relevance_array(relevance, path_qna))


def evaluate_relevance_array(relevance, path_qna=None):
    """Get array from relevance results
    Args:

        relevance (str): relevance statement string
    """
    return parse_raw_result_array(evaluate_relevance_raw(relevance, path_qna))


def evaluate_relevance_raw_stdin(relevance, path_qna=None):
    """This function will get raw text client relevance results using stdin."""

    # need to remove the Q: from the relevance string if present
    # this is because the QNA executable does not require it if stdin is used
    # but it does require it if a file is used
    if relevance.startswith("Q: "):
        relevance = relevance[3:]

    # must be run as root or with sudo on MacOS
    # Check if the user is root if on MacOS:
    if sys.platform == "darwin" and os.geteuid() != 0:
        # If not, print a message and exit
        raise PermissionError("This script must be run as root or with sudo on MacOS.")

    if not path_qna:
        path_qna = get_path_qna()

    start_time = time.perf_counter()
    qna_run = subprocess.run(
        [path_qna, "-t", "-showtypes"],
        input=relevance + "\n",
        check=True,
        capture_output=True,
        text=True,
    )
    end_time = time.perf_counter()

    output_data = qna_run.stdout
    # error_data = qna_run.stderr

    time_taken = end_time - start_time

    output_data += (
        "Time Taken: "
        + str(datetime.timedelta(seconds=time_taken))
        + " as measured by python.\n"
    )
    # if error_data:
    #     print("Error: " + error_data)

    if 'E: The operator "string" is not defined.' in output_data:
        output_data += "\nInfo: This error means a result was found, but it does not have a string representation."

    if FILE_WRITE_OUTPUT:
        with open("relevance_out.txt", "w", encoding="utf-8") as rel_output:
            # Writing data to a file
            rel_output.write(output_data)

        with open("relevance_str.txt", "w", encoding="utf-8") as rel_output:
            # Writing data to a file
            rel_output.write("\n".join(parse_raw_result_array(output_data)))

    return output_data


def evaluate_relevance_raw_file(rel_file_path=DEFAULT_INPUT_FILE):
    """This function will get raw text client relevance string input from a file.

    Args:
        rel_file_path (str): path to the file containing the relevance string

    Returns:
        str: raw output from QNA

    This function is less efficient than using stdin, evaluate_relevance_raw_stdin should be preferred.
    This is included for completeness and to allow for file input even though it is no longer used internally.
    This is also used in the main function to allow for command line input of a file path.
    """

    # must be run as root or with sudo on MacOS
    # Check if the user is root if on MacOS:
    if sys.platform == "darwin" and os.geteuid() != 0:
        # If not, print a message and exit
        raise PermissionError("This script must be run as root or with sudo on MacOS.")

    # measure runtime of QNA:
    # https://stackoverflow.com/a/26099345/861745
    start_time = time.perf_counter()
    qna_run = subprocess.run(
        [get_path_qna(), "-t", "-showtypes", rel_file_path],
        check=True,
        capture_output=True,
        text=True,
    )
    end_time = time.perf_counter()

    output_data = qna_run.stdout
    error_data = qna_run.stderr

    output_data += (
        "Time Taken: "
        + str(datetime.timedelta(seconds=end_time - start_time))
        + " as measured by python.\n"
    )
    if error_data:
        print("Error: " + error_data)

    if 'E: The operator "string" is not defined.' in output_data:
        output_data += "\nInfo: This error means a result was found, but it does not have a string representation."

    with open("relevance_out.txt", "w", encoding="utf-8") as rel_output:
        # Writing data to a file
        rel_output.write(output_data)

    with open("relevance_str.txt", "w", encoding="utf-8") as rel_output:
        # Writing data to a file
        rel_output.write("\n".join(parse_raw_result_array(output_data)))

    return output_data


def write_relevance_file(relevance, rel_file_path=DEFAULT_INPUT_FILE):
    """Write relevance to a file for use with QNA."""
    with open(rel_file_path, "w", encoding="utf-8") as rel_file:
        if not relevance.startswith("Q: "):
            relevance = "Q: " + relevance
        # Writing data to a file
        rel_file.write(relevance)


def evaluate_relevances_array_to_many(relevances, results_type="array", path_qna=None):
    """Evaluate multiple relevances from an array and return the results as an array.

    Args:
        relevances (list): list of relevance strings
        results_type (str): array or string
            - array: return an array of array of plural results
            - string: return an array of strings with newlines between plural results
    Returns:
        list: array of relevance results (array of strings or multidimensional array)

    Example:
        evaluate_relevances_array_to_many(["version of client", "Q: TRUE;FALSE"])
    """
    # check if the input is a list
    if not isinstance(relevances, list):
        raise ValueError("Relevances must be a list.")
    # check if the input is empty
    if not relevances:
        raise ValueError("Relevances list is empty.")

    if not path_qna:
        path_qna = get_path_qna()

    results = []
    for relevance in relevances:
        if isinstance(relevance, str):
            if results_type == "array":
                results.append(evaluate_relevance_array(relevance, path_qna))
            else:
                results.append(evaluate_relevance_string(relevance, path_qna=path_qna))
        else:
            raise ValueError("Relevance must be a string.")
    return results


def evaluate_relevance_raw(relevance="TRUE", path_qna=None):
    """This function will get raw text client relevance results."""

    return evaluate_relevance_raw_stdin(relevance, path_qna)


def string_truncate(text, max_length=70):
    """Truncate a string to a maximum length and append ellipsis if truncated."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def evaluate_relevance_file_compare(rel_file_path=DEFAULT_INPUT_FILE, iterations=3):
    """
    This function will evaluate relevance from a file multiple times and return
    average time taken.
    """

    # must be run as root or with sudo on MacOS
    # Check if the user is root if on MacOS:
    if sys.platform == "darwin" and os.geteuid() != 0:
        # If not, print a message and exit
        raise PermissionError("This script must be run as root or with sudo on MacOS.")

    # parse the relevance from the file:
    with open(rel_file_path, "r", encoding="utf-8") as rel_file:
        file_text = rel_file.read()

    print("Evaluating relevance from file: " + rel_file_path)

    # get lines starting with "Q:"
    relevance_lines = []
    for line in file_text.splitlines():
        if line.strip().startswith("Q:"):
            relevance_lines.append(line.strip()[3:].strip())

    print("Found " + str(len(relevance_lines)) + " relevance lines in file.")
    # print(string_truncate(str(relevance_lines)))

    for relevance in relevance_lines:
        print("\nQ: " + string_truncate(relevance))

        # evaluate using file method
        total_time_file = 0.0
        result = ""
        for _ in range(iterations):
            start_time = time.perf_counter()
            result = evaluate_relevance_raw_stdin(relevance)
            end_time = time.perf_counter()
            total_time_file += end_time - start_time
        avg_time_file = total_time_file / iterations
        result_string = "\n".join(parse_raw_result_array(result))
        print("A: " + string_truncate(result_string))
        print(
            "Average Time Taken ("
            + str(iterations)
            + " iterations): "
            + str(datetime.timedelta(seconds=avg_time_file))
        )


def main(relevance="version of client"):
    """Execution starts here:"""
    print(evaluate_relevance_raw(relevance))
    # try:
    #     os.remove(DEFAULT_INPUT_FILE)
    # except FileNotFoundError:
    #     pass


if __name__ == "__main__":
    # check for command argument, and use it as the relevance
    if len(sys.argv) == 2:
        # handle the case in which the commandline is a single string already:
        cmd_args = sys.argv[1]
    else:
        # the following doesn't work in all cases:
        cmd_args = subprocess.list2cmdline(sys.argv[1:])

    if cmd_args:
        # check if the command argument is a file
        # if it is, use it as the relevance file
        # if it is not, use it as the relevance string
        if os.path.isfile(cmd_args):
            evaluate_relevance_file_compare(cmd_args)
        else:
            print(
                "Note: this will not work on the command line directly "
                + "in all cases. May require odd quote escaping."
            )
            if cmd_args.startswith("Q: "):
                print(cmd_args + "\n")
            else:
                print("Q: " + cmd_args + "\n")
            main(cmd_args)
    else:
        if os.path.isfile(DEFAULT_INPUT_FILE):
            print(evaluate_relevance_raw_file())
        else:
            main('("No Relevance Specified", TRUE, version of client)')
