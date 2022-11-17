#!/usr/local/python
#
# Related:
#  - https://git.psu.edu/sysman/besengine/blob/master/Code/BESRelevanceProvider.py
"""
EvaluateRelevance.py

Created by James Stewart (@JGStew) on 2020-02-26.
"""
from __future__ import absolute_import

import os
import subprocess
import sys


def get_path_QNA():
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


def EvaluateRelevance(relevance="TRUE", returntype="RAW"):
    path_QNA = get_path_QNA()
    # print(path_QNA)

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
    with open("relevance_tmp.txt", "w") as rel_file:
        # Writing data to a file
        rel_file.write("Q: " + relevance + "\n")

    qna_run = subprocess.run(
        [path_QNA, "-t", "-showtypes", "relevance_tmp.txt"],
        check=True,
        capture_output=True,
        text=True,
    )
    output_data = qna_run.stdout
    error_data = qna_run.stderr

    if error_data:
        print("Error: " + error_data)

    # Return raw output data:   TODO: implement other return types
    return output_data


def main(relevance="version of client"):
    print(EvaluateRelevance(relevance))


if __name__ == "__main__":
    # check for command argument, and try to pass it as the relevance to be evaluated
    # TODO: find a better way to get the raw commandline string
    if len(sys.argv) == 2:
        # handle the case in which the commandline is a single string already:
        cmd_line = sys.argv[1]
    else:
        # the following doesn't work in all cases, only tested on mac:
        cmd_line = subprocess.list2cmdline(sys.argv[1:])
        # cmdline = " ".join(map(cmd_quote, sys.argv[1:]))

    if cmd_line:
        # print len(sys.argv)
        print("Note: this will not work on the command line directly in all cases")
        print("Q: " + cmd_line)
        main(cmd_line)
    else:
        main()
