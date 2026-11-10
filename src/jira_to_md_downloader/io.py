from pathlib import Path


def read_issue_ids(path: Path) -> list[str]:
    ids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ids.append(stripped)
    return ids


def write_markdown(
    path: Path,
    summary: str,
    body_md: str,
    comments: list[tuple[str, str]] | None = None,
    omitted: int = 0,
) -> None:
    """comments: (heading, body markdown) pairs, oldest first."""
    content = f"# {summary}\n"
    if body_md.strip():
        content += f"\n{body_md.rstrip()}\n"
    if comments or omitted:
        content += "\n## Comments\n"
        for heading, body in comments or []:
            content += f"\n### {heading}\n"
            if body.strip():
                content += f"\n{body.rstrip()}\n"
        if omitted:
            content += f"\n({omitted} more comments are not shown; open the issue to read them.)\n"
    path.write_text(content, encoding="utf-8", newline="\n")
