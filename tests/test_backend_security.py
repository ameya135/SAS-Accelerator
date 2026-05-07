import os
import io
import json
import tempfile
import pytest
from datetime import datetime


@pytest.mark.security
class TestAPIKeyAuthentication:
    def test_health_endpoint_no_auth_required(self, no_auth_client):
        response = no_auth_client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"

    def test_protected_endpoint_requires_key_when_not_testing_or_dev_mode(
        self, app, monkeypatch
    ):
        app.config["TESTING"] = False
        monkeypatch.delenv("SAS_ACCELERATOR_DEV_MODE", raising=False)
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        try:
            response = app.test_client().post(
                "/api/graph-migrate/initialize",
                data=json.dumps({}),
                content_type="application/json",
            )
            assert response.status_code == 401
            data = response.get_json()
            assert "API key required" in data["error"]
        finally:
            app.config["TESTING"] = True

    def test_protected_endpoint_rejects_wrong_key_when_not_testing(
        self, app, monkeypatch, api_key
    ):
        app.config["TESTING"] = False
        monkeypatch.delenv("SAS_ACCELERATOR_DEV_MODE", raising=False)
        monkeypatch.setenv("SAS_ACCELERATOR_API_KEY", api_key)
        try:
            response = app.test_client().post(
                "/api/graph-migrate/initialize",
                data=json.dumps({}),
                content_type="application/json",
                headers={"X-API-Key": "wrong-key"},
            )
            assert response.status_code == 401
            data = response.get_json()
            assert "Invalid API key" in data["error"]
        finally:
            app.config["TESTING"] = True

    def test_protected_endpoint_accepts_valid_key_header_when_not_testing(
        self, app, monkeypatch, api_key
    ):
        app.config["TESTING"] = False
        monkeypatch.delenv("SAS_ACCELERATOR_DEV_MODE", raising=False)
        monkeypatch.setenv("SAS_ACCELERATOR_API_KEY", api_key)
        try:
            response = app.test_client().post(
                "/api/graph-migrate/initialize",
                data=json.dumps({}),
                content_type="application/json",
                headers={"X-API-Key": api_key},
            )
            assert response.status_code != 401
        finally:
            app.config["TESTING"] = True

    def test_protected_endpoint_rejects_valid_key_query_when_not_testing(
        self, app, monkeypatch, api_key
    ):
        app.config["TESTING"] = False
        monkeypatch.delenv("SAS_ACCELERATOR_DEV_MODE", raising=False)
        monkeypatch.setenv("SAS_ACCELERATOR_API_KEY", api_key)
        try:
            response = app.test_client().post(
                f"/api/graph-migrate/initialize?api_key={api_key}",
                data=json.dumps({}),
                content_type="application/json",
            )
            assert response.status_code == 401
            data = response.get_json()
            assert "API key required" in data["error"]
        finally:
            app.config["TESTING"] = True

    def test_dev_mode_allows_no_api_key_when_not_testing(self, app, monkeypatch):
        app.config["TESTING"] = False
        monkeypatch.setenv("SAS_ACCELERATOR_DEV_MODE", "true")
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        try:
            response = app.test_client().post(
                "/api/graph-migrate/initialize",
                data=json.dumps({}),
                content_type="application/json",
            )
            assert response.status_code != 401
        finally:
            app.config["TESTING"] = True

    def test_testing_mode_allows_no_api_key(self, no_auth_client):
        response = no_auth_client.post(
            "/api/graph-migrate/initialize",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code != 401

    def test_protected_endpoint_accepts_bearer_token_when_not_testing(
        self, app, monkeypatch, api_key
    ):
        app.config["TESTING"] = False
        monkeypatch.delenv("SAS_ACCELERATOR_DEV_MODE", raising=False)
        monkeypatch.setenv("SAS_ACCELERATOR_API_KEY", api_key)
        try:
            response = app.test_client().post(
                "/api/graph-migrate/initialize",
                data=json.dumps({}),
                content_type="application/json",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            assert response.status_code != 401
        finally:
            app.config["TESTING"] = True

    def test_analyze_endpoint_requires_auth_when_not_testing(self, app, monkeypatch):
        app.config["TESTING"] = False
        monkeypatch.delenv("SAS_ACCELERATOR_DEV_MODE", raising=False)
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        try:
            response = app.test_client().post("/api/graph/analyze")
            assert response.status_code == 401
        finally:
            app.config["TESTING"] = True

    def test_upload_endpoint_requires_auth_when_not_testing(self, app, monkeypatch):
        app.config["TESTING"] = False
        monkeypatch.delenv("SAS_ACCELERATOR_DEV_MODE", raising=False)
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        try:
            response = app.test_client().post("/api/graph-migrate/upload")
            assert response.status_code == 401
        finally:
            app.config["TESTING"] = True

    def test_status_endpoint_requires_auth_when_not_testing(self, app, monkeypatch):
        app.config["TESTING"] = False
        monkeypatch.delenv("SAS_ACCELERATOR_DEV_MODE", raising=False)
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        try:
            response = app.test_client().get("/api/graph-migrate/status/test-session")
            assert response.status_code == 401
        finally:
            app.config["TESTING"] = True


@pytest.mark.security
class TestPathTraversal:
    def test_download_rejects_path_traversal(self, app, monkeypatch):
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        client = app.test_client()

        session_id = "test-traversal-session"
        temp_dir = tempfile.mkdtemp()
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)

        with open(os.path.join(output_dir, "safe.py"), "w") as f:
            f.write("# safe file")

        from backend.app import sessions

        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "download-token",
            "temp_dir": temp_dir,
            "output_dir": output_dir,
            "status": "completed",
            "created_at": datetime.now(),
            "sas_files": [],
        }

        try:
            response = client.get(
                f"/api/graph-migrate/download/{session_id}/../../../etc/passwd",
                headers={"X-Session-Token": "download-token"},
            )
            assert response.status_code in (400, 404)
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)

    def test_download_rejects_dot_dot_filename(self, app, monkeypatch):
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        client = app.test_client()

        session_id = "test-dotdot-session"
        temp_dir = tempfile.mkdtemp()
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)

        from backend.app import sessions

        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "download-token",
            "temp_dir": temp_dir,
            "output_dir": output_dir,
            "status": "completed",
            "created_at": datetime.now(),
            "sas_files": [],
        }

        try:
            response = client.get(
                f"/api/graph-migrate/download/{session_id}/..%2F..%2Fetc%2Fpasswd",
                headers={"X-Session-Token": "download-token"},
            )
            assert response.status_code in (400, 404)
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)

    def test_download_serves_valid_file(self, app, monkeypatch):
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        client = app.test_client()

        session_id = "test-valid-download"
        temp_dir = tempfile.mkdtemp()
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)

        with open(os.path.join(output_dir, "result.py"), "w") as f:
            f.write("print('hello')")

        from backend.app import sessions

        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "download-token",
            "temp_dir": temp_dir,
            "output_dir": output_dir,
            "status": "completed",
            "created_at": datetime.now(),
            "sas_files": [],
        }

        try:
            response = client.get(
                f"/api/graph-migrate/download/{session_id}/result.py",
                headers={"X-Session-Token": "download-token"},
            )
            from backend.app import GRAPH_MODULES_AVAILABLE

            if GRAPH_MODULES_AVAILABLE:
                assert response.status_code == 200
            else:
                assert response.status_code == 503
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)


