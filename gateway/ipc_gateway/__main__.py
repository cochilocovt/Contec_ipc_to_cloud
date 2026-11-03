"""Run with: python -m ipc_gateway --config config/gateway.yaml"""
from __future__ import annotations

import argparse
import logging
import logging.handlers
import sys
from pathlib import Path

from . import __version__
from .app import Gateway
from .config import ConfigError, load


def main() -> int:
    ap = argparse.ArgumentParser(prog="ipc_gateway")
    ap.add_argument("--config", default="config/gateway.yaml")
    ap.add_argument("--log-file", help="rotating log file (5 x 2 MB); omit to log to the console only")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if args.log_file:
        Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.handlers.RotatingFileHandler(args.log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8"))
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", handlers=handlers)
    logging.getLogger("pymodbus").setLevel(logging.WARNING)

    try:
        cfg = load(args.config)
    except (OSError, ConfigError) as e:
        logging.error("config: %s", e)
        return 2
    logging.info("ipc_gateway %s", __version__)
    gw = Gateway(cfg)
    gw.install_signal_handlers()
    gw.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
