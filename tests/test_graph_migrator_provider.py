"""Provider configuration tests for GraphMigrator."""

import pytest

from graph_approach.migration import graph_migrator as migrator_module
from graph_approach.migration.graph_migrator import GraphMigrator


class FakeClient:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.__class__.instances.append(self)


class FakeAsyncClient(FakeClient):
    instances = []


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content, finish_reason="stop"):
        self.message = FakeMessage(content)
        self.finish_reason = finish_reason


class FakeCompletion:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


@pytest.fixture(autouse=True)
def disable_dotenv(monkeypatch):
    monkeypatch.setattr(migrator_module, "load_dotenv", lambda: None)


@pytest.fixture(autouse=True)
def clear_fake_clients():
    FakeClient.instances = []
    FakeAsyncClient.instances = []


def test_openrouter_provider_uses_openai_compatible_clients(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)

    migrator = GraphMigrator(provider="openrouter", use_rag=False)

    assert migrator.provider == "openrouter"
    assert migrator.model == "qwen/qwen-2.5-coder-32b-instruct"
    assert migrator.base_url == "https://openrouter.ai/api/v1"
    assert FakeClient.instances[0].kwargs["api_key"] == "test-openrouter-key"
    assert FakeClient.instances[0].kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert FakeAsyncClient.instances[0].kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert migrator.code_reconciler.llm_model == migrator.model


def test_openrouter_provider_accepts_cli_overrides(monkeypatch):
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)

    migrator = GraphMigrator(
        provider="openrouter",
        api_key="cli-key",
        base_url="https://example.test/v1",
        model="google/gemini-2.0-flash-lite-001",
        use_rag=False,
    )

    assert migrator.provider == "openrouter"
    assert migrator.model == "google/gemini-2.0-flash-lite-001"
    assert FakeClient.instances[0].kwargs["api_key"] == "cli-key"
    assert FakeClient.instances[0].kwargs["base_url"] == "https://example.test/v1"


def test_openrouter_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OpenRouter API key not provided"):
        GraphMigrator(provider="openrouter", use_rag=False)


def test_azure_provider_keeps_existing_client_configuration(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-azure-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://azure.example.test/")
    monkeypatch.setattr(migrator_module, "AzureOpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncAzureOpenAI", FakeAsyncClient)

    migrator = GraphMigrator(provider="azure", use_rag=False)

    assert migrator.provider == "azure"
    assert migrator.model == "gpt-4"
    assert FakeClient.instances[0].kwargs["api_key"] == "test-azure-key"
    assert FakeClient.instances[0].kwargs["azure_endpoint"] == "https://azure.example.test/"
    assert FakeClient.instances[0].kwargs["api_version"] == "2024-08-01-preview"


def test_openrouter_disables_response_format_by_default(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)

    migrator = GraphMigrator(provider="openrouter", use_rag=False)
    response_format = migrator._migration_response_format()

    assert response_format == {}


def test_openrouter_json_schema_can_be_enabled(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("OPENROUTER_RESPONSE_FORMAT", "json_schema")
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)

    migrator = GraphMigrator(provider="openrouter", use_rag=False)
    response_format = migrator._migration_response_format()

    assert response_format["type"] == "json_schema"
    schema = response_format["json_schema"]["schema"]
    assert set(schema["properties"]) == {
        "pyspark_code_lines",
        "mapping",
        "variables_created",
    }
    assert schema["required"] == list(schema["properties"])
    assert schema["additionalProperties"] is False


def test_parse_migration_response_accepts_markdown_wrapped_json(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)
    migrator = GraphMigrator(provider="openrouter", use_rag=False)

    parsed = migrator._parse_migration_response(
        FakeCompletion(
            """```json
{"pyspark_code": "df = spark.table('x')", "mapping": ["a", "b"], "variables_created": ["df"]}
```"""
        )
    )

    assert parsed["pyspark_code"] == "df = spark.table('x')"
    assert parsed["mapping"] == "a\nb"
    assert parsed["variables_created"] == ["df"]


def test_parse_migration_response_accepts_pyspark_code_lines(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)
    migrator = GraphMigrator(provider="openrouter", use_rag=False)

    parsed = migrator._parse_migration_response(
        FakeCompletion(
            '{"pyspark_code_lines": ["line1", "line2"], "mapping": "ok", '
            '"variables_created": "df"}'
        )
    )

    assert parsed["pyspark_code"] == "line1\nline2"
    assert parsed["variables_created"] == ["df"]


def test_parse_migration_response_finds_json_after_prose_and_other_fences(
    monkeypatch,
):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)
    migrator = GraphMigrator(provider="openrouter", use_rag=False)

    parsed = migrator._parse_migration_response(
        FakeCompletion(
            """Here is an example:
```python
print("not json")
```
```json
{"pyspark_code_lines": ["df = spark.table('x')"], "mapping": "ok", "variables_created": ["df"]}
```"""
        )
    )

    assert parsed["pyspark_code"] == "df = spark.table('x')"


def test_parse_migration_response_rejects_prose_only(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)
    migrator = GraphMigrator(provider="openrouter", use_rag=False)

    with pytest.raises(ValueError, match="invalid JSON"):
        migrator._parse_migration_response(FakeCompletion("Certainly, here is code."))


def test_parse_migration_response_reports_empty_content(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)
    migrator = GraphMigrator(provider="openrouter", use_rag=False)

    with pytest.raises(ValueError, match="content was empty"):
        migrator._parse_migration_response(FakeCompletion(""))


def test_openrouter_chat_kwargs_use_system_json_contract(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)
    migrator = GraphMigrator(provider="openrouter", use_rag=False)

    kwargs = migrator._chat_kwargs("convert this")

    assert kwargs["messages"][0]["role"] == "system"
    assert "raw JSON object" in kwargs["messages"][0]["content"]
    assert kwargs["messages"][1] == {"role": "user", "content": "convert this"}
    assert "response_format" not in kwargs
    assert kwargs["max_tokens"] == 12000


def test_chat_kwargs_accepts_max_tokens_override(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(migrator_module, "OpenAI", FakeClient)
    monkeypatch.setattr(migrator_module, "AsyncOpenAI", FakeAsyncClient)
    migrator = GraphMigrator(provider="openrouter", use_rag=False, max_tokens=4096)

    assert migrator._chat_kwargs("convert this")["max_tokens"] == 4096