@pytest.mark.security
class TestFilenameSanitization:
    def test_upload_rejects_malicious_filename(self, app, monkeypatch):
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        client = app.test_client()

        session_id = "test-upload-session"
        temp_dir = tempfile.mkdtemp()

        from backend.app import sessions

        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "upload-token",
            "temp_dir": temp_dir,
            "sas_files": [],
            "status": "initialized",
            "created_at": datetime.now(),
        }

        try:
            data = {"session_id": session_id}
            malicious_content = io.BytesIO(b"DATA test; RUN;")
            malicious_file = (
                io.BytesIO(b"DATA test; RUN;"),
                "../../../tmp/malicious.sas",
            )

            response = client.post(
                "/api/graph-migrate/upload",
                data={
                    "session_id": session_id,
                    "files[]": (
                        io.BytesIO(b"DATA test; RUN;"),
                        "../../../tmp/malicious.sas",
                    ),
                },
                headers={"X-Session-Token": "upload-token"},
                content_type="multipart/form-data",
            )

            for sid in list(sessions.keys()):
                sess = sessions[sid]
                base = os.path.normpath(sess["temp_dir"])
                for fpath in sess.get("sas_files", []):
                    assert ".." not in fpath
                    # secure_filename strips traversal before paths are stored.
                    norm = os.path.normpath(fpath)
                    assert norm.startswith(base), (norm, base)
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)


@pytest.mark.security
class TestRequestSizeLimit:
    def test_rejects_oversized_upload(self, app, monkeypatch):
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        client = app.test_client()
        temp_dir = tempfile.mkdtemp()
        session_id = "test-size-session"
        from backend.app import sessions

        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "size-token",
            "temp_dir": temp_dir,
            "sas_files": [],
            "status": "initialized",
            "created_at": datetime.now(),
        }
        try:
            large_content = b"x" * (17 * 1024 * 1024)
            response = client.post(
                "/api/graph-migrate/upload",
                data={
                    "session_id": session_id,
                    "files[]": (io.BytesIO(large_content), "big.sas"),
                },
                headers={"X-Session-Token": "size-token"},
                content_type="multipart/form-data",
            )
            # 413 = MAX_CONTENT_LENGTH (16MB); 503 if graph modules unavailable
            assert response.status_code in (413, 503)
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)


