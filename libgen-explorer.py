#!/usr/bin/env python3
"""
LibGen Explorer - Command-line interface script.

This script provides a convenient entry point to the LibGen Explorer functionality.
"""

import sys
import os
import argparse
import logging

# Add the parent directory to the Python path to import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libgen_explorer.cli import main

if __name__ == '__main__':
    main()