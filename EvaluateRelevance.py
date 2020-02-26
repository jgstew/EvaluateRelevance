#!/usr/local/python
# 
# Related: 
#  - https://git.psu.edu/sysman/besengine/blob/master/Code/BESRelevanceProvider.py
"""
BESRelevanceProvider.py

Created by James Stewart (@JGStew) on 2020-02-26.
"""
from __future__ import absolute_import

import os
import subprocess

def getPathQNA():
  testFilePaths = ["QnA", "/usr/local/bin/QnA", "/Library/BESAgent/BESAgent.app/Contents/MacOS/QnA", "/opt/BESClient/bin/QnA", "C:\Program Files (x86)\BigFix Enterprise\BES Client\qna.exe"]
  
  for file in testFilePaths:
    # test if path exists and is executable: https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python 
    if os.path.isfile(file) and os.access(file, os.X_OK):
      # return first valid path
      return file
  
  # TODO: need to have some sort of error handling
  return "ERROR: Valid QNA path not found!"

def EvaluateRelevance(relevance="TRUE", returntype="RAW"):
  pathQNA = getPathQNA()

  if not ( os.path.isfile(pathQNA) and os.access(pathQNA, os.X_OK) ):
    # TODO: error handling in this case:
    return pathQNA

  # There are 2 methods to eval relevance using the QNA executable
  #   - Subprocess using FileIn(relevance), FileOut(results)
  #     - After testing, this method has the same results parsing issues as using StdIn/StdOut
  #     - The only potential advantage to this method is if there is a character limit for StdIn/StdOut method
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

  process = subprocess.Popen([pathQNA, "-t", "-showtypes"], bufsize=-1, universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  outputdata, errordata = process.communicate(relevance.encode())

  # TODO: implement, but for now, return path
  return outputdata


def main(relevance='version of client'):
  print EvaluateRelevance(relevance)

if __name__ == '__main__':
  main()
