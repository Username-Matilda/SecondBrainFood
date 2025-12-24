"""
LessWrong/Alignment Forum GraphQL fetcher
Bypasses bot detection by using their intended API
"""

import requests
import re
from urllib.parse import urlparse
from typing import Optional, Tuple
import html2text

# Both sites use same API structure
GRAPHQL_ENDPOINTS = {
    'lesswrong.com': 'https://www.lesswrong.com/graphql',
    'www.lesswrong.com': 'https://www.lesswrong.com/graphql',
    'alignmentforum.org': 'https://www.alignmentforum.org/graphql',
    'www.alignmentforum.org': 'https://www.alignmentforum.org/graphql',
}

POST_QUERY = """
query getPost($slug: String) {
  post(input: {selector: {slug: $slug}}) {
    result {
      _id
      title
      slug
      htmlBody
      contents {
        html
      }
      user {
        displayName
      }
      postedAt
      baseScore
      commentCount
    }
  }
}
"""

POST_BY_ID_QUERY = """
query getPostById($id: String) {
  post(input: {selector: {_id: $id}}) {
    result {
      _id
      title
      slug
      htmlBody
      contents {
        html
      }
      user {
        displayName
      }
      postedAt
      baseScore
      commentCount
    }
  }
}
"""


def is_lw_url(url: str) -> bool:
    """Check if URL is LessWrong or Alignment Forum"""
    try:
        domain = urlparse(url).netloc.lower()
        return domain in GRAPHQL_ENDPOINTS
    except:
        return False


def extract_slug_or_id(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract post slug or ID from LW/AF URL
    
    URL patterns:
    - /posts/{id}/{slug}
    - /posts/{id}
    - /s/{sequence_id}/p/{slug}  (sequence posts)
    - /lw/{shortcode}/{slug}     (old format)
    
    Returns: (slug, post_id) - one will be None
    """
    path = urlparse(url).path
    
    # Standard format: /posts/{id}/{slug}
    match = re.search(r'/posts/([A-Za-z0-9]+)/([A-Za-z0-9_-]+)', path)
    if match:
        return (match.group(2), match.group(1))  # (slug, id)
    
    # ID only: /posts/{id}
    match = re.search(r'/posts/([A-Za-z0-9]+)/?$', path)
    if match:
        return (None, match.group(1))
    
    # Sequence post: /s/{seq}/p/{slug}
    match = re.search(r'/s/[A-Za-z0-9]+/p/([A-Za-z0-9_-]+)', path)
    if match:
        return (match.group(1), None)
    
    # Old format: /lw/{code}/{slug}
    match = re.search(r'/lw/[A-Za-z0-9]+/([A-Za-z0-9_-]+)', path)
    if match:
        return (match.group(1), None)
    
    return (None, None)


def fetch_lw_post(url: str) -> Optional[dict]:
    """
    Fetch post content via GraphQL API
    
    Returns dict with: title, author, date, html_content, text_content, score, comments
    Or None if fetch failed
    """
    if not is_lw_url(url):
        return None
    
    domain = urlparse(url).netloc.lower()
    endpoint = GRAPHQL_ENDPOINTS.get(domain)
    if not endpoint:
        return None
    
    slug, post_id = extract_slug_or_id(url)
    
    if not slug and not post_id:
        print(f"  Could not extract slug/id from: {url}")
        return None
    
    # Try slug first, fall back to ID
    if slug:
        query = POST_QUERY
        variables = {"slug": slug}
    else:
        query = POST_BY_ID_QUERY
        variables = {"id": post_id}
    
    try:
        response = requests.post(
            endpoint,
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                # GraphQL API doesn't need browser UA, but doesn't hurt
                "User-Agent": "SecondBrainFood/1.0 (personal knowledge management)"
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        post = data.get("data", {}).get("post", {}).get("result")
        if not post:
            # If slug failed, try ID extraction from URL and retry
            if slug and not post_id:
                _, post_id = extract_slug_or_id(url)
                if post_id:
                    return fetch_lw_post_by_id(endpoint, post_id)
            print(f"  No post data returned for: {url}")
            return None
        
        # Extract HTML content (try both fields)
        html_content = post.get("htmlBody") or ""
        if not html_content:
            contents = post.get("contents", {})
            html_content = contents.get("html", "") if contents else ""
        
        # Convert to plain text
        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.ignore_images = True
        h2t.body_width = 0  # No wrapping
        text_content = h2t.handle(html_content) if html_content else ""
        
        return {
            "title": post.get("title", "Untitled"),
            "author": post.get("user", {}).get("displayName", "Unknown"),
            "date": post.get("postedAt", ""),
            "html_content": html_content,
            "text_content": text_content,
            "score": post.get("baseScore", 0),
            "comments": post.get("commentCount", 0),
            "url": url,
            "source": "lesswrong" if "lesswrong" in domain else "alignmentforum"
        }
        
    except requests.RequestException as e:
        print(f"  GraphQL request failed: {e}")
        return None
    except Exception as e:
        print(f"  Error processing LW post: {e}")
        return None


def fetch_lw_post_by_id(endpoint: str, post_id: str) -> Optional[dict]:
    """Fallback fetch by ID"""
    try:
        response = requests.post(
            endpoint,
            json={"query": POST_BY_ID_QUERY, "variables": {"id": post_id}},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        # ... same processing as above
        # (You'd factor this out in production)
    except:
        return None


# Integration point for your existing scraper:
def get_content(url: str) -> Optional[str]:
    """
    Drop-in replacement for your existing scraper's get_content()
    Returns markdown text or None
    """
    result = fetch_lw_post(url)
    if result:
        # Format as markdown with metadata
        header = f"# {result['title']}\n\n"
        header += f"**Author:** {result['author']}\n"
        header += f"**Date:** {result['date'][:10] if result['date'] else 'Unknown'}\n"
        header += f"**Score:** {result['score']} | **Comments:** {result['comments']}\n"
        header += f"**Source:** {url}\n\n---\n\n"
        return header + result['text_content']
    return None


# Test
if __name__ == "__main__":
    test_urls = [
        "https://www.lesswrong.com/posts/rQKstXH8ZMAdN5iqD/concentration-of-force",
        "https://www.lesswrong.com/posts/qNZM3EGoE5ZeMdCRt/reversed-stupidity-is-not-intelligence",
        "https://www.alignmentforum.org/posts/ho63vCb2MNFijinzY/agi-safety-career-advice",
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        result = fetch_lw_post(url)
        if result:
            print(f"  ✓ {result['title']} by {result['author']}")
            print(f"    {len(result['text_content'])} chars")
        else:
            print(f"  ✗ Failed")