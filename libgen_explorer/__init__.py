"""
LibGen Explorer - A Python tool to search and analyze LibGen resources.

This package provides tools to:
- Connect to the LibGen API
- Process and analyze book data using Pandas
- Rate search results based on relevance
- Export results to various formats
"""

__version__ = '0.1.0'
__author__ = 'Ray Zhang, Ian Jiang'
__email__ = 'rui.zhang@sjsu.edu, jisheng.jiang@sjsu.edu'

from libgen_explorer.api import LibGenAPI
from libgen_explorer.database import GUNDatabase
from libgen_explorer.extraction import DataExtractor
from libgen_explorer.rating import ResultRater
from libgen_explorer.export import FileExporter

__all__ = ['LibGenAPI', 'GUNDatabase', 'DataExtractor', 'ResultRater', 'FileExporter']