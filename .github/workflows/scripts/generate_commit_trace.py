
import json
import os
import html
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USERNAME = "ROHANYERNENI"
OUTPUT = Path("assets/commit-trace.svg")
API = "https://api.github.com"

TOKEN = os.environ.get("GH_TOKEN", "")

def fetch(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Rohan-Commit-Trace"
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def get_commits():
    repos = fetch(
        f"{API}/users/{USERNAME}/repos"
        "?type=owner&sort=pushed&per_page=100"
    )

    commits = []

    for repo in repos:
        if repo["fork"] or repo["archived"]:
            continue

        name = repo["name"]
        branch = repo["default_branch"]

        try:
            data = fetch(
                f"{API}/repos/{USERNAME}/{name}/commits"
                f"?sha={branch}&per_page=5"
            )

            for item in data:
                info = item["commit"]
                author = info.get("author") or info.get("committer") or {}

                commits.append({
                    "repo": name,
                    "message": info["message"].splitlines()[0],
                    "sha": item["sha"][:7],
                    "date": author.get("date", "")
                })

        except Exception as error:
            print(f"Skipping {name}: {error}")

    commits.sort(key=lambda c: c["date"], reverse=True)
    return commits[:7]


def shorten(value, limit):
    if len(value) > limit:
        return value[:limit - 3] + "..."
    return value


def generate_svg(commits):
    width = 1100
    height = 440

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        """
        <defs>
          <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#101820"/>
            <stop offset="100%" stop-color="#080B10"/>
          </linearGradient>
          <pattern id="grid" width="32" height="32"
                   patternUnits="userSpaceOnUse">
            <path d="M32 0H0V32" fill="none"
                  stroke="#26343D" stroke-opacity=".22"/>
          </pattern>
        </defs>

        <rect width="1100" height="440" rx="12" fill="url(#panel)"/>
        <rect width="1100" height="440" rx="12" fill="url(#grid)"/>
        <rect x="1" y="1" width="1098" height="438"
              rx="12" fill="none" stroke="#26343D"/>

        <text x="38" y="48" fill="#91A5B0"
              font-family="monospace" font-size="13"
              letter-spacing="3">ENGINEERING / ACTIVITY LOG</text>

        <text x="38" y="91" fill="#E2E8EC"
              font-family="monospace" font-size="27"
              font-weight="bold">COMMIT TRACE</text>

        <circle cx="1010" cy="42" r="5" fill="#6D9C84"/>
        <text x="1025" y="47" fill="#8FA3AD"
              font-family="monospace" font-size="11">SYNCED</text>

        <path d="M38 112H1062" stroke="#34434C"/>

        <text x="38" y="143" fill="#607985"
              font-family="monospace" font-size="11">REPOSITORY</text>
        <text x="350" y="143" fill="#607985"
              font-family="monospace" font-size="11">COMMIT MESSAGE</text>
        <text x="890" y="143" fill="#607985"
              font-family="monospace" font-size="11">HASH</text>
        <text x="990" y="143" fill="#607985"
              font-family="monospace" font-size="11">DATE</text>
        """
    ]

    if not commits:
        svg.append("""
        <text x="38" y="205" fill="#8FA3AD"
              font-family="monospace" font-size="14">
          No public commits found.
        </text>
        """)
    else:
        for index, commit in enumerate(commits):
            y = 180 + index * 35

            repo = html.escape(shorten(commit["repo"], 22))
            message = html.escape(shorten(commit["message"], 55))
            sha = html.escape(commit["sha"])

            try:
                date = datetime.fromisoformat(
                    commit["date"].replace("Z", "+00:00")
                ).strftime("%b %d")
            except ValueError:
                date = "Unknown"

            svg.append(f"""
            <circle cx="43" cy="{y-4}" r="3" fill="#648B9C"/>

            <text x="58" y="{y}" fill="#91A5B0"
                  font-family="monospace" font-size="12">
              {repo}
            </text>

            <text x="350" y="{y}" fill="#D2DCE2"
                  font-family="monospace" font-size="12">
              {message}
            </text>

            <text x="890" y="{y}" fill="#648B9C"
                  font-family="monospace" font-size="12">
              {sha}
            </text>

            <text x="990" y="{y}" fill="#82939D"
                  font-family="monospace" font-size="11">
              {date}
            </text>

            <path d="M38 {y+13}H1062"
                  stroke="#26343D" stroke-opacity=".65"/>
            """)

    svg.append(f"""
      <text x="38" y="415" fill="#526975"
            font-family="monospace" font-size="10">
        SOURCE: GITHUB PUBLIC REPOSITORIES
      </text>

      <text x="1062" y="415" text-anchor="end"
            fill="#526975" font-family="monospace" font-size="10">
        LAST SYNC: {now}
      </text>
    </svg>
    """)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")


if __name__ == "__main__":
    commits = get_commits()
    generate_svg(commits)
    print(f"Generated {OUTPUT} with {len(commits)} commits.")
