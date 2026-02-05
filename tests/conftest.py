"""pytest configuration for lattice tests"""

import sys
from pathlib import Path

# add project root to path so src imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
