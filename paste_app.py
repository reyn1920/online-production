#!/usr/bin/env python3
"""
Paste App - Simple Flask application with automatic port detection

Usage:
    python3 paste_app.py              # Auto-detects port starting from 8000
    PORT=8001 python3 paste_app.py    # Auto-detects port starting from 8001
"""

import math
import os
import shutil
import socket
import time
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template_string, request, send_file
from werkzeug.exceptions import HTTPException
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


# ---------- BEGIN PATCH: Places + JSON errors + Dev stubs ----------
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
    return jsonify(
        {"status": "healthy", "timestamp": time.time(), "service": "paste-app"}
    )


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
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


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
                stat = file_path.stat()
                files.append(
                    {
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "extension": file_path.suffix.lower(),
                    }
                )

        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)

        return jsonify({"success": True, "files": files, "count": len(files)})

    except Exception as e:
        return jsonify({"error": f"Failed to list files: {str(e)}"}), 500


@app.route("/downloads/process", methods=["POST"])
@app.route("/api/downloads/process", methods=["POST"])  # alias
def process_downloads_file():
    """Process a file from downloads folder"""
    try:
        data = request.get_json()
        if not data or "filename" not in data:
            return jsonify({"error": "Filename is required"}), 400

        filename = secure_filename(data["filename"])
        action = data.get("action", "read")

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404

        if action == "read":
            # Read file content (for text files)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                return jsonify(
                    {
                        "success": True,
                        "filename": filename,
                        "content": content,
                        "action": "read",
                    }
                )
            except UnicodeDecodeError:
                return jsonify(
                    {
                        "success": True,
                        "filename": filename,
                        "content": "[Binary file - cannot display content]",
                        "action": "read",
                        "is_binary": True,
                    }
                )

        elif action == "download":
            # Send file for download
            return send_file(filepath, as_attachment=True)

        elif action == "delete":
            # Delete file
            os.remove(filepath)
            return jsonify(
                {
                    "success": True,
                    "filename": filename,
                    "action": "delete",
                    "message": "File deleted successfully",
                }
            )

        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

    except Exception as e:
        return jsonify({"error": f"File processing failed: {str(e)}"}), 500


