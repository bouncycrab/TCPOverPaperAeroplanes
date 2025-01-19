#!/usr/bin/env python3
import argparse
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


class HTTPClient:
    def __init__(self):
        # Set up directory structure
        self.base_dir = PROJECT_ROOT
        self.http_outgoing = self.base_dir / "data" / "app" / "out"
        self.http_incoming = self.base_dir / "data" / "app" / "in"

        # Create directories if they don't exist
        self.http_outgoing.mkdir(parents=True, exist_ok=True)
        self.http_incoming.mkdir(parents=True, exist_ok=True)

    def send_get_request(self, path):
        """
        Create a simplified HTTP GET request and pass it to the transport layer
        """
        # Create simplified HTTP GET request
        request = {
            "method": "GET",
            "path": path,
            "headers": {"Host": "paperplane.local"},
        }

        # Write to outgoing directory with timestamp to ensure unique filename
        timestamp = int(time.time() * 1000)
        outfile = self.http_outgoing / f"request_{timestamp}.json"
        with open(outfile, "w") as f:
            json.dump(request, f, indent=2)

        print(f"GET request sent for path: {path}")
        return timestamp

    def wait_for_response(self, request_timestamp, path, timeout=1200):
        """
        Wait for and process the HTTP response
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Look for response file
            for file in self.http_incoming.glob("response_.json"):
                try:
                    with open(file) as f:
                        response = json.load(f)

                    # Save the HTML content
                    if response.get("status_code") == 200:
                        output_file = self.base_dir / "data" / "app" / "content" / path[1:]
                        with open(output_file, "w") as f:
                            f.write(response["body"])
                        print(f"Response received and saved to {output_file}")
                        # Clean up response file
                        file.unlink()
                        return True
                except json.JSONDecodeError:
                    continue

            time.sleep(0.1)  # Small delay to prevent busy waiting

        print("Timeout waiting for response")
        return False


def main():
    parser = argparse.ArgumentParser(description="Simple HTTP Client")
    parser.add_argument("path", help="Path to request (e.g., /index.html)")
    args = parser.parse_args()

    client = HTTPClient()
    request_timestamp = client.send_get_request(args.path)
    client.wait_for_response(request_timestamp, args.path)


if __name__ == "__main__":
    main()
