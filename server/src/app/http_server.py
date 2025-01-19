#!/usr/bin/env python3
import json
import mimetypes
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


class HTTPServer:
    def __init__(self):
        # Set up directory structure
        self.base_dir = PROJECT_ROOT
        self.web_root = self.base_dir / "data" / "app" / "content"
        self.http_incoming = self.base_dir / "data" / "app" / "in"
        self.http_outgoing = self.base_dir / "data" / "app" / "out"

        # Create directories if they don't exist
        self.http_incoming.mkdir(parents=True, exist_ok=True)
        self.http_outgoing.mkdir(parents=True, exist_ok=True)
        self.web_root.mkdir(parents=True, exist_ok=True)

        # Create a sample index.html if it doesn't exist
        self._create_sample_page()

    def _create_sample_page(self):
        index_path = self.web_root / "index.html"
        if not index_path.exists():
            with open(index_path, "w") as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Paper Airplane Network</title>
</head>
<body>
    <h1>Welcome to the Paper Airplane Network!</h1>
    <p>This page was delivered by paper airplane.</p>
</body>
</html>""")

    def handle_request(self, request):
        """
        Process an HTTP request and generate a response
        """
        path = request.get("path", "/")
        if path == "/":
            path = "/index.html"

        file_path = self.web_root / path.lstrip("/")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            status_code = 200
            status_text = "OK"
        except FileNotFoundError:
            content = "<h1>404 Not Found</h1>"
            status_code = 404
            status_text = "Not Found"

        return {
            "status_code": status_code,
            "status_text": status_text,
            "headers": {
                "Content-Type": mimetypes.guess_type(str(file_path))[0] or "text/html"
            },
            "body": content,
        }

    def run(self):
        print("HTTP Server running...")
        print(f"Serving files from: {self.web_root.absolute()}")

        while True:
            # Check for new requests
            for file in self.http_incoming.glob("request_*.json"):
                try:
                    with open(file) as f:
                        request = json.load(f)

                    print(f"Processing request for: {request.get('path', '/')}")

                    # Generate response
                    response = self.handle_request(request)

                    # Write response
                    response_file = (
                        self.http_outgoing / f"response_{int(time.time() * 1000)}.json"
                    )
                    with open(response_file, "w") as f:
                        json.dump(response, f, indent=2)

                    # Clean up request file
                    file.unlink()

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error processing request: {e}")
                    continue

            time.sleep(0.1)  # Small delay to prevent busy waiting


def main():
    server = HTTPServer()
    server.run()


if __name__ == "__main__":
    main()
