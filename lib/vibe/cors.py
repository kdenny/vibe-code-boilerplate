"""CORS diagnostic utilities."""

import json
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class CORSCheckResult:
    """Result of a CORS check."""

    url: str
    success: bool
    status_code: int | None = None
    cors_headers: dict[str, str] | None = None
    issues: list[str] | None = None
    suggestions: list[str] | None = None
    error: str | None = None
    preflight_status: int | None = None
    preflight_headers: dict[str, str] | None = None


# Common CORS headers to check
CORS_HEADERS = [
    "Access-Control-Allow-Origin",
    "Access-Control-Allow-Methods",
    "Access-Control-Allow-Headers",
    "Access-Control-Allow-Credentials",
    "Access-Control-Max-Age",
    "Access-Control-Expose-Headers",
]


def check_cors(
    url: str,
    origin: str = "http://localhost:3000",
    method: str = "GET",
    headers: list[str] | None = None,
) -> CORSCheckResult:
    """
    Check CORS configuration for a URL.

    Args:
        url: The URL to check
        origin: The origin to test from (default: http://localhost:3000)
        method: The HTTP method to test (default: GET)
        headers: Additional headers to include in preflight check

    Returns:
        CORSCheckResult with diagnostic information
    """
    import urllib.error
    import urllib.request

    issues: list[str] = []
    suggestions: list[str] = []
    cors_headers: dict[str, str] = {}
    preflight_headers: dict[str, str] = {}
    preflight_status: int | None = None

    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return CORSCheckResult(
            url=url,
            success=False,
            error="Invalid URL. Must include scheme (http/https) and host.",
            issues=["Invalid URL format"],
            suggestions=["Use a full URL like https://api.example.com/endpoint"],
        )

    # Step 1: Send preflight OPTIONS request
    try:
        preflight_req = urllib.request.Request(url, method="OPTIONS")
        preflight_req.add_header("Origin", origin)
        preflight_req.add_header("Access-Control-Request-Method", method)
        if headers:
            preflight_req.add_header("Access-Control-Request-Headers", ", ".join(headers))

        with urllib.request.urlopen(preflight_req, timeout=10) as response:
            preflight_status = response.status
            for header in CORS_HEADERS:
                value = response.getheader(header)
                if value:
                    preflight_headers[header] = value

    except urllib.error.HTTPError as e:
        preflight_status = e.code
        # Still try to get headers from error response
        for header in CORS_HEADERS:
            value = e.headers.get(header)
            if value:
                preflight_headers[header] = value
    except urllib.error.URLError as e:
        return CORSCheckResult(
            url=url,
            success=False,
            error=f"Connection error: {e.reason}",
            issues=["Cannot reach the server"],
            suggestions=[
                "Check that the server is running",
                "Verify the URL is correct",
                "Check network connectivity",
            ],
        )
    except Exception as e:
        return CORSCheckResult(
            url=url,
            success=False,
            error=f"Preflight request failed: {e}",
            issues=["Preflight OPTIONS request failed"],
            suggestions=["Ensure the server handles OPTIONS requests"],
        )

    # Step 2: Send actual request
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header("Origin", origin)

        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.status
            for header in CORS_HEADERS:
                value = response.getheader(header)
                if value:
                    cors_headers[header] = value

    except urllib.error.HTTPError as e:
        status_code = e.code
        for header in CORS_HEADERS:
            value = e.headers.get(header)
            if value:
                cors_headers[header] = value
    except Exception as e:
        return CORSCheckResult(
            url=url,
            success=False,
            error=f"Request failed: {e}",
            issues=["Cannot complete request to server"],
            suggestions=["Check server logs for errors"],
        )

    # Analyze CORS headers
    acao = cors_headers.get("Access-Control-Allow-Origin") or preflight_headers.get(
        "Access-Control-Allow-Origin"
    )

    if not acao:
        issues.append("Missing Access-Control-Allow-Origin header")
        suggestions.append("Add CORS headers to your server response")
        suggestions.append(f"Set Access-Control-Allow-Origin to '{origin}' or '*'")
    elif acao != "*" and acao != origin:
        issues.append(f"Origin mismatch: server allows '{acao}' but request is from '{origin}'")
        suggestions.append(f"Add '{origin}' to allowed origins")

    acam = cors_headers.get("Access-Control-Allow-Methods") or preflight_headers.get(
        "Access-Control-Allow-Methods"
    )
    if method not in ["GET", "HEAD", "POST"] and not acam:
        issues.append(f"Missing Access-Control-Allow-Methods for {method}")
        suggestions.append(f"Add '{method}' to Access-Control-Allow-Methods")
    elif acam and method not in acam:
        issues.append(f"Method '{method}' not in allowed methods: {acam}")
        suggestions.append(f"Add '{method}' to Access-Control-Allow-Methods")

    if headers:
        acah = cors_headers.get("Access-Control-Allow-Headers") or preflight_headers.get(
            "Access-Control-Allow-Headers"
        )
        if not acah:
            issues.append("Missing Access-Control-Allow-Headers")
            suggestions.append(f"Add Access-Control-Allow-Headers: {', '.join(headers)}")

    success = len(issues) == 0

    return CORSCheckResult(
        url=url,
        success=success,
        status_code=status_code,
        cors_headers=cors_headers,
        issues=issues if issues else None,
        suggestions=suggestions if suggestions else None,
        preflight_status=preflight_status,
        preflight_headers=preflight_headers if preflight_headers else None,
    )


def format_cors_result(result: CORSCheckResult, json_output: bool = False) -> str:
    """Format CORS check result for display."""
    if json_output:
        return json.dumps(
            {
                "url": result.url,
                "success": result.success,
                "status_code": result.status_code,
                "preflight_status": result.preflight_status,
                "cors_headers": result.cors_headers,
                "preflight_headers": result.preflight_headers,
                "issues": result.issues,
                "suggestions": result.suggestions,
                "error": result.error,
            },
            indent=2,
        )

    lines = []
    lines.append(f"CORS Check: {result.url}")
    lines.append("=" * 60)

    if result.error:
        lines.append(f"\nError: {result.error}")
        if result.issues:
            lines.append("\nIssues:")
            for issue in result.issues:
                lines.append(f"  - {issue}")
        if result.suggestions:
            lines.append("\nSuggestions:")
            for suggestion in result.suggestions:
                lines.append(f"  - {suggestion}")
        return "\n".join(lines)

    # Status
    if result.success:
        lines.append("\nStatus: CORS configured correctly")
    else:
        lines.append("\nStatus: CORS issues detected")

    # Response info
    lines.append(f"\nHTTP Status: {result.status_code}")
    if result.preflight_status:
        lines.append(f"Preflight Status: {result.preflight_status}")

    # Headers found
    all_headers = {**(result.preflight_headers or {}), **(result.cors_headers or {})}
    if all_headers:
        lines.append("\nCORS Headers:")
        for header, value in sorted(all_headers.items()):
            lines.append(f"  {header}: {value}")
    else:
        lines.append("\nNo CORS headers found!")

    # Issues
    if result.issues:
        lines.append("\nIssues:")
        for issue in result.issues:
            lines.append(f"  - {issue}")

    # Suggestions
    if result.suggestions:
        lines.append("\nSuggestions:")
        for suggestion in result.suggestions:
            lines.append(f"  - {suggestion}")

    # Framework-specific hints
    lines.append("\n" + "-" * 60)
    lines.append("Framework-specific fixes: See recipes/debugging/cors-errors.md")

    return "\n".join(lines)
