#!/usr/bin/env python3
"""
Paste App - Simple Flask application with automatic port detection

Usage:
    python3 paste_app.py              # Auto-detects port starting from 8000
    PORT=8001 python3 paste_app.py    # Auto-detects port starting from 8001
"""

import os
import socket
import time
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template_string, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload settings
UPLOAD_FOLDER = os.path.expanduser("~/Downloads")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "doc",
    "docx",
    "py",
    "js",
    "html",
    "css",
    "json",
    "xml",
    "zip",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# In-memory provider status (for lights)
PROVIDER_STATUS = {
    "overpass": {
        "name": "OpenStreetMap Overpass",
        "color": "green",
        "last_error": None,
        "requires_key": False,
    },
    "nominatim": {
        "name": "OpenStreetMap Nominatim",
        "color": "green",
        "last_error": None,
        "requires_key": False,
    },
}


# Dev-only route that some UIs ping; return 204 instead of 404 noise
@app.route("/@vite/client")
def _vite_client_placeholder():
    return ("", 204)


# Minimal system status (handy for quick checks)
@app.get("/api/status")
def api_status():
    return jsonify(
        {
            "framework": "flask",
            "port": 8080,  # Updated to reflect new default port
            "services": {"places": True, "pets": True},
            "providers": PROVIDER_STATUS,
            "time": int(time.time()),
        }
    )


# Health check endpoint for Docker healthcheck
@app.get("/health")
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time(), "service": "paste-app"})


# Provider statuses (green/purple/red)
@app.get("/places/providers")
@app.get("/api/places/providers")  # alias
def places_providers():
    items = []
    for key, v in PROVIDER_STATUS.items():
        color = v["color"]
        if v.get("requires_key"):
            color = "purple"
        items.append(
            {
                "key": key,
                "name": v["name"],
                "color": color,
                "last_error": v["last_error"],
            }
        )
    return jsonify({"items": items})


