# 🤖 Cursor Agent Data Fetcher

A comprehensive tool for fetching, processing, and analyzing data from Cursor agent URLs. This project provides both a command-line interface and a web-based viewer for exploring Cursor agent data.

## ✨ Features

- **🔍 URL Data Fetching**: Fetch data from Cursor agent URLs with robust error handling
- **🛠️ Content Processing**: Handle various content types including HTML, JSON, and binary data
- **🌐 Web Interface**: Beautiful web UI for interactive data exploration
- **📊 Data Analysis**: Extract structured information from HTML content
- **🔄 Alternative Endpoints**: Automatically try alternative API endpoints when main URL fails
- **💾 Data Storage**: Save fetched data in JSON format for later analysis
- **📋 Agent Management**: Track and manage multiple fetched agents

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Command Line Usage

```bash
# Basic usage
python3 cursor_agent_fetcher.py "https://cursor.com/agents?selectedBcId=your-agent-id"

# Save data to file
python3 cursor_agent_fetcher.py "https://cursor.com/agents?selectedBcId=your-agent-id" --output agent_data.json

# Try alternative endpoints if main URL fails
python3 cursor_agent_fetcher.py "https://cursor.com/agents?selectedBcId=your-agent-id" --try-alternatives

# Set custom timeout
python3 cursor_agent_fetcher.py "https://cursor.com/agents?selectedBcId=your-agent-id" --timeout 60
```

### Web Interface

Launch the web interface for interactive data exploration:

```bash
python3 web_viewer.py
```

Then open your browser to `http://localhost:5000`

## 📁 Project Structure

```
cursor-agent-fetcher/
├── cursor_agent_fetcher.py    # Main CLI tool
├── web_viewer.py             # Web interface
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── templates/               # Web interface templates
│   ├── index.html          # Main page
│   ├── view.html           # Agent data viewer
│   └── list.html           # Agent list
└── *.json                  # Saved agent data files
```

## 🔧 Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `url` | Cursor agent URL to fetch (required) | `"https://cursor.com/agents?selectedBcId=..."` |
| `--output`, `-o` | Output file for JSON data | `--output data.json` |
| `--timeout`, `-t` | Request timeout in seconds | `--timeout 30` |
| `--try-alternatives`, `-a` | Try alternative API endpoints | `--try-alternatives` |

## 🌐 Web Interface Features

### Main Dashboard
- **URL Input**: Enter any Cursor agent URL
- **Real-time Fetching**: Fetch and process data instantly
- **Agent Management**: View all previously fetched agents

### Agent Data Viewer
- **Comprehensive Analysis**: View all extracted data and metadata
- **Status Monitoring**: Check fetch status and response codes
- **Content Processing**: Handle different content types appropriately
- **Binary Detection**: Identify and handle binary/compressed content

### Agent List
- **Overview**: See all fetched agents at a glance
- **Quick Access**: Jump to detailed views or raw JSON data
- **Status Tracking**: Monitor success/failure status

## 🔍 Data Processing Capabilities

### Content Types Supported
- **JSON**: Direct parsing and display
- **HTML**: Structure extraction with BeautifulSoup
- **Binary/Compressed**: Detection and appropriate handling
- **Text**: Plain text content processing

### Extracted Information
- **Agent ID**: Extracted from URL parameters
- **Metadata**: Response headers, status codes, timestamps
- **HTML Analysis**: Title, meta tags, structured data
- **Data Attributes**: HTML data-* attributes
- **JavaScript Objects**: Window state and initial data

## 🛡️ Error Handling

The tool includes comprehensive error handling for:
- **Network Issues**: Connection timeouts, DNS failures
- **HTTP Errors**: 404, 403, 500, and other status codes
- **Content Issues**: Binary data, encoding problems
- **Parsing Errors**: Malformed JSON, invalid HTML

## 📊 Example Output

### Command Line
```
============================================================
CURSOR AGENT DATA SUMMARY
============================================================
URL: https://cursor.com/agents?selectedBcId=bc-89bdb1ce-f9e2-4db0-a1f4-e703b692633a
Agent ID: bc-89bdb1ce-f9e2-4db0-a1f4-e703b692633a
Timestamp: 2025-10-20 06:19:32 UTC
Status Code: 200
Content Type: text/html; charset=utf-8
Response Size: 9866 bytes
Data Keys: ['content', 'content_type']
============================================================
```

### JSON Output Structure
```json
{
  "agent_id": "bc-89bdb1ce-f9e2-4db0-a1f4-e703b692633a",
  "url": "https://cursor.com/agents?selectedBcId=...",
  "status_code": 200,
  "content_type": "text/html; charset=utf-8",
  "response_size": 9866,
  "error_message": null,
  "timestamp": "2025-10-20 06:19:32 UTC",
  "data": {
    "content_type": "html",
    "extracted_info": {
      "title": "Page Title",
      "meta_tags": {...},
      "structured_data": [...]
    },
    "raw_html": "..."
  }
}
```

## 🔧 Technical Details

### Dependencies
- **requests**: HTTP client for fetching data
- **beautifulsoup4**: HTML parsing and analysis
- **lxml**: XML/HTML parser backend
- **flask**: Web interface framework

### Architecture
- **Modular Design**: Separate CLI and web components
- **Data Classes**: Structured data representation
- **Error Recovery**: Multiple fallback strategies
- **Content Detection**: Automatic content type handling

## 🚨 Known Limitations

1. **Binary Content**: Some responses may contain binary/compressed data that appears as encoded text
2. **Authentication**: Currently doesn't handle authenticated endpoints
3. **Rate Limiting**: No built-in rate limiting for multiple requests
4. **JavaScript Rendering**: Doesn't execute JavaScript for dynamic content

## 🤝 Contributing

Feel free to contribute by:
- Reporting bugs and issues
- Suggesting new features
- Submitting pull requests
- Improving documentation

## 📝 License

This project is open source and available under the MIT License.

## 🆘 Support

If you encounter any issues:
1. Check the error messages in the console output
2. Try the `--try-alternatives` flag for failed requests
3. Verify the URL format is correct
4. Check your internet connection

---

**Made with ❤️ for the Cursor community**
