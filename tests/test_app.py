#!/usr/bin/env python3
"""
ESTOP System Test Suite
Basic tests to verify application functionality
"""
import unittest
import sys
import os
import signal
import time

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Set timeout for tests (60 seconds as per rules)
def timeout_handler(signum, frame):
    raise TimeoutError("Test script timed out after 60 seconds")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)

class ESTOPSystemTests(unittest.TestCase):
    """Test cases for ESTOP System"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from app import create_app
            self.app = create_app()
            self.app.config['TESTING'] = True
            self.client = self.app.test_client()
            print(f"Test setup complete: {time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Setup failed: {e}")
            raise
    
    def test_app_creation(self):
        """Test that the app can be created successfully"""
        self.assertIsNotNone(self.app)
        print("✓ App creation test passed")
    
    def test_login_page_loads(self):
        """Test that login page loads without error"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ESTOP Function Record System', response.data)
        print("✓ Login page loads correctly")
    
    def test_main_page_redirects_when_not_logged_in(self):
        """Test that main page redirects to login when not authenticated"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect
        print("✓ Main page redirect test passed")
    
    def test_authentication_system(self):
        """Test authentication with valid credentials"""
        # Test login POST
        response = self.client.post('/login', data={
            'username': 'ckull',
            'password': 'mera7'
        })
        # Should redirect on successful login
        self.assertEqual(response.status_code, 302)
        print("✓ Authentication system test passed")
    
    def test_invalid_login(self):
        """Test authentication with invalid credentials"""
        response = self.client.post('/login', data={
            'username': 'invalid',
            'password': 'wrong'
        })
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        print("✓ Invalid login test passed")
    
    def test_debug_endpoint_requires_auth(self):
        """Test that debug endpoint requires authentication"""
        response = self.client.get('/debug')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        print("✓ Debug endpoint auth test passed")
    
    def test_history_endpoint_requires_auth(self):
        """Test that history endpoint requires authentication"""
        response = self.client.get('/history')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        print("✓ History endpoint auth test passed")
    
    def test_api_endpoint_requires_auth(self):
        """Test that API endpoints require authentication"""
        response = self.client.get('/api/devices/1')
        self.assertEqual(response.status_code, 401)  # Unauthorized
        print("✓ API endpoint auth test passed")
    
    def test_404_handling(self):
        """Test 404 error handling"""
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
        print("✓ 404 error handling test passed")

def run_tests():
    """Run all tests"""
    print("="*60)
    print("ESTOP System Test Suite Starting...")
    print(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ESTOPSystemTests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("="*60)
    print(f"Tests completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    print("="*60)
    
    return len(result.failures) + len(result.errors) == 0

if __name__ == '__main__':
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except TimeoutError:
        print("Test script timed out after 60 seconds")
        sys.exit(1)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)