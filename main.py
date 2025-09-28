"""HTML Content Fetcher Actor

This Apify Actor functions as an API endpoint that fetches and returns the HTML content
of any given URL. It can also extract specific price information from eBay-style pages.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, Optional

# Beautiful Soup - A library for pulling data out of HTML and XML files
from bs4 import BeautifulSoup

# Apify SDK - A toolkit for building Apify Actors. Read more at:
# https://docs.apify.com/sdk/python
from apify import Actor

# HTTPX - A library for making asynchronous HTTP requests in Python. Read more at:
# https://www.python-httpx.org/
from httpx import AsyncClient, HTTPError, TimeoutException


def extract_price_from_html(html_content: str) -> Optional[str]:
    """Extract price from HTML content using Beautiful Soup.
    
    Specifically looks for div elements with class 'x-price-primary' and 
    data-testid 'x-price-primary' to extract price information.
    
    Args:
        html_content: The raw HTML content to parse
        
    Returns:
        The extracted price as a string, or None if not found
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Look for price element with specific class and data-testid
        price_element = soup.find('div', {
            'class': 'x-price-primary',
            'data-testid': 'x-price-primary'
        })
        
        if price_element:
            # Look for span with class ux-textspans inside the price element
            price_span = price_element.find('span', class_='ux-textspans')
            if price_span:
                price_text = price_span.get_text(strip=True)
                return price_text
            
            # Fallback: get any text from the price element
            price_text = price_element.get_text(strip=True)
            if price_text:
                return price_text
        
        # Alternative: look for any element with x-price-primary class
        price_element_alt = soup.find(class_='x-price-primary')
        if price_element_alt:
            price_span = price_element_alt.find('span', class_='ux-textspans')
            if price_span:
                return price_span.get_text(strip=True)
            
            # Get text from the element
            price_text = price_element_alt.get_text(strip=True)
            if price_text:
                return price_text
                
        return None
        
    except Exception as e:
        # Log the error but don't fail the entire request
        print(f"Error extracting price: {e}")
        return None


def _is_not_found_page(html_content: str, status_code: int) -> bool:
    """Check if the page appears to be a 'not found' or error page based on content.
    
    Args:
        html_content: The HTML content to analyze
        status_code: The HTTP status code
        
    Returns:
        True if the page appears to be a "not found" page, False otherwise
    """
    try:
        # Convert to lowercase for case-insensitive matching
        content_lower = html_content.lower()
        
        # Common indicators of "not found" pages
        not_found_indicators = [
            'page not found',
            'item not found',
            'product not found',
            'listing not found',
            '404 error',
            'page does not exist',
            'item no longer available',
            'this listing has ended',
            'listing has been removed',
            'item has been removed',
            'no longer available',
            'page unavailable',
            'item unavailable',
            'access denied',
            'forbidden',
            'page not available'
        ]
        
        # eBay specific indicators
        ebay_not_found_indicators = [
            'we looked everywhere',
            "couldn't find that page",
            'listing was ended',
            'item you requested could not be found',
            'this listing is no longer available',
            'item has ended',
            'page cannot be found'
        ]
        
        # Check for indicators in the content
        all_indicators = not_found_indicators + ebay_not_found_indicators
        
        for indicator in all_indicators:
            if indicator in content_lower:
                return True
        
        # Check if the page is unusually short (likely an error page)
        if len(html_content.strip()) < 500 and status_code == 200:
            return True
            
        # Check for common error page titles
        soup = BeautifulSoup(html_content, 'lxml')
        title = soup.find('title')
        if title:
            title_text = title.get_text().lower()
            title_indicators = ['404', 'not found', 'error', 'unavailable', 'forbidden']
            for indicator in title_indicators:
                if indicator in title_text:
                    return True
                    
        return False
        
    except Exception:
        # If we can't parse the content, assume it's valid
        return False


