# SPDX-License-Identifier: Apache-2.0

import github
import os

def connect():
    token = os.environ.get('GITHUB_TOKEN', None)
    return github.Github(token)

def create_card(column, content_id, content_type):
    try:	
        column.create_card(content_id=content_id, content_type=content_type)
    except github.GithubException as e:	
        error = e.data["errors"][0]	
        if error["resource"] != "ProjectCard" or error["code"] != "unprocessable":	
            raise	
        print("Card already in project.")
