from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
from urllib import request as url_request

# Get API key from environment
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

def derive_name(url):
    """Derive Name from domain (example.com -> Example)"""
    domain = urlparse(url).netloc.replace("www.", "")
    name = domain.split(".")[0].replace("-", " ").title()
    return name

def detect_topic(query):
    """Detect if query is news/finance or general - combine finance and news for better results"""
    query_lower = query.lower()
    
    # News + Finance keywords (combined for better diversity)
    news_finance_keywords = ['news', 'latest', 'today', 'yesterday', 'breaking', 'current', 
                             'recent', 'update', 'happened', 'president', 'election', 
                             'government', 'politics', 'war', 'crisis', 'attack',
                             'stock', 'price', 'market', 'trading', 'investment',
                             'crypto', 'bitcoin', 'nasdaq', 'dow jones', 'earnings',
                             'revenue', 'profit', 'ipo', 'dividend', 'forex']
    
    # Check if news or finance related
    if any(keyword in query_lower for keyword in news_finance_keywords):
        return 'news'
    
    return 'general'

def tavily_search(query):
    """Call Tavily API directly using HTTP requests"""
    url = "https://api.tavily.com/search"
    
    topic = detect_topic(query)
    
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": 20,
        "include_favicon": True,
        "include_answer": "advanced",
        "include_images": True,
        
        "topic": topic,
        "exclude_domains": [
            "tiktok.com",
            "snapchat.com", 
            "facebook.com",
            "instagram.com"
        ]
    }
    
    # Make HTTP POST request
    req = url_request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with url_request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        print(f"Tavily API error: {e}")
        return {"results": []}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)
        query = params.get("q", [""])[0].strip()
        
        if not query:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps([]).encode())
            return
        
        try:
            # Search with Tavily using REST API
            response = tavily_search(query)
            
            # Format results
            results = []
            for r in response.get("results", []):
                url = r.get("url", "")
                results.append({
                    "favicon": r.get("favicon"),
                    "name": derive_name(url),
                    "source": urlparse(url).netloc,
                    "title": r.get("title"),
                    "url": url,
                    "summary": r.get("content")
                })
            
            # Include Tavily's AI answer if available
            output = {
                "answer": response.get("answer", ""),
                "images": response.get("images", []),
                "results": results
            }
            
            # Send response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(output).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())