async def main() -> None:
    """Define the main entry point for the Apify Actor.

    This coroutine fetches HTML content from the provided URL and returns it
    in a structured format that can be easily consumed by other applications.
    """
    async with Actor:
        # Retrieve the input object for the Actor
        actor_input = await Actor.get_input() or {}
        
        # Extract URL from input
        url = actor_input.get('url')
        if not url:
            error_msg = 'Missing "url" attribute in input!'
            Actor.log.error(error_msg)
            await Actor.push_data({
                'success': False,
                'error': error_msg,
                'url': None,
                'html_content': None,
                'price': None,
                'price_found': False,
                'status_code': None,
                'headers': None,
                'page_exists': False
            })
            return

        # Extract optional parameters
        timeout = actor_input.get('timeout', 30)  # Default 30 seconds timeout
        follow_redirects = actor_input.get('follow_redirects', True)
        user_agent = actor_input.get('user_agent', 'Mozilla/5.0 (compatible; ApifyBot/1.0)')
        
        Actor.log.info(f'Fetching HTML content from: {url}')
        Actor.log.info(f'Timeout: {timeout}s, Follow redirects: {follow_redirects}')

        try:
            # Create an asynchronous HTTPX client with custom configuration
            async with AsyncClient(
                timeout=timeout,
                follow_redirects=follow_redirects,
                headers={'User-Agent': user_agent}
            ) as client:
                
                # Fetch the HTML content of the page
                response = await client.get(url)
                
                # Extract response data first (before raising for status)
                html_content = response.text
                status_code = response.status_code
                headers = dict(response.headers)
                final_url = str(response.url)
                
                Actor.log.info(f'Response received from {final_url}')
                Actor.log.info(f'Status code: {status_code}')
                Actor.log.info(f'Content length: {len(html_content)} characters')
                
                # Handle specific status codes
                if status_code == 404:
                    Actor.log.warning('Page not found (404)')
                    await Actor.push_data({
                        'success': False,
                        'error': 'Page not found (404)',
                        'url': url,
                        'final_url': final_url,
                        'html_content': None,
                        'price': None,
                        'price_found': False,
                        'status_code': status_code,
                        'content_type': headers.get('content-type', 'unknown'),
                        'page_exists': False
                    })
                    return
                
                elif status_code in [403, 410, 451]:  # Forbidden, Gone, Unavailable for Legal Reasons
                    error_msg = f'Page unavailable (HTTP {status_code})'
                    Actor.log.warning(error_msg)
                    await Actor.push_data({
                        'success': False,
                        'error': error_msg,
                        'url': url,
                        'final_url': final_url,
                        'html_content': None,
                        'price': None,
                        'price_found': False,
                        'status_code': status_code,
                        'content_type': headers.get('content-type', 'unknown'),
                        'page_exists': False
                    })
                    return
                
                elif status_code >= 400:
                    error_msg = f'Client/Server error (HTTP {status_code})'
                    Actor.log.error(error_msg)
                    await Actor.push_data({
                        'success': False,
                        'error': error_msg,
                        'url': url,
                        'final_url': final_url,
                        'html_content': html_content if len(html_content) < 10000 else None,  # Include short error pages
                        'price': None,
                        'price_found': False,
                        'status_code': status_code,
                        'content_type': headers.get('content-type', 'unknown'),
                        'page_exists': False
                    })
                    return
                
                # Check for common "not found" indicators in the content
                if _is_not_found_page(html_content, status_code):
                    Actor.log.warning('Page appears to be a "not found" or error page based on content')
                    await Actor.push_data({
                        'success': False,
                        'error': 'Page not found or unavailable (detected from content)',
                        'url': url,
                        'final_url': final_url,
                        'html_content': None,
                        'price': None,
                        'price_found': False,
                        'status_code': status_code,
                        'content_type': headers.get('content-type', 'unknown'),
                        'page_exists': False
                    })
                    return
                
                Actor.log.info('Page successfully loaded and appears to be valid')
                
                # Try to extract price from the HTML content
                extracted_price = extract_price_from_html(html_content)
                
                if extracted_price:
                    Actor.log.info(f'Price found: {extracted_price}')
                    # Price found - return structured data without HTML content
                    result = {
                        'success': True,
                        'error': None,
                        'url': url,
                        'final_url': final_url,
                        'price': extracted_price,
                        'price_found': True,
                        'status_code': status_code,
                        'content_type': headers.get('content-type', 'unknown'),
                        'page_exists': True
                    }
                else:
                    Actor.log.info('No price found in the expected format')
                    # No price found - return full HTML content
                    result = {
                        'success': True,
                        'error': None,
                        'url': url,
                        'final_url': final_url,
                        'html_content': html_content,
                        'price': None,
                        'price_found': False,
                        'status_code': status_code,
                        'headers': headers,
                        'content_length': len(html_content),
                        'content_type': headers.get('content-type', 'unknown'),
                        'page_exists': True
                    }
                
                # Save the result to the dataset
                await Actor.push_data(result)
                
                Actor.log.info('HTML content successfully extracted and saved')

        except TimeoutException:
            error_msg = f'Request timeout after {timeout} seconds'
            Actor.log.error(error_msg)
            await Actor.push_data({
                'success': False,
                'error': error_msg,
                'url': url,
                'final_url': None,
                'html_content': None,
                'price': None,
                'price_found': False,
                'status_code': None,
                'headers': None,
                'content_length': 0,
                'content_type': None,
                'page_exists': False
            })

        except HTTPError as e:
            error_msg = f'HTTP error occurred: {str(e)}'
            Actor.log.error(error_msg)
            await Actor.push_data({
                'success': False,
                'error': error_msg,
                'url': url,
                'final_url': None,
                'html_content': None,
                'price': None,
                'price_found': False,
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                'headers': None,
                'content_length': 0,
                'content_type': None,
                'page_exists': False
            })

        except Exception as e:
            error_msg = f'Unexpected error occurred: {str(e)}'
            Actor.log.error(error_msg)
            await Actor.push_data({
                'success': False,
                'error': error_msg,
                'url': url,
                'final_url': None,
                'html_content': None,
                'price': None,
                'price_found': False,
                'status_code': None,
                'headers': None,
                'content_length': 0,
                'content_type': None,
                'page_exists': False
            })


if __name__ == '__main__':
    asyncio.run(main())
