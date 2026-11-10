import argparse
import shutil
import sys
from pathlib import Path

from jira_to_md_downloader import convert, jira
from jira_to_md_downloader import io as issue_io


EXIT_OK = 0
EXIT_PARTIAL = 1
EXIT_FATAL = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jira-to-md-download",
        description="Download Jira issues from jira.cubrid.org as Markdown files.",
    )
    parser.add_argument(
        "issue_ids",
        nargs="*",
        metavar="ISSUE_ID",
        help="One or more Jira issue IDs. If omitted, IDs are read from --file.",
    )
    parser.add_argument(
        "-f",
        "--file",
        default="./issues.txt",
        help="Path to newline-separated issue ID list (default: ./issues.txt). Ignored when ISSUE_IDs are given.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="./out/",
        help="Output directory for generated .md files (default: ./out/).",
    )
    return parser


def _resolve_issue_ids(args: argparse.Namespace) -> list[str] | None:
    if args.issue_ids:
        return args.issue_ids
    path = Path(args.file)
    if not path.exists():
        print(
            f"error: no issue IDs provided and input file not found: {path}",
            file=sys.stderr,
        )
        return None
    try:
        return issue_io.read_issue_ids(path)
    except OSError as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        return None


def _comment_heading(comment: jira.Comment) -> str:
    # "2026-11-06T14:03:12.000+0900" -> "2026-11-06 14:03" (the server's local time)
    heading = f"{comment.author} · {comment.created[:16].replace('T', ' ')}"
    if comment.visibility:
        heading += f" · restricted to {comment.visibility}"
    return heading


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        creds = jira.load_credentials()
    except jira.MissingCredentials as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_FATAL

    if shutil.which("pandoc") is None:
        print("error: pandoc not found in PATH. Install pandoc first.", file=sys.stderr)
        return EXIT_FATAL

    issue_ids = _resolve_issue_ids(args)
    if issue_ids is None:
        return EXIT_FATAL
    if not issue_ids:
        print("error: no issue IDs to process.", file=sys.stderr)
        return EXIT_FATAL

    output_dir = Path(args.output)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(
            f"error: cannot create output directory {output_dir}: {e}",
            file=sys.stderr,
        )
        return EXIT_FATAL

    results: list[tuple[str, bool, str]] = []
    for issue_id in issue_ids:
        try:
            issue = jira.fetch_issue(creds, issue_id)
            body_md = convert.jira_to_markdown(issue.description or "")
            comments = [
                # headings inside a comment go below its "### author · date" heading
                (_comment_heading(c), convert.jira_to_markdown(c.body, shift_headings=3))
                for c in issue.comments
            ]
            out_path = output_dir / f"{issue_id}.md"
            issue_io.write_markdown(
                out_path,
                issue.summary,
                body_md,
                comments,
                issue.comment_total - len(issue.comments),
            )
            results.append((issue_id, True, str(out_path)))
        except (jira.IssueFetchError, convert.ConvertError, OSError) as e:
            print(f"warning: {issue_id}: {e}", file=sys.stderr)
            results.append((issue_id, False, str(e)))

    print()
    for issue_id, ok, detail in results:
        mark = "✓" if ok else "✗"
        arrow = "→"
        print(f"{mark} {issue_id}  {arrow} {detail}")

    succeeded = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - succeeded
    print()
    print(f"{succeeded} succeeded, {failed} failed.")

    return EXIT_OK if failed == 0 else EXIT_PARTIAL
