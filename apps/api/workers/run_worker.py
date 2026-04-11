#!/usr/bin/env python3
"""CLI script to start the ARQ worker process.

Supports two modes:
- Standard mode: Redis queue only (default)
- Dual mode: Redis + in-memory fallback (DUAL_MODE=true)
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path modification to avoid import errors
from arq import run_worker  # noqa: E402

from workers.worker import WorkerSettings, start_dual_worker  # noqa: E402


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

    # Check if we should run in dual-mode (Redis + in-memory fallback)
    if os.environ.get("DUAL_MODE", "").lower() == "true":
        logging.info("Starting in dual-mode (Redis + in-memory fallback)")
        logging.info(
            "Dispatch API will listen on %s:%s",
            os.environ.get("DISPATCH_HOST", "127.0.0.1"),
            os.environ.get("DISPATCH_PORT", "8001"),
        )
        print("Starting Learning Space task worker (dual-mode)...")
        print("Press Ctrl+C to stop")

        try:
            asyncio.run(start_dual_worker())
        except KeyboardInterrupt:
            print("\nWorker stopped by user")
        except Exception as e:
            logging.error(f"Worker failed: {e}")
            sys.exit(1)
    else:
        logging.info("Starting in standard mode (Redis queue only)")
        print("Starting Learning Space task worker...")
        print("Press Ctrl+C to stop")

        try:
            run_worker(WorkerSettings)
        except KeyboardInterrupt:
            print("\nWorker stopped by user")
        except Exception as e:
            logging.error(f"Worker failed: {e}")
            sys.exit(1)
