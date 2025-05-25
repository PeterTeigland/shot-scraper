import time
import urllib.parse
import re

disallowed_re = re.compile("[^a-zA-Z0-9_-]")


def file_exists_never(filename):
    return False


def filename_for_url(url, ext=None, file_exists=file_exists_never, add_timestamp=None):
    ext = ext or "png"
    bits = urllib.parse.urlparse(url)
    filename = (bits.netloc + bits.path).replace(".", "-").replace("/", "-").rstrip("-")
    # Remove any characters outside of the allowed range
    base_filename = disallowed_re.sub("", filename).lstrip("-")
    filename = base_filename + "." + ext
    suffix = 0

    ts_string = ""
    if add_timestamp:
        # Append a timestamp to the filename
        # Very possibly not an appropriate place for this
        if add_timestamp == "epoch":
            ts_string = f"_{int(time.time())}"
        elif add_timestamp == "utc":
            ts_string = f"_{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}"
        elif add_timestamp == "local":
            ts_string = f"_{time.strftime('%Y%m%dT%H%M%S')}"
        else:
            raise ValueError("Invalid timestamp format. Use 'epoch', 'utc', or 'local'.")

    filename = f"{base_filename}{ts_string}.{ext}" 

    while file_exists(filename):
        suffix += 1
        filename = f"{base_filename}{ts_string}.{suffix}.{ext}"
        
    return filename


def url_or_file_path(url, file_exists=file_exists_never):
    # If url exists as a file, convert that to file:/
    file_path = file_exists(url)
    if file_path:
        return f"file:{file_path}"
    if not (url.startswith("http://") or url.startswith("https://")):
        return f"http://{url}"
    return url


def load_github_script(github_path: str) -> str:
    """
    Load JavaScript script from GitHub

    Format: username/repo/path/to/file.js
      or username/file.js which means username/shot-scraper-scripts/file.js
    """
    if not github_path.endswith(".js"):
        github_path += ".js"
    parts = github_path.split("/")

    if len(parts) == 2:
        # Short form: username/file.js
        username, file_name = parts
        parts = [username, "shot-scraper-scripts", file_name]

    if len(parts) < 3:
        raise ValueError(
            "GitHub path format should be 'username/repo/path/to/file.js' or 'username/file.js'"
        )

    username = parts[0]
    repo = parts[1]
    file_path = "/".join(parts[2:])

    # Fetch from GitHub
    import urllib.request

    url = f"https://raw.githubusercontent.com/{username}/{repo}/main/{file_path}"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                return response.read().decode("utf-8")
            else:
                raise ValueError(
                    f"Failed to load content from GitHub: HTTP {response.status}\n"
                    f"URL: {url}"
                )
    except urllib.error.URLError as e:
        raise ValueError(f"Error fetching from GitHub: {e}")
