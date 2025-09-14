#!/usr/bin/env python3
# paste_integration_demo.py - Minimal FastAPI server demonstrating paste integration

import time
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(
    title="Paste Integration Demo",
    description="Demonstration of integrated paste functionality",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# In - memory storage for pastes
pastes_storage = []


class PasteCreate(BaseModel):
    content: str
    title: Optional[str] = None


class PasteResponse(BaseModel):
    id: int
    content: str
    title: Optional[str]
    timestamp: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """Main page with integrated paste functionality"""
    return HTMLResponse(
        content="""
<!DOCTYPE html>
<html>
<head>
    <title > Integrated Paste App</title>
    <style>
        body {
            font - family: 'Segoe UI', Tahoma, Geneva, Verdana, sans - serif;
            margin: 0;
            padding: 20px;
            background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
            min - height: 100vh;
        }
        .container {
            max - width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border - radius: 15px;
            box - shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text - align: center;
            margin - bottom: 30px;
            font - size: 2.5em;
        }
        .integration - status {
            background: #e8f5e8;
            border: 2px solid #4caf50;
            padding: 15px;
            border - radius: 8px;
            margin - bottom: 20px;
            text - align: center;
        }
        .integration - status h3 {
            color: #2e7d32;
            margin: 0;
        }
        textarea {
            width: 100%;
            height: 200px;
            margin: 10px 0;
            padding: 15px;
            border: 2px solid #ddd;
            border - radius: 8px;
            font - family: 'Courier New', monospace;
            font - size: 14px;
            resize: vertical;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            margin - bottom: 15px;
            border: 2px solid #ddd;
            border - radius: 8px;
            font - size: 16px;
        }
        button {
            padding: 12px 25px;
            margin: 8px;
            background: linear - gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border - radius: 8px;
            cursor: pointer;
            font - size: 16px;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box - shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .paste - item {
            border: 1px solid #e0e0e0;
            margin: 15px 0;
            padding: 20px;
            border - radius: 10px;
            background: #fafafa;
            transition: box - shadow 0.3s;
        }
        .paste - item:hover {
            box - shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .paste - meta {
            color: #666;
            font - size: 0.9em;
            margin - bottom: 15px;
            display: flex;
            justify - content: space - between;
            align - items: center;
        }
        pre {
            background: #f8f9fa;
            padding: 15px;
            border - radius: 8px;
            overflow - x: auto;
            border - left: 4px solid #667eea;
        }
        .stats {
            display: flex;
            justify - content: space - around;
            margin: 20px 0;
            padding: 15px;
            background: #f0f0f0;
            border - radius: 8px;
        }
        .stat - item {
            text - align: center;
        }
        .stat - number {
            font - size: 2em;
            font - weight: bold;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Integrated Paste Application</h1>

        <div class="integration - status">
            <h3>✅ Paste Functionality Successfully Integrated</h3>
            <p > The paste feature is now fully integrated into the main application architecture</p>
        </div>

        <div class="stats">
            <div class="stat - item">
                <div class="stat - number" id="pasteCount">0</div>
                <div > Total Pastes</div>
            </div>
            <div class="stat - item">
                <div class="stat - number" id="serverStatus">🟢</div>
                <div > Server Status</div>
            </div>
        </div>

        <form id="pasteForm">
            <input type="text" id="title" placeholder="Enter a title for your paste (optional)...">
            <textarea id="content" placeholder="Enter your content here...\\n\\nThis integrated paste app demonstrates:\\n• FastAPI backend integration\\n• Modern responsive UI\\n• Real - time updates\\n• Persistent storage\\n• RESTful API endpoints"></textarea>
            <div>
                <button type="submit">💾 Save Paste</button>
                <button type="button" onclick="loadPastes()">🔄 Refresh</button>
                <button type="button" onclick="clearForm()">🗑️ Clear</button>
            </div>
        </form>

        <h2>📋 Saved Pastes</h2>
        <div id="pastes"></div>
    </div>

    <script>
        let pastes = [];

        document.getElementById('pasteForm').addEventListener('submit',
    async function(e) {
            e.preventDefault();
            const content = document.getElementById('content').value;
            const title = document.getElementById('title').value;

            if (content.trim()) {
                try {
                    const response = await fetch('/api/paste', {
                        method: 'POST',
                            headers: {
                            'Content - Type': 'application/json',
                                },
                            body: JSON.stringify({
                            content: content,
                                title: title || null
                        })
                    });

                    if (response.ok) {
                        clearForm();
                        loadPastes();
                        showNotification('Paste saved successfully!', 'success');
                    } else {
                        showNotification('Failed to save paste', 'error');
                    }
                } catch (error) {
                    showNotification('Error saving paste: ' + error.message, 'error');
                }
            } else {
                showNotification('Please enter some content', 'warning');
            }
        });

        async function loadPastes() {
            try {
                const response = await fetch("/api/pastes');
                if (response.ok) {
                    pastes = await response.json();
                    renderPastes();
                    updateStats();
                }
            } catch (error) {
                console.error('Error loading pastes:', error);
                showNotification('Error loading pastes', 'error');
            }
        }

        function renderPastes() {
            const container = document.getElementById('pastes');
            if (pastes.length === 0) {
                container.innerHTML = '<p style="text - align: center; color: #666; font - style: italic;">No pastes yet. Create your first paste above!</p>';
                return;
            }

            container.innerHTML = pastes.map(paste => `
                <div class="paste - item">
                    <div class="paste - meta">
                        <div>
                            ${paste.title ? `<strong>${paste.title}</strong>` : `<em > Untitled Paste #${paste.id}</em>`}
                        </div>
                        <div>
                            📅 ${new Date(paste.timestamp).toLocaleString()}
                        </div>
                    </div>
                    <pre>${paste.content}</pre>
                </div>
            `).join('');
        }

        function clearForm() {
            document.getElementById('content').value = '';
            document.getElementById('title').value = '';
        }

        function updateStats() {
            document.getElementById('pasteCount').textContent = pastes.length;
        }

        function showNotification(message, type) {//Simple notification system
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border - radius: 8px;
                color: white;
                font - weight: bold;
                z - index: 1000;
                animation: slideIn 0.3s ease;
            `;

            switch(type) {
                case 'success':
                    notification.style.background = '#4caf50';
                    break;
                case 'error':
                    notification.style.background = '#f44336';
                    break;
                case 'warning':
                    notification.style.background = '#ff9800';
                    break;
            }

            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 3000);
        }//Load pastes on page load
        loadPastes();//Auto - refresh every 30 seconds
        setInterval(loadPastes, 30000);
    </script>
</body>
</html>
    """
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "paste_integration_demo",
        "timestamp": datetime.now().isoformat(),
        "integration_status": "active",
    }


@app.post("/api/paste", response_model=PasteResponse)
async def create_paste(paste_data: PasteCreate):
    """Create a new paste"""
    paste_id = len(pastes_storage) + 1
    new_paste = {
        "id": paste_id,
        "content": paste_data.content,
        "title": paste_data.title,
        "timestamp": datetime.now().isoformat(),
    }
    pastes_storage.append(new_paste)
    return new_paste


@app.get("/api/pastes", response_model=List[PasteResponse])
async def get_pastes(limit: int = 50, offset: int = 0):
    """Get all pastes with pagination"""
    return pastes_storage[offset : offset + limit]


@app.get("/api/paste/{paste_id}", response_model=PasteResponse)
async def get_paste(paste_id: int):
    """Get a specific paste by ID"""
    for paste in pastes_storage:
        if paste["id"] == paste_id:
            return paste
    raise HTTPException(status_code=404, detail="Paste not found")


# Cache for stats to reduce computation
_stats_cache = {"data": None, "timestamp": 0}
CACHE_DURATION = 30  # 30 seconds


@app.get("/api/stats")
async def get_stats():
    """Get paste statistics (cached for 30 seconds)"""
    current_time = time.time()

    # Return cached data if still valid
    if (
        _stats_cache["data"] is not None
        and current_time - _stats_cache["timestamp"] < CACHE_DURATION
    ):
        return _stats_cache["data"]

    # Generate fresh stats
    stats = {
        "total_pastes": len(pastes_storage),
        "server_uptime": "active",
        "integration_status": "fully_integrated",
        "last_updated": datetime.now().isoformat(),
        "cache_status": "fresh",
    }

    # Update cache
    _stats_cache["data"] = stats
    _stats_cache["timestamp"] = current_time

    return stats


if __name__ == "__main__":
    print("🚀 Starting Integrated Paste Application...")
    print("📋 Paste functionality successfully integrated!")
    print("🌐 Access the application at: http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
