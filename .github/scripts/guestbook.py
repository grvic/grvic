#!/usr/bin/env python3
"""Add the author of a guestbook issue to data/guestbook.json.

Only the GitHub login is stored and published (never the issue title or body), so visitors
cannot inject text into the README. Invoked by .github/workflows/guestbook.yml.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
PATH = os.path.join(ROOT, "data", "guestbook.json")
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
KEEP = 200


def main() -> int:
    login = os.environ.get("LOGIN", "").strip()
    if not LOGIN_RE.match(login):
        print(f"skip: '{login}' is not a valid GitHub login")
        return 0
    data = {"signers": []}
    if os.path.exists(PATH):
        with open(PATH, encoding="utf-8") as f:
            data = json.load(f)
    signers = [s for s in data.get("signers", []) if s.get("login", "").lower() != login.lower()]
    signers.insert(0, {"login": login, "date": dt.date.today().isoformat()})
    data["signers"] = signers[:KEEP]
    with open(PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"signed: {login} ({len(signers)} total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
