<p align="center">
    <img src="https://github.com/GatorEducator/reporover/blob/main/.github/images/reporover-logo.svg" alt="RepoRover Logo" title="RepoRover Logo" />
</p>

# RepoRover

[![build](https://github.com/GatorEducator/reporover/actions/workflows/build.yml/badge.svg)](https://github.com/GatorEducator/reporover/actions/workflows/build.yml)
[![Code Style: ruff](https://img.shields.io/badge/Code%20Style-Ruff-blue.svg)](https://docs.astral.sh/ruff/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-Yes-blue.svg)](https://github.com/gkapfham/chasten/graphs/commit-activity)
[![License LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

## :sparkles: Introduction

**RepoRover** is your command-line buddy for managing and analyzing multiple
GitHub repositories at once! Whether you're an instructor managing student
repositories on GitHub Classroom or a developer handling multiple project
repositories, RepoRover is here to make your life easier and more fun! 

## :smile: Perspectives

- RepoRover is a tool that automatically manages and analyzes multiple GitHub
repositories within a GitHub organization. Here are three different perspectives
that people may have about the tool!
    - **Student perspective**: "I'm glad RepoRover made it easy for me to
    quickly receive feedback on my project repositories from GitHub Classroom.""
    - **Instructor perspective**: "RepoRover makes it much easier for me to
    oversee my students' repositories, manage access levels, and leave feedback
    on their pull requests."
    - **Developer perspective**: "Since RepoRover uses `uv` to manage its
    development, I found that it is very easy to add features, saving me a lot
    of time and effort."

## :rocket: Motivation

Handy command-line tools like `gh` let you access and manipulate a GitHub
repository. However, these tools may be limiting for certain scenarios because
they normally operate on a single repository. In contrast, RepoRover operates on
multiple repositories within the same GitHub organization. It's perfect for
managing project repositories created by GitHub Classroom, making it easier to
handle bulk operations efficiently. When you use RepoRover, you can say goodbye
to repetitive tasks and hello to automation! RepoRover roves across the remote
GitHub repositories for your student's projects, operating like a trusty robotic
dog as it fetches the results you need.

## :package: Installation and Configuration

### :wrench: Prerequisites

To use RepoRover, you'll need the following:

- Python 3.11+
- GitHub Personal Access Token

To use RepoRover, you'll need a GitHub Personal Access Token with the necessary
permissions to complete tasks like managing repositories and leave comments on
pull requests. Keep it handy and make sure to keep it secure!

### :inbox_tray: Installation

Installing RepoRover is a breeze with `pipx` or `uv`! Depending on which tool
you prefer, just run one of the following commands:

Install RepoRover with `pipx`:

```bash
pipx install reporover
```

Install RepoRover with `uv`:

```bash
uv tool install reporover
```

## :running: Running the Tool

RepoRover comes with several powerful commands to make your life easier when you
manage multiple GitHub repositories. The concrete examples of these commands use
a synthetic GitHub personal access token of
`ghp_12345ABCDEfghijKLMNOP67890qrstuvWXYZ`. Please note that this is a fake
token used for illustrative purposes. To run these commands you need to create
your own GitHub personal access token and use it in the command-line.

### :key: Access Command

Need to modify user access levels for multiple repositories? You can type the
command `reporover access --help` to change the access level for one or more
users, providing the following arguments and options:

```bash
Arguments:
*    github_org_url      TEXT  URL of GitHub organization [default: None] [required]
*    repo_prefix         TEXT  Prefix for GitHub repository [default: None] [required]
*    usernames_file      PATH  Path to JSON file with usernames [default: None] [required]
*    token               TEXT  GitHub token for authentication [default: None] [required]

Options:
--username            TEXT                                One or more usernames' accounts to modify [default: None]
--pr-number           INTEGER                             Pull request number in GitHub repository [default: 1]
--pr-message          TEXT                                Pull request number in GitHub repository
--access-level        [read|triage|write|maintain|admin]  The access level for user [default: read]
--help                                                    Show this message and exit.
```

Here is a concrete example that shows how to use the `reporover access` command.
Please note that in this command-line example on the following examples, the `$`
indicates that you should type the command at the prompt in your terminal window.

```bash
$ reporover access https://github.com/my-org repo-prefix usernames.json \
ghp_12345ABCDEfghijKLMNOP67890qrstuvWXYZ --username student1 --access-level write
```

This command will change the access level for the specified users in all
repositories matching the prefix. An example `usernames.json` file might include
the following content:

```json
{
  "usernames": [
    "gkapfham",
    "student1",
    "student2",
  ]
}
```

### :speech_balloon: Comment Command

Want to leave comments on pull requests for multiple repositories? RepoRover
makes it a breeze!

```bash
reporover comment <github_org_url> <repo_prefix> <usernames_file> <pr_message> <token> --username <username> --pr-number <pr_number>
```

Example:

```bash
reporover comment https://github.com/my-org repo-prefix usernames.json "Great job!" my-github-token --username student1 --pr-number 1
```

This command will leave a comment on the specified pull request for each
repository. Spread the love!

### :bar_chart: Status Command

Curious about the GitHub Actions status for multiple repositories? RepoRover has
your back!

```bash
reporover status <github_org_url> <repo_prefix> <usernames_file> <token> --username <username>
```

Example:

```bash
reporover status https://github.com/my-org repo-prefix usernames.json my-github-token --username student1
```

This command will fetch and display the latest GitHub Actions status for each
repository. Stay informed!

## :handshake: Contributing

We welcome contributions with open arms! If you find a bug or have a feature
request, please open an issue on our [GitHub
repository](https://github.com/your-repo/reporover/issues). Feel free to fork
the repository and submit a pull request. Let's make RepoRover even better
together. For any questions or feedback, please reach out to us via GitHub
Issues. We'd love to hear from you! Happy RepoRovering!
