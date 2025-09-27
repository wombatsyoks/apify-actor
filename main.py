"""HTML Content Fetcher Actor

This Apify Actor functions as an API endpoint that fetches and returns the HTML content
of any given URL. It can be used for web scraping, content analysis, or as a proxy
for accessing web pages.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

# Apify SDK - A toolkit for building Apify Actors. Read more at:
# https://docs.apify.com/sdk/python
from apify import Actor

# HTTPX - A library for making asynchronous HTTP requests in Python. Read more at:
# https://www.python-httpx.org/
from httpx import AsyncClient, HTTPError, TimeoutException


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
                'status_code': None,
                'headers': None
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
                
                # Check if the request was successful
                response.raise_for_status()
                
                # Extract response data
                html_content = response.text
                status_code = response.status_code
                headers = dict(response.headers)
                final_url = str(response.url)
                
                Actor.log.info(f'Successfully fetched content from {final_url}')
                Actor.log.info(f'Status code: {status_code}')
                Actor.log.info(f'Content length: {len(html_content)} characters')
                
                # Prepare the result data
                result = {
                    'success': True,
                    'error': None,
                    'url': url,
                    'final_url': final_url,
                    'html_content': html_content,
                    'status_code': status_code,
                    'headers': headers,
                    'content_length': len(html_content),
                    'content_type': headers.get('content-type', 'unknown')
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
                'status_code': None,
                'headers': None,
                'content_length': 0,
                'content_type': None
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
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                'headers': None,
                'content_length': 0,
                'content_type': None
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
                'status_code': None,
                'headers': None,
                'content_length': 0,
                'content_type': None
            })


if __name__ == '__main__':
    asyncio.run(main())
