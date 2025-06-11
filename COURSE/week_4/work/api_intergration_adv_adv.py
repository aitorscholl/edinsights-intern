"""
API Integration Advanced
---------------------
Complete the multi-API integration according to the specified requirements.
This exercise focuses on combining data from multiple APIs and implementing
advanced API interaction techniques.
"""

import requests
import aiohttp
import asyncio
import json
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiAPIClient:
    """
    A class for interacting with multiple APIs and combining their data.
    
    Attributes:
        apis (dict): Dictionary of API configurations
        cache (dict): Simple cache for API responses
        cache_expiry (dict): Expiry times for cached responses
        
    Methods:
        get_weather_data: Get weather data for a location
        get_news_data: Get news articles
        get_stock_data: Get stock market data
        combine_data: Combine data from multiple APIs
    """
    
    def __init__(self, config=None):
        """
        Initialize the MultiAPIClient.
        
        Args:
            config (dict, optional): Configuration for APIs. Defaults to None.
                Format: {
                    'api_name': {
                        'base_url': 'https://api.example.com',
                        'api_key': 'your-api-key',
                        'endpoints': {...}
                    },
                    ...
                }
        """
        self.apis = config or {}
        self.cache = {}
        self.cache_expiry = {}
        self.session = requests.Session()
        
        # Set default timeout and headers
        self.session.timeout = 30
        self.session.headers.update({
            'User-Agent': 'MultiAPIClient/1.0',
            'Accept': 'application/json'
        })
        
        logger.info("MultiAPIClient initialized")
    
    def get_weather_data(self, location, units='metric'):
        """
        Get weather data for a location using OpenWeatherMap API.
        
        Args:
            location (str): City name or coordinates
            units (str, optional): Units of measurement ('metric', 'imperial'). Defaults to 'metric'.
            
        Returns:
            dict: Weather data
            
        Raises:
            ValueError: If the location is not found
            requests.exceptions.RequestException: If the request fails
        """
        cache_key = f"weather_{location}_{units}"
        
        # Check cache first
        cached_data = self._get_cached_response(cache_key)
        if cached_data:
            logger.info(f"Returning cached weather data for {location}")
            return cached_data
        
        if 'weather' not in self.apis:
            raise ValueError("Weather API configuration not found")
        
        weather_config = self.apis['weather']
        url = urljoin(weather_config['base_url'], weather_config['endpoints']['current'])
        
        params = {
            'q': location,
            'appid': weather_config['api_key'],
            'units': units
        }
        
        try:
            response = self._make_request(url, params=params)
            
            if response.get('cod') == '404':
                raise ValueError(f"Location '{location}' not found")
            
            # Cache the response for 10 minutes
            self._cache_response(cache_key, response, expire_seconds=600)
            
            logger.info(f"Retrieved weather data for {location}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get weather data for {location}: {e}")
            raise
    
    def get_news_data(self, query=None, category=None, country=None, max_results=10):
        """
        Get news articles using NewsAPI.
        
        Args:
            query (str, optional): Search query. Defaults to None.
            category (str, optional): News category. Defaults to None.
            country (str, optional): Country code. Defaults to None.
            max_results (int, optional): Maximum number of results. Defaults to 10.
            
        Returns:
            list: News articles
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        cache_key = f"news_{query}_{category}_{country}_{max_results}"
        
        # Check cache first
        cached_data = self._get_cached_response(cache_key)
        if cached_data:
            logger.info("Returning cached news data")
            return cached_data
        
        if 'news' not in self.apis:
            raise ValueError("News API configuration not found")
        
        news_config = self.apis['news']
        
        # Choose endpoint based on query
        if query:
            endpoint = news_config['endpoints']['everything']
            params = {'q': query}
        else:
            endpoint = news_config['endpoints']['top_headlines']
            params = {}
        
        url = urljoin(news_config['base_url'], endpoint)
        
        # Add optional parameters
        if category:
            params['category'] = category
        if country:
            params['country'] = country
        
        params['apiKey'] = news_config['api_key']
        params['pageSize'] = min(max_results, 100)  # API limit
        
        try:
            response = self._make_request(url, params=params)
            articles = response.get('articles', [])
            
            # Limit results
            articles = articles[:max_results]
            
            # Cache the response for 15 minutes
            self._cache_response(cache_key, articles, expire_seconds=900)
            
            logger.info(f"Retrieved {len(articles)} news articles")
            return articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get news data: {e}")
            raise
    
    def get_stock_data(self, symbol, interval='1d', period='1mo'):
        """
        Get stock market data using Alpha Vantage API.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            interval (str, optional): Time interval between data points. Defaults to '1d'.
            period (str, optional): Period to retrieve data for. Defaults to '1mo'.
            
        Returns:
            dict: Stock market data
            
        Raises:
            ValueError: If the symbol is not found
            requests.exceptions.RequestException: If the request fails
        """
        cache_key = f"stock_{symbol}_{interval}_{period}"
        
        # Check cache first
        cached_data = self._get_cached_response(cache_key)
        if cached_data:
            logger.info(f"Returning cached stock data for {symbol}")
            return cached_data
        
        if 'stocks' not in self.apis:
            raise ValueError("Stock API configuration not found")
        
        stocks_config = self.apis['stocks']
        url = stocks_config['base_url']
        
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': stocks_config['api_key'],
            'outputsize': 'compact'
        }
        
        try:
            response = self._make_request(url, params=params)
            
            # Check for API errors
            if 'Error Message' in response:
                raise ValueError(f"Stock symbol '{symbol}' not found")
            
            if 'Note' in response:
                raise requests.exceptions.RequestException("API call frequency limit reached")
            
            # Extract time series data
            time_series_key = 'Time Series (Daily)'
            if time_series_key not in response:
                raise ValueError("Invalid response format from stock API")
            
            time_series = response[time_series_key]
            metadata = response.get('Meta Data', {})
            
            # Format the response
            formatted_response = {
                'symbol': symbol,
                'metadata': metadata,
                'data': time_series,
                'latest_date': max(time_series.keys()) if time_series else None,
                'latest_price': None
            }
            
            if formatted_response['latest_date']:
                latest_data = time_series[formatted_response['latest_date']]
                formatted_response['latest_price'] = float(latest_data['4. close'])
            
            # Cache the response for 5 minutes (stock data changes frequently during market hours)
            self._cache_response(cache_key, formatted_response, expire_seconds=300)
            
            logger.info(f"Retrieved stock data for {symbol}")
            return formatted_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get stock data for {symbol}: {e}")
            raise
    
    def combine_data(self, location, stock_symbols=None):
        """
        Combine data from weather, news, and optionally stock APIs.
        
        Args:
            location (str): Location for weather and news
            stock_symbols (list, optional): Stock symbols to include. Defaults to None.
            
        Returns:
            dict: Combined data from multiple APIs
            
        Raises:
            ValueError: If data cannot be retrieved
        """
        logger.info(f"Combining data for location: {location}")
        
        combined_data = {
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'weather': None,
            'news': [],
            'stocks': {}
        }
        
        try:
            # Get weather data
            combined_data['weather'] = self.get_weather_data(location)
            
            # Get news data for the location
            combined_data['news'] = self.get_news_data(query=location, max_results=5)
            
            # Get stock data if symbols provided
            if stock_symbols:
                for symbol in stock_symbols:
                    try:
                        combined_data['stocks'][symbol] = self.get_stock_data(symbol)
                    except Exception as e:
                        logger.warning(f"Failed to get stock data for {symbol}: {e}")
                        combined_data['stocks'][symbol] = {'error': str(e)}
            
            logger.info("Successfully combined data from multiple APIs")
            return combined_data
            
        except Exception as e:
            logger.error(f"Failed to combine data: {e}")
            raise ValueError(f"Cannot retrieve combined data: {e}")
    
    def _cache_response(self, cache_key, data, expire_seconds=3600):
        """
        Cache an API response.
        
        Args:
            cache_key (str): Key for the cached data
            data: Data to cache
            expire_seconds (int, optional): Cache expiry time in seconds. Defaults to 3600.
            
        Returns:
            None
        """
        expiry_time = datetime.now() + timedelta(seconds=expire_seconds)
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = expiry_time
        logger.debug(f"Cached response for key: {cache_key}")
    
    def _get_cached_response(self, cache_key):
        """
        Get a cached API response if available and not expired.
        
        Args:
            cache_key (str): Key for the cached data
            
        Returns:
            The cached data if available and not expired, None otherwise
        """
        if cache_key in self.cache:
            if datetime.now() < self.cache_expiry[cache_key]:
                logger.debug(f"Cache hit for key: {cache_key}")
                return self.cache[cache_key]
            else:
                # Cache expired, remove it
                del self.cache[cache_key]
                del self.cache_expiry[cache_key]
                logger.debug(f"Cache expired for key: {cache_key}")
        
        return None
    
    def _make_request(self, url, params=None, headers=None, method='GET'):
        """
        Make an API request with error handling.
        
        Args:
            url (str): The API endpoint URL
            params (dict, optional): Query parameters. Defaults to None.
            headers (dict, optional): HTTP headers. Defaults to None.
            method (str, optional): HTTP method. Defaults to 'GET'.
            
        Returns:
            dict or list: Parsed JSON response
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        logger.debug(f"Making {method} request to {url}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=request_headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            raise requests.exceptions.RequestException("Request timeout")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {response.status_code} for {url}")
            raise requests.exceptions.RequestException(f"HTTP {response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from {url}")
            raise requests.exceptions.RequestException("Invalid JSON response")
    
    async def fetch_parallel_data_async(self, requests_config):
        """
        Fetch data from multiple APIs in parallel using async/await.
        
        Args:
            requests_config (list): List of request configurations
                Format: [
                    {
                        'url': 'https://api.example.com/endpoint',
                        'params': {'param1': 'value1'},
                        'headers': {'header1': 'value1'},
                        'method': 'GET'
                    },
                    ...
                ]
            
        Returns:
            list: Responses from all requests
            
        Raises:
            Exception: If any request fails
        """
        async def make_single_async_request(session, config):
            try:
                method = config.get('method', 'GET').lower()
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with session.request(
                    method=method,
                    url=config['url'],
                    params=config.get('params'),
                    headers=config.get('headers'),
                    timeout=timeout
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    return {
                        'success': True,
                        'data': data,
                        'config': config,
                        'status_code': response.status
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'config': config
                }
        
        logger.info(f"Making {len(requests_config)} parallel async requests")
        
        # Create aiohttp session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=20,  # Connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            # Create tasks for all requests
            tasks = [
                make_single_async_request(session, config) 
                for config in requests_config
            ]
            
            # Execute all requests concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'config': None
                })
            else:
                processed_results.append(result)
        
        failed_requests = [r for r in processed_results if not r['success']]
        if failed_requests:
            logger.warning(f"{len(failed_requests)} out of {len(requests_config)} async requests failed")
        
        logger.info(f"Completed {len(processed_results)} parallel async requests")
        return processed_results
    
    async def combine_data_async(self, location, stock_symbols=None):
        """
        Combine data from multiple APIs using async requests.
        
        Args:
            location (str): Location for weather and news
            stock_symbols (list, optional): Stock symbols to include
            
        Returns:
            dict: Combined data from multiple APIs
        """
        logger.info(f"Combining data asynchronously for location: {location}")
        
        # Prepare all requests
        requests_config = []
        
        # Weather request
        if 'weather' in self.apis:
            weather_config = self.apis['weather']
            weather_url = urljoin(weather_config['base_url'], weather_config['endpoints']['current'])
            requests_config.append({
                'id': 'weather',
                'url': weather_url,
                'params': {
                    'q': location,
                    'appid': weather_config['api_key'],
                    'units': 'metric'
                }
            })
        
        # News request
        if 'news' in self.apis:
            news_config = self.apis['news']
            news_url = urljoin(news_config['base_url'], news_config['endpoints']['everything'])
            requests_config.append({
                'id': 'news',
                'url': news_url,
                'params': {
                    'q': location,
                    'apiKey': news_config['api_key'],
                    'pageSize': 5
                }
            })
        
        # Stock requests
        if stock_symbols and 'stocks' in self.apis:
            stocks_config = self.apis['stocks']
            for symbol in stock_symbols:
                requests_config.append({
                    'id': f'stock_{symbol}',
                    'url': stocks_config['base_url'],
                    'params': {
                        'function': 'TIME_SERIES_DAILY',
                        'symbol': symbol,
                        'apikey': stocks_config['api_key'],
                        'outputsize': 'compact'
                    }
                })
        
        # Execute all requests in parallel
        results = await self.fetch_parallel_data_async(requests_config)
        
        # Organize results
        combined_data = {
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'weather': None,
            'news': [],
            'stocks': {}
        }
        
        for result in results:
            if not result['success']:
                logger.warning(f"Request failed: {result.get('error')}")
                continue
                
            config = result['config']
            request_id = config.get('id', '')
            data = result['data']
            
            if request_id == 'weather':
                combined_data['weather'] = data
            elif request_id == 'news':
                combined_data['news'] = data.get('articles', [])
            elif request_id.startswith('stock_'):
                symbol = request_id.replace('stock_', '')
                # Process stock data
                time_series_key = 'Time Series (Daily)'
                if time_series_key in data:
                    time_series = data[time_series_key]
                    latest_date = max(time_series.keys()) if time_series else None
                    latest_price = None
                    if latest_date:
                        latest_data = time_series[latest_date]
                        latest_price = float(latest_data['4. close'])
                    
                    combined_data['stocks'][symbol] = {
                        'symbol': symbol,
                        'metadata': data.get('Meta Data', {}),
                        'data': time_series,
                        'latest_date': latest_date,
                        'latest_price': latest_price
                    }
        
        logger.info("Successfully combined data from multiple APIs asynchronously")
        return combined_data


