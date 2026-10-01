"""Serve the built site on localhost so it can be tested in a browser.

    py tools/serve.py            serves this folder on the first free port
    py tools/serve.py --port 8080

The site is plain files, so this is only needed for local testing: on GitHub
Pages the same files are served by GitHub. Open the address it prints, and
resize the window down to a phone width to check the layout.
"""

from __future__ import annotations

import argparse
import http.server
import socket
import socketserver
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402


def free_port(start: int, attempts: int = 25) -> int:
    for offset in range(attempts):
        candidate = start + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", candidate))
            except OSError:
                continue
            return candidate
    raise SystemExit(f"no free port between {start} and {start + attempts - 1}")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".csv": "text/csv; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".md": "text/plain; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".svg": "image/svg+xml",
    }

    def log_message(self, fmt, *args):  # quieter, but still useful
        sys.stderr.write("  %s\n" % (fmt % args))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Serve the Ground Truth site locally.")
    parser.add_argument("--root", default=str(common.repo_root()))
    parser.add_argument("--port", type=int, default=8000)
    options = parser.parse_args(argv)

    root = Path(options.root).resolve()
    port = free_port(options.port)
    handler = lambda *args, **kwargs: Handler(*args, directory=str(root), **kwargs)  # noqa: E731

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"serving {root}")
        print(f"  http://127.0.0.1:{port}/         (English)")
        print(f"  http://127.0.0.1:{port}/bn/      (Bangla)")
        print("press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
