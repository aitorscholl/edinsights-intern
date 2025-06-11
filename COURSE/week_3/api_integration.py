"""
API Integration
------------
Complete the following functions according to their docstrings.
This exercise focuses on working with APIs in Python.
"""

import requests
import json
import time
from datetime import datetime

def make_api_request(url, method="GET", headers=None, params=None, data=None, timeout=10):
    """
    Make an API request.
    
    Args:
        url (str): The API endpoint URL
        method (str, optional): HTTP method ('GET', 'POST', 'PUT', 'DELETE'). Defaults to "GET".
        headers (dict, optional): HTTP headers. Defaults to None.
        params (dict, optional): Query parameters. Defaults to None.
        data (dict, optional): Request body for POST/PUT. Defaults to None.
        timeout (int, optional): Request timeout in seconds. Defaults to 10.
        
    Returns:
        tuple: (response_data, status_code)
        
    Raises:
        requests.exceptions.RequestException: If the request fails
    """
    try:
        # Make the request based on method
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, params=params, json=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, params=params, json=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, params=params, timeout=timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            # If not JSON, return text
            response_data = response.text
            
        return response_data, response.status_code
        
    except requests.exceptions.RequestException:
        raise

def get_weather_data(api_key, city):
    """
    Get current weather data for a city using OpenWeatherMap API.
    
    Args:
        api_key (str): OpenWeatherMap API key
        city (str): City name
        
    Returns:
        dict: Weather data
        
    Raises:
        ValueError: If the city is not found
        requests.exceptions.RequestException: If the request fails
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"  # Use metric units
    }
    
    try:
        response = requests.get(base_url, params=params)
        
        # Check if city was found
        if response.status_code == 404:
            raise ValueError(f"City '{city}' not found")
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException:
        raise

def get_github_user_repos(username):
    """
    Get the public repositories for a GitHub user.
    
    Args:
        username (str): GitHub username
        
    Returns:
        list: List of repository dictionaries
        
    Raises:
        ValueError: If the user is not found
        requests.exceptions.RequestException: If the request fails
    """
    url = f"https://api.github.com/users/{username}/repos"
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        # Check if user was found
        if response.status_code == 404:
            raise ValueError(f"User '{username}' not found")
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException:
        raise

def post_data_to_api(url, data, headers=None):
    """
    Send data to an API using a POST request.
    
    Args:
        url (str): The API endpoint URL
        data (dict): Data to send
        headers (dict, optional): HTTP headers. Defaults to None.
        
    Returns:
        tuple: (response_data, status_code)
        
    Raises:
        requests.exceptions.RequestException: If the request fails
    """
    if headers is None:
        headers = {"Content-Type": "application/json"}
    elif "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text
            
        return response_data, response.status_code
        
    except requests.exceptions.RequestException:
        raise

def fetch_paginated_data(url, params=None, page_param="page", limit=None):
    """
    Fetch data from a paginated API endpoint.
    
    Args:
        url (str): The API endpoint URL
        params (dict, optional): Query parameters. Defaults to None.
        page_param (str, optional): Name of the page parameter. Defaults to "page".
        limit (int, optional): Maximum number of items to fetch. Defaults to None (fetch all).
        
    Returns:
        list: Combined results from all pages
        
    Raises:
        requests.exceptions.RequestException: If the request fails
    """
    if params is None:
        params = {}
    
    all_results = []
    page = 1
    items_fetched = 0
    
    while True:
        # Set page parameter
        params[page_param] = page
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                # Response is a list
                results = data
            elif isinstance(data, dict):
                # Look for common keys that contain results
                if 'results' in data:
                    results = data['results']
                elif 'data' in data:
                    results = data['data']
                elif 'items' in data:
                    results = data['items']
                else:
                    # Assume the whole dict is one item
                    results = [data]
            else:
                break
            
            # Check if we got any results
            if not results:
                break
                
            # Add results to our collection
            for item in results:
                if limit and items_fetched >= limit:
                    return all_results
                all_results.append(item)
                items_fetched += 1
            
            # Check if we've reached the limit
            if limit and items_fetched >= limit:
                break
                
            # Move to next page
            page += 1
            
        except requests.exceptions.RequestException:
            raise
    
    return all_results

def handle_rate_limits(func, max_retries=3, delay=1):
    """
    Decorator function to handle API rate limits.
    
    Args:
        func (function): Function to decorate
        max_retries (int, optional): Maximum number of retries. Defaults to 3.
        delay (int, optional): Delay between retries in seconds. Defaults to 1.
        
    Returns:
        function: Decorated function
    """
    def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < max_retries:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                # Check if rate limited (usually 429 Too Many Requests)
                if e.response.status_code == 429:
                    attempts += 1
                    if attempts < max_retries:
                        retry_after = int(e.response.headers.get('Retry-After', delay))
                        print(f"Rate limited. Retrying in {retry_after} seconds...")
                        time.sleep(retry_after)
                    else:
                        raise ValueError("Max retries exceeded due to rate limiting")
                else:
                    raise
    return wrapper

def download_file_from_url(url, save_path):
    """
    Download a file from a URL and save it to the specified path.
    
    Args:
        url (str): URL of the file to download
        save_path (str): Path where the file should be saved
        
    Returns:
        bool: True if download was successful
        
    Raises:
        requests.exceptions.RequestException: If the request fails
    """
    try:
        # Stream the download to handle large files
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Write to file in chunks
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
        
    except requests.exceptions.RequestException:
        raise

def create_api_client(base_url, auth_token=None):
    """
    Create a simple API client with preset base URL and auth token.
    
    Args:
        base_url (str): Base URL for API requests
        auth_token (str, optional): Authentication token. Defaults to None.
        
    Returns:
        dict: Dictionary containing API client functions:
            - get(endpoint, params): Make GET request
            - post(endpoint, data): Make POST request
            - put(endpoint, data): Make PUT request
            - delete(endpoint): Make DELETE request
    """
    # Ensure base_url ends without trailing slash
    base_url = base_url.rstrip('/')
    
    # Prepare headers with auth token if provided
    headers = {}
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    def get(endpoint, params=None):
        """Make GET request to endpoint"""
        url = f"{base_url}/{endpoint.lstrip('/')}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(endpoint, data):
        """Make POST request to endpoint"""
        url = f"{base_url}/{endpoint.lstrip('/')}"
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def put(endpoint, data):
        """Make PUT request to endpoint"""
        url = f"{base_url}/{endpoint.lstrip('/')}"
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def delete(endpoint):
        """Make DELETE request to endpoint"""
        url = f"{base_url}/{endpoint.lstrip('/')}"
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.status_code == 204  # 204 No Content is typical for DELETE
    
    return {
        'get': get,
        'post': post,
        'put': put,
        'delete': delete
    }

def main():
    """Run examples to test your functions."""
    print("API Integration Examples")
    
    # Note: In a real assignment, students would use their own API keys
    # For this template, we'll use placeholders
    
    # Example 1: Get GitHub user repositories
    try:
        print("\nFetching public repositories for 'octocat':")
        repos = get_github_user_repos("octocat")
        print(f"Found {len(repos)} repositories")
        # Print the first 3 repo names
        if repos:
            print("Repository names:")
            for repo in repos[:3]:
                print(f"- {repo['name']}")
    except Exception as e:
        print(f"Error fetching GitHub repos: {e}")
    
    # Example 2: Make a simple API request
    try:
        print("\nMaking request to JSONPlaceholder API:")
        url = "https://jsonplaceholder.typicode.com/posts/1"
        data, status = make_api_request(url)
        print(f"Status code: {status}")
        print(f"Data: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Error making API request: {e}")
    
    # Example 3: Fetch paginated data
    try:
        print("\nFetching paginated data (first 5 items):")
        url = "https://jsonplaceholder.typicode.com/posts"
        data = fetch_paginated_data(url, limit=5)
        print(f"Fetched {len(data)} items")
    except Exception as e:
        print(f"Error fetching paginated data: {e}")
    
    # Example 4: Create API client
    try:
        print("\nCreating API client for JSONPlaceholder:")
        client = create_api_client("https://jsonplaceholder.typicode.com")
        
        # Get a post
        post = client['get']("posts/1")
        print(f"Retrieved post: {post['title']}")
        
        # Create a new post
        new_post = client['post']("posts", {
            "title": "Test Post",
            "body": "This is a test",
            "userId": 1
        })
        print(f"Created post with ID: {new_post['id']}")
    except Exception as e:
        print(f"Error with API client: {e}")
    
    # Example 5: Download file
    try:
        print("\nDownloading sample file:")
        # Using a small test file
        url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        success = download_file_from_url(url, "sample_download.pdf")
        if success:
            print("File downloaded successfully!")
    except Exception as e:
        print(f"Error downloading file: {e}")
    
    print("\nAll examples completed!")
`1  Z`
if __name__ == "__main__":
    main()