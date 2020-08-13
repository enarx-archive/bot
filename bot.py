# SPDX-License-Identifier: Apache-2.0

import requests
import json
import os

PROJECT_PLANNING = "MDc6UHJvamVjdDQ5NjA4NDg="
PROJECT_PLANNING_TRIAGE = "MDEzOlByb2plY3RDb2x1bW4xMDAwMzg0MA=="
PROJECT_SPRINT = "MDc6UHJvamVjdDQ4MjA5OTM="

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
    url = os.environ.get("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql")

    params = { "query": query.strip(), "variables": json.dumps(kwargs) }
    token = os.environ.get('GITHUB_TOKEN', None)
    headers = {}

    if token is not None:
        headers["Authorization"] = f"token {token}"

    # Do the request and check for HTTP errors.
    reply = requests.post(url, json=params, headers=headers)
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
