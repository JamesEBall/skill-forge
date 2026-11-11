---
name: overleaf-olcli
description: Work with Overleaf projects from the terminal using the olcli CLI (@aloth/olcli). Use when asked to list, pull, push, sync, diff, or compile an Overleaf project, download its PDF or build logs, or read and answer Overleaf comments.
---

# Overleaf via olcli

`olcli` is a third-party command-line client for Overleaf by Alexander Loth (MIT, https://github.com/aloth/olcli). This skill only describes how to drive it. Written against version 0.13.0; run `olcli <command> --help` if a flag here is rejected.

Install:

```bash
npm install -g @aloth/olcli
```

## Authentication

Check first:

```bash
olcli whoami
```

If that fails, the user has to sign in themselves. Do not ask for, type, or store their Overleaf password or session cookie. Tell them to run `olcli auth` in their own terminal (it prompts for the password, or takes `--cookie` with the `overleaf_session2` value from their browser), then carry on once `olcli whoami` succeeds.

`olcli check` shows where credentials and config are being read from. Self-hosted instances need `--base-url <url>`, and older ones `--cookie-name overleaf.sid`.

## Everyday commands

| Task | Command |
| --- | --- |
| List projects | `olcli list` |
| Project details | `olcli info "<project>"` |
| Download a project into a folder | `olcli pull "<project>" <dir>` |
| See what differs from remote | `olcli diff "<project>" <dir>` |
| Upload local changes | `olcli push <dir>` |
| Pull then push | `olcli sync <dir>` |
| Compile and fetch the PDF | `olcli pdf "<project>" -o out.pdf` |
| Fetch build outputs | `olcli output log "<project>"` (also `bbl`, `aux`) |
| One file down / up | `olcli download <file> "<project>"`, `olcli upload <file> "<project>"` |
| Comments | `olcli comments list "<project>"`, then `reply`, `resolve`, `reopen`, `add` |

A project can be given by name or ID. After a `pull`, the folder has an `.olcli.json` that remembers the project, so `push`, `sync`, and `diff` can run there without naming it.

## Working rules

1. Pull before editing, so local files match what collaborators have written.
2. Before any upload, run the dry run and read it: `olcli push <dir> --dry-run` or `olcli sync <dir> --dry-run`.
3. `sync` propagates local deletions to Overleaf by default. Use `olcli sync <dir> --no-delete` unless the user wants remote files removed. `push` only deletes with `--delete`.
4. `pull --force` overwrites local files that are newer than the remote. Don't use it over uncommitted work.
5. Ask before `olcli delete`, `olcli comments delete`, `push --delete`, or anything under `olcli project` that renames in bulk. These change a shared document other people are editing.
6. LaTeX build artifacts are ignored on upload by default. Add project-specific patterns to `.olignore`; `olcli ignored <dir>` shows what is in effect.
7. When a compile fails, read `olcli output log` rather than guessing from the PDF step's error line.

## Typical loop

```bash
olcli pull "My Paper" paper
# edit files under paper/
olcli diff "My Paper" paper
olcli push paper --dry-run
olcli push paper
olcli pdf "My Paper" -o paper.pdf
```
