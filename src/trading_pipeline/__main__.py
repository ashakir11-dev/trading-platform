"""``python -m trading_pipeline`` — same as the ``trading-pipeline`` command."""

import sys

from .cli import main

sys.exit(main())
