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
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from contextlib import contextmanager

# Constants
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-key')  # In production, use an environment variable
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(hours=1)
API_KEYS_FILE = 'api_keys.json'
USERS_FILE = 'users.json'

class DatabaseManager:
    """Database abstraction layer for authentication data."""
    
    def __init__(self, db_path='auth.db'):
        """Initialize database connection and create tables."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            # Users table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TEXT
                )
            ''')
            
            # API keys table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    api_key TEXT PRIMARY KEY,
                    owner_name TEXT NOT NULL,
                    permissions TEXT NOT NULL,  -- JSON array
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    usage_count INTEGER DEFAULT 0,
                    revoked_at TEXT
                )
            ''')
            
            # JWT blacklist table (for token revocation)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jwt_blacklist (
                    jti TEXT PRIMARY KEY,
                    exp_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_owner ON api_keys(owner_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active)')
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def create_user(self, user_data):
        """Create a new user in the database."""
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO users (user_id, username, email, role, password_hash, 
                                 salt, created_at, is_active, login_attempts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data['user_id'], user_data['username'], user_data['email'],
                user_data['role'], user_data['password_hash'], user_data['salt'],
                user_data['created_at'], user_data['is_active'], user_data['login_attempts']
            ))
    
    def get_user(self, username):
        """Get user by username."""
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user(self, username, updates):
        """Update user data."""
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [username]
        
        with self._get_connection() as conn:
            conn.execute(f'UPDATE users SET {set_clause} WHERE username = ?', values)
    
    def create_api_key(self, key_data):
        """Create a new API key."""
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO api_keys (api_key, owner_name, permissions, created_at, 
                                    is_active, usage_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                key_data['api_key'], key_data['owner_name'], 
                json.dumps(key_data['permissions']), key_data['created_at'],
                key_data['is_active'], key_data['usage_count']
            ))
    
    def get_api_key(self, api_key):
        """Get API key data."""
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['permissions'] = json.loads(data['permissions'])
                return data
            return None
    
    def update_api_key(self, api_key, updates):
        """Update API key data."""
        if 'permissions' in updates:
            updates['permissions'] = json.dumps(updates['permissions'])
        
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [api_key]
        
        with self._get_connection() as conn:
            conn.execute(f'UPDATE api_keys SET {set_clause} WHERE api_key = ?', values)
    
    def get_user_api_keys(self, username):
        """Get all API keys for a user."""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT api_key, permissions, created_at, is_active, usage_count
                FROM api_keys WHERE owner_name = ?
            ''', (username,))
            
            keys = []
            for row in cursor.fetchall():
                data = dict(row)
                data['permissions'] = json.loads(data['permissions'])
                keys.append(data)
            return keys
    
    def cleanup_expired_tokens(self):
        """Remove expired JWT tokens from blacklist."""
        current_time = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute('DELETE FROM jwt_blacklist WHERE exp_date < ?', (current_time,))

    def get_user_by_email(self, email):
        """Get user by email address."""
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_api_keys_by_owner(self, owner_name):
        """Get all API keys for an owner."""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM api_keys WHERE owner_name = ? AND is_active = 1
            ''', (owner_name,))
            
            keys = []
            for row in cursor.fetchall():
                data = dict(row)
                data['permissions'] = json.loads(data['permissions'])
                keys.append(data)
            return keys
    
    def blacklist_jwt_token(self, jti, exp_date):
        """Add JWT token to blacklist."""
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR IGNORE INTO jwt_blacklist (jti, exp_date, created_at)
                VALUES (?, ?, ?)
            ''', (jti, exp_date, datetime.now().isoformat()))
    
    def is_token_blacklisted(self, jti):
        """Check if JWT token is blacklisted."""
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT 1 FROM jwt_blacklist WHERE jti = ?', (jti,))
            return cursor.fetchone() is not None


class AuthManager:
    """
    Enhanced AuthManager with database backend.
    """
    
    def __init__(self, db_path='auth.db'):
        """Initialize the AuthManager with database backend."""
        self.db = DatabaseManager(db_path)
        print(f"AuthManager initialized with database: {db_path}")
    
    def generate_api_key(self, owner_name, permissions=None):
        """Generate a new API key with database storage."""
        if not owner_name or not isinstance(owner_name, str):
            raise ValueError("Owner name must be a non-empty string")
        
        # Generate a secure random API key
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        
        # Set default permissions if none provided
        if permissions is None:
            permissions = ["read"]
        
        # Create key data
        key_data = {
            "api_key": api_key,
            "owner_name": owner_name,
            "permissions": permissions,
            "created_at": datetime.now().isoformat(),
            "is_active": True,
            "usage_count": 0
        }
        
        # Store in database
        self.db.create_api_key(key_data)
        
        print(f"Generated API key for {owner_name} with permissions: {permissions}")
        return api_key
    
    def validate_api_key(self, api_key, required_permissions=None):
        """Validate an API key using database lookup."""
        key_data = self.db.get_api_key(api_key)
        
        if not key_data or not key_data.get("is_active", False):
            return False, None, []
        
        # Update last used timestamp and usage count
        updates = {
            "last_used": datetime.now().isoformat(),
            "usage_count": key_data.get("usage_count", 0) + 1
        }
        self.db.update_api_key(api_key, updates)
        
        owner_name = key_data.get("owner_name")
        permissions = key_data.get("permissions", [])
        
        # Check required permissions if specified
        if required_permissions:
            if not all(perm in permissions for perm in required_permissions):
                return False, owner_name, permissions
        
        return True, owner_name, permissions
    
    def register_user(self, username, password, email, role='user'):
        """Register a new user with database storage."""
        # Validate inputs
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if not re.match(r'^[a-zA-Z0-9_]+
    
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
        Validate a JWT token with database blacklist check.
        
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
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and self.db.is_token_blacklisted(jti):
                return False, None
            
            # Check if user still exists and is active
            username = payload.get("username")
            if username:
                user_data = self.db.get_user(username)
                if not user_data or not user_data.get("is_active", False):
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
        Refresh a JWT token with database validation.
        
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
        
        # Get current user data from database
        username = payload.get("username")
        user_data = self.db.get_user(username)
        if not user_data:
            raise ValueError("User no longer exists")
        
        # Blacklist the old token
        old_jti = payload.get("jti")
        if old_jti:
            exp_date = datetime.fromtimestamp(payload.get("exp", 0)).isoformat()
            self.db.blacklist_jwt_token(old_jti, exp_date)
        
        # Create safe user data
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
        """Revoke an API key using database update."""
        key_data = self.db.get_api_key(api_key)
        if key_data:
            self.db.update_api_key(api_key, {
                "is_active": False,
                "revoked_at": datetime.now().isoformat()
            })
            print(f"Revoked API key: {api_key}")
            return True
        return False
    
    def get_user_api_keys(self, username):
        """Get all API keys for a user from database."""
        keys = self.db.get_user_api_keys(username)
        user_keys = []
        for key_data in keys:
            user_keys.append({
                "key": key_data['api_key'][:10] + "...",  # Masked key
                "permissions": key_data.get("permissions"),
                "created_at": key_data.get("created_at"),
                "is_active": key_data.get("is_active"),
                "usage_count": key_data.get("usage_count", 0)
            })
        return user_keys
    
    def update_user_role(self, username, new_role):
        """Update a user's role in database."""
        user_data = self.db.get_user(username)
        if not user_data:
            raise ValueError("User not found")
        
        if new_role not in ['user', 'admin', 'moderator']:
            raise ValueError("Invalid role")
        
        self.db.update_user(username, {"role": new_role})
        return True
    
    def cleanup_database(self):
        """Perform database maintenance tasks."""
        self.db.cleanup_expired_tokens()
        print("Database cleanup completed")


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
        
        # Clean up example database
        if os.path.exists('auth.db'):
            os.remove('auth.db')


