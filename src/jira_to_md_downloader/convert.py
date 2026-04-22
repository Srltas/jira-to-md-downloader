import subprocess


class ConvertError(Exception):
    pass


def jira_to_markdown(jira_wiki: str) -> str:
    if not jira_wiki:
        return ""
    try:
        result = subprocess.run(
            ["pandoc", "-f", "jira", "-t", "gfm"],
            input=jira_wiki,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise ConvertError(f"pandoc failed: {e.stderr.strip()}") from e
    return result.stdout
