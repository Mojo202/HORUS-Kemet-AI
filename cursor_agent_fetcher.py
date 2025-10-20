#!/usr/bin/env python3
"""
Cursor Agent Data Fetcher and Processor

This script fetches and processes data from Cursor agents URLs.
It handles various response types and provides structured output.
"""

import requests
import json
import sys
import argparse
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional
import time
from dataclasses import dataclass, asdict
import gzip
import base64
from bs4 import BeautifulSoup
import re


@dataclass
class AgentData:
    """Data structure for agent information"""
    agent_id: Optional[str] = None
    url: Optional[str] = None
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    response_size: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class CursorAgentFetcher:
    """Fetches and processes Cursor agent data"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_agent_id(self, url: str) -> Optional[str]:
        """Extract agent ID from URL parameters"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return params.get('selectedBcId', [None])[0]
        except Exception as e:
            print(f"Error extracting agent ID: {e}")
            return None
    
    def decode_content(self, response) -> str:
        """Decode response content handling various encodings"""
        content = response.content
        
        # Check if content is gzipped
        if content.startswith(b'\x1f\x8b'):
            try:
                content = gzip.decompress(content)
                print("✓ Decompressed gzipped content")
            except Exception as e:
                print(f"⚠ Failed to decompress gzip: {e}")
        
        # Try to decode as text
        try:
            # Try UTF-8 first
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Try latin-1 as fallback
                return content.decode('latin-1')
            except UnicodeDecodeError:
                # If all else fails, return as base64
                print("⚠ Content appears to be binary, encoding as base64")
                return base64.b64encode(content).decode('ascii')
    
    def extract_agent_info(self, html_content: str) -> Dict[str, Any]:
        """Extract agent information from HTML content"""
        extracted_data = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            if title:
                extracted_data['title'] = title.get_text().strip()
            
            # Extract meta tags
            meta_tags = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    meta_tags[name] = content
            if meta_tags:
                extracted_data['meta_tags'] = meta_tags
            
            # Look for JSON-LD structured data
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            if json_ld_scripts:
                json_ld_data = []
                for script in json_ld_scripts:
                    try:
                        data = json.loads(script.string)
                        json_ld_data.append(data)
                    except json.JSONDecodeError:
                        pass
                if json_ld_data:
                    extracted_data['structured_data'] = json_ld_data
            
            # Look for agent-specific data in scripts
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for window.__INITIAL_STATE__ or similar patterns
                    if 'window.__' in script.string or 'window.INITIAL' in script.string:
                        # Extract JavaScript object
                        js_content = script.string
                        # Simple regex to find JSON-like objects
                        json_matches = re.findall(r'({.*?});?$', js_content, re.MULTILINE | re.DOTALL)
                        for match in json_matches:
                            try:
                                data = json.loads(match)
                                if 'initial_state' not in extracted_data:
                                    extracted_data['initial_state'] = []
                                extracted_data['initial_state'].append(data)
                            except json.JSONDecodeError:
                                pass
            
            # Extract any data attributes
            elements_with_data = soup.find_all(attrs=lambda x: x and any(key.startswith('data-') for key in x.keys()))
            if elements_with_data:
                data_attributes = {}
                for elem in elements_with_data[:10]:  # Limit to first 10 to avoid too much data
                    for attr, value in elem.attrs.items():
                        if attr.startswith('data-'):
                            data_attributes[attr] = value
                if data_attributes:
                    extracted_data['data_attributes'] = data_attributes
                    
        except Exception as e:
            print(f"⚠ Error extracting agent info: {e}")
            extracted_data['extraction_error'] = str(e)
        
        return extracted_data

    def fetch_agent_data(self, url: str) -> AgentData:
        """Fetch data from the given URL"""
        agent_data = AgentData(
            url=url,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        )
        
        # Extract agent ID if available
        agent_data.agent_id = self.extract_agent_id(url)
        
        try:
            print(f"Fetching data from: {url}")
            response = self.session.get(url, timeout=self.timeout)
            
            agent_data.status_code = response.status_code
            agent_data.content_type = response.headers.get('content-type', 'unknown')
            agent_data.response_size = len(response.content)
            
            if response.status_code == 200:
                # Try to parse as JSON first
                try:
                    json_data = response.json()
                    agent_data.data = json_data
                    print("✓ Successfully fetched JSON data")
                except json.JSONDecodeError:
                    # Decode content properly
                    decoded_content = self.decode_content(response)
                    
                    # Check if it looks like HTML
                    if '<html' in decoded_content.lower() or '<!doctype' in decoded_content.lower():
                        print("✓ Successfully fetched HTML data")
                        extracted_info = self.extract_agent_info(decoded_content)
                        agent_data.data = {
                            'content_type': 'html',
                            'raw_html': decoded_content[:5000] + '...' if len(decoded_content) > 5000 else decoded_content,  # Truncate for storage
                            'extracted_info': extracted_info
                        }
                    else:
                        print("✓ Successfully fetched text data")
                        agent_data.data = {
                            'content_type': 'text',
                            'content': decoded_content
                        }
            
            elif response.status_code == 404:
                agent_data.error_message = "Agent not found (404). The URL may be invalid or the agent may not be publicly accessible."
                print("✗ Agent not found (404)")
            
            elif response.status_code == 403:
                agent_data.error_message = "Access forbidden (403). Authentication may be required."
                print("✗ Access forbidden (403)")
            
            else:
                agent_data.error_message = f"HTTP {response.status_code}: {response.reason}"
                print(f"✗ HTTP {response.status_code}: {response.reason}")
        
        except requests.exceptions.Timeout:
            agent_data.error_message = f"Request timed out after {self.timeout} seconds"
            print(f"✗ Request timed out after {self.timeout} seconds")
        
        except requests.exceptions.ConnectionError:
            agent_data.error_message = "Connection error. Check your internet connection."
            print("✗ Connection error")
        
        except Exception as e:
            agent_data.error_message = f"Unexpected error: {str(e)}"
            print(f"✗ Unexpected error: {e}")
        
        return agent_data
    
    def try_alternative_endpoints(self, base_url: str, agent_id: str) -> AgentData:
        """Try alternative API endpoints for the agent"""
        alternative_urls = [
            f"https://cursor.com/api/agents/{agent_id}",
            f"https://api.cursor.com/agents/{agent_id}",
            f"https://cursor.com/agents/{agent_id}.json",
            f"https://cursor.com/agents/data/{agent_id}",
        ]
        
        print("\nTrying alternative endpoints...")
        for alt_url in alternative_urls:
            print(f"Trying: {alt_url}")
            agent_data = self.fetch_agent_data(alt_url)
            if agent_data.status_code == 200:
                print(f"✓ Success with alternative endpoint: {alt_url}")
                return agent_data
            time.sleep(1)  # Be respectful with requests
        
        print("✗ No alternative endpoints worked")
        return AgentData(error_message="No accessible endpoints found for this agent")
    
    def save_data(self, agent_data: AgentData, output_file: str):
        """Save the fetched data to a file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(agent_data), f, indent=2, ensure_ascii=False)
            print(f"✓ Data saved to: {output_file}")
        except Exception as e:
            print(f"✗ Error saving data: {e}")
    
    def print_summary(self, agent_data: AgentData):
        """Print a summary of the fetched data"""
        print("\n" + "="*60)
        print("CURSOR AGENT DATA SUMMARY")
        print("="*60)
        print(f"URL: {agent_data.url}")
        print(f"Agent ID: {agent_data.agent_id or 'Not found'}")
        print(f"Timestamp: {agent_data.timestamp}")
        print(f"Status Code: {agent_data.status_code or 'N/A'}")
        print(f"Content Type: {agent_data.content_type or 'N/A'}")
        print(f"Response Size: {agent_data.response_size or 0} bytes")
        
        if agent_data.error_message:
            print(f"Error: {agent_data.error_message}")
        
        if agent_data.data:
            print(f"Data Keys: {list(agent_data.data.keys()) if isinstance(agent_data.data, dict) else 'Text content'}")
        
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Fetch and process Cursor agent data')
    parser.add_argument('url', help='Cursor agent URL to fetch')
    parser.add_argument('--output', '-o', help='Output file for JSON data')
    parser.add_argument('--timeout', '-t', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--try-alternatives', '-a', action='store_true', 
                       help='Try alternative API endpoints if main URL fails')
    
    args = parser.parse_args()
    
    fetcher = CursorAgentFetcher(timeout=args.timeout)
    
    # Fetch data from the main URL
    agent_data = fetcher.fetch_agent_data(args.url)
    
    # If the main URL failed and we have an agent ID, try alternatives
    if (agent_data.status_code != 200 and 
        args.try_alternatives and 
        agent_data.agent_id):
        print(f"\nMain URL failed, trying alternatives for agent ID: {agent_data.agent_id}")
        alt_data = fetcher.try_alternative_endpoints(args.url, agent_data.agent_id)
        if alt_data.status_code == 200:
            agent_data = alt_data
    
    # Print summary
    fetcher.print_summary(agent_data)
    
    # Save data if requested
    if args.output:
        fetcher.save_data(agent_data, args.output)
    
    # Return appropriate exit code
    return 0 if agent_data.status_code == 200 else 1


if __name__ == "__main__":
    sys.exit(main())