@pytest.mark.security
class TestCORSRestrictions:
    def test_default_cors_allows_localhost_frontend(self, client, monkeypatch):
        monkeypatch.delenv("SAS_ACCELERATOR_CORS_ORIGINS", raising=False)
        response = client.get("/api/health", headers={"Origin": "http://localhost:3001"})
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3001"

    def test_default_cors_rejects_unconfigured_origin(self, client, monkeypatch):
        monkeypatch.delenv("SAS_ACCELERATOR_CORS_ORIGINS", raising=False)
        response = client.get("/api/health", headers={"Origin": "https://evil.example"})
        assert "Access-Control-Allow-Origin" not in response.headers

    def test_env_cors_origin_is_allowed(self, client, monkeypatch):
        monkeypatch.setenv("SAS_ACCELERATOR_CORS_ORIGINS", "https://ui.example")
        response = client.get("/api/health", headers={"Origin": "https://ui.example"})
        assert response.headers.get("Access-Control-Allow-Origin") == "https://ui.example"


@pytest.mark.security
class TestSessionTokenOwnership:
    def test_initialize_returns_session_token(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.GRAPH_MODULES_AVAILABLE", True)
        response = client.post(
            "/api/graph-migrate/initialize",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["session_token"]
        assert data["session_token"] != data["session_id"]

    def test_status_requires_session_token_even_in_testing_mode(self, client):
        from backend.app import sessions

        session_id = "owned-session"
        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "owner-token",
            "temp_dir": tempfile.mkdtemp(),
            "sas_files": [],
            "status": "initialized",
            "results": None,
            "created_at": datetime.now(),
        }
        try:
            response = client.get(f"/api/graph-migrate/status/{session_id}")
            assert response.status_code == 403
            data = response.get_json()
            assert "Session token required" in data["error"]
        finally:
            temp_dir = sessions.get(session_id, {}).get("temp_dir")
            sessions.pop(session_id, None)
            if temp_dir:
                __import__("shutil").rmtree(temp_dir, ignore_errors=True)

    def test_status_accepts_correct_session_token(self, client):
        from backend.app import sessions

        session_id = "owned-session-ok"
        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "owner-token",
            "temp_dir": tempfile.mkdtemp(),
            "sas_files": [],
            "status": "initialized",
            "results": None,
            "created_at": datetime.now(),
        }
        try:
            response = client.get(
                f"/api/graph-migrate/status/{session_id}",
                headers={"X-Session-Token": "owner-token"},
            )
            assert response.status_code == 200
        finally:
            temp_dir = sessions.get(session_id, {}).get("temp_dir")
            sessions.pop(session_id, None)
            if temp_dir:
                __import__("shutil").rmtree(temp_dir, ignore_errors=True)

    def test_upload_requires_session_token_even_in_testing_mode(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.GRAPH_MODULES_AVAILABLE", True)
        from backend.app import sessions

        session_id = "upload-owned-session"
        temp_dir = tempfile.mkdtemp()
        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "upload-token",
            "temp_dir": temp_dir,
            "sas_files": [],
            "status": "initialized",
            "created_at": datetime.now(),
        }
        try:
            response = client.post(
                "/api/graph-migrate/upload",
                data={
                    "session_id": session_id,
                    "files[]": (io.BytesIO(b"DATA test; RUN;"), "test.sas"),
                },
                content_type="multipart/form-data",
            )
            assert response.status_code == 403
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)


