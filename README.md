# enarxbot

`enarxbot` is a set of Github-native tools for project organization designed to
be simple, stateless, and secure. It's built on Github Actions, and aims to
provide common-sense automation on top of Github's existing features (issues,
PRs, assignees, etc).

At the moment, this work is partially specific to the Enarx project -- though
modularization efforts are underway to make it generally available.

## Dashboard

See the status of Enarxbot on all repositories that use it.

![bot](https://github.com/enarx/bot/workflows/enarxbot/badge.svg)
![enarx-keepldr](https://github.com/enarx/enarx-keepldr/workflows/enarxbot/badge.svg)
![enarx-wasmldr](https://github.com/enarx/enarx-wasmldr/workflows/enarxbot/badge.svg)
![frenetic](https://github.com/enarx/frenetic/workflows/enarxbot/badge.svg)
![packet.com](https://github.com/enarx/packet.com/workflows/enarxbot/badge.svg)
![enarx.github.io](https://github.com/enarx/enarx.github.io/workflows/enarxbot/badge.svg)

## Usage

Setup takes just a few straightforward steps.

### Authenticating with Github

Enarxbot relies on a [personal access token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token)
to interact with Github and work its magic. If you're setting up a new
repository, you'll need to provision one with the `public_repo` and `write:org`
scopes enabled and make it available as a [shared secret](https://docs.github.com/en/free-pro-team@latest/actions/reference/encrypted-secrets)
to your repository, using the name `BOT_TOKEN`. (Organization-wide secrets also work.)

Github _strongly_
[recommends](https://docs.github.com/en/free-pro-team@latest/actions/learn-github-actions/security-hardening-for-github-actions#considering-cross-repository-access)
creating a separate account for PATs like this, and scoping access to that
account accordingly. The Enarx project uses the `enarxbot` account to provision
its key, for example.

If you're setting up an Enarx organization repository, you don't need to do this
step -- our token is already set up.

### Enabling Enarxbot on a repository

Once a token is available to your repo, the final step is to enable Enarxbot via
Github Actions. To do so, create a new workflow under `.github/workflows` with
the following structure:

```yml
name: enarxbot

on:
  check_run:
  check_suite:
  create:
  delete:
  deployment:
  deployment_status:
  fork:
  gollum:
  issue_comment:
  issues:
  label:
  milestone:
  page_build:
  project:
  project_card:
  project_column:
  public:
  pull_request_target:
    types:
      - assigned
      - unassigned
      - labeled
      - unlabeled
      - opened
      - edited
      - closed
      - reopened
      - synchronize
      - ready_for_review
      - locked
      - unlocked
      - review_requested
      - review_request_removed
  push:
  registry_package:
  release:
  status:
  watch:
  schedule:
    - cron: '*/15 * * * *'
  workflow_dispatch:

jobs:
  enarxbot:
    runs-on: ubuntu-latest
    env:
      BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
    name: enarxbot
    steps:
      - uses: enarx/bot@master
```

Have a look at [this repository's workflow](.github/workflows/enarxbot.yml) for
an example.

Once this is in place, you're done! Enarxbot should begin working on your repo
when certain events (ex. an issue/PR gets opened) happen.

## FAQ

### Why do I need to listen for every single Actions event in my workflow?

Enarxbot filters the actions it takes based on the event that occurs. For
example, it will request new reviewers when a new PR is opened, but it won't
attempt to do label management until that PR has been labeled.

Enarxbot doesn't _need_ every trigger to work properly -- in fact, it doesn't
use most of them at all. However, there's little downside to enabling all of
them, and doing so automatically opts your repository into new automation as
it's released.

### What happens if I don't set `BOT_TOKEN` properly?

If Enarxbot can't find a valid token under `BOT_TOKEN`, it will fail gracefully
with a note reminding you to add one if you want to opt into automation. It
should _not_ send you a failure email about it.

This avoids forks of repositories that have Enarxbot enabled from spamming their
authors with needless Actions failure emails about improperly-set credentials.
