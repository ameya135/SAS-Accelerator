"""
API Module for Graph-Based Migration

Provides utilities for exporting migration data to web-friendly formats.
"""

from graph_approach.api.graph_exporter import GraphExporter
from graph_approach.api.schema_exporter import SchemaExporter

__all__ = ["GraphExporter", "SchemaExporter", "RealtimeMigrator"]


def __getattr__(name):
    if name == "RealtimeMigrator":
        from graph_approach.api.realtime_migrator import RealtimeMigrator

        return RealtimeMigrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
