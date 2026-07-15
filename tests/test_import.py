import os
import re

import provenance_gate


def _pyproject_version():
    here = os.path.dirname(os.path.abspath(__file__))
    pyproject = os.path.join(here, os.pardir, "pyproject.toml")
    with open(pyproject) as fh:
        txt = fh.read()
    m = re.search(r'^version\s*=\s*"([^"]+)"', txt, re.MULTILINE)
    assert m, "version not found in pyproject.toml"
    return m.group(1)


def test_import_and_version():
    # single source of truth: package __version__ must match pyproject
    expected = _pyproject_version()
    assert provenance_gate.__version__ == expected, (
        f"__version__ {provenance_gate.__version__!r} != "
        f"pyproject {expected!r}"
    )
