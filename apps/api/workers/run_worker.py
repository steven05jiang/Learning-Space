#!/usr/bin/env python3
"""CLI script to start the ARQ worker process."""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path modification to avoid import errors
from arq import run_worker  # noqa: E402

from workers.worker import WorkerSettings  # noqa: E402


# Set up signal handling for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logging.info(f"Received signal {signum}, shutting down worker...")
    sys.exit(0)


if __name__ == "__main__":
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
    print("Starting Learning Space task worker...")
    print("Press Ctrl+C to stop")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        run_worker(WorkerSettings)
    except KeyboardInterrupt:
        print("\nWorker stopped by user")
    except Exception as e:
        logging.error(f"Worker failed: {e}")
        sys.exit(1)
