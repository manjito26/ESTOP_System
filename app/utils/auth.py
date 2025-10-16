"""
Authentication utility for ESTOP System
Loads users from RACE/users.json and handles authentication
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.users = {}
        self.load_users()
    
    def load_users(self):
        """Load users from RACE users.json file"""
        try:
            users_file = '/home/eraser/PycharmProjects/RACE/users.json'
            with open(users_file, 'r') as f:
                self.users = json.load(f)
            logger.info(f"Loaded {len(self.users)} users from {users_file}")
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            self.users = {}
    
    def authenticate(self, username, password):
        """Authenticate a user"""
        if username in self.users:
            if self.users[username]['password'] == password:
                logger.info(f"Successful authentication for user: {username}")
                return True
            else:
                logger.warning(f"Failed authentication for user: {username} (wrong password)")
        else:
            logger.warning(f"Failed authentication for unknown user: {username}")
        return False
    
    def get_user_privileges(self, username):
        """Get user privileges"""
        if username in self.users:
            return self.users[username].get('privileges', [])
        return []
    
    def get_all_users(self):
        """Get all usernames"""
        return list(self.users.keys())