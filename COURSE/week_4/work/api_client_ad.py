"""
RESTful API Client
---------------
Implement a complete API client according to the specified requirements.
This exercise focuses on creating a robust client for interacting with RESTful APIs.
"""

import requests
import json
import os
import time
import logging
from urllib.parse import urljoin
import base64

class APIClientConfig:
    """Configuration class for API client settings."""
    
    def __init__(self, 
                 timeout=30,
                 max_retries=3,
                 retry_delay=1,
                 verify_ssl=True,
                 log_level=logging.INFO,
                 rate_limit_requests_per_second=None,
                 default_headers=None):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verify_ssl = verify_ssl
        self.log_level = log_level
        self.rate_limit_requests_per_second = rate_limit_requests_per_second
        self.default_headers = default_headers or {}


class APIClient:
    """
    A class for interacting with RESTful APIs.
    
    Attributes:
        base_url (str): The base URL of the API
        headers (dict): Default headers to send with requests
        config (APIClientConfig): Configuration settings
        logger (logging.Logger): Logger for the client
        session (requests.Session): Persistent session for connection pooling
        
    Methods:
        get: Send a GET request
        post: Send a POST request
        put: Send a PUT request
        delete: Send a DELETE request
        handle_response: Process API responses
        set_auth_token: Set an authentication token
    """
    
    def __init__(self, base_url, auth_token=None, config=None):
        """
        Initialize the API client.
        
        Args:
            base_url (str): The base URL of the API
            auth_token (str, optional): Authentication token. Defaults to None.
            config (APIClientConfig, optional): Configuration object. Defaults to None.
        """
        self.base_url = base_url.rstrip('/') + '/'
        self.config = config or APIClientConfig()
        self.last_request_time = 0
        
        # Use session for connection pooling and better performance
        self.session = requests.Session()
        
        # Set up default headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'APIClient/2.0',
            **self.config.default_headers
        }
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(self.config.log_level)
        
        # Set authentication token if provided
        if auth_token:
            self.set_auth_token(auth_token)
    
    def _rate_limit(self):
        """Apply rate limiting if configured."""
        if self.config.rate_limit_requests_per_second:
            min_interval = 1.0 / self.config.rate_limit_requests_per_second
            elapsed = time.time() - self.last_request_time
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get(self, endpoint, params=None):
        """
        Send a GET request to the API.
        
        Args:
            endpoint (str): API endpoint (relative to base_url)
            params (dict, optional): Query parameters. Defaults to None.
            
        Returns:
            dict or list: Parsed JSON response
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            ValueError: If the API returns an error response
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        self.logger.info(f"GET request to {url}")
        
        self._rate_limit()
        
        try:
            response = self.session.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            return self.handle_response(response)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"GET request failed: {e}")
            raise
    
    def post(self, endpoint, data=None, json_data=None):
        """
        Send a POST request to the API.
        
        Args:
            endpoint (str): API endpoint (relative to base_url)
            data (dict, optional): Form data. Defaults to None.
            json_data (dict, optional): JSON data. Defaults to None.
            
        Returns:
            dict or list: Parsed JSON response
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            ValueError: If the API returns an error response
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        self.logger.info(f"POST request to {url}")
        
        # Determine content type and prepare data
        headers = self.headers.copy()
        if json_data is not None:
            payload = json.dumps(json_data)
            headers['Content-Type'] = 'application/json'
        elif data is not None:
            payload = data
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            payload = None
        
        try:
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )
            return self.handle_response(response)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"POST request failed: {e}")
            raise
    
    def put(self, endpoint, data=None, json_data=None):
        """
        Send a PUT request to the API.
        
        Args:
            endpoint (str): API endpoint (relative to base_url)
            data (dict, optional): Form data. Defaults to None.
            json_data (dict, optional): JSON data. Defaults to None.
            
        Returns:
            dict or list: Parsed JSON response
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            ValueError: If the API returns an error response
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        self.logger.info(f"PUT request to {url}")
        
        # Determine content type and prepare data
        headers = self.headers.copy()
        if json_data is not None:
            payload = json.dumps(json_data)
            headers['Content-Type'] = 'application/json'
        elif data is not None:
            payload = data
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            payload = None
        
        try:
            response = requests.put(
                url,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )
            return self.handle_response(response)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"PUT request failed: {e}")
            raise
    
    def delete(self, endpoint, params=None):
        """
        Send a DELETE request to the API.
        
        Args:
            endpoint (str): API endpoint (relative to base_url)
            params (dict, optional): Query parameters. Defaults to None.
            
        Returns:
            dict or list: Parsed JSON response
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            ValueError: If the API returns an error response
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        self.logger.info(f"DELETE request to {url}")
        
        try:
            response = requests.delete(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            return self.handle_response(response)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"DELETE request failed: {e}")
            raise
    
    def handle_response(self, response):
        """
        Process the API response.
        
        Args:
            response (requests.Response): The HTTP response
            
        Returns:
            dict or list: Parsed JSON response
            
        Raises:
            ValueError: If the response contains an error
        """
        self.logger.info(f"Response status: {response.status_code}")
        
        # Check if the request was successful
        if response.status_code >= 400:
            error_msg = f"API request failed with status {response.status_code}"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg += f": {error_data['message']}"
                elif 'error' in error_data:
                    error_msg += f": {error_data['error']}"
            except json.JSONDecodeError:
                error_msg += f": {response.text}"
            
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Handle successful responses
        if response.status_code == 204:  # No Content
            return {}
        
        try:
            return response.json()
        except json.JSONDecodeError:
            # If response is not JSON, return the text
            return response.text
    
    def set_auth_token(self, token, token_type="Bearer"):
        """
        Set an authentication token for the client.
        
        Args:
            token (str): The authentication token
            token_type (str, optional): The token type. Defaults to "Bearer".
            
        Returns:
            None
        """
        self.headers['Authorization'] = f"{token_type} {token}"
        self.logger.info(f"Authentication token set with type: {token_type}")
    
    def set_basic_auth(self, username, password):
        """
        Set basic authentication for the client.
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            None
        """
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers['Authorization'] = f"Basic {credentials}"
        self.logger.info("Basic authentication credentials set")
    
    def set_custom_header(self, key, value):
        """
        Set a custom header for requests.
        
        Args:
            key (str): Header name
            value (str): Header value
            
        Returns:
            None
        """
        self.headers[key] = value
        self.logger.info(f"Custom header set: {key}")
    
    def upload_file(self, endpoint, filepath, file_param_name='file', additional_data=None):
        """
        Upload a file to the API.
        
        Args:
            endpoint (str): API endpoint (relative to base_url)
            filepath (str): Path to the file to upload
            file_param_name (str, optional): Name of the file parameter. Defaults to 'file'.
            additional_data (dict, optional): Additional form data. Defaults to None.
            
        Returns:
            dict or list: Parsed JSON response
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            requests.exceptions.RequestException: If the request fails
            ValueError: If the API returns an error response
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        self.logger.info(f"Uploading file {filepath} to {url}")
        
        # Prepare headers without Content-Type (let requests handle it for multipart)
        headers = {k: v for k, v in self.headers.items() if k.lower() != 'content-type'}
        
        try:
            with open(filepath, 'rb') as f:
                files = {file_param_name: f}
                data = additional_data or {}
                
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=self.timeout
                )
                
            return self.handle_response(response)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"File upload failed: {e}")
            raise
        except IOError as e:
            self.logger.error(f"File read error: {e}")
            raise
    
    def download_file(self, endpoint, save_path, params=None):
        """
        Download a file from the API.
        
        Args:
            endpoint (str): API endpoint (relative to base_url)
            save_path (str): Path where to save the file
            params (dict, optional): Query parameters. Defaults to None.
            
        Returns:
            bool: True if download was successful
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            IOError: If writing to the file fails
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        self.logger.info(f"Downloading file from {url} to {save_path}")
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code >= 400:
                error_msg = f"Download failed with status {response.status_code}"
                self.logger.error(error_msg)
                raise requests.exceptions.RequestException(error_msg)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"File downloaded successfully to {save_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Download failed: {e}")
            raise
        except IOError as e:
            self.logger.error(f"File write error: {e}")
            raise
    
    def retry_request(self, method, endpoint, max_retries=3, retry_delay=1, **kwargs):
        """
        Send a request with automatic retry logic.
        
        Args:
            method (str): HTTP method ('get', 'post', 'put', 'delete')
            endpoint (str): API endpoint (relative to base_url)
            max_retries (int, optional): Maximum number of retries. Defaults to 3.
            retry_delay (int, optional): Delay between retries in seconds. Defaults to 1.
            **kwargs: Additional arguments to pass to the request method
            
        Returns:
            dict or list: Parsed JSON response
            
        Raises:
            requests.exceptions.RequestException: If all retries fail
            ValueError: If the API returns an error response on all retries
        """
        method = method.lower()
        if method not in ['get', 'post', 'put', 'delete']:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        method_func = getattr(self, method)
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"Attempt {attempt + 1} of {max_retries + 1}")
                return method_func(endpoint, **kwargs)
            except (requests.exceptions.RequestException, ValueError) as e:
                last_exception = e
                if attempt < max_retries:
                    self.logger.warning(f"Request failed, retrying in {retry_delay} seconds: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"All retry attempts failed")
        
        raise last_exception


class APIClientExample:
    """Examples of how to use the APIClient class."""
    
    def run_examples(self):
        """Run some example API requests."""
        # Initialize client with JSONPlaceholder API
        client = APIClient('https://jsonplaceholder.typicode.com/')
        
        # Example 1: GET request
        print("Example 1: GET request")
        try:
            posts = client.get('posts')
            print(f"Retrieved {len(posts)} posts")
            print(f"First post title: {posts[0]['title']}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 2: GET request with parameters
        print("\nExample 2: GET request with parameters")
        try:
            posts = client.get('posts', params={'userId': 1})
            print(f"Retrieved {len(posts)} posts for user 1")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 3: POST request
        print("\nExample 3: POST request")
        try:
            new_post = {
                'title': 'New Post',
                'body': 'This is a new post',
                'userId': 1
            }
            response = client.post('posts', json_data=new_post)
            print(f"Created new post with ID: {response.get('id')}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 4: PUT request
        print("\nExample 4: PUT request")
        try:
            updated_post = {
                'id': 1,
                'title': 'Updated Post',
                'body': 'This post has been updated',
                'userId': 1
            }
            response = client.put('posts/1', json_data=updated_post)
            print(f"Updated post: {response.get('title')}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 5: DELETE request
        print("\nExample 5: DELETE request")
        try:
            response = client.delete('posts/1')
            print(f"Deleted post. Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 6: Using authentication
        print("\nExample 6: Setting authentication")
        try:
            client.set_auth_token('your-token-here')
            client.set_custom_header('X-Custom-Header', 'custom-value')
            print("Authentication and custom headers set")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 7: Retry mechanism
        print("\nExample 7: Retry mechanism")
        try:
            response = client.retry_request('get', 'posts/1', max_retries=2)
            print(f"Retrieved post with retry: {response.get('title')}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\nNote: These examples use JSONPlaceholder, a fake REST API for testing")


def main():
    """Run the API client examples."""
    example = APIClientExample()
    example.run_examples()

if __name__ == "__main__":
    main()