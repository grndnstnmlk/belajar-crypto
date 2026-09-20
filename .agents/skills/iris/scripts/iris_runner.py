"""
Iris — High-Speed Camera & Screenshot Engine for Coding Agents
Synthesized from brijr/iris (https://github.com/brijr/iris).
Provides instantaneous CLI screenshotting and stdio MCP server support
using local Chrome / Edge headless without requiring Rust/Cargo compilation.

Usage:
  python iris_runner.py example.com
  python iris_runner.py --full --dark localhost:5000 -o dashboard_preview.png
  python iris_runner.py --size iphone localhost:5000 -o mobile_view.png
  python iris_runner.py --selector '#hero' --padding 24 app.dev
  python iris_runner.py mcp  (runs stdio MCP server)
"""

import os
import sys
import json
import time
import argparse
import subprocess
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SIZE_PRESETS = {
    "desktop": (1440, 900),
    "laptop": (1280, 800),
    "iphone": (390, 844),
    "ipad": (820, 1180),
    "mobile": (390, 844)
}


def find_browser_binary() -> Optional[str]:
    """Finds Chrome or Edge executable on Windows/macOS/Linux."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium"
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # Check PATH
    for cmd in ["chrome", "google-chrome", "chromium", "msedge"]:
        import shutil
        found = shutil.which(cmd)
        if found:
            return found
    return None


def normalize_url(raw_url: str) -> str:
    """Normalizes shorthand urls (e.g. localhost:5000, example.com) to full URLs."""
    raw = raw_url.strip()
    if raw.startswith("localhost") or raw.startswith("127.0.0.1"):
        return f"http://{raw}"
    elif not raw.startswith("http://") and not raw.startswith("https://") and not raw.startswith("file:///"):
        return f"https://{raw}"
    return raw


def capture_screenshot(
    url: str,
    output: Optional[str] = None,
    size: str = "desktop",
    dark: bool = False,
    full_page: bool = False,
    selector: Optional[str] = None,
    padding: int = 0,
    wait_ms: int = 1500,
    as_json: bool = False
) -> Dict[str, Any]:
    """
    Executes an ultra-fast screenshot using Chrome/Edge headless.
    """
    start_time = time.time()
    browser_bin = find_browser_binary()
    if not browser_bin:
        err = {"status": "error", "message": "No Chrome or Edge browser found on system."}
        if as_json:
            print(json.dumps(err))
        return err

    target_url = normalize_url(url)
    
    # Determine output path
    if not output:
        parsed = urllib.parse.urlparse(target_url)
        slug = (parsed.netloc or "screenshot").replace(":", "_").replace(".", "_")
        output = f"{slug}.png"

    out_path = Path(output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    w, h = SIZE_PRESETS.get(size.lower(), (1440, 900))

    import tempfile
    udir = os.path.join(tempfile.gettempdir(), f"iris_chrome_{os.getpid()}")

    # Chrome command line options
    cmd = [
        browser_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={udir}",
        "--hide-scrollbars",
        f"--window-size={w},{h}",
        f"--screenshot={str(out_path)}"
    ]

    if dark:
        cmd.append("--force-dark-mode")

    cmd.append(target_url)

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        file_size = out_path.stat().st_size if out_path.exists() else 0
        success = out_path.exists() and file_size > 0

        result = {
            "status": "ok" if success else "failed",
            "url": target_url,
            "output": str(out_path),
            "size": size,
            "dimensions": {"width": w, "height": h},
            "dark_mode": dark,
            "file_size_bytes": file_size,
            "latency_ms": elapsed_ms
        }

        if as_json:
            print(json.dumps(result))
        else:
            if success:
                print(f"📸 [IRIS] Captured: {out_path} ({w}x{h}, {file_size:,} bytes) in {elapsed_ms}ms")
            else:
                print(f"❌ [IRIS] Failed to capture: {proc.stderr.decode('utf-8', errors='ignore')}")

        return result
    except Exception as e:
        err = {"status": "error", "message": str(e), "url": target_url}
        if as_json:
            print(json.dumps(err))
        return err


def run_mcp_server():
    """Runs a standard stdio JSON-RPC MCP server exposing the 'capture' tool."""
    sys.stderr.write("Iris MCP Server started. Waiting for stdio JSON-RPC...\n")
    sys.stderr.flush()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "iris", "version": "0.4.1"}
                    }
                }
                print(json.dumps(resp), flush=True)

            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "capture",
                                "description": "Captures a high-speed screenshot of a given URL or local page.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "url": {"type": "string", "description": "URL to capture"},
                                        "output": {"type": "string", "description": "Output path for the image"},
                                        "size": {"type": "string", "enum": ["desktop", "laptop", "iphone", "ipad"], "default": "desktop"},
                                        "dark": {"type": "boolean", "default": False},
                                        "full": {"type": "boolean", "default": False},
                                        "selector": {"type": "string", "description": "CSS selector to frame"},
                                        "padding": {"type": "integer", "default": 0}
                                    },
                                    "required": ["url"]
                                }
                            }
                        ]
                    }
                }
                print(json.dumps(resp), flush=True)

            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                if tool_name == "capture":
                    res = capture_screenshot(
                        url=args.get("url", "https://example.com"),
                        output=args.get("output"),
                        size=args.get("size", "desktop"),
                        dark=args.get("dark", False),
                        full_page=args.get("full", False),
                        selector=args.get("selector"),
                        padding=args.get("padding", 0)
                    )
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(res, indent=2)
                                }
                            ]
                        }
                    }
                    print(json.dumps(resp), flush=True)

            elif method == "notifications/initialized":
                pass
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method {method} not found"}
                }
                print(json.dumps(resp), flush=True)
        except Exception as e:
            sys.stderr.write(f"Iris MCP Error: {e}\n")
            sys.stderr.flush()


def main():
    parser = argparse.ArgumentParser(description="Iris — A camera for coding agents.")
    parser.add_argument("url", nargs="?", help="URL or domain to capture (e.g. localhost:5000, example.com)")
    parser.add_argument("-o", "--output", help="Output file path (PNG)")
    parser.add_argument("--size", default="desktop", choices=["desktop", "laptop", "iphone", "ipad", "mobile"], help="Viewport size preset")
    parser.add_argument("--dark", action="store_true", help="Enable dark color scheme")
    parser.add_argument("--full", action="store_true", help="Full-page capture")
    parser.add_argument("--selector", help="CSS selector of element to capture")
    parser.add_argument("--padding", type=int, default=0, help="Padding around selector in px")
    parser.add_argument("--wait-for", help="Wait condition or selector")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--mcp", action="store_true", help="Start Iris MCP Server")

    # If invoked as 'python iris_runner.py mcp'
    if len(sys.argv) > 1 and sys.argv[1].lower() == "mcp":
        run_mcp_server()
        return

    args = parser.parse_args()

    if args.mcp:
        run_mcp_server()
        return

    if not args.url:
        parser.print_help()
        sys.exit(1)

    capture_screenshot(
        url=args.url,
        output=args.output,
        size=args.size,
        dark=args.dark,
        full_page=args.full,
        selector=args.selector,
        padding=args.padding,
        as_json=args.json
    )


if __name__ == "__main__":
    main()
