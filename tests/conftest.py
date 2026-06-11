import sys, os
from pathlib import Path

# Ensure repo root is on sys.path so imports like 'backend.schemas' resolve
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Also ensure the packaged `trading_os_v1` implementation directory is available
# so tests under `trading_os_v1/tests` can import `trading_os_v1.*`.
PACKAGE_PARENT = str(Path(ROOT) / "trading_os_v1")
if PACKAGE_PARENT not in sys.path:
    sys.path.insert(0, PACKAGE_PARENT)
