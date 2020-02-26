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
    # test if path exists and is executable
    if os.path.isfile(file) and os.access(file, os.X_OK):
      # return first valid path
      return file
  
  # TODO: need to have some sort of error handling
  return "Not Found!"

def main():
  print getPathQNA()

if __name__ == '__main__':
  main()