class DataAnalyzer:
    """
    A class for analyzing and processing data from multiple APIs.
    
    Methods:
        find_weather_news_correlation: Find news articles related to weather conditions
        analyze_stock_vs_news: Analyze correlation between stock prices and news sentiment
        generate_summary_report: Generate a summary report of all data
    """
    
    def find_weather_news_correlation(self, weather_data, news_data):
        """
        Find news articles that might be related to current weather conditions.
        
        Args:
            weather_data (dict): Weather data
            news_data (list): News articles
            
        Returns:
            list: News articles related to weather
        """
        if not weather_data or not news_data:
            return []
        
        # Extract weather keywords
        weather_keywords = set()
        
        # Add weather condition keywords
        if 'weather' in weather_data:
            for condition in weather_data['weather']:
                weather_keywords.add(condition.get('main', '').lower())
                weather_keywords.add(condition.get('description', '').lower())
        
        # Add temperature-related keywords
        if 'main' in weather_data:
            temp = weather_data['main'].get('temp', 0)
            if temp > 30:  # Hot weather
                weather_keywords.update(['hot', 'heat', 'temperature', 'warm'])
            elif temp < 0:  # Cold weather
                weather_keywords.update(['cold', 'freeze', 'ice', 'snow'])
        
        # Add general weather keywords
        weather_keywords.update([
            'weather', 'storm', 'rain', 'snow', 'wind', 'flood', 'drought',
            'hurricane', 'tornado', 'blizzard', 'sunshine', 'cloud'
        ])
        
        # Find articles with weather-related content
        weather_related_articles = []
        
        for article in news_data:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = f"{title} {description}"
            
            # Check if any weather keywords appear in the article
            if any(keyword in content for keyword in weather_keywords):
                article_copy = article.copy()
                article_copy['weather_relevance_score'] = self._calculate_weather_relevance(
                    content, weather_keywords
                )
                weather_related_articles.append(article_copy)
        
        # Sort by relevance score
        weather_related_articles.sort(
            key=lambda x: x.get('weather_relevance_score', 0), 
            reverse=True
        )
        
        logger.info(f"Found {len(weather_related_articles)} weather-related articles")
        return weather_related_articles
    
    def analyze_stock_vs_news(self, stock_data, news_data):
        """
        Analyze correlation between stock prices and news sentiment.
        
        Args:
            stock_data (dict): Stock market data
            news_data (list): News articles
            
        Returns:
            dict: Analysis results
        """
        if not stock_data or not news_data:
            return {'error': 'Insufficient data for analysis'}
        
        # Calculate news sentiment
        news_sentiments = []
        stock_mentions = []
        
        symbol = stock_data.get('symbol', '').upper()
        company_keywords = [symbol.lower()]
        
        # Add common company name variations (simplified)
        company_map = {
            'AAPL': ['apple', 'iphone', 'ipad', 'mac'],
            'MSFT': ['microsoft', 'windows', 'azure', 'office'],
            'GOOGL': ['google', 'alphabet', 'android', 'youtube'],
            'AMZN': ['amazon', 'aws', 'prime'],
            'TSLA': ['tesla', 'musk', 'electric vehicle']
        }
        
        if symbol in company_map:
            company_keywords.extend(company_map[symbol])
        
        for article in news_data:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = f"{title} {description}"
            
            # Check if article mentions the company
            if any(keyword in content for keyword in company_keywords):
                sentiment = self._calculate_simple_sentiment(content)
                news_sentiments.append(sentiment)
                stock_mentions.append({
                    'title': article.get('title'),
                    'sentiment': sentiment,
                    'published_at': article.get('publishedAt')
                })
        
        # Calculate overall sentiment
        avg_sentiment = sum(news_sentiments) / len(news_sentiments) if news_sentiments else 0
        
        # Get current stock price
        current_price = stock_data.get('latest_price', 0)
        
        analysis_result = {
            'symbol': symbol,
            'current_price': current_price,
            'news_mentions': len(stock_mentions),
            'average_sentiment': round(avg_sentiment, 3),
            'sentiment_interpretation': self._interpret_sentiment(avg_sentiment),
            'mentions': stock_mentions[:5],  # Top 5 mentions
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Analyzed {len(stock_mentions)} news mentions for {symbol}")
        return analysis_result
    
    def generate_summary_report(self, combined_data):
        """
        Generate a summary report of all data.
        
        Args:
            combined_data (dict): Combined data from multiple APIs
            
        Returns:
            str: Summary report in a formatted string
        """
        if not combined_data:
            return "No data available for summary report."
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("MULTI-API DATA SUMMARY REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Location: {combined_data.get('location', 'Unknown')}")
        report_lines.append("")
        
        # Weather Summary
        weather_data = combined_data.get('weather')
        if weather_data:
            report_lines.append("WEATHER SUMMARY")
            report_lines.append("-" * 20)
            
            if 'main' in weather_data:
                temp = weather_data['main'].get('temp', 'N/A')
                humidity = weather_data['main'].get('humidity', 'N/A')
                report_lines.append(f"Temperature: {temp}°C")
                report_lines.append(f"Humidity: {humidity}%")
            
            if 'weather' in weather_data and weather_data['weather']:
                condition = weather_data['weather'][0]
                report_lines.append(f"Condition: {condition.get('main', 'N/A')}")
                report_lines.append(f"Description: {condition.get('description', 'N/A')}")
            
            report_lines.append("")
        
        # News Summary
        news_data = combined_data.get('news', [])
        if news_data:
            report_lines.append("NEWS SUMMARY")
            report_lines.append("-" * 15)
            report_lines.append(f"Total articles: {len(news_data)}")
            
            # Show top 3 headlines
            for i, article in enumerate(news_data[:3], 1):
                title = article.get('title', 'No title')
                report_lines.append(f"{i}. {title[:80]}{'...' if len(title) > 80 else ''}")
            
            report_lines.append("")
        
        # Stock Summary
        stocks_data = combined_data.get('stocks', {})
        if stocks_data:
            report_lines.append("STOCK SUMMARY")
            report_lines.append("-" * 15)
            
            for symbol, stock_info in stocks_data.items():
                if 'error' in stock_info:
                    report_lines.append(f"{symbol}: Error - {stock_info['error']}")
                else:
                    price = stock_info.get('latest_price', 'N/A')
                    date = stock_info.get('latest_date', 'N/A')
                    report_lines.append(f"{symbol}: ${price} (as of {date})")
            
            report_lines.append("")
        
        # Analysis Section
        if weather_data and news_data:
            analyzer = DataAnalyzer()
            weather_news = analyzer.find_weather_news_correlation(weather_data, news_data)
            
            if weather_news:
                report_lines.append("WEATHER-NEWS CORRELATION")
                report_lines.append("-" * 25)
                report_lines.append(f"Found {len(weather_news)} weather-related articles")
                
                for article in weather_news[:2]:  # Top 2
                    title = article.get('title', 'No title')
                    score = article.get('weather_relevance_score', 0)
                    report_lines.append(f"• {title[:60]}... (Score: {score:.2f})")
                
                report_lines.append("")
        
        report_lines.append("=" * 60)
        report_lines.append("End of Report")
        
        return "\n".join(report_lines)
    
    def _extract_keywords(self, text):
        """
        Extract important keywords from text.
        
        Args:
            text (str): Input text
            
        Returns:
            list: Extracted keywords
        """
        if not text:
            return []
        
        # Simple keyword extraction
        # Remove punctuation and convert to lowercase
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Return unique keywords
        return list(set(keywords))
    
    def _calculate_simple_sentiment(self, text):
        """
        Calculate a simple sentiment score for text.
        
        Args:
            text (str): Input text
            
        Returns:
            float: Sentiment score (-1.0 to 1.0)
        """
        if not text:
            return 0.0
        
        # Simple word-based sentiment analysis
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'positive', 'success', 'win', 'profit', 'gain', 'up', 'rise', 'growth',
            'improve', 'better', 'best', 'strong', 'bullish', 'optimistic'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'negative', 'loss', 'lose',
            'down', 'fall', 'decline', 'drop', 'weak', 'bearish', 'pessimistic',
            'crash', 'crisis', 'problem', 'issue', 'concern', 'worry', 'risk'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            return 0.0
        
        # Calculate sentiment score
        sentiment = (positive_count - negative_count) / total_sentiment_words
        
        # Normalize to -1.0 to 1.0 range
        return max(-1.0, min(1.0, sentiment))
    
    def _calculate_weather_relevance(self, content, weather_keywords):
        """Calculate how relevant content is to weather."""
        matches = sum(1 for keyword in weather_keywords if keyword in content)
        return matches / len(weather_keywords) if weather_keywords else 0
    
    def _interpret_sentiment(self, sentiment_score):
        """Interpret numerical sentiment score."""
        if sentiment_score > 0.2:
            return "Positive"
        elif sentiment_score < -0.2:
            return "Negative"
        else:
            return "Neutral"


def main():
    """Run examples demonstrating the MultiAPIClient and DataAnalyzer."""
    print("API Integration Advanced Example")
    
    # Note: In a real assignment, students would use their own API keys
    # For this template, we'll use placeholders
    
    # Sample configuration (in a real scenario, keys would come from environment variables)
    config = {
        'weather': {
            'base_url': 'https://api.openweathermap.org/data/2.5',
            'api_key': os.environ.get('OPENWEATHER_API_KEY', 'your-api-key-here'),
            'endpoints': {
                'current': '/weather'
            }
        },
        'news': {
            'base_url': 'https://newsapi.org/v2',
            'api_key': os.environ.get('NEWS_API_KEY', 'your-api-key-here'),
            'endpoints': {
                'top_headlines': '/top-headlines',
                'everything': '/everything'
            }
        },
        'stocks': {
            'base_url': 'https://www.alphavantage.co/query',
            'api_key': os.environ.get('ALPHAVANTAGE_API_KEY', 'your-api-key-here'),
            'endpoints': {
                'time_series_daily': ''
            }
        }
    }
    
    # Normally we would use real API keys, but for the assignment template we'll just show the structure
    print("Note: This example requires real API keys to work correctly.")
    print("In a real assignment, students would use their own API keys.")
    
    try:
        # Initialize the client
        client = MultiAPIClient(config)
        
        # Demonstrate combining data (this would call the APIs with real keys)
        # combined_data = client.combine_data('New York', stock_symbols=['AAPL', 'MSFT'])
        
        # Initialize the analyzer
        analyzer = DataAnalyzer()
        
        # Demonstrate analysis (using fake data for this example)
        print("\nExample weather-news correlation analysis:")
        weather_data = {
            'main': {'temp': 25, 'humidity': 80},
            'weather': [{'main': 'Rain', 'description': 'heavy rain'}],
            'name': 'New York'
        }
        
        news_data = [
            {'title': 'Flooding in New York after heavy rain', 'description': 'Roads closed due to flooding'},
            {'title': 'Tech stocks rally continues', 'description': 'Apple and Microsoft lead gains'},
            {'title': 'Summer tourism booming', 'description': 'Despite weather challenges, tourism numbers up'}
        ]
        
        weather_related_news = analyzer.find_weather_news_correlation(weather_data, news_data)
        print("Weather-related news articles:")
        for article in weather_related_news:
            title = article['title']
            score = article.get('weather_relevance_score', 0)
            print(f"- {title} (Relevance: {score:.2f})")
        
        # Demonstrate stock analysis
        print("\nExample stock-news analysis:")
        stock_data = {
            'symbol': 'AAPL',
            'latest_price': 150.25
        }
        
        stock_analysis = analyzer.analyze_stock_vs_news(stock_data, news_data)
        print(f"Stock: {stock_analysis.get('symbol')}")
        print(f"Price: ${stock_analysis.get('current_price')}")
        print(f"News mentions: {stock_analysis.get('news_mentions')}")
        print(f"Sentiment: {stock_analysis.get('sentiment_interpretation')} ({stock_analysis.get('average_sentiment')})")
        
        # Demonstrate summary report
        print("\nExample summary report:")
        combined_data = {
            'location': 'New York',
            'weather': weather_data,
            'news': news_data,
            'stocks': {'AAPL': stock_data}
        }
        
        summary = analyzer.generate_summary_report(combined_data)
        print(summary)
        
        # Demonstrate parallel requests
        print("\nExample parallel requests:")
        requests_config = [
            {
                'url': 'https://httpbin.org/delay/1',
                'method': 'GET'
            },
            {
                'url': 'https://httpbin.org/delay/1', 
                'method': 'GET'
            }
        ]
        
        start_time = time.time()
        results = client.fetch_parallel_data(requests_config)
        end_time = time.time()
        
        successful_requests = sum(1 for r in results if r['success'])
        print(f"Completed {successful_requests}/{len(results)} requests in {end_time - start_time:.2f} seconds")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nIn a real assignment, you would implement all methods and use actual API calls.")

if __name__ == "__main__":
    main()