# --------- Paste API ----------
@app.route("/paste", methods=["POST"])
@app.route("/api/paste", methods=["POST"])  # alias
def create_paste():
    """Create a new paste entry"""
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        content = data.get("content", "").strip()
        if not content:
            return jsonify({"error": "Content is required"}), 400

        # Create paste object
        paste = {
            "id": int(time.time() * 1000),  # timestamp in milliseconds
            "content": content,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": time.time(),
        }

        # In a real app, you'd save to database
        # For now, just return the created paste
        return (
            jsonify(
                {
                    "success": True,
                    "paste": paste,
                    "message": "Paste created successfully",
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to create paste: {str(e)}"}), 500


# --------- Downloads Integration API ----------
@app.route("/upload", methods=["POST"])
@app.route("/api/upload", methods=["POST"])  # alias
def upload_file():
    """Upload file to downloads folder"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Handle custom filename from form data
            custom_filename = request.form.get("filename")
            if custom_filename:
                filename = secure_filename(custom_filename)

            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            return (
                jsonify(
                    {
                        "success": True,
                        "filename": filename,
                        "filepath": filepath,
                        "message": "File uploaded successfully",
                    }
                ),
                201,
            )
        else:
            return jsonify({"error": "File type not allowed"}), 400

    except Exception as e:
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500


@app.route("/downloads/list", methods=["GET"])
@app.route("/api/downloads/list", methods=["GET"])  # alias
def list_downloads():
    """List files in downloads folder"""
    try:
        downloads_path = Path(app.config["UPLOAD_FOLDER"])
        if not downloads_path.exists():
            return jsonify({"files": []})

        files = []
        for file_path in downloads_path.iterdir():
            if file_path.is_file():
                files.append(
                    {
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime,
                    }
                )

        return jsonify({"files": files})

    except Exception as e:
        return jsonify({"error": f"Failed to list downloads: {str(e)}"}), 500


@app.route("/downloads/process", methods=["POST"])
@app.route("/api/downloads/process", methods=["POST"])  # alias
def process_downloads_file():
    """Process a file from downloads folder"""
    try:
        data = request.get_json()
        if not data or "filename" not in data:
            return jsonify({"error": "Filename is required"}), 400

        filename = secure_filename(data["filename"])
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404

        # Basic file processing - read content if it's a text file
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return jsonify(
                {
                    "success": True,
                    "filename": filename,
                    "content": content[:1000],  # First 1000 chars
                    "message": "File processed successfully",
                }
            )
        except UnicodeDecodeError:
            return jsonify(
                {
                    "success": True,
                    "filename": filename,
                    "message": "Binary file detected - content not displayed",
                }
            )

    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


@app.route("/paste/avatar", methods=["POST"])
@app.route("/api/paste/avatar", methods=["POST"])  # alias
def paste_avatar():
    """Generate avatar for paste"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Simple avatar generation based on content hash
        content = data.get("content", "")
        if not content:
            return jsonify({"error": "Content is required"}), 400

        # Generate a simple hash-based avatar
        import hashlib

        hash_obj = hashlib.md5(content.encode())
        hash_hex = hash_obj.hexdigest()

        # Use hash to generate avatar properties
        avatar = {
            "color": f"#{hash_hex[:6]}",
            "initials": content[:2].upper() if len(content) >= 2 else "PA",
            "hash": hash_hex[:8],
        }

        return jsonify(
            {
                "success": True,
                "avatar": avatar,
                "message": "Avatar generated successfully",
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to generate avatar: {str(e)}"}), 500


# OSM tags for different place categories
_OSM_TAGS = {
    "veterinary": {"amenity": "veterinary"},
    "clinic": {"amenity": "clinic"},
    "hospital": {"amenity": "hospital"},
    "pharmacy": {"amenity": "pharmacy"},
    "pet_store": {"shop": "pet"},
    "dog_park": {"leisure": "dog_park"},
}


def _overpass_query(lat, lng, radius_m, tag_key, tag_val, limit):
    """Build Overpass API query"""
    query = f"""
    [out:json][timeout:25];
    (
      node["{tag_key}"="{tag_val}"](around:{radius_m},{lat},{lng});
      way["{tag_key}"="{tag_val}"](around:{radius_m},{lat},{lng});
      relation["{tag_key}"="{tag_val}"](around:{radius_m},{lat},{lng});
    );
    out center {limit};
    """
    return query.strip()


def _elements_to_items(js):
    """Convert Overpass API elements to standardized items"""
    items = []
    for elem in js.get("elements", []):
        tags = elem.get("tags", {})
        name = tags.get("name", "Unnamed")

        # Get coordinates
        if elem["type"] == "node":
            lat, lng = elem["lat"], elem["lon"]
        elif "center" in elem:
            lat, lng = elem["center"]["lat"], elem["center"]["lon"]
        else:
            continue

        # Build address
        addr_parts = []
        for key in ["addr:housenumber", "addr:street", "addr:city"]:
            if key in tags:
                addr_parts.append(tags[key])
        address = ", ".join(addr_parts) if addr_parts else ""

        items.append(
            {
                "name": name,
                "lat": lat,
                "lng": lng,
                "address": address,
                "tags": tags,
            }
        )
    return items


@app.get("/places/search")
@app.get("/api/places/search")  # alias
def places_search():
    """Search for places using OpenStreetMap data"""
    try:
        # Get query parameters
        category = request.args.get("category", "veterinary")
        lat = float(request.args.get("lat", 40.7128))
        lng = float(request.args.get("lng", -74.0060))
        radius_m = int(request.args.get("radius_m", 5000))
        limit = int(request.args.get("limit", 50))

        # Get OSM tags for category
        if category not in _OSM_TAGS:
            return jsonify({"error": f"Unknown category: {category}"}), 400

        tag_data = _OSM_TAGS[category]
        tag_key, tag_val = next(iter(tag_data.items()))

        # Build and execute Overpass query
        query = _overpass_query(lat, lng, radius_m, tag_key, tag_val, limit)

        response = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=30)
        response.raise_for_status()

        # Convert to standardized format
        items = _elements_to_items(response.json())

        return jsonify(
            {
                "items": items,
                "provider": "overpass",
                "query": {
                    "category": category,
                    "lat": lat,
                    "lng": lng,
                    "radius_m": radius_m,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500


# HTML templates for the locator interfaces
_LOCATOR_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Places Locator</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<style>
  html,body,#map { height:100%; margin:0 }
  body { background:#0f1220; color:#e7e7ea; font:14px/1.4 system-ui, sans-serif; }
  .panel { position:absolute; top:10px; left:10px; z-index:1000; background:#11142a; border:1px solid #2a2e44; padding:10px; border-radius:10px; }
  label { display:block; margin-bottom:6px }
  select,input { background:#0f1220; color:#e7e7ea; border:1px solid #2a2e44; border-radius:6px; padding:6px; }
  button { padding:6px 10px; border-radius:6px; border:1px solid #2a2e44; background:#1b2140; color:#e7e7ea }
</style>
</head>
<body>
<div class="panel">
  <label>Category
    <select id="cat">
      <option value="veterinary">Veterinary</option>
      <option value="clinic">Clinic</option>
      <option value="hospital">Hospital</option>
      <option value="pharmacy">Pharmacy</option>
      <option value="pet_store">Pet Store</option>
      <option value="dog_park">Dog Park</option>
    </select>
  </label>
  <button id="btn">Search here</button>
  <span id="badge" style="margin-left:8px; opacity:.8">Ready</span>
</div>
<div id="map"></div>
<script>
  const map = L.map('map').setView([40.7128,-74.0060], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      {maxZoom:19, attribution:'&copy; OpenStreetMap'}).addTo(map);
  const cluster = L.markerClusterGroup({chunkedLoading:true, maxClusterRadius:50});
  map.addLayer(cluster);
  const badge = document.getElementById('badge');
  const catSel = document.getElementById('cat');
  const btn = document.getElementById('btn');
  async function runSearch() {
      const c = catSel.value;
    const center = map.getCenter();
    const url = `/places/search?category=${encodeURIComponent(c)}&lat=${center.lat}&lng=${center.lng}&radius_m=5000&limit=50`;
    badge.textContent = 'Searching…';
    const r = await fetch(url);
    const js = await r.json();
    cluster.clearLayers();
    (js.items||[]).forEach(x=>{
        if(!x.lat || !x.lng) return;
      const html = `<b>${x.name||'Unnamed'}</b><br/>${x.address||''}`;
      cluster.addLayer(L.marker([x.lat,x.lng]).bindPopup(html));
    });
    badge.textContent = `${(js.items||[]).length} found via ${js.provider}`;
  }
  btn.addEventListener('click', runSearch);
  runSearch();
</script>
</body>
</html>
"""

_MINI_LOCATOR_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Mini Locator</title>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
  <style>
    html,body,#map { height:100%; margin:0; background:#0f1220 }
    .badge { position:absolute; top:8px; left:8px; z-index:1000; background:#11142a; color:#e7e7ea; border:1px solid #2a2e44; padding:6px 10px; border-radius:999px; font:12px system-ui }
  </style>
</head>
<body>
  <div class="badge" id="badge">Loading…</div>
  <div id="map"></div>
  <script>
    const qs = new URLSearchParams(location.search);
    const cat = qs.get('cat') || 'veterinary';
    const lat = parseFloat(qs.get('lat') || '40.7128');
    const lng = parseFloat(qs.get('lng') || '-74.0060');
    const zoom = parseInt(qs.get('zoom') || '12', 10);
    const map = L.map('map').setView([lat,lng], zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {maxZoom:19, attribution:'&copy; OpenStreetMap'}).addTo(map);
    const cluster = L.markerClusterGroup({chunkedLoading:true, maxClusterRadius:50});
    map.addLayer(cluster);
    const badge = document.getElementById('badge');
    async function load() {
        const center = map.getCenter();
      const r = await fetch(`/places/search?category=${encodeURIComponent(cat)}&lat=${center.lat}&lng=${center.lng}&radius_m=5000&limit=50`);
      const js = await r.json();
      cluster.clearLayers();
      (js.items||[]).forEach(x=>{
          if(!x.lat || !x.lng) return;
        const html = `<b>${x.name||'Unnamed'}</b><br/>${x.address||''}`;
        cluster.addLayer(L.marker([x.lat,x.lng]).bindPopup(html));
      });
      badge.textContent = `${(js.items||[]).length} ${cat} — ${js.provider}`;
    }
    load();
  </script>
</body>
</html>
"""


@app.get("/places")
@app.get("/locator")
def places_locator():
    """Full-featured places locator interface"""
    return render_template_string(_LOCATOR_HTML)


@app.get("/mini")
def mini_locator():
    """Minimal places locator interface"""
    return render_template_string(_MINI_LOCATOR_HTML)


# Main paste app interface
_PASTE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Paste App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        textarea { width: 100%; height: 300px; margin: 10px 0; }
        button { padding: 10px 20px; margin: 5px; }
        .paste-item { border: 1px solid #ddd; margin: 10px 0; padding: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Simple Paste App</h1>
        <form id="pasteForm">
            <textarea id="content" placeholder="Enter your text here..."></textarea><br>
            <button type="submit">Save Paste</button>
        </form>
        <div id="pastes"></div>
    </div>
    <script>
        let pastes = [];
        document.getElementById('pasteForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const content = document.getElementById('content').value;
            if (content.trim()) {
                const paste = {
                    id: Date.now(),
                    content: content,
                    timestamp: new Date().toLocaleString()
                };
                pastes.unshift(paste);
                document.getElementById('content').value = '';
                renderPastes();
            }
        });
        function renderPastes() {
            const container = document.getElementById('pastes');
            container.innerHTML = pastes.map(paste => `
                <div class="paste-item">
                    <small>Saved: ${paste.timestamp}</small>
                    <pre>${paste.content}</pre>
                </div>
            `).join('');
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Main paste app interface"""
    return render_template_string(_PASTE_HTML)


def find_free_port(start_port=8000):
    """Find the first available port starting from start_port"""
    port = start_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            port += 1
    raise RuntimeError("No free ports available")


if __name__ == "__main__":
    # Get starting port from environment or use default
    start_port = int(os.environ.get("PORT", 8000))
    port = find_free_port(start_port)
    print(f"Starting Paste App on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
