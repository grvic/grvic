#!/usr/bin/env python3
"""Render the 'system_monitor.exe' GitHub activity card (light + dark) into an output folder.

Runs daily in GitHub Actions (see .github/workflows/profile.yml) with the built-in GITHUB_TOKEN.
Only public data is read. Local preview without network:  python .github/scripts/stats_card.py --mock --out dist
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from pixelkit import (FONT_MONO, FONT_UI, TB_SHINE_CSS, THEMES, esc, grad_defs, icon, ptext,  # noqa: E402
                      ptext_width, svg_doc, window)

QUERY = """query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes { stargazerCount languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { contributionCount date } } }
    }
  }
}"""


def fetch(login: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "grvic-profile"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "GraphQL error"))
    return payload["data"]["user"]


def mock() -> dict:
    rnd = random.Random(42)
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks, d = [], start
    while d <= today:
        week = []
        for _ in range(7):
            if d > today:
                break
            week.append({"contributionCount": rnd.choice([0, 0, 1, 2, 3, 5, 8, 12]), "date": d.isoformat()})
            d += dt.timedelta(days=1)
        weeks.append({"contributionDays": week})
    langs = [("Python", "#3572A5", 600), ("TypeScript", "#3178C6", 260), ("PowerShell", "#012456", 90), ("JavaScript", "#F1E05A", 40)]
    return {"followers": {"totalCount": 12}, "pullRequests": {"totalCount": 9},
            "repositories": {"totalCount": 7, "nodes": [{"stargazerCount": 1, "languages": {"edges": [
                {"size": s, "node": {"name": n, "color": c}} for n, c, s in langs]}}]},
            "contributionsCollection": {"contributionCalendar": {"totalContributions": sum(
                x["contributionCount"] for w in weeks for x in w["contributionDays"]), "weeks": weeks}}}


def summarize(u: dict) -> dict:
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    # current streak (today may still be empty, so it doesn't break the streak)
    cur, i = 0, len(days) - 1
    if i >= 0 and days[i]["contributionCount"] == 0:
        i -= 1
    while i >= 0 and days[i]["contributionCount"] > 0:
        cur += 1
        i -= 1
    best = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        best = max(best, run)
    langs: dict[str, list] = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"].get("color") or "#9AA6B8"])[0] += e["size"]
    total = sum(v[0] for v in langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:5]
    return {
        "total": cal["totalContributions"], "streak": cur, "best": best,
        "repos": u["repositories"]["totalCount"], "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "prs": u["pullRequests"]["totalCount"], "followers": u["followers"]["totalCount"],
        "weeks": cal["weeks"][-30:], "langs": [(n, v[1], v[0] / total) for n, v in top],
    }


def level(count: int, mx: int) -> int:
    if count <= 0:
        return 0
    q = count / max(mx, 1)
    return 1 if q < .25 else 2 if q < .5 else 3 if q < .75 else 4


def card(t: dict, s: dict | None, updated: str) -> str:
    W, H = 1280, 336
    body = [window(8, 8, W - 22, H - 22, "system_monitor.exe — GitHub activity", t, icon_name="chart",
                   subtitle=f"updated {updated}")]
    css = [TB_SHINE_CSS]
    if s is None:
        body.append(f'<text x="{W / 2}" y="{H / 2 + 10}" text-anchor="middle" font-family="{FONT_MONO}" font-size="20" fill="{t["ink2"]}">'
                    f"stats are offline right now — they refresh automatically every day</text>")
        return svg_doc(W, H, "".join(body), defs=grad_defs(t), style="".join(css), title="GitHub activity (offline)")
    # heatmap
    mx = max([d["contributionCount"] for w in s["weeks"] for d in w["contributionDays"]] + [1])
    x0, y0, cell = 36, 72, 16
    for wi, w in enumerate(s["weeks"]):
        for d in w["contributionDays"]:
            wd = (dt.date.fromisoformat(d["date"]).weekday() + 1) % 7  # Sunday first, like GitHub
            col = t["heat"][level(d["contributionCount"], mx)]
            body.append(f'<rect class="cell" style="animation-delay:{wi * .03:.2f}s" x="{x0 + wi * cell}" y="{y0 + wd * cell}" '
                        f'width="13" height="13" rx="2" fill="{col}" stroke="{t["ink"]}" stroke-opacity=".12"/>')
    ly = y0 + 7 * cell + 22
    body.append(f'<text x="{x0}" y="{ly}" font-family="{FONT_MONO}" font-size="12" fill="{t["ink2"]}">last 30 weeks</text>')
    lx = x0 + 30 * cell - 5 * 16 - 44
    body.append(f'<text x="{lx - 8}" y="{ly}" text-anchor="end" font-family="{FONT_MONO}" font-size="12" fill="{t["ink2"]}">less</text>')
    for k in range(5):
        body.append(f'<rect x="{lx + k * 16}" y="{ly - 11}" width="13" height="13" rx="2" fill="{t["heat"][k]}" stroke="{t["ink"]}" stroke-opacity=".12"/>')
    body.append(f'<text x="{lx + 5 * 16 + 4}" y="{ly}" font-family="{FONT_MONO}" font-size="12" fill="{t["ink2"]}">more</text>')
    # tiles
    tiles = [("CONTRIBUTIONS · 1Y", s["total"], "chart"), ("CURRENT STREAK · DAYS", s["streak"], "star"),
             ("BEST STREAK · DAYS", s["best"], "medal"), ("PUBLIC REPOS", s["repos"], "folder"),
             ("STARS EARNED", s["stars"], "star"), ("PULL REQUESTS", s["prs"], "pen")]
    tx0, ty0, tw, th = 548, 64, 222, 78
    for i, (label, val, ic) in enumerate(tiles):
        cx, cy = tx0 + (i % 3) * (tw + 12), ty0 + (i // 3) * (th + 12)
        body.append(f'<g transform="translate({cx} {cy})"><g class="tile" style="animation-delay:{.2 + i * .08:.2f}s">'
                    f'<rect x="3" y="3" width="{tw}" height="{th}" rx="8" fill="{t["shadow"]}" fill-opacity="{t["shadow_op"]}"/>'
                    f'<rect width="{tw}" height="{th}" rx="8" fill="{t["paper2"]}" stroke="{t["ink3"]}" stroke-width="2"/>'
                    + icon(ic, 12, 12, 1.25) +
                    f'<text x="40" y="28" font-family="{FONT_MONO}" font-size="12" font-weight="700" fill="{t["ink2"]}">{esc(label)}</text>'
                    + ptext(str(val), 14, 42, 4, t["accent"]) + "</g></g>")
    # languages bar
    by, bx, bw = 262, 36, W - 36 - 50
    body.append(f'<text x="{bx}" y="{by - 10}" font-family="{FONT_MONO}" font-size="12" font-weight="700" fill="{t["ink2"]}">TOP LANGUAGES · PUBLIC REPOS</text>')
    body.append(f'<g class="grow"><rect x="{bx}" y="{by}" width="{bw}" height="18" rx="4" fill="{t["paper2"]}" stroke="{t["ink"]}" stroke-width="2"/>')
    x = bx + 2
    for name, color, frac in s["langs"]:
        w_ = (bw - 4) * frac
        body.append(f'<rect x="{x:.1f}" y="{by + 2}" width="{w_:.1f}" height="14" fill="{color}"/>')
        x += w_
    body.append("</g>")
    x = bx
    for name, color, frac in s["langs"]:
        body.append(f'<rect x="{x}" y="{by + 32}" width="12" height="12" fill="{color}" stroke="{t["ink"]}" stroke-width="1.5"/>'
                    f'<text x="{x + 18}" y="{by + 43}" font-family="{FONT_UI}" font-size="14" fill="{t["ink"]}">{esc(name)} {frac * 100:.0f}%</text>')
        x += 40 + len(name) * 8.5 + 40
    css.append(".cell{animation:cin .35s steps(2,end) both}@keyframes cin{from{opacity:0}}"
               ".tile{animation:tin .5s cubic-bezier(.2,.9,.3,1.3) both}@keyframes tin{from{opacity:0;transform:translateY(8px)}}"
               ".grow{transform-box:fill-box;transform-origin:left center;animation:grow 1.2s cubic-bezier(.2,.8,.2,1) .3s both}"
               "@keyframes grow{from{transform:scaleX(0)}}")
    desc = (f'{s["total"]} contributions in the last year · current streak {s["streak"]} days · longest {s["best"]} days · '
            f'{s["repos"]} public repos · {s["stars"]} stars · {s["prs"]} pull requests · top languages: '
            + ", ".join(f"{n} {f * 100:.0f}%" for n, _, f in s["langs"]))
    return svg_doc(W, H, "".join(body), defs=grad_defs(t), style="".join(css), title="GitHub activity", desc=desc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    stats = None
    try:
        user = mock() if a.mock else fetch(os.environ["LOGIN"], os.environ["GITHUB_TOKEN"])
        stats = summarize(user)
    except Exception as exc:  # never fail the workflow: publish an 'offline' card instead
        print(f"::warning::stats unavailable: {exc}")
    updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    for th in ("light", "dark"):
        with open(os.path.join(a.out, f"stats-{th}.svg"), "w", encoding="utf-8") as f:
            f.write(card(THEMES[th], stats, updated))
    print("stats cards written to", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
