#!/usr/bin/env python3
"""CLI script to start the ARQ worker process.

Always runs in dual-mode (Redis + in-memory fallback).
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path modification to avoid import errors
from workers.worker import start_dual_worker  # noqa: E402

# CLI argument parsing
import argparse


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Learning Space task worker")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the dispatch API server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind the dispatch API server (default: 8001)",
    )
    return parser.parse_args()


# Set up signal handling for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logging.info(f"Received signal {signum}, shutting down worker...")
    sys.exit(0)


if __name__ == "__main__":
    args = parse_args()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    log_level = logging.getLevelName(logging.getLogger().getEffectiveLevel())
    logging.info("Worker starting up | log_level=%s", log_level)
    logging.info(
        "Starting in dual-mode (Redis + in-memory fallback) | dispatch server: %s:%s",
        args.host,
        args.port,
    )

    print("Starting Learning Space task worker (dual-mode)...")
    print("Press Ctrl+C to stop")

    try:
        asyncio.run(start_dual_worker(host=args.host, port=args.port))
    except KeyboardInterrupt:
        print("\nWorker stopped by user")
    except Exception as e:
        logging.error(f"Worker failed: {e}")
        sys.exit(1)
