"""Compare working-tree files against the git blobs they are pinned to.

Several batches assert that the user's uploaded references are untouched, by
comparing the working-tree bytes with `git show <pinned_commit>:<file>`. The
pinned commits only exist in a checkout that carries the full history; Arena
sandboxes are shallow clones (see `.git/shallow`), so the blob can be missing
even though the file itself is perfectly intact.

Callers must therefore distinguish "file was modified" from "history is not
available here" and report the latter as a skip, never as a pass.
"""

import subprocess
from pathlib import Path
from typing import Optional


def commit_available(rev: str, repo: Path) -> bool:
    """True when `rev` resolves to a commit object in this checkout."""
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{rev}^{{commit}}"],
        cwd=repo, capture_output=True,
    )
    return probe.returncode == 0


def pinned_blob(rev: str, path: str, repo: Path) -> Optional[bytes]:
    """Bytes of `path` at `rev`, or None if that object is not in this checkout.

    Never raises: an unavailable pinned commit is an environment limit, not a
    finding about the file.
    """
    if not commit_available(rev, repo):
        return None
    try:
        return subprocess.check_output(["git", "show", f"{rev}:{path}"], cwd=repo)
    except subprocess.CalledProcessError:
        return None
