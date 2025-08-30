"""
Pytest configuration for API testing
"""
import os
import sys

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Test configuration
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest settings"""
    pass

def pytest_runtest_setup(item):
    """Setup before each test"""
    pass

def pytest_runtest_teardown(item, nextitem):
    """Teardown after each test"""
    pass
