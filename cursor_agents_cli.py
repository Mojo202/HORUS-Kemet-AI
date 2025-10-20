#!/usr/bin/env python3

import argparse
import json
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

BCID_REGEX = re.compile(r"bc-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)


def parse_bcid_from_url(url: str) -> Optional[str]:
    """Extract bcId from a URL query string or anywhere in the URL.

    Supports parameters like `selectedBcId` or `bcId`, or any `bc-...` substring.
    """
    # Quick extraction from query params
    match = re.search(r"[?&](?:selectedBcId|bcId)=([^&#]+)", url, flags=re.IGNORECASE)
    if match:
        candidate = match.group(1)
        bcid_match = BCID_REGEX.search(candidate)
        if bcid_match:
            return bcid_match.group(0)

    # Fallback: anywhere in the URL
    bcid_match = BCID_REGEX.search(url)
    if bcid_match:
        return bcid_match.group(0)

    return None


def build_cookie_header(raw_cookie: Optional[str], cookie_file: Optional[str]) -> Optional[str]:
    if raw_cookie:
        return raw_cookie.strip()
    if cookie_file:
        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError as exc:
            print(f"[error] Failed to read cookie file: {exc}", file=sys.stderr)
            return None
    return None


def fetch_html(url: str, cookie_header: Optional[str], timeout: float) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
    }
    if cookie_header:
        headers["Cookie"] = cookie_header

    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_next_data(html: str) -> Optional[Dict[str, Any]]:
    """Extract Next.js __NEXT_DATA__ JSON from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", {"id": "__NEXT_DATA__", "type": "application/json"})
    if not tag or not tag.text:
        # Fallback: try to find any script containing JSON-ish content with __NEXT_DATA__ pattern
        # Though Next.js typically uses a dedicated tag.
        return None
    try:
        return json.loads(tag.text)
    except json.JSONDecodeError:
        return None


def iterate_json_nodes(node: Any, path: Tuple[Any, ...] = ()) -> Iterable[Tuple[Tuple[Any, ...], Any]]:
    """Depth-first traversal yielding (path, node)."""
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from iterate_json_nodes(value, path + (key,))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            yield from iterate_json_nodes(value, path + (idx,))


def find_bc_objects(data: Dict[str, Any], bcid_filter: Optional[str]) -> List[Dict[str, Any]]:
    """Find objects containing a bc id. If bcid_filter is provided, restrict to that id."""
    results: List[Dict[str, Any]] = []

    for _path, node in iterate_json_nodes(data):
        if isinstance(node, dict):
            # Check common fields
            candidates: List[str] = []
            for field in ("id", "bcId", "bc_id", "bcid"):
                value = node.get(field)
                if isinstance(value, str):
                    candidates.append(value)
            # Also scan any string field for inline bc-
            for value in node.values():
                if isinstance(value, str):
                    candidates.append(value)

            # Evaluate candidates
            for candidate in candidates:
                match = BCID_REGEX.search(candidate)
                if not match:
                    continue
                bcid = match.group(0)
                if bcid_filter and bcid.lower() != bcid_filter.lower():
                    continue
                # Avoid duplicates by id + some stable fields
                results.append(node)
                break
    return results


def summarize_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a concise summary from an object dict."""
    keys_of_interest = [
        "id",
        "bcId",
        "name",
        "title",
        "displayName",
        "description",
        "createdAt",
        "updatedAt",
        "ownerId",
        "visibility",
        "slug",
        "type",
    ]
    summary: Dict[str, Any] = {}
    for key in keys_of_interest:
        if key in obj:
            summary[key] = obj[key]
    # Heuristic: include any key that looks important if few standard keys were present
    if len(summary) <= 2:
        for key in list(obj.keys())[:10]:  # cap to avoid huge output
            if key not in summary:
                summary[key] = obj[key]
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch Cursor Agents page, parse Next.js __NEXT_DATA__, and search for agent objects by bcId."
        )
    )
    parser.add_argument("--url", required=True, help="Cursor agents URL, e.g. https://cursor.com/agents?selectedBcId=bc-...")
    parser.add_argument("--bcid", help="Explicit bcId to search for; if omitted, derived from URL")
    parser.add_argument("--cookie", help="Cookie header string to include in the request")
    parser.add_argument("--cookie-file", help="Path to a file containing Cookie header contents")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds (default: 20)")
    parser.add_argument(
        "--format",
        choices=["summary", "json", "pretty"],
        default="summary",
        help="Output format: summary|json|pretty (default: summary)",
    )
    parser.add_argument("--output", help="Optional path to write extracted JSON data")

    args = parser.parse_args(argv)

    bcid = args.bcid or parse_bcid_from_url(args.url)
    if not bcid:
        print(
            "[warn] No bcId found in arguments or URL. Will search for any bc-* objects.",
            file=sys.stderr,
        )

    cookie_header = build_cookie_header(args.cookie, args.cookie_file)

    try:
        html = fetch_html(args.url, cookie_header=cookie_header, timeout=args.timeout)
    except requests.HTTPError as http_err:
        print(f"[error] HTTP error: {http_err}", file=sys.stderr)
        return 2
    except requests.RequestException as req_err:
        print(f"[error] Request failed: {req_err}", file=sys.stderr)
        return 2

    data = extract_next_data(html)
    if data is None:
        print(
            "[error] Could not locate Next.js __NEXT_DATA__. You may need to provide a valid Cookie.",
            file=sys.stderr,
        )
        return 3

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except OSError as exc:
            print(f"[warn] Failed to write output file: {exc}", file=sys.stderr)

    matches = find_bc_objects(data, bcid_filter=bcid)
    if not matches:
        if bcid:
            print(f"[warn] No objects found for bcId {bcid}")
        else:
            print("[warn] No bc-* objects found in page data")
        # Still allow zero matches as a valid run
        return 0

    if args.format == "json":
        json.dump(matches, sys.stdout)
        print()
    elif args.format == "pretty":
        print(json.dumps(matches, indent=2))
    else:  # summary
        summaries = [summarize_object(obj) for obj in matches]
        print(json.dumps(summaries, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
