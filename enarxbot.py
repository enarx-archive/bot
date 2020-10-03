# SPDX-License-Identifier: Apache-2.0

import requests
import github
import json
import os
import re

class Suggestion:
    QUERY = """
query($owner:String!, $repo:String!, $pr:Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      suggestedReviewers {
        isAuthor
        isCommenter
        reviewer {
          login
        }
      }
    }
  }
}
"""

    @classmethod
    def query(cls, github, repo, pr):
        data = graphql(cls.QUERY, owner=repo.owner.login, repo=repo.name, pr=pr.number)
        for x in data["repository"]["pullRequest"]["suggestedReviewers"]:
            reviewer = github.get_user(x["reviewer"]["login"])
            yield cls(reviewer, x["isAuthor"], x["isCommenter"])

    def __init__(self, reviewer, author, commenter):
        self.reviewer = reviewer
        self.is_author = author
        self.is_commenter = commenter

def connect():
    token = os.environ.get('GITHUB_TOKEN', None)
    return github.Github(token)

class HTTPError(Exception):
    def __init__(self, reply):
        self.reply = reply

class GraphQLError(Exception):
    def __init__(self, errors):
        self.errors = errors

# A depagination example: fetch all PR numbers for enarx/enarx.
#
# query = """
# query($owner:String!, $name:String!, $cursor:String) {
#   repository(owner:$owner, name:$name) {
#     pullRequests(first:100, after:$cursor) {
#       pageInfo { endCursor hasNextPage }
#       nodes {
#         number
#       }
#     }
#   }
# }
# """
#
# data = graphql(query, page=["repository", "pullRequests"], owner="enarx", name="enarx")
#
# Your query:
#   * MUST have a `$cursor:String` variable
#   * MUST specify `after: $cursor` correctly
#   * MUST fetch `pageInfo { endCursor hasNextPage }`
#   * MUST have a `nodes` entity on the pagination object
#   * SHOULD fetch as many objects as you can (i.e. `first: 100`)
#
# The results of depagination are merged. Therefore, you receive one big output list.
# Similarly, the `pageInfo` object is removed from the result.
def graphql(query, page=None, **kwargs):
    "Perform a GraphQL query."
    params = { "query": query.strip(), "variables": json.dumps(kwargs) }
    token = os.environ.get('GITHUB_TOKEN', None)
    headers = {}

    if token is not None:
        headers["Authorization"] = f"token {token}"

    # Do the request and check for HTTP errors.
    reply = requests.post("https://api.github.com/graphql", json=params, headers=headers)
    if reply.status_code != 200:
        raise HTTPError(reply)

    # Check for GraphQL errors.
    data = reply.json()
    if "errors" in data:
        raise GraphQLError(data["errors"])
    data = data["data"]

    # Do depagination.
    if page is not None:
        obj = data
        for name in page:
            obj = obj[name]

        pi = obj.pop("pageInfo")
        if pi["hasNextPage"]:
            kwargs["cursor"] = pi["endCursor"]
            next = graphql(query, page, **kwargs)
            for name in page:
                next = next[name]

            obj["nodes"].extend(next["nodes"])

    return data

def create_card(column, content_id, content_type):
    try:
        column.create_card(content_id=content_id, content_type=content_type)
    except github.GithubException as e:
        error = e.data["errors"][0]
        if error["resource"] != "ProjectCard" or error["code"] != "unprocessable":
            raise
        print("Card already in project.")

def merge(pr):
    try:
        pr.merge(merge_method="rebase")
    except github.GithubException as e:
        error = e.data["errors"][0]
        if error["resource"] != "PullRequest":
            raise
        print(f"PR {pr.number} needs attention from the author. Assigning.")
        pr.add_to_assignees([pr.user.login])

def review_request(pr, reviewers):
    try:
        pr.create_review_request(reviewers)
    except github.GithubException as e:
        error = e.data["message"]
        if error != "Must have admin rights to Repository.":
            raise
        print(f"Enarxbot does not have correct permissions on this repo.")

def add_to_assignees(pr, additions):
    try:
        pr.add_to_assignees(*additions)
    except github.GithubException as e:
        error = e.data["message"]
        if error != "Must have admin rights to Repository.":
            raise
        print(f"Enarxbot does not have correct permissions on this repo.")

def remove_from_assignees(pr, removals):
    try:
        pr.add_to_assignees(*removals)
    except github.GithubException as e:
        error = e.data["message"]
        if error != "Must have admin rights to Repository.":
            raise
        print(f"Enarxbot does not have correct permissions on this repo.")

# Get all issue numbers related to a PR.
def get_related_issues(pr):
    # Regex to pick out closing keywords.
    regex = re.compile("(close[sd]?|fix|fixe[sd]?|resolve[sd]?)\s*:?\s+#(\d+)", re.I)

    # Extract all associated issues from closing keyword in PR
    for verb, num in regex.findall(pr.body):
        yield int(num)

    # Extract all associated issues from PR commit messages
    for c in pr.get_commits():
        for verb, num in regex.findall(c.commit.message):
            yield int(num)
