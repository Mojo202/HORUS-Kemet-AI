#!/usr/bin/env python3
"""
Demo script showing all features of the Cursor Agent Data Fetcher
"""

import sys
import time
from cursor_agent_fetcher import CursorAgentFetcher

def main():
    print("🤖 Cursor Agent Data Fetcher - Demo")
    print("=" * 50)
    
    # Example URL (the one provided by the user)
    example_url = "https://cursor.com/agents?selectedBcId=bc-89bdb1ce-f9e2-4db0-a1f4-e703b692633a"
    
    print(f"📡 Fetching data from: {example_url}")
    print()
    
    # Create fetcher instance
    fetcher = CursorAgentFetcher(timeout=30)
    
    # Fetch the data
    agent_data = fetcher.fetch_agent_data(example_url)
    
    # Display summary
    fetcher.print_summary(agent_data)
    
    # Save data
    output_file = f"demo_agent_data_{int(time.time())}.json"
    fetcher.save_data(agent_data, output_file)
    
    print("\n🎯 Demo Complete!")
    print("\n📋 What you can do next:")
    print("1. 🖥️  Run the web interface: python3 web_viewer.py")
    print("2. 📄 View the saved data: cat", output_file)
    print("3. 🔍 Try other URLs with the CLI tool")
    print("4. 📚 Read the README.md for full documentation")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())