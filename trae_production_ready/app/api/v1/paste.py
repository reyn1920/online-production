#!/usr/bin/env python3
"""
Paste Router - Handles paste functionality for production app
Provides endpoints for creating, retrieving, and managing text pastes
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

router = APIRouter()

# In-memory storage for pastes (in production, use a database)
pastes_storage = []


class PasteCreate(BaseModel):
    content: str
    title: Optional[str] = None


class PasteResponse(BaseModel):
    id: int
    content: str
    title: Optional[str]
    timestamp: str


@router.get("/status")
async def paste_status():
    """Paste service status endpoint"""
    return {
        "status": "healthy",
        "service": "paste",
        "total_pastes": len(pastes_storage),
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/paste", response_model=PasteResponse)
async def create_paste(paste_data: PasteCreate):
    """Create a new paste"""
    if not paste_data.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    paste_id = len(pastes_storage) + 1
    new_paste = {
        "id": paste_id,
        "content": paste_data.content,
        "title": paste_data.title,
        "timestamp": datetime.now().isoformat(),
    }

    pastes_storage.append(new_paste)
    return new_paste


@router.get("/pastes", response_model=List[PasteResponse])
async def get_pastes(limit: int = 10, offset: int = 0):
    """Get all pastes with pagination"""
    start = offset
    end = offset + limit
    return pastes_storage[start:end]


@router.get("/paste/{paste_id}", response_model=PasteResponse)
async def get_paste(paste_id: int):
    """Get a specific paste by ID"""
    for paste in pastes_storage:
        if paste["id"] == paste_id:
            return paste
    raise HTTPException(status_code=404, detail="Paste not found")


@router.delete("/paste/{paste_id}")
async def delete_paste(paste_id: int):
    """Delete a specific paste by ID"""
    global pastes_storage
    original_length = len(pastes_storage)
    pastes_storage = [paste for paste in pastes_storage if paste["id"] != paste_id]
    
    if len(pastes_storage) == original_length:
        raise HTTPException(status_code=404, detail="Paste not found")
    
    return {"message": "Paste deleted successfully"}


@router.get("/ui", response_class=HTMLResponse)
async def paste_ui():
    """Serve the paste UI"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Paste App - Production</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        input[type="text"]:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            height: 200px;
            resize: vertical;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background: #c82333;
        }
        .paste-item {
            border: 1px solid #e1e5e9;
            margin: 15px 0;
            padding: 20px;
            border-radius: 8px;
            background: #f8f9fa;
            transition: box-shadow 0.3s ease;
        }
        .paste-item:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .paste-meta {
            color: #6c757d;
            font-size: 0.9em;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .paste-title {
            font-weight: 600;
            color: #495057;
        }
        .paste-content {
            background: white;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.5;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 20px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #6c757d;
            font-size: 0.9em;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #6c757d;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
        }
        .success {
            background: #d4edda;
            color: #155724;
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Paste App - Production</h1>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number" id="pasteCount">0</div>
                <div class="stat-label">Total Pastes</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="serverStatus">🟢</div>
                <div class="stat-label">Server Status</div>
            </div>
        </div>

        <form id="pasteForm">
            <div class="form-group">
                <label for="title">Title (Optional)</label>
                <input type="text" id="title" placeholder="Enter a title for your paste...">
            </div>
            <div class="form-group">
                <label for="content">Content</label>
                <textarea id="content" placeholder="Enter your content here...\n\nThis production paste app features:\n• FastAPI backend integration\n• Modern responsive UI\n• Real-time updates\n• RESTful API endpoints\n• Production-ready architecture"></textarea>
            </div>
            <div class="button-group">
                <button type="submit" class="btn-primary">💾 Save Paste</button>
                <button type="button" onclick="loadPastes()" class="btn-secondary">🔄 Refresh</button>
                <button type="button" onclick="clearForm()" class="btn-secondary">🗑️ Clear</button>
            </div>
        </form>

        <div id="message"></div>
        <h2>📋 Saved Pastes</h2>
        <div id="pastes"></div>
    </div>

    <script>
        let pastes = [];

        function showMessage(text, type = 'success') {
            const messageDiv = document.getElementById('message');
            messageDiv.innerHTML = `<div class="${type}">${text}</div>`;
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, 3000);
        }

        document.getElementById('pasteForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const content = document.getElementById('content').value;
            const title = document.getElementById('title').value;

            if (content.trim()) {
                try {
                    const response = await fetch('/api/v1/paste/paste', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            content: content,
                            title: title || null
                        })
                    });

                    if (response.ok) {
                        const result = await response.json();
                        showMessage('Paste saved successfully!');
                        clearForm();
                        loadPastes();
                    } else {
                        const error = await response.json();
                        showMessage(error.detail || 'Failed to save paste', 'error');
                    }
                } catch (error) {
                    showMessage('Error saving paste: ' + error.message, 'error');
                }
            } else {
                showMessage('Please enter some content', 'error');
            }
        });

        async function loadPastes() {
            try {
                const response = await fetch('/api/v1/paste/pastes');
                if (response.ok) {
                    pastes = await response.json();
                    renderPastes();
                    updateStats();
                } else {
                    showMessage('Failed to load pastes', 'error');
                }
            } catch (error) {
                showMessage('Error loading pastes: ' + error.message, 'error');
            }
        }

        async function deletePaste(pasteId) {
            if (confirm('Are you sure you want to delete this paste?')) {
                try {
                    const response = await fetch(`/api/v1/paste/paste/${pasteId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        showMessage('Paste deleted successfully!');
                        loadPastes();
                    } else {
                        showMessage('Failed to delete paste', 'error');
                    }
                } catch (error) {
                    showMessage('Error deleting paste: ' + error.message, 'error');
                }
            }
        }

        function renderPastes() {
            const container = document.getElementById('pastes');
            if (pastes.length === 0) {
                container.innerHTML = '<div class="loading">No pastes yet. Create your first paste above!</div>';
                return;
            }
            
            container.innerHTML = pastes.map(paste => `
                <div class="paste-item">
                    <div class="paste-meta">
                        <div>
                            ${paste.title ? `<span class="paste-title">${paste.title}</span> - ` : ''}
                            <span>Saved: ${new Date(paste.timestamp).toLocaleString()}</span>
                        </div>
                        <button onclick="deletePaste(${paste.id})" class="btn-danger" style="padding: 4px 8px; font-size: 12px;">Delete</button>
                    </div>
                    <div class="paste-content">${paste.content}</div>
                </div>
            `).join('');
        }

        function updateStats() {
            document.getElementById('pasteCount').textContent = pastes.length;
        }

        function clearForm() {
            document.getElementById('content').value = '';
            document.getElementById('title').value = '';
        }

        // Load pastes on page load
        loadPastes();
    </script>
</body>
</html>
    """