def main():
    """Run the AuthManager examples."""
    example = AuthExample()
    example.run_examples()

if __name__ == "__main__":
    main(), username):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        
        # Check if username already exists
        if self.db.get_user(username):
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
            "is_active": True,
            "login_attempts": 0
        }
        
        # Store user in database
        self.db.create_user(user_data)
        
        # Return user data without sensitive information
        safe_user_data = {k: v for k, v in user_data.items() 
                         if k not in ['password_hash', 'salt']}
        
        print(f"Registered user: {username}")
        return safe_user_data
    
    def authenticate_user(self, username, password):
        """Authenticate a user using database lookup."""
        if not username or not password:
            return False, None
        
        user_data = self.db.get_user(username)
        if not user_data:
            return False, None
        
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
                self.db.update_user(username, {
                    "locked_until": None,
                    "login_attempts": 0
                })
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
            login_attempts = user_data.get("login_attempts", 0) + 1
            updates = {"login_attempts": login_attempts}
            
            # Lock account after 5 failed attempts
            if login_attempts >= 5:
                locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                updates["locked_until"] = locked_until
                print(f"Account locked for {username} due to too many failed attempts")
            
            self.db.update_user(username, updates)
            return False, None
        
        # Successful authentication
        self.db.update_user(username, {
            "last_login": datetime.now().isoformat(),
            "login_attempts": 0,
            "locked_until": None
        })
        
        # Return safe user data
        safe_user_data = {k: v for k, v in user_data.items() 
                         if k not in ['password_hash', 'salt']}
        safe_user_data["last_login"] = datetime.now().isoformat()
        safe_user_data["login_attempts"] = 0
        safe_user_data["locked_until"] = None
        
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