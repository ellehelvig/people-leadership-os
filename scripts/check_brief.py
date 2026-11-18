"""Check the weekly CPO brief against the open issues it summarizes.

The brief is only useful if the CPO can trust it. This script checks the rules in
.github/copilot-instructions.md that can be checked mechanically:

1. Every bullet in the brief cites at least one issue, like [#4].
2. Every cited issue exists and is still open.
3. Every open issue with no owner is named in the brief's owner-gap note.

It also lists open issues the brief does not mention, as a prompt for the
Chief of Staff, not a failure. Some issues are rightly left out of a brief.

It does not judge whether a claim is a fair reading of its issue. A person
still has to do that.

Usage:
    python scripts/check_brief.py                         # live issues via the GitHub API
    python scripts/check_brief.py --issues-json FILE      # offline, from a saved snapshot
    python scripts/check_brief.py --brief briefs/X.md     # a specific brief

Live mode reads GITHUB_REPOSITORY and GITHUB_TOKEN, which GitHub Actions sets.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CITATION = re.compile(r"\[#(\d+)\]")
BARE_REF = re.compile(r"#(\d+)\b")
NO_OWNER = {"", "_no response_", "none", "n/a", "tbd", "unassigned"}


@dataclass
class Issue:
    number: int
    title: str
    state: str
    body: str

    @property
    def owner(self) -> str:
        return form_field(self.body, "Owner")

    @property
    def has_owner(self) -> bool:
        return self.owner.strip().lower() not in NO_OWNER


@dataclass
class Report:
    brief: str
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def markdown(self) -> str:
        lines = [f"## Brief check: `{self.brief}`", ""]
        if self.ok:
            lines.append("**Pass.** Every bullet cites an open issue and every owner gap is named.")
        else:
            lines.append(f"**{len(self.errors)} problem(s) to fix before this brief goes to the CPO:**")
            lines.append("")
            lines += [f"- {e}" for e in self.errors]
        if self.notes:
            lines += ["", "**For the Chief of Staff to consider:**", ""]
            lines += [f"- {n}" for n in self.notes]
        lines += ["", "This check covers citations and owners only. Whether each line is a fair reading of its issue still needs a person."]
        return "\n".join(lines) + "\n"


def form_field(body: str, label: str) -> str:
    """Return the text under a '### Label' heading from a GitHub issue form."""
    match = re.search(rf"^###\s+{re.escape(label)}\s*$\n(.*?)(?=^###\s|^---\s*$|\Z)", body or "", re.M | re.S)
    return match.group(1).strip() if match else ""


def latest_brief(briefs_dir: Path) -> Path:
    briefs = sorted(briefs_dir.glob("*.md"))
    if not briefs:
        raise SystemExit(f"No briefs found in {briefs_dir}")
    return briefs[-1]


def load_issues_json(path: Path) -> dict[int, Issue]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        i["number"]: Issue(i["number"], i["title"], i["state"], i.get("body") or "")
        for i in raw
        if "pull_request" not in i
    }


def fetch_issues(repo: str, token: str) -> dict[int, Issue]:
    issues: dict[int, Issue] = {}
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100&page={page}"
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not batch:
            return issues
        for i in batch:
            if "pull_request" in i:
                continue
            issues[i["number"]] = Issue(i["number"], i["title"], i["state"], i.get("body") or "")
        page += 1


def check(brief_text: str, brief_name: str, issues: dict[int, Issue]) -> Report:
    report = Report(brief_name)
    cited: set[int] = set()
    owner_gap_line = ""

    for lineno, line in enumerate(brief_text.splitlines(), start=1):
        if line.lower().startswith("**owner gap"):
            owner_gap_line = line
        if not line.startswith("- "):
            continue
        refs = [int(n) for n in CITATION.findall(line)]
        if not refs:
            report.errors.append(f"Line {lineno} has no issue citation: \"{line[2:72].strip()}...\"")
        cited.update(refs)

    for number in sorted(cited):
        issue = issues.get(number)
        if issue is None:
            report.errors.append(f"#{number} is cited but does not exist.")
        elif issue.state != "open":
            report.errors.append(f"#{number} ({issue.title}) is cited but closed. Update or drop the line.")

    open_issues = {n: i for n, i in issues.items() if i.state == "open"}
    gaps = sorted(n for n, i in open_issues.items() if not i.has_owner)
    named = {int(n) for n in BARE_REF.findall(owner_gap_line)}

    for number in gaps:
        if number not in named:
            report.errors.append(f"#{number} ({open_issues[number].title}) has no owner but is missing from the owner-gap note.")
    for number in sorted(named - set(gaps)):
        if number in open_issues:
            report.notes.append(f"#{number} is in the owner-gap note but now has an owner ({open_issues[number].owner}).")
    if not gaps and not owner_gap_line:
        report.notes.append("No open issue lacks an owner. The brief can say so.")

    for number in sorted(set(open_issues) - cited - named):
        report.notes.append(f"#{number} ({open_issues[number].title}) is open but not in this brief.")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brief", type=Path, help="Brief to check. Defaults to the latest in briefs/.")
    parser.add_argument("--issues-json", type=Path, help="Offline issue snapshot instead of the GitHub API.")
    args = parser.parse_args(argv)

    brief_path = args.brief or latest_brief(ROOT / "briefs")
    if args.issues_json:
        issues = load_issues_json(args.issues_json)
    else:
        repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
        if not repo or not token:
            parser.error("Set GITHUB_REPOSITORY and GITHUB_TOKEN, or pass --issues-json.")
        issues = fetch_issues(repo, token)

    try:
        brief_name = str(brief_path.resolve().relative_to(ROOT))
    except ValueError:
        brief_name = str(brief_path)
    report = check(brief_path.read_text(encoding="utf-8"), brief_name, issues)
    output = report.markdown()
    print(output)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(output)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