@pytest.mark.security
class TestUploadValidation:
    def test_upload_rejects_uppercase_sas_extension(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.GRAPH_MODULES_AVAILABLE", True)
        from backend.app import sessions

        session_id = "uppercase-extension"
        temp_dir = tempfile.mkdtemp()
        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "upload-token",
            "temp_dir": temp_dir,
            "sas_files": [],
            "status": "initialized",
            "created_at": datetime.now(),
        }
        try:
            response = client.post(
                "/api/graph-migrate/upload",
                data={
                    "session_id": session_id,
                    "files[]": (io.BytesIO(b"DATA test; RUN;"), "TEST.SAS"),
                },
                headers={"X-Session-Token": "upload-token"},
                content_type="multipart/form-data",
            )
            assert response.status_code == 400
            assert "lowercase .sas" in response.get_json()["error"]
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)

    def test_upload_rejects_binary_content(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.GRAPH_MODULES_AVAILABLE", True)
        from backend.app import sessions

        session_id = "binary-upload"
        temp_dir = tempfile.mkdtemp()
        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "upload-token",
            "temp_dir": temp_dir,
            "sas_files": [],
            "status": "initialized",
            "created_at": datetime.now(),
        }
        try:
            response = client.post(
                "/api/graph-migrate/upload",
                data={
                    "session_id": session_id,
                    "files[]": (io.BytesIO(b"\x00\x01\x02DATA test; RUN;"), "test.sas"),
                },
                headers={"X-Session-Token": "upload-token"},
                content_type="multipart/form-data",
            )
            assert response.status_code == 400
            assert "text" in response.get_json()["error"]
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)

    def test_upload_rejects_non_sas_text(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.GRAPH_MODULES_AVAILABLE", True)
        from backend.app import sessions

        session_id = "non-sas-upload"
        temp_dir = tempfile.mkdtemp()
        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "upload-token",
            "temp_dir": temp_dir,
            "sas_files": [],
            "status": "initialized",
            "created_at": datetime.now(),
        }
        try:
            response = client.post(
                "/api/graph-migrate/upload",
                data={
                    "session_id": session_id,
                    "files[]": (io.BytesIO(b"this is a plain text note"), "test.sas"),
                },
                headers={"X-Session-Token": "upload-token"},
                content_type="multipart/form-data",
            )
            assert response.status_code == 400
            assert "SAS" in response.get_json()["error"]
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)

    def test_upload_rejects_too_many_files(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.GRAPH_MODULES_AVAILABLE", True)
        monkeypatch.setattr("backend.app.MAX_SAS_FILES_PER_UPLOAD", 1, raising=False)
        from backend.app import sessions

        session_id = "too-many-files"
        temp_dir = tempfile.mkdtemp()
        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "upload-token",
            "temp_dir": temp_dir,
            "sas_files": [],
            "status": "initialized",
            "created_at": datetime.now(),
        }
        try:
            response = client.post(
                "/api/graph-migrate/upload",
                data={
                    "session_id": session_id,
                    "files[]": [
                        (io.BytesIO(b"DATA one; RUN;"), "one.sas"),
                        (io.BytesIO(b"DATA two; RUN;"), "two.sas"),
                    ],
                },
                headers={"X-Session-Token": "upload-token"},
                content_type="multipart/form-data",
            )
            assert response.status_code == 400
            assert "Too many files" in response.get_json()["error"]
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)

    def test_upload_rejects_file_over_per_file_limit(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.GRAPH_MODULES_AVAILABLE", True)
        monkeypatch.setattr("backend.app.MAX_SAS_FILE_SIZE_BYTES", 10, raising=False)
        from backend.app import sessions

        session_id = "file-too-large"
        temp_dir = tempfile.mkdtemp()
        sessions[session_id] = {
            "session_id": session_id,
            "session_token": "upload-token",
            "temp_dir": temp_dir,
            "sas_files": [],
            "status": "initialized",
            "created_at": datetime.now(),
        }
        try:
            response = client.post(
                "/api/graph-migrate/upload",
                data={
                    "session_id": session_id,
                    "files[]": (io.BytesIO(b"DATA test; value = 1; RUN;"), "test.sas"),
                },
                headers={"X-Session-Token": "upload-token"},
                content_type="multipart/form-data",
            )
            assert response.status_code == 413
            assert "File too large" in response.get_json()["error"]
        finally:
            sessions.pop(session_id, None)
            __import__("shutil").rmtree(temp_dir, ignore_errors=True)


@pytest.mark.security
class TestErrorMessages:
    def test_analyze_does_not_leak_internal_details(self, app, monkeypatch):
        monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
        client = app.test_client()
        response = client.post(
            "/api/graph/analyze",
            data={"file": (io.BytesIO(b"invalid content"), "test.sas")},
            content_type="multipart/form-data",
        )
        from backend.app import GRAPH_MODULES_AVAILABLE

        if not GRAPH_MODULES_AVAILABLE:
            assert response.status_code == 503
        else:
            # With the built-in AST fallback, arbitrary bytes may parse as an empty
            # program and return 200; failures should still avoid leaking tracebacks.
            assert response.status_code in (200, 400, 500)
            raw = str(response.get_json())
            assert "Traceback" not in raw
            if response.status_code != 200:
                data = response.get_json()
                assert "error" in data
                assert "Traceback" not in str(data.get("error", ""))

    def test_initialize_does_not_leak_details(self, no_auth_client, monkeypatch):
        monkeypatch.setenv("GRAPH_MODULES_AVAILABLE", "false")
        response = no_auth_client.post(
            "/api/graph-migrate/initialize",
            data=json.dumps({"model": "invalid" * 10000}),
            content_type="application/json",
        )
        if response.status_code == 500:
            data = response.get_json()
            assert data["error"] == "Initialization failed"
            assert "Traceback" not in data["error"]