@app.route("/paste/avatar", methods=["POST"])
@app.route("/api/paste/avatar", methods=["POST"])  # alias
def paste_avatar():
    """Avatar generation endpoint for paste integration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        content = data.get("content", "")
        avatar_type = data.get("avatar_type", "professional")
        voice_style = data.get("voice_style", "natural")
        quality = data.get("quality", "high")
        template = data.get("template", "professional_presenter")

        # Simulate avatar generation (in real implementation, this would call actual avatar service)
        avatar_result = {
            "id": int(time.time() * 1000),
            "content": content,
            "avatar_type": avatar_type,
            "voice_style": voice_style,
            "quality": quality,
            "template": template,
            "status": "generated",
            "url": f"/avatar/{int(time.time() * 1000)}.mp4",
            "thumbnail": f"/avatar/thumb_{int(time.time() * 1000)}.jpg",
            "duration": len(content.split()) * 0.5,  # Rough estimate
            "created_at": time.time(),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "avatar": avatar_result,
                    "message": "Avatar generated successfully",
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": f"Avatar generation failed: {str(e)}"}), 500


# --------- Places search (free Overpass) ----------
# category -> OSM tag mapping (add more as you like)
_OSM_TAGS = {
    "veterinary": {"amenity": "veterinary"},
    "clinic": {"amenity": "clinic"},
    "hospital": {"amenity": "hospital"},
    "pharmacy": {"amenity": "pharmacy"},
    "pet_store": {"shop": "pet"},
    "dog_park": {"leisure": "dog_park"},
}


def _overpass_query(lat, lng, radius_m, tag_key, tag_val, limit):
    # Overpass QL for nodes/ways/relations around a point; include center for ways/relations
    q = f"""
    [out:json][timeout:25];
    (
      node(around:{radius_m},{lat},{lng})[{tag_key}="{tag_val}"];
      way(around:{radius_m},{lat},{lng})[{tag_key}="{tag_val}"];
      relation(around:{radius_m},{lat},{lng})[{tag_key}="{tag_val}"];
    );
    out center {limit};
    """
    r = requests.post(
        "https://overpass-api.de/api/interpreter", data={"data": q}, timeout=30
    )
    r.raise_for_status()
    return r.json()


def _elements_to_items(js):
    items = []
    for el in js.get("elements", []):
        tags = el.get("tags", {}) or {}
        lat = el.get("lat")
        lng = el.get("lon")
        if not lat or not lng:
            # ways/relations have center
            center = el.get("center")
            if center:
                lat, lng = center.get("lat"), center.get("lon")
        if not (lat and lng):
            continue
        items.append(
            {
                "id": el.get("id"),
                "name": tags.get("name") or "Unnamed place",
                "address": ", ".join(
                    filter(
                        None,
                        [
                            tags.get("addr:street"),
                            tags.get("addr:housenumber"),
                            tags.get("addr:city"),
                            tags.get("addr:state"),
                            tags.get("addr:country"),
                        ],
                    )
                )
                or None,
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "website": tags.get("website") or tags.get("contact:website"),
                "lat": lat,
                "lng": lng,
                "raw_tags": tags,
            }
        )
    return items


@app.get("/places/search")
@app.get("/api/places/search")  # alias
def places_search():
    category = (request.args.get("category") or "veterinary").lower()
    lat = float(request.args.get("lat", "40.7128"))
    lng = float(request.args.get("lng", "-74.0060"))
    radius_m = int(request.args.get("radius_m", "5000"))
    limit = int(request.args.get("limit", "50"))

    tag = _OSM_TAGS.get(category) or _OSM_TAGS["veterinary"]
    tag_key, tag_val = list(tag.items())[0]

    try:
        js = _overpass_query(lat, lng, radius_m, tag_key, tag_val, limit)
        items = _elements_to_items(js)
        PROVIDER_STATUS["overpass"]["color"] = "green"
        PROVIDER_STATUS["overpass"]["last_error"] = None
        return jsonify({"provider": "overpass", "items": items})
    except Exception as e:
        # Mark provider red and return a friendly fallback
        PROVIDER_STATUS["overpass"]["color"] = "red"
        PROVIDER_STATUS["overpass"]["last_error"] = str(e)

        fallback = [
            {
                "id": "fallback_1",
                "name": "Example Clinic",
                "address": "123 Example St",
                "lat": lat,
                "lng": lng,
                "phone": None,
                "website": None,
            }
        ]
        return jsonify({"provider": "static_fallback", "items": fallback})


# --------- Locator pages (HTML) ----------
_LOCATOR_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Places Locator</title>
<meta name="viewport" content="width=device-width,initial-scale=1" />
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


@app.get("/places/locator")
@app.get("/api/places/locator")  # alias
def places_locator():
    return render_template_string(_LOCATOR_HTML)


# Embeddable mini-map
_LOCATOR_EMBED_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Mini Locator</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
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


@app.get("/places/locator/embed")
@app.get("/api/places/locator/embed")  # alias
def places_locator_embed():
    return render_template_string(_LOCATOR_EMBED_HTML)


@app.get("/integrations/providers/ui")
def providers_ui():
    html = """
    <!doctype html><meta charset="utf-8">
    <title>Providers</title>
    <style>
      body{font:14px system-ui;background:#0f1220;color:#e7e7ea;padding:20px}
      .row{display:flex;gap:10px;align-items:center;margin:8px 0}
      .dot{width:10px;height:10px;border-radius:50%}
    </style>
    <div id="list">Loading…</div>
    <script>
      const colors = {green:"#20d56b", purple:"#a78bfa", red:"#ef4444"};
      async function load(){
        const r = await fetch('/places/providers'); const js = await r.json();
        const list = document.getElementById('list');
        list.innerHTML = (js.items||[]).map(x=>{
          const c = colors[x.color] || "#94a3b8";
          return `<div class="row"><span class="dot" style="background:${c}"></span><b>${x.name}</b><small style="opacity:.7">&nbsp;(${x.key})</small>${x.last_error?`&nbsp;<small style="color:#ef4444">${x.last_error}</small>`:''}}</div>`;
        }).join('') || "No providers";
      }
      load(); setInterval(load, 10000);
    </script>
    """
    return html


# --------- JSON error handler (prevents plain-text 500s) ----------
@app.errorhandler(Exception)
def _json_errors(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code or 500

    # Friendly fallbacks for known paths you're hitting with curl
    p = request.path or ""
    if p.startswith("/content/pets/fish/species"):
        # static fish fallback (always JSON, 200)
        return (
            jsonify(
                {
                    "provider": "static_fallback",
                    "count": 5,
                    "species": [
                        {
                            "name": "Atlantic Salmon",
                            "scientific": "Salmo salar",
                            "biology": "Atlantic salmon are anadromous fish...",
                            "habitat": "North Atlantic Ocean...",
                        },
                        {
                            "name": "Pacific Cod",
                            "scientific": "Gadus macrocephalus",
                            "biology": "Pacific cod are bottom-dwelling...",
                            "habitat": "North Pacific Ocean...",
                        },
                        {
                            "name": "Yellowfin Tuna",
                            "scientific": "Thunnus albacares",
                            "biology": "Yellowfin tuna are fast-swimming...",
                            "habitat": "Tropical and subtropical waters...",
                        },
                        {
                            "name": "Red Snapper",
                            "scientific": "Lutjanus campechanus",
                            "biology": "Red snapper are long-lived...",
                            "habitat": "Gulf of Mexico...",
                        },
                        {
                            "name": "Mahi-Mahi",
                            "scientific": "Coryphaena hippurus",
                            "biology": "Mahi-mahi are fast-growing...",
                            "habitat": "Warm tropical/subtropical seas...",
                        },
                    ],
                }
            ),
            200,
        )

    if p.startswith("/content/pets/birds/nearby"):
        return (
            jsonify(
                {
                    "provider": "static",
                    "data": [
                        {
                            "speciesCode": "amecro",
                            "comName": "American Crow",
                            "sciName": "Corvus brachyrhynchos",
                            "locName": "Central Park, New York",
                            "obsDt": "2024-01-15 10:30",
                            "howMany": 3,
                        },
                        {
                            "speciesCode": "norcrd",
                            "comName": "Northern Cardinal",
                            "sciName": "Cardinalis cardinalis",
                            "locName": "Bryant Park, New York",
                            "obsDt": "2024-01-15 09:45",
                            "howMany": 2,
                        },
                        {
                            "speciesCode": "blujay",
                            "comName": "Blue Jay",
                            "sciName": "Cyanocitta cristata",
                            "locName": "Washington Square Park, New York",
                            "obsDt": "2024-01-15 11:15",
                            "howMany": 1,
                        },
                    ],
                }
            ),
            200,
        )

    # generic JSON error for everything else
    return jsonify({"error": "internal_error", "status": code, "message": str(e)}), code


# ---------- END PATCH ----------

# Simple HTML template for the paste app
HTML_TEMPLATE = """
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
    """Main page with paste interface"""
    return render_template_string(HTML_TEMPLATE)


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "app": "paste_app"})


def first_free(start, max_tries=50):
    """Find the first free port starting from 'start'"""
    host = os.getenv("HOST", "127.0.0.1")
    p = start
    for _ in range(max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, p))
                return p
            except OSError:
                p += 1
    raise RuntimeError(
        f"No free port found after trying {max_tries} ports starting from {start}"
    )


if __name__ == "__main__":
    port = first_free(8081)
    print(f"Starting paste app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
