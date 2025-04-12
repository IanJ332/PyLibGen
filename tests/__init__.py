"""
Test package for LibGen Explorer.
"""

import unittest
import logging

# Configure logging for tests
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    start_dir = '.'
    suite = loader.discover(start_dir)
    
    runner = unittest.TextTestRunner()
    runner.run(suite)
    
if __name__ == '__main__':
    run_tests()