from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from tavily import TavilyClient
import json
import os

# Initialize Tavily client
tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

def derive_name(url):
    """Derive Name from domain (example.com -> Example)"""
    domain = urlparse(url).netloc.replace("www.", "")
    name = domain.split(".")[0].replace("-", " ").title()
    return name

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
            # Search with Tavily
            response = tavily.search(
                query=query,
                max_results=20,
                include_favicon=True
            )
            
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
            
            # Send response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())