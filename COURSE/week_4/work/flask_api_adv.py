"""
Flask API Server
-------------
Create a simple Flask API server according to the specified requirements.
This exercise focuses on building RESTful APIs with Flask.
"""

from flask import Flask, request, jsonify, abort, make_response
import json
import os
import uuid
from datetime import datetime
from functools import wraps
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Sample data (in a real app, this would come from a database)
BOOKS_FILE = 'books.json'

# Valid API keys (in a real app, these would be stored securely)
VALID_API_KEYS = {'your-api-key-here', 'test-key-123', 'admin-key-456'}

def load_books():
    """Load books from JSON file or create empty list if file doesn't exist."""
    try:
        if os.path.exists(BOOKS_FILE):
            with open(BOOKS_FILE, 'r') as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        logger.error(f"Error loading books: {e}")
        return []

def save_books(books):
    """Save books to JSON file."""
    try:
        with open(BOOKS_FILE, 'w') as f:
            json.dump(books, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving books: {e}")
        return False

def validate_book_data(data, required_fields=None):
    """Validate book data structure."""
    if required_fields is None:
        required_fields = ['title', 'author', 'published_year', 'genre']
    
    if not isinstance(data, dict):
        return False, "Request data must be a JSON object"
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate data types
    if 'published_year' in data and not isinstance(data['published_year'], int):
        return False, "published_year must be an integer"
    
    if 'title' in data and not isinstance(data['title'], str):
        return False, "title must be a string"
        
    if 'author' in data and not isinstance(data['author'], str):
        return False, "author must be a string"
        
    if 'genre' in data and not isinstance(data['genre'], str):
        return False, "genre must be a string"
    
    return True, None

# Sample books data for initial setup
SAMPLE_BOOKS = [
    {
        "id": "1",
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "published_year": 1925,
        "genre": "Fiction"
    },
    {
        "id": "2",
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "published_year": 1960,
        "genre": "Fiction"
    },
    {
        "id": "3",
        "title": "1984",
        "author": "George Orwell",
        "published_year": 1949,
        "genre": "Dystopian"
    }
]

# Create sample data file if it doesn't exist
if not os.path.exists(BOOKS_FILE):
    save_books(SAMPLE_BOOKS)

# Auth functions
def require_api_key(f):
    """Decorator for requiring API key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return make_response(jsonify({'error': 'API key is required'}), 401)
        
        if api_key not in VALID_API_KEYS:
            return make_response(jsonify({'error': 'Invalid API key'}), 401)
        
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/v1/books', methods=['GET'])
def get_books():
    """
    Get all books or filter by query parameters.
    
    Returns:
        json: A list of books
    """
    books = load_books()
    
    # Handle query parameters for filtering
    author = request.args.get('author')
    genre = request.args.get('genre')
    year = request.args.get('year')
    
    filtered_books = books
    
    if author:
        filtered_books = [book for book in filtered_books 
                         if author.lower() in book['author'].lower()]
    
    if genre:
        filtered_books = [book for book in filtered_books 
                         if genre.lower() in book['genre'].lower()]
    
    if year:
        try:
            year_int = int(year)
            filtered_books = [book for book in filtered_books 
                             if book['published_year'] == year_int]
        except ValueError:
            return make_response(jsonify({'error': 'Year must be a valid integer'}), 400)
    
    return jsonify({
        'books': filtered_books,
        'total': len(filtered_books)
    })

@app.route('/api/v1/books/<book_id>', methods=['GET'])
def get_book(book_id):
    """
    Get a specific book by ID.
    
    Args:
        book_id (str): The ID of the book to retrieve
        
    Returns:
        json: The book data
        
    Raises:
        404: If the book is not found
    """
    books = load_books()
    book = next((book for book in books if book['id'] == book_id), None)
    
    if book is None:
        abort(404)
    
    return jsonify(book)

@app.route('/api/v1/books', methods=['POST'])
@require_api_key
def create_book():
    """
    Create a new book.
    
    Returns:
        json: The created book data
        
    Raises:
        400: If the request data is invalid
    """
    if not request.json:
        return make_response(jsonify({'error': 'Request must contain JSON data'}), 400)
    
    is_valid, error_msg = validate_book_data(request.json)
    if not is_valid:
        return make_response(jsonify({'error': error_msg}), 400)
    
    books = load_books()
    
    # Create new book with unique ID
    new_book = {
        'id': str(uuid.uuid4()),
        'title': request.json['title'],
        'author': request.json['author'],
        'published_year': request.json['published_year'],
        'genre': request.json['genre'],
        'created_at': datetime.now().isoformat()
    }
    
    books.append(new_book)
    
    if not save_books(books):
        return make_response(jsonify({'error': 'Failed to save book'}), 500)
    
    return jsonify(new_book), 201

@app.route('/api/v1/books/<book_id>', methods=['PUT'])
@require_api_key
def update_book(book_id):
    """
    Update a specific book by ID.
    
    Args:
        book_id (str): The ID of the book to update
        
    Returns:
        json: The updated book data
        
    Raises:
        404: If the book is not found
        400: If the request data is invalid
    """
    if not request.json:
        return make_response(jsonify({'error': 'Request must contain JSON data'}), 400)
    
    books = load_books()
    book_index = next((i for i, book in enumerate(books) if book['id'] == book_id), None)
    
    if book_index is None:
        abort(404)
    
    # For updates, we don't require all fields, just validate the ones provided
    update_data = request.json
    allowed_fields = ['title', 'author', 'published_year', 'genre']
    
    # Validate only the fields that are being updated
    for field in update_data:
        if field not in allowed_fields:
            return make_response(jsonify({'error': f'Invalid field: {field}'}), 400)
    
    is_valid, error_msg = validate_book_data(update_data, required_fields=[])
    if not is_valid:
        return make_response(jsonify({'error': error_msg}), 400)
    
    # Update the book
    books[book_index].update(update_data)
    books[book_index]['updated_at'] = datetime.now().isoformat()
    
    if not save_books(books):
        return make_response(jsonify({'error': 'Failed to update book'}), 500)
    
    return jsonify(books[book_index])

@app.route('/api/v1/books/<book_id>', methods=['DELETE'])
@require_api_key
def delete_book(book_id):
    """
    Delete a specific book by ID.
    
    Args:
        book_id (str): The ID of the book to delete
        
    Returns:
        json: Success message
        
    Raises:
        404: If the book is not found
    """
    books = load_books()
    book_index = next((i for i, book in enumerate(books) if book['id'] == book_id), None)
    
    if book_index is None:
        abort(404)
    
    deleted_book = books.pop(book_index)
    
    if not save_books(books):
        return make_response(jsonify({'error': 'Failed to delete book'}), 500)
    
    return jsonify({
        'message': 'Book deleted successfully',
        'deleted_book': deleted_book
    })

@app.route('/api/v1/books/search', methods=['GET'])
def search_books():
    """
    Search for books by title, author, or genre.
    
    Returns:
        json: A list of matching books
    """
    query = request.args.get('q', '').lower()
    if not query:
        return make_response(jsonify({'error': 'Search query parameter "q" is required'}), 400)
    
    books = load_books()
    matching_books = []
    
    for book in books:
        if (query in book['title'].lower() or 
            query in book['author'].lower() or 
            query in book['genre'].lower()):
            matching_books.append(book)
    
    return jsonify({
        'query': request.args.get('q'),
        'books': matching_books,
        'total': len(matching_books)
    })

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about the books collection.
    
    Returns:
        json: Statistics like total books, books per genre, etc.
    """
    books = load_books()
    
    if not books:
        return jsonify({
            'total_books': 0,
            'genres': {},
            'authors': {},
            'publication_years': {},
            'oldest_book': None,
            'newest_book': None
        })
    
    # Calculate statistics
    genre_counts = {}
    author_counts = {}
    year_counts = {}
    
    for book in books:
        # Genre statistics
        genre = book['genre']
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Author statistics
        author = book['author']
        author_counts[author] = author_counts.get(author, 0) + 1
        
        # Year statistics
        year = book['published_year']
        year_counts[year] = year_counts.get(year, 0) + 1
    
    # Find oldest and newest books
    oldest_book = min(books, key=lambda x: x['published_year'])
    newest_book = max(books, key=lambda x: x['published_year'])
    
    return jsonify({
        'total_books': len(books),
        'genres': genre_counts,
        'authors': author_counts,
        'publication_years': year_counts,
        'oldest_book': {
            'title': oldest_book['title'],
            'author': oldest_book['author'],
            'year': oldest_book['published_year']
        },
        'newest_book': {
            'title': newest_book['title'],
            'author': newest_book['author'],
            'year': newest_book['published_year']
        }
    })

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 errors."""
    return make_response(jsonify({'error': 'Bad Request'}), 400)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return make_response(jsonify({'error': 'Not Found'}), 404)

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return make_response(jsonify({'error': 'Internal Server Error'}), 500)

# Custom middleware to log requests
@app.before_request
def log_request_info():
    """Log request information."""
    logger.info(f"Request: {request.method} {request.path} {request.remote_addr}")

@app.after_request
def add_header(response):
    """Add common headers to response."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-API-Key'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

if __name__ == '__main__':
    # Ensure books.json exists with sample data
    if not os.path.exists(BOOKS_FILE):
        save_books(SAMPLE_BOOKS)
    
    print("Flask API Server")
    print("Available endpoints:")
    print("  GET    /api/v1/books           - Get all books")
    print("  GET    /api/v1/books/<id>      - Get book by ID")
    print("  POST   /api/v1/books           - Create a new book (requires API key)")
    print("  PUT    /api/v1/books/<id>      - Update a book (requires API key)")
    print("  DELETE /api/v1/books/<id>      - Delete a book (requires API key)")
    print("  GET    /api/v1/books/search    - Search books")
    print("  GET    /api/v1/stats           - Get collection statistics")
    print("\nValid API Keys for testing:")
    print("  - your-api-key-here")
    print("  - test-key-123")
    print("  - admin-key-456")
    print("\nRunning on http://127.0.0.1:5000/")
    
    app.run(debug=True)