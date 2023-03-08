#!/usr/local/python
#
# Related:
#  - https://git.psu.edu/sysman/besengine/blob/master/Code/BESRelevanceProvider.py
"""
EvaluateRelevance.py

Created by James Stewart (@JGStew) on 2020-02-26.
"""
from __future__ import absolute_import

import datetime
import os
import subprocess
import sys
import time

import regex

DEFAULT_INPUT_FILE = "relevance_tmp.txt"


def get_path_qna():
    """find path for the QNA binary"""
    test_file_paths = [
        "QnA",
        "/usr/local/bin/QnA",
        "/Library/BESAgent/BESAgent.app/Contents/MacOS/QnA",
        "/opt/BESClient/bin/QnA",
        "C:/Program Files (x86)/BigFix Enterprise/BES Client/qna.exe",
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
    """parse a raw relevance result into an array"""
    results_array_raw = regex.regex.split("\r\n|\r|\n", result)
    results_array = []
    for result_raw in results_array_raw:
        if result_raw.startswith("A: "):
            results_array.append(result_raw.split("A: ", 1)[1])
    return results_array


def EvaluateRelevanceString(relevance, separator="\n"):
    """get string with newlines from relevance results"""
    return separator.join(EvaluateRelevanceArray(relevance))


def EvaluateRelevanceArray(relevance):
    """get array from relevance results"""
    return parse_raw_result_array(EvaluateRelevanceRaw(relevance))


def EvaluateRelevanceRawFile(rel_file=DEFAULT_INPUT_FILE):
    """This function will get raw text client relevance results from a file"""
    # measure runtime of QNA:
    # https://stackoverflow.com/a/26099345/861745
    start_time = time.monotonic()
    qna_run = subprocess.run(
        [get_path_qna(), "-t", "-showtypes", rel_file],
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

    with open("relevance_out.txt", "w") as rel_output:
        # Writing data to a file
        rel_output.write(output_data)

    with open("relevance_str.txt", "w") as rel_output:
        # Writing data to a file
        rel_output.write("\n".join(parse_raw_result_array(output_data)))

    return output_data


def EvaluateRelevanceRaw(relevance="TRUE"):
    """This function will get raw text client relevance results"""
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
    #   - Single String with separator between plural results (newline by default?)
    #   - Array of Strings for plural results
    #   - Hash with array of strings for results, plus timing info, return type info

    # How to (optionally?) return other metadata
    #  - Timing info
    #  - Relevance Return type (-showtypes)
    #  - Error info

    # write relevance to local tmp file:
    with open(DEFAULT_INPUT_FILE, "w") as rel_file:
        # Writing data to a file
        rel_file.write("Q: " + relevance)

    # Return raw output data:
    return EvaluateRelevanceRawFile(DEFAULT_INPUT_FILE)


def main(relevance="version of client"):
    """Execution starts here:"""
    print(EvaluateRelevanceRaw(relevance))


if __name__ == "__main__":
    # check for command argument, and use it as the relevance
    if len(sys.argv) == 2:
        # handle the case in which the commandline is a single string already:
        CMD_LINE = sys.argv[1]
    else:
        # the following doesn't work in all cases:
        CMD_LINE = subprocess.list2cmdline(sys.argv[1:])

    if CMD_LINE:
        if os.path.isfile(CMD_LINE):
            print(EvaluateRelevanceRawFile(CMD_LINE))
        else:
            print(
                "Note: this will not work on the command line directly "
                + "in all cases. May require odd quote escaping."
            )
            print("Q: " + CMD_LINE + "\n")
            main(CMD_LINE)
    else:
        main()
