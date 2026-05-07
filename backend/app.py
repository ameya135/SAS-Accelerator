"""
Graph Approach Backend API

Flask application providing REST API endpoints for graph-based SAS to PySpark migration.
This backend integrates with the graph_approach core modules.
"""

import os
import sys
import json
import uuid
import shutil
import tempfile
import threading
import secrets
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

# Add project root to path (backend/ is one level below repo root)
_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))

# Import graph approach modules
try:
    from graph_approach.core.graph_builder import GraphBuilder
    from graph_approach.core.chunk_optimizer import ChunkOptimizer
    from graph_approach.core.dependency_graph import NodeType, EdgeType
    from graph_approach.api.graph_exporter import GraphExporter
    from graph_approach.migration.graph_migrator import GraphMigrator, MigrationResult

    GRAPH_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import graph modules: {e}")
    GRAPH_MODULES_AVAILABLE = False

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3001",
    "http://127.0.0.1:3001",
)
MAX_SAS_FILES_PER_UPLOAD = 25
MAX_SAS_FILE_SIZE_BYTES = 2 * 1024 * 1024
SAS_KEYWORD_PATTERN = re.compile(
    r"(?is)(\bdata\b|\bproc\b|%macro\b|%let\b|\blibname\b|\bfilename\b|\brun\s*;)"
)


@app.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(_e):
    return jsonify({"error": "Payload too large"}), 413


def _env_flag_enabled(name):
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _configured_cors_origins():
    configured = os.getenv("SAS_ACCELERATOR_CORS_ORIGINS")
    if not configured:
        return set(DEFAULT_CORS_ORIGINS)
    return {origin.strip() for origin in configured.split(",") if origin.strip()}


@app.after_request
def apply_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin and origin in _configured_cors_origins():
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, X-API-Key, X-Session-Token"
        )
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, DELETE, OPTIONS"
        )
    return response


@app.before_request
def require_api_key():
    """API key authentication for all endpoints except health check"""
    if request.method == "OPTIONS":
        return None

    if request.path == "/api/health":
        return None

    if app.config.get("TESTING") or _env_flag_enabled("SAS_ACCELERATOR_DEV_MODE"):
        return None

    api_key = os.getenv("SAS_ACCELERATOR_API_KEY")
    if not api_key:
        return jsonify({"error": "API key required"}), 401

    provided_key = _provided_api_key()
    if not provided_key:
        return jsonify({"error": "API key required"}), 401
    if not secrets.compare_digest(provided_key, api_key):
        return jsonify({"error": "Invalid API key"}), 401


def _provided_api_key():
    header_key = request.headers.get("X-API-Key")
    if header_key:
        return header_key

    auth_header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if auth_header.startswith(prefix):
        return auth_header[len(prefix) :].strip()

    return None


def _require_session_token(session):
    expected_token = session.get("session_token")
    if not expected_token:
        return None

    provided_token = request.headers.get("X-Session-Token")
    if not provided_token:
        return jsonify({"error": "Session token required"}), 403
    if not secrets.compare_digest(provided_token, expected_token):
        return jsonify({"error": "Invalid session token"}), 403
    return None


def _validate_uploaded_sas_file(file_storage):
    filename = file_storage.filename or ""
    if not filename:
        return None, None, (jsonify({"error": "Empty filename"}), 400)

    safe_name = secure_filename(filename)
    if not safe_name:
        return None, None, (jsonify({"error": "Invalid filename"}), 400)

    if not filename.endswith(".sas") or not safe_name.endswith(".sas"):
        return None, None, (jsonify({"error": "Files must use lowercase .sas extension"}), 400)

    content = file_storage.read()
    if len(content) > MAX_SAS_FILE_SIZE_BYTES:
        return None, None, (jsonify({"error": "File too large"}), 413)

    if b"\x00" in content:
        return None, None, (jsonify({"error": "SAS file must be text"}), 400)

    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        return None, None, (jsonify({"error": "SAS file must be text"}), 400)

    if not SAS_KEYWORD_PATTERN.search(decoded):
        return None, None, (jsonify({"error": "File content does not look like SAS"}), 400)

    return safe_name, content, None


