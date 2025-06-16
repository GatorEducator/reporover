<p align="center">
  <img src="https://github.com/GatorEducator/reporover/blob/main/.github/images/reporover-logo.svg" alt="RepoRover Logo"
    title="RepoRover Logo" />
</p>

# RepoRover

[![Build](https://github.com/GatorEducator/reporover/actions/workflows/build.yml/badge.svg)](https://github.com/GatorEducator/reporover/actions/workflows/build.yml)
[![Coverage](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.totals.percent_covered_display&suffix=%25&url=https%3A//raw.githubusercontent.com/wiki/GatorEducator/reporover/coverage.json)](https://github.com/GatorEducator/reporover)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/reporover)
![PyPI - Version](https://img.shields.io/pypi/v/reporover?logoColor=blue&color=blue)
[![Code Style: ruff](https://img.shields.io/badge/style-Ruff-blue.svg)](https://docs.astral.sh/ruff/)
[![Maintenance](https://img.shields.io/badge/maintained%3F-Yes-blue.svg)](https://github.com/gkapfham/chasten/graphs/commit-activity)
[![License LGPL v3](https://img.shields.io/badge/license-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

## :sparkles: Table of Contents

<!---toc start-->

- [:robot: Introduction](#robot-introduction)
- [:smile: Perspectives](#smile-perspectives)
- [:rocket: Motivation](#rocket-motivation)
- [:package: Installation and Configuration](#package-installation-and-configuration)
- [:wrench: Prerequisites](#wrench-prerequisites)
- [:inbox_tray: Installation](#inbox_tray-installation)
- [:dog: Running RepoRover](#dog-running-reporover)
- [:key: Access Command](#key-access-command)
- [:bulb: Comment Command](#speech_balloon-comment-command)
- [:bar_chart: Status Command](#bar_chart-status-command)
- [:handshake: Contributing](#handshake-contributing)

<!---toc end-->

## :robot: Introduction

RepoRover is your command-line companion for managing and analyzing multiple
GitHub repositories at once! Whether you're an instructor managing student
repositories on GitHub Classroom or a developer handling multiple project
repositories, RepoRover is here to make your life easier and more fun!

## :smile: Perspectives

RepoRover is a tool that automatically manages and analyzes multiple GitHub
repositories within a GitHub organization. Here are three different perspectives
that people may have about the tool!

- **Student perspective**: "I'm glad RepoRover made it easy for me to quickly
receive feedback on my project repositories from GitHub Classroom."
- **Instructor perspective**: "RepoRover makes it much easier for me to oversee
my students' repositories, manage access levels, and leave feedback on their
pull requests."
- **Developer perspective**: "Since RepoRover uses `uv` to manage its
development, I found that it is very easy to add features, saving me a lot of
time and effort."

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

You can easily install RepoRover with `pipx` or `uv`! Depending on which tool
you prefer, just run one of the following commands:

Install RepoRover with `pipx`:

```bash
pipx install reporover
```

Install RepoRover with `uv`:

```bash
uv tool install reporover
```

If you do not want to install `reporover` directly but you have `uv` installed,
then you can also replace the `reporover` command in the following instructions
with `uvx reporover`. This will run the `reporover` tool with the `uvx` command
without requiring you to install it globally on your system.

## :dog: Running RepoRover

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
Usage: reporover access [OPTIONS] github_org_url repo_prefix usernames_file token

Arguments:
* github_org_url TEXT URL of GitHub organization [default: None] [required]
* repo_prefix TEXT Prefix for GitHub repository [default: None] [required]
* usernames_file PATH Path to JSON file with usernames [default: None] [required]
* token TEXT GitHub token for authentication [default: None] [required]

Options:
--username TEXT One or more usernames accounts to modify [default: None]
--pr-number INTEGER Pull request number in GitHub repository [default: 1]
--pr-message TEXT Pull request number in GitHub repository
--access-level [read|triage|write|maintain|admin] The access level for user [default: read]
--help Show this message and exit.
```

Here is a concrete example that shows how to use the `reporover access` command.
Please note that in this command-line example on the following examples, the `$`
indicates that you should type the command at the prompt in your terminal
window.

```bash
$ reporover access https://github.com/my-org repo-prefix usernames.json \
ghp_12345ABCDEfghijKLMNOP67890qrstuvWXYZ --username student1 --access-level write
```

This command will change the access level for the specified users in all
repositories matching the prefix. In the context of GitHub Classroom, the
`repo_prefix` is the initial part of the name of a GitHub repository that is
shared in common by the individual repository for each student who accepted the
assignment. Finally, an example `usernames.json` file might include the
following content for a class that has two students and `gkapfham` as the course
instructor:

```json
{
"usernames": ["gkapfham", "student1", "student2"]
}
```

### :bulb: Comment Command

Need to leave comments on pull requests for multiple repositories? You can type
the command `reporover comment --help` to learn how to comment on an existing
pull request in the GitHub repository for one or more users. To run this command
you need to provide the following arguments and options:

```bash
Usage: reporover comment [OPTIONS] github_org_url repo_prefix usernames_file pr_message token

Arguments:
* github_org_url TEXT URL of GitHub organization [default: None] [required]
* repo_prefix TEXT Prefix for GitHub repository [default: None] [required]
* usernames_file PATH Path to JSON file with usernames [default: None] [required]
* pr_message TEXT Pull request message for GitHub repository [default: None] [required]
* token TEXT GitHub token for authentication [default: None] [required]

Options:
--username TEXT One or more usernames accounts to modify [default: None]
--pr-number INTEGER Pull request number in GitHub repository [default: 1]
--help Show this message and exit.
```

Here is a concrete example that shows how to use the `reporover comment`
command:

```bash
$ reporover comment https://github.com/my-org repo-prefix usernames.json \
"✨Update?" ghp_12345ABCDEfghijKLMNOP67890qrstuvWXYZ --pr-number 1
```

This command will leave a comment on the specified pull request for each
matching repository. When using this command, it is important to note that, if
configured correctly, GitHub Classroom will automatically create pull request
number `1` that can be used for sending the comment.

### :cyclone: Clone Command

Need to clone multiple GitHub repositories to your local machine? The clone
command makes it easy to download all repositories matching a prefix to a local
directory. You can type the command `reporover clone --help` to learn how to
clone repositories from a GitHub organization. To run this command you need to
provide the following arguments and options:

```bash
Usage: reporover clone [OPTIONS] github_org_url repo_prefix usernames_file token destination_directory

Arguments:
* github_org_url TEXT URL of GitHub organization [default: None] [required]
* repo_prefix TEXT Prefix for GitHub repository [default: None] [required]
* usernames_file PATH Path to JSON file with usernames [default: None] [required]
* token TEXT GitHub token for authentication [default: None] [required]
* destination_directory PATH Local directory to clone repositories into [default: None] [required]

Options:
--username TEXT One or more usernames accounts to clone [default: None]
--help Show this message and exit.
```

Here is a concrete example that shows how to use the `reporover clone` command:

```bash
$ reporover clone https://github.com/my-org repo-prefix usernames.json \
ghp_12345ABCDEfghijKLMNOP67890qrstuvWXYZ /tmp/cloned-repos --username student1
```

This command will clone the specified repositories to the chosen local
directory. Each repository will be cloned into a subdirectory named after the
full repository name. This is particularly useful for instructors who want to
download all student repositories for local review, grading, or analysis. The
command respects the username filtering, so you can clone repositories for
specific students or all students at once.

### :hammer: Commit Command

Need to commit one or more files to multiple GitHub repositories? The commit
command allows you to add and commit files to repositories across your
organization. You can type the command `reporover commit --help` to learn how to
commit files to repositories. To run this command you need to provide the
following arguments and options:

```bash
Usage: reporover commit [OPTIONS] github_org_url repo_prefix usernames_file token directory files commit_message
destination_directory

Arguments:
* github_org_url TEXT URL of GitHub organization [default: None] [required]
* repo_prefix TEXT Prefix for GitHub repository [default: None] [required]
* usernames_file PATH Path to JSON file with usernames [default: None] [required]
* token TEXT GitHub token for authentication [default: None] [required]
* directory PATH Directory containing the file(s) to commit [default: None] [required]
* files PATH File(s) to commit [default: None] [required]
* commit_message TEXT Commit message for the files [default: None] [required]
* destination_directory PATH Destination directory inside the GitHub repository [default: None] [required]

Options:
--username TEXT One or more usernames accounts to modify [default: None]
--help Show this message and exit.
```

Here is a concrete example that shows how to use the `reporover commit` command:

```bash
$ reporover commit https://github.com/my-org repo-prefix usernames.json \
ghp_12345ABCDEfghijKLMNOP67890qrstuvWXYZ /local/files test.py main.py \
"Add new test files" src --username student1
```

This command will commit the specified files from your local directory to the
destination directory in each matching repository. This sub-command of
`reporover` is perfect using the command-line to distribute starter files,
tests, or updates to all student repositories at once.

### :bar_chart: Status Command

Curious about the GitHub Actions status for multiple repositories? RepoRover has
can fetch that information for you! You can type the command `reporover status
--help` to learn how to comment on an existing pull request in the GitHub
repository for one or more users. To run this command you need to provide the
following arguments and options:

```bash
Usage: reporover status [OPTIONS] github_org_url repo_prefix usernames_file token

Get the GitHub Actions status for repositories.

Arguments:
* github_org_url TEXT URL of GitHub organization [default: None] [required]
* repo_prefix TEXT Prefix for GitHub repository [default: None] [required]
* usernames_file PATH Path to JSON file with usernames [default: None] [required]
* token TEXT GitHub token for authentication [default: None] [required]

Options:
--username TEXT One or more usernames accounts to modify [default: None]
--pr-number INTEGER Pull request number in GitHub repository [default: 1]
--pr-message TEXT Pull request number in GitHub repository
--access-level [read|triage|write|maintain|admin] The access level for user [default: read]
--help Show this message and exit.
```

Here is a concrete example that shows how to use the `reporover status` command:

```bash
reporover status https://github.com/my-org repo-prefix usernames.json ghp_12345ABCDEfghijKLMNOP67890qrstuvWXYZ
```

This command will fetch and display the latest GitHub Actions status for each
repository. If you are a course instructor, this will help you to quickly stay
informed about the status of each student's project, all without leaving the
comfort of your terminal window!

## :handshake: Contributing

The RepoRover developers welcome contributions with wagging tails! If you find a
bug or have a feature request, please open an issue on our [issue
tracker](https://github.com/your-repo/reporover/issues). Potential contributions
can fork this repository and submit a pull request with their suggested changes.
Questions or comments about RepoRover? You can direct those to the development
by opening an issue in our [issue
tracker](https://github.com/your-repo/reporover/issues). We'd love to hear from
and collaborate with you! Happy RepoRovering!
