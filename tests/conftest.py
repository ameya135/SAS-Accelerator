import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


@pytest.fixture
def app():
    from backend.app import app as flask_app

    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def api_key():
    return "test-api-key-12345"


@pytest.fixture
def auth_client(client, api_key, monkeypatch):
    monkeypatch.setenv("SAS_ACCELERATOR_API_KEY", api_key)
    return client


@pytest.fixture
def no_auth_client(client, monkeypatch):
    monkeypatch.delenv("SAS_ACCELERATOR_API_KEY", raising=False)
    return client


@pytest.fixture
def sample_sas_code():
    return """/* Sample SAS code for testing */
LIBNAME mylib '/data/projects';

%LET max_rows = 1000;

DATA mylib.employees;
    SET mylib.raw_employees;
    WHERE salary > 50000;
    bonus = salary * 0.1;
    KEEP name salary bonus dept;
RUN;

PROC MEANS DATA=mylib.employees;
    VAR salary bonus;
    CLASS dept;
    OUTPUT OUT=mylib.summary MEAN=avg_salary avg_bonus;
RUN;

PROC SORT DATA=mylib.employees OUT=mylib.sorted_employees;
    BY DESCENDING salary;
RUN;
"""


@pytest.fixture
def sample_sas_file(sample_sas_code, tmp_path):
    sas_file = tmp_path / "test_sample.sas"
    sas_file.write_text(sample_sas_code)
    return str(sas_file)


@pytest.fixture
def temp_output_dir(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)
