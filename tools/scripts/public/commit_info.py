#!/usr/bin/env python3

"""
Please see the
  ***** API BACKWARD COMPATIBILITY CAVEAT *****
near the top of git-filter-repo
"""

import re
import datetime

import importlib
fr = importlib.import_module("git-filter-repo")

def change_up_them_commits(commit, _):
  # Change the commit author
  if commit.author_name == b"Amy Liu":
    commit.author_name = b"mialana"
    commit.author_email = b"liu.amy05@gmail.com"
    
  if commit.committer_name == b"Amy Liu":
    commit.committer_name = b"mialana"
    commit.committer_email = b"liu.amy05@gmail.com"


args = fr.FilteringOptions.parse_args(['--force'])
filter = fr.RepoFilter(args, commit_callback = change_up_them_commits)
filter.run()
