#!/usr/bin/env python3
"""
Simple web interface to view Cursor agent data
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from cursor_agent_fetcher import CursorAgentFetcher
import threading
import time

app = Flask(__name__)

# Store fetched data
agent_data_store = {}

@app.route('/')
def index():
    """Main page with form to fetch agent data"""
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch_agent():
    """Fetch agent data from URL"""
    url = request.form.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        fetcher = CursorAgentFetcher()
        agent_data = fetcher.fetch_agent_data(url)
        
        # Store the data with a timestamp key
        timestamp = str(int(time.time()))
        agent_data_store[timestamp] = agent_data
        
        return redirect(url_for('view_agent', timestamp=timestamp))
    
    except Exception as e:
        return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500

@app.route('/view/<timestamp>')
def view_agent(timestamp):
    """View agent data"""
    if timestamp not in agent_data_store:
        return "Agent data not found", 404
    
    agent_data = agent_data_store[timestamp]
    return render_template('view.html', agent_data=agent_data, timestamp=timestamp)

@app.route('/api/data/<timestamp>')
def get_agent_data(timestamp):
    """API endpoint to get raw agent data"""
    if timestamp not in agent_data_store:
        return jsonify({'error': 'Agent data not found'}), 404
    
    from dataclasses import asdict
    return jsonify(asdict(agent_data_store[timestamp]))

@app.route('/list')
def list_agents():
    """List all fetched agents"""
    agents = []
    for timestamp, data in agent_data_store.items():
        agents.append({
            'timestamp': timestamp,
            'url': data.url,
            'agent_id': data.agent_id,
            'status_code': data.status_code,
            'fetch_time': data.timestamp
        })
    
    return render_template('list.html', agents=agents)

if __name__ == '__main__':
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    # Create index template
    with open('templates/index.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Cursor Agent Data Fetcher</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="url"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005a87; }
        .header { text-align: center; margin-bottom: 30px; }
        .links { margin-top: 20px; text-align: center; }
        .links a { margin: 0 10px; color: #007cba; text-decoration: none; }
        .links a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Cursor Agent Data Fetcher</h1>
        <p>Fetch and analyze data from Cursor agent URLs</p>
    </div>
    
    <form method="POST" action="/fetch">
        <div class="form-group">
            <label for="url">Cursor Agent URL:</label>
            <input type="url" id="url" name="url" placeholder="https://cursor.com/agents?selectedBcId=..." required>
        </div>
        <button type="submit">🔍 Fetch Agent Data</button>
    </form>
    
    <div class="links">
        <a href="/list">📋 View All Fetched Agents</a>
    </div>
</body>
</html>''')
    
    # Create view template
    with open('templates/view.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Agent Data - {{ agent_data.agent_id or 'Unknown' }}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { border-bottom: 2px solid #007cba; padding-bottom: 10px; margin-bottom: 20px; }
        .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .info-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007cba; }
        .info-card h3 { margin-top: 0; color: #007cba; }
        .status-success { color: #28a745; }
        .status-error { color: #dc3545; }
        .data-section { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 20px; }
        .data-content { background: white; padding: 15px; border-radius: 4px; border: 1px solid #ddd; max-height: 400px; overflow-y: auto; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
        .nav-links { margin-bottom: 20px; }
        .nav-links a { color: #007cba; text-decoration: none; margin-right: 15px; }
        .nav-links a:hover { text-decoration: underline; }
        .binary-warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="nav-links">
        <a href="/">← Back to Fetcher</a>
        <a href="/list">📋 All Agents</a>
        <a href="/api/data/{{ timestamp }}">📄 Raw JSON</a>
    </div>
    
    <div class="header">
        <h1>🤖 Agent Data Analysis</h1>
        <p>{{ agent_data.url }}</p>
    </div>
    
    <div class="info-grid">
        <div class="info-card">
            <h3>Agent ID</h3>
            <p>{{ agent_data.agent_id or 'Not found' }}</p>
        </div>
        
        <div class="info-card">
            <h3>Status</h3>
            <p class="{% if agent_data.status_code == 200 %}status-success{% else %}status-error{% endif %}">
                {{ agent_data.status_code or 'N/A' }}
                {% if agent_data.status_code == 200 %}✓ Success{% endif %}
            </p>
        </div>
        
        <div class="info-card">
            <h3>Content Type</h3>
            <p>{{ agent_data.content_type or 'Unknown' }}</p>
        </div>
        
        <div class="info-card">
            <h3>Response Size</h3>
            <p>{{ agent_data.response_size or 0 }} bytes</p>
        </div>
        
        <div class="info-card">
            <h3>Fetch Time</h3>
            <p>{{ agent_data.timestamp }}</p>
        </div>
        
        {% if agent_data.error_message %}
        <div class="info-card">
            <h3>Error</h3>
            <p class="status-error">{{ agent_data.error_message }}</p>
        </div>
        {% endif %}
    </div>
    
    {% if agent_data.data %}
    <div class="data-section">
        <h2>📊 Fetched Data</h2>
        
        {% if agent_data.data.content_type == 'html' and agent_data.data.extracted_info %}
            <h3>Extracted Information</h3>
            <div class="data-content">
                <pre>{{ agent_data.data.extracted_info | tojson(indent=2) }}</pre>
            </div>
            
            {% if agent_data.data.raw_html %}
            <h3>Raw HTML (truncated)</h3>
            <div class="data-content">
                <pre>{{ agent_data.data.raw_html }}</pre>
            </div>
            {% endif %}
        {% else %}
            {% if agent_data.data.content and agent_data.data.content[0:10].find('\x00') != -1 %}
            <div class="binary-warning">
                ⚠️ <strong>Binary Content Detected:</strong> The response appears to contain binary data. This might be compressed content, images, or other non-text data.
            </div>
            {% endif %}
            
            <div class="data-content">
                <pre>{{ agent_data.data | tojson(indent=2) }}</pre>
            </div>
        {% endif %}
    </div>
    {% endif %}
</body>
</html>''')
    
    # Create list template
    with open('templates/list.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>All Fetched Agents</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { border-bottom: 2px solid #007cba; padding-bottom: 10px; margin-bottom: 20px; }
        .nav-links { margin-bottom: 20px; }
        .nav-links a { color: #007cba; text-decoration: none; margin-right: 15px; }
        .nav-links a:hover { text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        tr:hover { background-color: #f8f9fa; }
        .status-success { color: #28a745; }
        .status-error { color: #dc3545; }
        .agent-id { font-family: monospace; font-size: 0.9em; }
        .url { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    </style>
</head>
<body>
    <div class="nav-links">
        <a href="/">← Back to Fetcher</a>
    </div>
    
    <div class="header">
        <h1>📋 All Fetched Agents</h1>
        <p>{{ agents|length }} agent(s) fetched</p>
    </div>
    
    {% if agents %}
    <table>
        <thead>
            <tr>
                <th>Agent ID</th>
                <th>URL</th>
                <th>Status</th>
                <th>Fetch Time</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for agent in agents %}
            <tr>
                <td class="agent-id">{{ agent.agent_id or 'N/A' }}</td>
                <td class="url" title="{{ agent.url }}">{{ agent.url }}</td>
                <td class="{% if agent.status_code == 200 %}status-success{% else %}status-error{% endif %}">
                    {{ agent.status_code or 'N/A' }}
                </td>
                <td>{{ agent.fetch_time }}</td>
                <td>
                    <a href="/view/{{ agent.timestamp }}">View</a> |
                    <a href="/api/data/{{ agent.timestamp }}">JSON</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>No agents fetched yet. <a href="/">Fetch your first agent</a>!</p>
    {% endif %}
</body>
</html>''')
    
    print("🚀 Starting Cursor Agent Data Viewer...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🔍 Enter a Cursor agent URL to fetch and analyze data")
    
    app.run(host='0.0.0.0', port=5000, debug=True)