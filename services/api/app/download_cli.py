"""Operator CLI for a permitted HTTPS source; no public URL-fetch endpoint."""
import argparse
import asyncio
from dataclasses import asdict
import json
import os
from pathlib import Path

from .download_engine import DownloadEngine, DownloadError, DownloadSource, TransferPolicy


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New output path; never overwrites an existing file")
    parser.add_argument("--host", action="append", required=True, help="Exact approved source hostname; repeat as needed")
    parser.add_argument("--max-bytes", type=int, default=1024 * 1024 * 1024)
    parser.add_argument("--max-transfer-bytes", type=int, help="Total body bytes allowed across retries")
    parser.add_argument("--expected-bytes", type=int)
    parser.add_argument("--sha256", help="Independently known lowercase SHA-256, when available")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--total-timeout", type=float, default=300)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args(argv)
    try:
        # Avoid putting signed source URLs in CLI arguments or routine output.
        source = DownloadSource(os.environ.get("ENGINE_SOURCE_URL", ""), frozenset(args.host),
                                expected_sha256=args.sha256, expected_bytes=args.expected_bytes)
        policy = TransferPolicy(max_bytes=args.max_bytes, max_attempts=args.attempts,
                                total_timeout=args.total_timeout, resume=not args.no_resume,
                                max_transfer_bytes=args.max_transfer_bytes)
        result = asyncio.run(DownloadEngine(policy).download(source, args.destination))
    except DownloadError as failure:
        print(json.dumps({"error": {"code": failure.code}}))
        return 1
    except (ValueError, TypeError):
        print(json.dumps({"error": {"code": "invalid_configuration"}}))
        return 2
    except KeyboardInterrupt:
        print(json.dumps({"error": {"code": "cancelled"}}))
        return 130
    print(json.dumps({"completed": True, **asdict(result)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
