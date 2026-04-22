from pathlib import Path


def read_issue_ids(path: Path) -> list[str]:
    ids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ids.append(stripped)
    return ids


def write_markdown(path: Path, summary: str, body_md: str) -> None:
    content = f"# {summary}\n"
    if body_md.strip():
        content += f"\n{body_md.rstrip()}\n"
    path.write_text(content, encoding="utf-8", newline="\n")
