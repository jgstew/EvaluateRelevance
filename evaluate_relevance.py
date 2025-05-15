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


def evaluate_relevance_string(relevance, separator="\n"):
    """Get string with newlines from relevance results
    Args:

        relevance (str): relevance statement string
        separator (str): separator for multiple results
    """
    return separator.join(evaluate_relevance_array(relevance))


def evaluate_relevance_array(relevance):
    """Get array from relevance results
    Args:

        relevance (str): relevance statement string
    """
    return parse_raw_result_array(evaluate_relevance_raw(relevance))


def evaluate_relevance_raw_stdin(relevance):
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

    start_time = time.monotonic()
    qna_run = subprocess.run(
        [get_path_qna(), "-t", "-showtypes"],
        input=relevance + "\n",
        check=True,
        capture_output=True,
        text=True,
    )
    end_time = time.monotonic()

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

    if FILE_WRITE_OUTPUT:
        with open("relevance_out.txt", "w", encoding="utf-8") as rel_output:
            # Writing data to a file
            rel_output.write(output_data)

        with open("relevance_str.txt", "w", encoding="utf-8") as rel_output:
            # Writing data to a file
            rel_output.write("\n".join(parse_raw_result_array(output_data)))

    return output_data


def evaluate_relevance_raw_file(rel_file_path=DEFAULT_INPUT_FILE):
    """This function will get raw text client relevance string input from a file."""

    # must be run as root or with sudo on MacOS
    # Check if the user is root if on MacOS:
    if sys.platform == "darwin" and os.geteuid() != 0:
        # If not, print a message and exit
        raise PermissionError("This script must be run as root or with sudo on MacOS.")

    # measure runtime of QNA:
    # https://stackoverflow.com/a/26099345/861745
    start_time = time.monotonic()
    qna_run = subprocess.run(
        [get_path_qna(), "-t", "-showtypes", rel_file_path],
        check=True,
        capture_output=True,
        text=True,
    )
    end_time = time.monotonic()

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


def evaluate_relevance_raw(relevance="TRUE"):
    """This function will get raw text client relevance results."""
    # There are 2 methods to eval relevance using the QNA executable
    #   - Subprocess using FileIn(relevance), FileOut(results)
    #     - After testing, this method has the same results parsing issues as using StdIn/StdOut
    #     - The potential advantage to this method is if there is a character limit for StdIn/StdOut
    #     - Can this method use filestreams instead of files? I hope so, but would need to test
    #   - Subprocess using StdIn(relevance), StdOut(results)
    #     - Has issues with parsing results
    #     - Example: https://git.psu.edu/sysman/besengine/blob/master/Code/BESRelevanceProvider.py#L68
    #   - Is there a better way using a library or an API of some sort?

    # There are 4 ways to return the relevance evaluation results
    #   - Raw String of Results
    #     - Easiest method
    #   - Single String with separator between plural results (newline by default)
    #   - Array of Strings for plural results
    #   - Hash with array of strings for results, plus timing info, return type info

    # How to (optionally?) return other metadata
    #  - Timing info
    #  - Relevance Return type (-showtypes)
    #  - Error info

    return evaluate_relevance_raw_stdin(relevance)


def write_relevance_file(relevance, rel_file_path=DEFAULT_INPUT_FILE):
    """Write relevance to a file for use with QNA."""
    with open(rel_file_path, "w", encoding="utf-8") as rel_file:
        if not relevance.startswith("Q: "):
            relevance = "Q: " + relevance
        # Writing data to a file
        rel_file.write(relevance)


def evaluate_relevances_array_to_array(relevances):
    """Evaluate multiple relevances from an array and return the results as an array.

    Args:
        relevances (list): list of relevance strings
    Returns:
        list: array of relevance results

    Example:
        evaluate_relevances_array_to_array(["version of client", "Q: TRUE;FALSE"])
    """
    # check if the input is a list
    if not isinstance(relevances, list):
        raise ValueError("Relevances must be a list.")
    # check if the input is empty
    if not relevances:
        raise ValueError("Relevances list is empty.")
    results = []
    for relevance in relevances:
        if isinstance(relevance, str):
            results.append(evaluate_relevance_string(relevance))
        else:
            raise ValueError("Relevance must be a string.")
    return results


def main(relevance="version of client"):
    """Execution starts here:"""
    print(evaluate_relevance_raw(relevance))
    try:
        os.remove(DEFAULT_INPUT_FILE)
    except FileNotFoundError:
        pass


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
            print(evaluate_relevance_raw_file(cmd_args))
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
