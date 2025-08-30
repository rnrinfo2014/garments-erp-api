import pytest
import asyncio
import requests
import json
from typing import Dict, Any
import time


class APITestBase:
    """Base class for API testing with common functionality"""
    
    BASE_URL = "http://127.0.0.1:8001"
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.headers = {"Content-Type": "application/json"}
    
    def login(self) -> str:
        """Login and get JWT token"""
        login_data = {
            "username": "rnrinfo",
            "password": "rnrinfo"
        }
        
        response = self.session.post(
            f"{self.BASE_URL}/api/auth/login",
            json=login_data,
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
            return self.auth_token
        else:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    def get(self, endpoint: str) -> requests.Response:
        """Make GET request"""
        return self.session.get(
            f"{self.BASE_URL}{endpoint}",
            headers=self.headers
        )
    
    def post(self, endpoint: str, data: Dict[Any, Any]) -> requests.Response:
        """Make POST request"""
        return self.session.post(
            f"{self.BASE_URL}{endpoint}",
            json=data,
            headers=self.headers
        )
    
    def put(self, endpoint: str, data: Dict[Any, Any]) -> requests.Response:
        """Make PUT request"""
        return self.session.put(
            f"{self.BASE_URL}{endpoint}",
            json=data,
            headers=self.headers
        )
    
    def delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request"""
        return self.session.delete(
            f"{self.BASE_URL}{endpoint}",
            headers=self.headers
        )
    
    def wait_for_server(self, max_attempts: int = 30):
        """Wait for server to be available"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.BASE_URL}/health", timeout=2)
                if response.status_code == 200:
                    print(f"Server is ready after {attempt + 1} attempts")
                    return True
            except:
                time.sleep(1)
        
        raise Exception("Server did not start within the expected time")


@pytest.fixture(scope="session")
def api_client():
    """Pytest fixture for API client"""
    client = APITestBase()
    client.wait_for_server()
    client.login()
    return client


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
