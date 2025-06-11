"""
Authentication System
------------------
Implement an authentication system according to the specified requirements.
This exercise focuses on implementing secure authentication methods for APIs.
"""

import jwt
import uuid
import json
import os
import hashlib
import hmac
import secrets
import time
import re
from datetime import datetime, timedelta
from functools import wraps

# Constants
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-key')  # In production, use an environment variable
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(hours=1)
API_KEYS_FILE = 'api_keys.json'
USERS_FILE = 'users.json'

class AuthManager:
    """
    A class for managing authentication and authorization.
    
    Attributes:
        api_keys (dict): Dictionary of API keys and their metadata
        users (dict): Dictionary of user data
        
    Methods:
        generate_api_key: Generate a new API key
        validate_api_key: Validate an API key
        register_user: Register a new user
        authenticate_user: Authenticate a user with username and password
        generate_jwt_token: Generate a JWT token for a user
        validate_jwt_token: Validate a JWT token
    """
    
    def __init__(self):
        """Initialize the AuthManager."""
        self.api_keys = self._load_api_keys()
        self.users = self._load_users()
    
    def _load_api_keys(self):
        """Load API keys from file or create empty dict if file doesn't exist."""
        try:
            if os.path.exists(API_KEYS_FILE):
                with open(API_KEYS_FILE, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"Error loading API keys: {e}")
            return {}
    
    def _save_api_keys(self):
        """Save API keys to file."""
        try:
            with open(API_KEYS_FILE, 'w') as f:
                json.dump(self.api_keys, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving API keys: {e}")
            return False
    
    def _load_users(self):
        """Load users from file or create empty dict if file doesn't exist."""
        try:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"Error loading users: {e}")
            return {}
    
    def _save_users(self):
        """Save users to file."""
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump(self.users, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            return False
    
    def generate_api_key(self, owner_name, permissions=None):
        """
        Generate a new API key.
        
        Args:
            owner_name (str): Name of the API key owner
            permissions (list, optional): List of permissions. Defaults to None.
            
        Returns:
            str: The generated API key
        """
        if not owner_name or not isinstance(owner_name, str):
            raise ValueError("Owner name must be a non-empty string")
        
        # Generate a secure random API key
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        
        # Set default permissions if none provided
        if permissions is None:
            permissions = ["read"]
        
        # Store API key metadata
        self.api_keys[api_key] = {
            "owner": owner_name,
            "permissions": permissions,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "is_active": True,
            "usage_count": 0
        }
        
        # Save to file
        self._save_api_keys()
        
        print(f"Generated API key for {owner_name} with permissions: {permissions}")
        return api_key
    
    def validate_api_key(self, api_key, required_permissions=None):
        """
        Validate an API key and check permissions.
        
        Args:
            api_key (str): The API key to validate
            required_permissions (list, optional): Required permissions. Defaults to None.
            
        Returns:
            tuple: (is_valid, owner_name, permissions)
        """
        if not api_key or api_key not in self.api_keys:
            return False, None, []
        
        key_data = self.api_keys[api_key]
        
        # Check if key is active
        if not key_data.get("is_active", False):
            return False, None, []
        
        # Update last used timestamp and usage count
        key_data["last_used"] = datetime.now().isoformat()
        key_data["usage_count"] = key_data.get("usage_count", 0) + 1
        self._save_api_keys()
        
        owner_name = key_data.get("owner")
        permissions = key_data.get("permissions", [])
        
        # Check required permissions if specified
        if required_permissions:
            if not all(perm in permissions for perm in required_permissions):
                return False, owner_name, permissions
        
        return True, owner_name, permissions
    
    def register_user(self, username, password, email, role='user'):
        """
        Register a new user.
        
        Args:
            username (str): Username
            password (str): Password
            email (str): Email address
            role (str, optional): User role. Defaults to 'user'.
            
        Returns:
            dict: User data without password
            
        Raises:
            ValueError: If username already exists or validation fails
        """
        # Validate inputs
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        
        if username in self.users:
            raise ValueError("Username already exists")
        
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not self._validate_email(email):
            raise ValueError("Invalid email format")
        
        if role not in ['user', 'admin', 'moderator']:
            raise ValueError("Invalid role. Must be 'user', 'admin', or 'moderator'")
        
        # Hash the password
        password_hash, salt = self._hash_password(password)
        
        # Create user data
        user_data = {
            "user_id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "role": role,
            "password_hash": password_hash,
            "salt": salt,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True,
            "login_attempts": 0,
            "locked_until": None
        }
        
        # Store user
        self.users[username] = user_data
        self._save_users()
        
        # Return user data without sensitive information
        safe_user_data = {k: v for k, v in user_data.items() 
                         if k not in ['password_hash', 'salt']}
        
        print(f"Registered user: {username}")
        return safe_user_data
    
    def authenticate_user(self, username, password):
        """
        Authenticate a user with username and password.
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            tuple: (is_authenticated, user_data)
        """
        if not username or not password:
            return False, None
        
        if username not in self.users:
            return False, None
        
        user_data = self.users[username]
        
        # Check if user is active
        if not user_data.get("is_active", False):
            return False, None
        
        # Check if account is locked
        locked_until = user_data.get("locked_until")
        if locked_until:
            lock_time = datetime.fromisoformat(locked_until)
            if datetime.now() < lock_time:
                return False, None
            else:
                # Unlock account
                user_data["locked_until"] = None
                user_data["login_attempts"] = 0
        
        # Verify password
        stored_hash = user_data.get("password_hash")
        salt = user_data.get("salt")
        
        if not stored_hash or not salt:
            return False, None
        
        password_hash, _ = self._hash_password(password, salt)
        
        if not hmac.compare_digest(stored_hash, password_hash):
            # Increment failed login attempts
            user_data["login_attempts"] = user_data.get("login_attempts", 0) + 1
            
            # Lock account after 5 failed attempts
            if user_data["login_attempts"] >= 5:
                user_data["locked_until"] = (datetime.now() + timedelta(minutes=30)).isoformat()
                print(f"Account locked for {username} due to too many failed attempts")
            
            self._save_users()
            return False, None
        
        # Successful authentication
        user_data["last_login"] = datetime.now().isoformat()
        user_data["login_attempts"] = 0
        user_data["locked_until"] = None
        self._save_users()
        
        # Return safe user data
        safe_user_data = {k: v for k, v in user_data.items() 
                         if k not in ['password_hash', 'salt']}
        
        return True, safe_user_data
    
    def generate_jwt_token(self, user_data):
        """
        Generate a JWT token for a user.
        
        Args:
            user_data (dict): User data
            
        Returns:
            str: JWT token
        """
        if not user_data:
            raise ValueError("User data is required")
        
        # Create payload
        payload = {
            "user_id": user_data.get("user_id"),
            "username": user_data.get("username"),
            "role": user_data.get("role"),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + JWT_EXPIRATION_DELTA,
            "jti": str(uuid.uuid4())  # JWT ID for token revocation
        }
        
        # Generate token
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        print(f"Generated JWT token for user: {user_data.get('username')}")
        return token
    
    def validate_jwt_token(self, token):
        """
        Validate a JWT token.
        
        Args:
            token (str): JWT token
            
        Returns:
            tuple: (is_valid, payload)
        """
        if not token:
            return False, None
        
        try:
            # Decode and validate token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Check if user still exists and is active
            username = payload.get("username")
            if username and username in self.users:
                user_data = self.users[username]
                if not user_data.get("is_active", False):
                    return False, None
            else:
                return False, None
            
            return True, payload
            
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return False, None
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return False, None
        except Exception as e:
            print(f"Token validation error: {e}")
            return False, None
    
    def refresh_jwt_token(self, token):
        """
        Refresh a JWT token.
        
        Args:
            token (str): JWT token
            
        Returns:
            str: New JWT token
            
        Raises:
            ValueError: If token is invalid or expired
        """
        is_valid, payload = self.validate_jwt_token(token)
        
        if not is_valid:
            raise ValueError("Invalid or expired token")
        
        # Get current user data
        username = payload.get("username")
        if username not in self.users:
            raise ValueError("User no longer exists")
        
        user_data = self.users[username]
        safe_user_data = {k: v for k, v in user_data.items() 
                         if k not in ['password_hash', 'salt']}
        
        # Generate new token
        new_token = self.generate_jwt_token(safe_user_data)
        
        print(f"Refreshed JWT token for user: {username}")
        return new_token
    
    def _hash_password(self, password, salt=None):
        """
        Hash a password securely using PBKDF2.
        
        Args:
            password (str): Password to hash
            salt (str, optional): Salt for hashing. Defaults to None.
            
        Returns:
            tuple: (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        elif isinstance(salt, str):
            salt = salt
        
        # Use PBKDF2 with SHA-256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
        
        return password_hash, salt
    
    def _validate_email(self, email):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def revoke_api_key(self, api_key):
        """
        Revoke an API key.
        
        Args:
            api_key (str): The API key to revoke
            
        Returns:
            bool: True if revoked successfully
        """
        if api_key in self.api_keys:
            self.api_keys[api_key]["is_active"] = False
            self.api_keys[api_key]["revoked_at"] = datetime.now().isoformat()
            self._save_api_keys()
            print(f"Revoked API key: {api_key}")
            return True
        return False
    
    def get_user_api_keys(self, username):
        """Get all API keys for a user."""
        user_keys = []
        for key, data in self.api_keys.items():
            if data.get("owner") == username:
                user_keys.append({
                    "key": key[:10] + "...",  # Masked key
                    "permissions": data.get("permissions"),
                    "created_at": data.get("created_at"),
                    "is_active": data.get("is_active")
                })
        return user_keys
    
    def update_user_role(self, username, new_role):
        """Update a user's role."""
        if username not in self.users:
            raise ValueError("User not found")
        
        if new_role not in ['user', 'admin', 'moderator']:
            raise ValueError("Invalid role")
        
        self.users[username]["role"] = new_role
        self._save_users()
        return True


# Flask middleware decorators (for use with the Flask API exercise)
def require_api_key(auth_manager, required_permissions=None):
    """
    Decorator for requiring API key in Flask routes.
    
    Args:
        auth_manager (AuthManager): AuthManager instance
        required_permissions (list, optional): Required permissions
        
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                from flask import request, jsonify, g
                
                # Get API key from header
                api_key = request.headers.get('X-API-Key')
                if not api_key:
                    # Try Authorization header
                    auth_header = request.headers.get('Authorization')
                    if auth_header and auth_header.startswith('ApiKey '):
                        api_key = auth_header[7:]  # Remove 'ApiKey ' prefix
                
                if not api_key:
                    return jsonify({"error": "API key required"}), 401
                
                # Validate API key
                is_valid, owner, permissions = auth_manager.validate_api_key(
                    api_key, required_permissions
                )
                
                if not is_valid:
                    return jsonify({"error": "Invalid API key or insufficient permissions"}), 403
                
                # Store in Flask's g object for use in the route
                g.api_key_owner = owner
                g.api_key_permissions = permissions
                
                return f(*args, **kwargs)
                
            except ImportError:
                # Flask not available, skip validation for testing
                print("Flask not available, skipping API key validation")
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": f"Authentication error: {str(e)}"}), 500
                
        return decorated_function
    return decorator

def require_jwt_token(auth_manager):
    """
    Decorator for requiring JWT token in Flask routes.
    
    Args:
        auth_manager (AuthManager): AuthManager instance
        
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                from flask import request, jsonify, g
                
                # Get JWT token from header
                auth_header = request.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    return jsonify({"error": "JWT token required"}), 401
                
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                
                # Validate token
                is_valid, payload = auth_manager.validate_jwt_token(token)
                
                if not is_valid:
                    return jsonify({"error": "Invalid or expired token"}), 403
                
                # Store user info in Flask's g object
                g.current_user = payload
                
                return f(*args, **kwargs)
                
            except ImportError:
                # Flask not available, skip validation for testing
                print("Flask not available, skipping JWT validation")
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": f"Authentication error: {str(e)}"}), 500
                
        return decorated_function
    return decorator

def require_role(auth_manager, required_roles):
    """
    Decorator for requiring specific roles in Flask routes.
    
    Args:
        auth_manager (AuthManager): AuthManager instance
        required_roles (list): List of required roles
        
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                from flask import request, jsonify, g
                
                # This decorator should be used after require_jwt_token
                if not hasattr(g, 'current_user'):
                    return jsonify({"error": "Authentication required"}), 401
                
                user_role = g.current_user.get('role')
                
                if user_role not in required_roles:
                    return jsonify({"error": "Insufficient permissions"}), 403
                
                return f(*args, **kwargs)
                
            except ImportError:
                # Flask not available, skip validation for testing
                print("Flask not available, skipping role validation")
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": f"Authorization error: {str(e)}"}), 500
                
        return decorated_function
    return decorator


class AuthExample:
    """Examples of how to use the AuthManager class."""
    
    def run_examples(self):
        """Run some examples demonstrating the AuthManager."""
        auth_manager = AuthManager()
        
        print("Authentication System Example")
        
        # Example 1: Generate API Key
        print("\nExample 1: Generate API Key")
        try:
            api_key = auth_manager.generate_api_key("Test User", ["read", "write"])
            print(f"Generated API Key: {api_key}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 2: Validate API Key
        print("\nExample 2: Validate API Key")
        try:
            is_valid, owner, permissions = auth_manager.validate_api_key(api_key, ["read"])
            print(f"API Key Valid: {is_valid}")
            print(f"Owner: {owner}")
            print(f"Permissions: {permissions}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 3: Register User
        print("\nExample 3: Register User")
        try:
            user = auth_manager.register_user("testuser", "password123!", "test@example.com")
            print(f"Registered User: {user}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 4: Authenticate User
        print("\nExample 4: Authenticate User")
        try:
            is_authenticated, user_data = auth_manager.authenticate_user("testuser", "password123!")
            print(f"Authentication Successful: {is_authenticated}")
            if is_authenticated:
                print(f"User Data: {user_data}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 5: Generate JWT Token
        print("\nExample 5: Generate JWT Token")
        try:
            if is_authenticated:
                token = auth_manager.generate_jwt_token(user_data)
                print(f"JWT Token: {token}")
                
                # Validate the token
                is_valid, payload = auth_manager.validate_jwt_token(token)
                print(f"Token Valid: {is_valid}")
                if is_valid:
                    print(f"Token Payload: {payload}")
                
                # Test token refresh
                print("\nExample 6: Refresh JWT Token")
                new_token = auth_manager.refresh_jwt_token(token)
                print(f"Refreshed Token: {new_token}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 7: Test failed authentication
        print("\nExample 7: Test Failed Authentication")
        try:
            is_auth, _ = auth_manager.authenticate_user("testuser", "wrongpassword")
            print(f"Failed Authentication: {not is_auth}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 8: Revoke API Key
        print("\nExample 8: Revoke API Key")
        try:
            revoked = auth_manager.revoke_api_key(api_key)
            print(f"API Key Revoked: {revoked}")
            
            # Try to use revoked key
            is_valid, _, _ = auth_manager.validate_api_key(api_key)
            print(f"Revoked Key Still Valid: {is_valid}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Clean up example files
        if os.path.exists(API_KEYS_FILE):
            os.remove(API_KEYS_FILE)
        if os.path.exists(USERS_FILE):
            os.remove(USERS_FILE)


def main():
    """Run the AuthManager examples."""
    example = AuthExample()
    example.run_examples()

if __name__ == "__main__":
    main()