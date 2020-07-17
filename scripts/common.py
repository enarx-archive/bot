# SPDX-License-Identifier: Apache-2.0

def github():
    import github
    import os

    url = github.MainClass.DEFAULT_BASE_URL
    url = os.environ.get('GITHUB_API_URL', url)
    url = os.environ.get('PROXY_API_URL', url)

    token = os.environ['GITHUB_TOKEN']

    return github.Github(token, base_url=url)
