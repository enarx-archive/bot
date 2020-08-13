# SPDX-License-Identifier: Apache-2.0

import requests
import json
import os

PROJECTS = {
    'Conferences': 'MDc6UHJvamVjdDQ5OTI0MzM=',
    'Planning': 'MDc6UHJvamVjdDQ5NjA4NDg=',
    'Sprint': 'MDc6UHJvamVjdDQ4MjA5OTM='
}

COLUMNS = {
    'Conferences': {
        'Accepted': 'MDEzOlByb2plY3RDb2x1bW4xMDA1NzA1Ng==',
        'Completed': 'MDEzOlByb2plY3RDb2x1bW4xMDA1NzA1OQ==',
        'Considering': 'MDEzOlByb2plY3RDb2x1bW4xMDA1NzA0OQ==',
        'Delivered': 'MDEzOlByb2plY3RDb2x1bW4xMDA1NzA1Nw==',
        'Submitted': 'MDEzOlByb2plY3RDb2x1bW4xMDA1NzA1Mw=='
    },
    'Planning': {
        'Accepted': 'MDEzOlByb2plY3RDb2x1bW4xMDAwMzg0OQ==',
        'Assigned': 'MDEzOlByb2plY3RDb2x1bW4xMDAwODk1MQ==',
        'Backlog': 'MDEzOlByb2plY3RDb2x1bW4xMDAwMzg0Nw==',
        'Done': 'MDEzOlByb2plY3RDb2x1bW4xMDAwOTI3OA==',
        'Nominated': 'MDEzOlByb2plY3RDb2x1bW4xMDAwMzg0OA==',
        'Triage': 'MDEzOlByb2plY3RDb2x1bW4xMDAwMzg0MA=='
    },
    'Sprint': {
        'Active': 'MDEzOlByb2plY3RDb2x1bW4xMDQxMTcwOA==',
        'Assigned': 'MDEzOlByb2plY3RDb2x1bW45ODA1MjQ5',
        'Done': 'MDEzOlByb2plY3RDb2x1bW45ODA0Mzc2',
        'Reviewed': 'MDEzOlByb2plY3RDb2x1bW4xMDQxMTcyMg==',
        'Reviewing': 'MDEzOlByb2plY3RDb2x1bW45ODA1MjY1'
    }
}

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