# Session storage
sessions = {}
SESSION_TIMEOUT_HOURS = 24


def cleanup_old_sessions():
    """Remove sessions older than SESSION_TIMEOUT_HOURS"""
    now = datetime.now()
    expired = []
    for session_id, session in sessions.items():
        age = (now - session["created_at"]).total_seconds() / 3600
        if age > SESSION_TIMEOUT_HOURS:
            expired.append(session_id)

    for session_id in expired:
        session = sessions.pop(session_id, None)
        if session and session.get("temp_dir"):
            shutil.rmtree(session["temp_dir"], ignore_errors=True)


def periodic_cleanup():
    """Run cleanup every hour"""
    import time

    while True:
        time.sleep(3600)
        try:
            cleanup_old_sessions()
        except Exception:
            pass


# =====================================================
# Health Check
# =====================================================


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "graph_modules_available": GRAPH_MODULES_AVAILABLE,
            "timestamp": datetime.now().isoformat(),
        }
    )


# =====================================================
# Graph Analysis Endpoints
# =====================================================


@app.route("/api/graph/analyze", methods=["POST"])
def graph_analyze():
    """
    Analyze SAS file and return dependency graph with chunks

    Request: multipart/form-data with 'file' (SAS file) and optional 'format' (react-flow, d3, json)
    Response: { success, graph, chunks, summary, chunk_summary }
    """
    if not GRAPH_MODULES_AVAILABLE:
        return jsonify({"error": "Graph modules not available"}), 503

    try:
        # Get file from request
        if "file" not in request.files:
            # Check if we have a filename and session_id for session-based analysis
            filename = request.form.get("filename")
            session_id = request.form.get("session_id")

            if filename and session_id and session_id in sessions:
                session = sessions[session_id]
                token_error = _require_session_token(session)
                if token_error:
                    return token_error
                # Find the file in session
                sas_file_path = None
                for f in session.get("sas_files", []):
                    if os.path.basename(f) == filename:
                        sas_file_path = f
                        break

                if not sas_file_path:
                    return jsonify(
                        {"error": f"File '{filename}' not found in session"}
                    ), 400
            else:
                return jsonify({"error": "No file provided"}), 400
        else:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "Empty filename"}), 400

            safe_name = secure_filename(file.filename)
            if not safe_name:
                return jsonify({"error": "Invalid filename"}), 400

            temp_dir = tempfile.mkdtemp(prefix="graph_analysis_")
            sas_file_path = os.path.join(temp_dir, safe_name)
            file.save(sas_file_path)

        # Get output format
        output_format = request.form.get("format", "react-flow")

        # Build dependency graph
        builder = GraphBuilder.from_file(sas_file_path)
        graph = builder.build_graph()
        summary = builder.get_summary()

        # Generate chunks
        optimizer = ChunkOptimizer(graph)
        chunks = optimizer.generate_chunks()
        chunk_summary = optimizer.get_chunk_summary(chunks)

        # Export graph to requested format
        if output_format == "d3":
            graph_json = GraphExporter.to_d3_format(graph)
        elif output_format == "react-flow":
            graph_json = GraphExporter.to_react_flow_format(graph)
        else:
            graph_json = GraphExporter.to_json(graph, include_source=True)

        # Add node type and edge type counts to stats
        if graph_json.get("stats"):
            graph_json["stats"]["node_types"] = summary.get("node_counts_by_type", {})
            # Count edge types
            edge_type_counts = {}
            for edge in graph_json.get("edges", []):
                edge_type = edge.get("data", {}).get("edgeType", "unknown")
                edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
            graph_json["stats"]["edge_types"] = edge_type_counts

        # Convert chunks to JSON-serializable format
        chunks_json = []
        for chunk in chunks:
            chunk_dict = {
                "chunk_id": chunk.chunk_id,
                "layer": chunk.layer,
                "estimated_tokens": chunk.estimated_tokens,
                "node_count": len(chunk.nodes),
                "dependencies": list(chunk.dependencies),
                "source_preview": chunk.source_code[:500] + "..."
                if len(chunk.source_code) > 500
                else chunk.source_code,
                "has_macros": chunk.context.get("has_macros", False),
                "has_data_steps": chunk.context.get("has_data_steps", False),
                "has_procs": chunk.context.get("has_procs", False),
                "node_types": chunk.context.get("node_types", []),
                "node_names": chunk.context.get("node_names", []),
            }
            chunks_json.append(chunk_dict)

        # Cleanup temp file if we created one
        if "file" in request.files:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return jsonify(
            {
                "success": True,
                "graph": graph_json,
                "chunks": chunks_json,
                "summary": summary,
                "chunk_summary": chunk_summary,
            }
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": "Analysis failed"}), 500


@app.route("/api/graph/analyze-session/<session_id>", methods=["GET"])
def graph_analyze_session(session_id):
    """
    Analyze all files in a session and return combined graph

    Response: { success, graph, chunks, summary }
    """
    if not GRAPH_MODULES_AVAILABLE:
        return jsonify({"error": "Graph modules not available"}), 503

    if session_id not in sessions:
        return jsonify({"error": "Invalid session ID"}), 400

    session = sessions[session_id]
    token_error = _require_session_token(session)
    if token_error:
        return token_error

    sas_files = session.get("sas_files", [])

    if not sas_files:
        return jsonify({"error": "No files in session"}), 400

    try:
        # For now, analyze the first file
        # TODO: Support multi-file analysis
        sas_file_path = sas_files[0]

        # Build dependency graph
        builder = GraphBuilder.from_file(sas_file_path)
        graph = builder.build_graph()
        summary = builder.get_summary()

        # Generate chunks
        optimizer = ChunkOptimizer(graph)
        chunks = optimizer.generate_chunks()
        chunk_summary = optimizer.get_chunk_summary(chunks)

        # Export graph
        graph_json = GraphExporter.to_react_flow_format(graph)

        # Add stats
        if graph_json.get("stats"):
            graph_json["stats"]["node_types"] = summary.get("node_counts_by_type", {})

        # Convert chunks
        chunks_json = []
        for chunk in chunks:
            chunks_json.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "layer": chunk.layer,
                    "estimated_tokens": chunk.estimated_tokens,
                    "node_count": len(chunk.nodes),
                    "dependencies": list(chunk.dependencies),
                    "source_preview": chunk.source_code[:500] + "..."
                    if len(chunk.source_code) > 500
                    else chunk.source_code,
                    "has_macros": chunk.context.get("has_macros", False),
                    "has_data_steps": chunk.context.get("has_data_steps", False),
                    "has_procs": chunk.context.get("has_procs", False),
                }
            )

        # Store in session for later use
        session["graph"] = graph
        session["chunks"] = chunks
        session["graph_json"] = graph_json

        return jsonify(
            {
                "success": True,
                "graph": graph_json,
                "chunks": chunks_json,
                "summary": summary,
                "chunk_summary": chunk_summary,
            }
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": "Analysis failed"}), 500


# =====================================================
# Migration Session Endpoints
# =====================================================


@app.route("/api/graph-migrate/initialize", methods=["POST"])
def initialize_session():
    """
    Initialize a new migration session

    Request JSON: { model?, use_rag? }
    Response: { success, session_id, config }
    """
    if not GRAPH_MODULES_AVAILABLE:
        return jsonify({"error": "Graph modules not available"}), 503

    try:
        data = request.get_json() or {}

        # Create session
        session_id = str(uuid.uuid4())
        session_token = secrets.token_urlsafe(32)
        temp_dir = tempfile.mkdtemp(prefix=f"graph_migration_{session_id}_")

        # Get configuration
        model = data.get("model", os.getenv("DEFAULT_MODEL", "gpt-4"))
        use_rag = data.get("use_rag", True)

        sessions[session_id] = {
            "session_id": session_id,
            "session_token": session_token,
            "temp_dir": temp_dir,
            "model": model,
            "use_rag": use_rag,
            "status": "initialized",
            "created_at": datetime.now(),
            "sas_files": [],
            "graph": None,
            "chunks": None,
            "results": None,
            "output_dir": None,
        }

        return jsonify(
            {
                "success": True,
                "session_id": session_id,
                "session_token": session_token,
                "config": {"model": model, "use_rag": use_rag},
            }
        )

    except Exception as e:
        return jsonify({"error": "Initialization failed"}), 500


@app.route("/api/graph-migrate/upload", methods=["POST"])
def upload_files():
    """
    Upload SAS files to a session

    Request: multipart/form-data with 'session_id' and 'files[]'
    Response: { success, session_id, uploaded_files, total_files }
    """
    if not GRAPH_MODULES_AVAILABLE:
        return jsonify({"error": "Graph modules not available"}), 503

    try:
        session_id = request.form.get("session_id")
        if not session_id or session_id not in sessions:
            return jsonify({"error": "Invalid session ID"}), 400

        session = sessions[session_id]
        token_error = _require_session_token(session)
        if token_error:
            return token_error

        # Get uploaded files
        if "files[]" not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist("files[]")
        if len(files) > MAX_SAS_FILES_PER_UPLOAD:
            return jsonify({"error": "Too many files"}), 400
        if len(session.get("sas_files", [])) + len(files) > MAX_SAS_FILES_PER_UPLOAD:
            return jsonify({"error": "Too many files"}), 400

        uploaded_files = []

        for file in files:
            safe_name, content, validation_error = _validate_uploaded_sas_file(file)
            if validation_error:
                return validation_error

            file_path = os.path.join(session["temp_dir"], safe_name)
            with open(file_path, "wb") as output_file:
                output_file.write(content)
            session["sas_files"].append(file_path)
            uploaded_files.append(
                {
                    "filename": file.filename,
                    "name": file.filename,
                    "size": os.path.getsize(file_path),
                }
            )

        session["status"] = "files_uploaded"

        return jsonify(
            {
                "success": True,
                "session_id": session_id,
                "uploaded_files": uploaded_files,
                "total_files": len(session["sas_files"]),
            }
        )

    except RequestEntityTooLarge:
        return jsonify({"error": "Payload too large"}), 413
    except Exception:
        return jsonify({"error": "Upload failed"}), 500


@app.route("/api/graph-migrate/start", methods=["POST"])
def start_migration():
    """
    Start graph-based migration for all files in session

    Request JSON: { session_id }
    Response: { success, session_id, results }
    """
    if not GRAPH_MODULES_AVAILABLE:
        return jsonify({"error": "Graph modules not available"}), 503

    try:
        data = request.get_json()
        session_id = data.get("session_id")

        if not session_id or session_id not in sessions:
            return jsonify({"error": "Invalid session ID"}), 400

        session = sessions[session_id]
        token_error = _require_session_token(session)
        if token_error:
            return token_error

        if not session["sas_files"]:
            return jsonify({"error": "No files uploaded"}), 400

        # Get API credentials
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

        if not api_key or not endpoint:
            return jsonify(
                {
                    "error": (
                        "Azure OpenAI credentials not configured. Set "
                        "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT "
                        "environment variables."
                    )
                }
            ), 500

        # Initialize migrator
        migrator = GraphMigrator(
            api_key=api_key,
            azure_endpoint=endpoint,
            model=session["model"],
            use_rag=session["use_rag"],
        )

        # Create output directory
        output_dir = os.path.join(session["temp_dir"], "output")
        os.makedirs(output_dir, exist_ok=True)

        # Migrate files
        results = []
        for sas_file in session["sas_files"]:
            try:
                result = migrator.migrate_file(
                    sas_file_path=sas_file, output_dir=output_dir, visualize=False
                )
                results.append(
                    {
                        "file": os.path.basename(sas_file),
                        "filename": os.path.basename(sas_file),
                        "success": result.success,
                        "chunks_converted": result.chunks_converted,
                        "total_chunks": result.total_chunks,
                        "errors": result.errors,
                        "warnings": result.warnings,
                        "pyspark_code": result.pyspark_code,
                        "mapping": result.mapping,
                        "execution_time": result.execution_time,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "file": os.path.basename(sas_file),
                        "filename": os.path.basename(sas_file),
                        "success": False,
                        "error": str(e),
                    }
                )

        session["status"] = "completed"
        session["results"] = results
        session["output_dir"] = output_dir

        return jsonify({"success": True, "session_id": session_id, "results": results})

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": "Migration failed"}), 500


@app.route("/api/graph-migrate/status/<session_id>", methods=["GET"])
def get_session_status(session_id):
    """Get current status of a migration session"""
    if session_id not in sessions:
        return jsonify({"error": "Invalid session ID"}), 400

    session = sessions[session_id]
    token_error = _require_session_token(session)
    if token_error:
        return token_error

    return jsonify(
        {
            "success": True,
            "session_id": session_id,
            "status": session["status"],
            "files_count": len(session["sas_files"]),
            "has_results": session["results"] is not None,
            "created_at": session["created_at"].isoformat(),
        }
    )


@app.route("/api/graph-migrate/download/<session_id>/<filename>", methods=["GET"])
def download_file(session_id, filename):
    """Download a converted file from a session"""
    if not GRAPH_MODULES_AVAILABLE:
        return jsonify({"error": "Graph modules not available"}), 503

    try:
        if session_id not in sessions:
            return jsonify({"error": "Invalid session ID"}), 400

        session = sessions[session_id]
        token_error = _require_session_token(session)
        if token_error:
            return token_error

        output_dir = session.get("output_dir")

        if not output_dir:
            return jsonify({"error": "No output available"}), 400

        safe_name = secure_filename(filename)
        if not safe_name:
            return jsonify({"error": "Invalid filename"}), 400

        output_real = os.path.realpath(output_dir)
        file_path = os.path.realpath(os.path.join(output_real, safe_name))
        if os.path.commonpath([output_real, file_path]) != output_real:
            return jsonify({"error": "Invalid file path"}), 400

        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        return send_file(file_path, as_attachment=True, download_name=safe_name)

    except Exception as e:
        return jsonify({"error": "Download failed"}), 500


@app.route("/api/graph-migrate/download-all/<session_id>", methods=["GET"])
def download_all_files(session_id):
    """Download all converted files as a ZIP archive"""
    if not GRAPH_MODULES_AVAILABLE:
        return jsonify({"error": "Graph modules not available"}), 503

    try:
        if session_id not in sessions:
            return jsonify({"error": "Invalid session ID"}), 400

        session = sessions[session_id]
        token_error = _require_session_token(session)
        if token_error:
            return token_error

        output_dir = session.get("output_dir")

        if not output_dir or not os.path.exists(output_dir):
            return jsonify({"error": "No output available"}), 400

        # Create ZIP archive
        import zipfile

        zip_path = os.path.join(session["temp_dir"], "migration_results.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)

        return send_file(
            zip_path,
            as_attachment=True,
            download_name="graph_migration_results.zip",
            mimetype="application/zip",
        )

    except Exception as e:
        return jsonify({"error": "Download failed"}), 500


@app.route("/api/graph-migrate/cleanup/<session_id>", methods=["DELETE"])
def cleanup_session(session_id):
    """Clean up a migration session"""
    try:
        if session_id in sessions:
            session = sessions[session_id]
            token_error = _require_session_token(session)
            if token_error:
                return token_error
            session = sessions.pop(session_id)
            if session.get("temp_dir"):
                shutil.rmtree(session["temp_dir"], ignore_errors=True)
            return jsonify({"success": True, "message": "Session cleaned up"})
        else:
            return jsonify({"success": False, "error": "Session not found"}), 400
    except Exception as e:
        return jsonify({"error": "Cleanup failed"}), 500


# =====================================================
# Main Entry Point
# =====================================================

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    api_auth_status = (
        "Disabled (dev mode)"
        if _env_flag_enabled("SAS_ACCELERATOR_DEV_MODE")
        else "Required"
    )

    # Start cleanup thread
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()

    # Get port from environment or use default
    port = int(os.getenv("GRAPH_BACKEND_PORT", 5002))

    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║        Graph-Based SAS to PySpark Migration Backend           ║
╠═══════════════════════════════════════════════════════════════╣
║  Server running on: http://localhost:{port}                    ║
║  Graph modules: {"Available" if GRAPH_MODULES_AVAILABLE else "Not Available"}                              ║
║  API Key Auth: {api_auth_status}                                      ║
╚═══════════════════════════════════════════════════════════════╝
""")

    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    app.run(debug=debug, host=host, port=port)
