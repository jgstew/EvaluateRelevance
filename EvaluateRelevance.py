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

def EvaluateRelevance(relevance="TRUE"):
  pathQNA = getPathQNA()

  # There are 2 methods to eval relevance using the QNA executable
  #   - Subprocess using FileIn(relevance), FileOut(results)
  #      - I need to test this method
  #      - Can this method use filestreams instead of files? I hope so
  #   - Subprocess using StdIn(relevance), StdOut(results)
  #      - Has issues with parsing results
  #      - Example: https://git.psu.edu/sysman/besengine/blob/master/Code/BESRelevanceProvider.py#L68
  #   - Is there a better way using a library or an API of some sort?

  # TODO: implement, but for now, return path
  return pathQNA


def main():
  print EvaluateRelevance()

if __name__ == '__main__':
  main()
