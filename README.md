# HTML Content Fetcher Actor

A simple yet powerful Apify Actor that functions as an API endpoint for fetching raw HTML content from any given URL. This actor is perfect for web scraping projects, content analysis, or as a proxy service for accessing web pages programmatically.

## Features

- **Simple API Interface**: Just provide a URL and get back the complete HTML content
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Customizable Requests**: Configure timeout, user-agent, and redirect behavior
- **Detailed Response**: Returns not just HTML content but also status codes, headers, and metadata
- **Async Performance**: Built with async/await for optimal performance

## Input Parameters

### Required Parameters

- **`url`** (string, required): The URL of the webpage to fetch HTML content from
  - Example: `"https://example.com"`

### Optional Parameters

- **`timeout`** (integer, optional): Request timeout in seconds (default: 30, range: 1-300)
- **`follow_redirects`** (boolean, optional): Whether to automatically follow HTTP redirects (default: true)
- **`user_agent`** (string, optional): Custom User-Agent string for the request (default: "Mozilla/5.0 (compatible; ApifyBot/1.0)")

## Output Format

The actor returns a JSON object with the following structure:

```json
{
    "success": true,
    "error": null,
    "url": "https://example.com",
    "final_url": "https://example.com",
    "html_content": "<!DOCTYPE html><html>...</html>",
    "status_code": 200,
    "headers": {
        "content-type": "text/html; charset=utf-8",
        "content-length": "1256",
        ...
    },
    "content_length": 1256,
    "content_type": "text/html; charset=utf-8"
}
```

### Output Fields

- **`success`**: Boolean indicating if the request was successful
- **`error`**: Error message if the request failed, null otherwise
- **`url`**: Original URL provided in the input
- **`final_url`**: Final URL after following redirects (if any)
- **`html_content`**: Raw HTML content of the webpage
- **`status_code`**: HTTP status code of the response
- **`headers`**: HTTP response headers as a key-value object
- **`content_length`**: Length of the HTML content in characters
- **`content_type`**: Content-Type header value

## Usage Examples

### Basic Usage

```json
{
    "url": "https://example.com"
}
```

### Advanced Usage with Custom Settings

```json
{
    "url": "https://example.com",
    "timeout": 60,
    "follow_redirects": false,
    "user_agent": "MyCustomBot/1.0"
}
```

## Error Handling

The actor handles various types of errors gracefully:

- **Missing URL**: When no URL is provided in the input
- **Timeout Errors**: When the request takes longer than the specified timeout
- **HTTP Errors**: When the server returns an error status code (4xx, 5xx)
- **Network Errors**: When there are connectivity issues
- **Unexpected Errors**: Any other unforeseen errors

In case of an error, the output will have `success: false` and the `error` field will contain a descriptive error message.

## Use Cases

1. **Web Scraping**: Fetch HTML content to parse and extract specific data
2. **Content Monitoring**: Monitor websites for changes
3. **SEO Analysis**: Analyze webpage structure and content
4. **Proxy Service**: Access websites through Apify's infrastructure
5. **Content Backup**: Create backups of web pages
6. **Testing**: Test how your applications handle different HTML structures

## Integration

### Using Apify API

You can call this actor through the Apify API:

```bash
curl -X POST https://api.apify.com/v2/acts/YOUR_ACTOR_ID/runs \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'
```

### Using Apify SDK

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_API_TOKEN")

# Run the actor
run = client.actor("YOUR_ACTOR_ID").call(run_input={
    "url": "https://example.com"
})

# Fetch the results
dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
html_content = dataset_items[0]["html_content"]
```

## Development

To run this actor locally:

1. Install dependencies: `pip install -r requirements.txt`
2. Set your Apify token: `export APIFY_TOKEN=your_token_here`
3. Run the actor: `python main.py`

## Requirements

- Python 3.8+
- Apify SDK
- HTTPX
- Internet connection

## License

This actor is available under the MIT License.

## Support

For issues, questions, or feature requests, please contact the actor developer or create an issue in the actor's repository.
# apify-actor
