"""
Tests for core DW-Util functionality.
"""

import pytest
from dw_util.core import DWUtil

def test_dw_util_init():
    """Test basic initialization of DWUtil."""
    util = DWUtil()
    assert isinstance(util, DWUtil) 