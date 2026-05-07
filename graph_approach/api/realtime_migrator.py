"""
Realtime Migrator

Wrapper around GraphMigrator that emits events for real-time UI updates.
"""

from typing import Callable, Optional, Dict, Any, List
from pathlib import Path
import time

from graph_approach.migration.graph_migrator import GraphMigrator, MigrationResult
from graph_approach.core.graph_builder import GraphBuilder
from graph_approach.core.chunk_optimizer import ChunkOptimizer, Chunk
from graph_approach.core.schema_tracker import ExecutionContext, SchemaInferencer
from graph_approach.api.graph_exporter import GraphExporter
from graph_approach.api.schema_exporter import SchemaExporter


class RealtimeMigrator:
    """
    Migration wrapper that emits real-time events

    Events:
    - phase_start: {'phase': int, 'name': str, 'description': str}
    - phase_complete: {'phase': int, 'duration': float}
    - graph_built: {'graph_json': dict, 'stats': dict}
    - chunks_generated: {'chunks': list, 'stats': dict}
    - chunk_start: {'chunk_id': str, 'index': int, 'total': int}
    - chunk_complete: {'chunk_id': str, 'success': bool, 'code': str}
    - chunk_error: {'chunk_id': str, 'error': str}
    - schema_update: {'schemas': dict}
    - reconciliation_start: {'total_chunks': int}
    - reconciliation_complete: {'final_code': str}
    - migration_complete: {'result': dict}
    - migration_error: {'error': str}
    """

    def __init__(
        self,
        migrator: GraphMigrator,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """
        Initialize realtime migrator

        Args:
            migrator: GraphMigrator instance
            event_callback: Callback function(event_name, event_data)
        """
        self.migrator = migrator
        self.event_callback = event_callback

    def emit_event(self, event_name: str, event_data: Dict[str, Any]):
        """Emit event to callback"""
        if self.event_callback:
            try:
                self.event_callback(event_name, event_data)
            except Exception as e:
                print(f"Error in event callback: {e}")

    def migrate_file_with_events(
        self,
        sas_file_path: str,
        output_dir: str,
        visualize: bool = False
    ) -> MigrationResult:
        """
        Migrate file with real-time event emissions

        Args:
            sas_file_path: Path to SAS file
            output_dir: Output directory
            visualize: Whether to generate visualizations

        Returns:
            MigrationResult
        """
        phase_start_times = {}

        try:
            # Phase 1: Build dependency graph
            self._emit_phase_start(1, "Graph Building", "Parsing SAS code and extracting dependencies")
            phase_start_times[1] = time.time()

            builder = GraphBuilder.from_file(sas_file_path)
            graph = builder.build_graph()
            summary = builder.get_summary()

            # Export graph to JSON
            graph_json = GraphExporter.to_react_flow_format(graph)

            self.emit_event('graph_built', {
                'graph': graph_json,
                'stats': summary
            })

            self._emit_phase_complete(1, time.time() - phase_start_times[1])

            # Phase 2: Generate chunks
            self._emit_phase_start(2, "Chunk Optimization", "Grouping nodes into optimal chunks")
            phase_start_times[2] = time.time()

            optimizer = ChunkOptimizer(graph)
            chunks = optimizer.generate_chunks()

            chunks_data = self._export_chunks(chunks)
            self.emit_event('chunks_generated', {
                'chunks': chunks_data,
                'stats': {
                    'total_chunks': len(chunks),
                    'total_tokens': sum(c['estimated_tokens'] for c in chunks_data),
                    'avg_tokens': sum(c['estimated_tokens'] for c in chunks_data) / len(chunks_data) if chunks_data else 0
                }
            })

            self._emit_phase_complete(2, time.time() - phase_start_times[2])

            # Phase 3: Initialize context
            self._emit_phase_start(3, "Context Enrichment", "Initializing execution context and schemas")
            phase_start_times[3] = time.time()

            execution_context = ExecutionContext()
            schema_inferencer = SchemaInferencer()

            # Initialize context (simplified - actual implementation would be more complex)
            self._emit_schema_update(execution_context)

            self._emit_phase_complete(3, time.time() - phase_start_times[3])

            # Phase 4: Convert chunks
            self._emit_phase_start(4, "LLM Conversion", "Converting chunks to PySpark")
            phase_start_times[4] = time.time()

            converted_chunks = []
            for i, chunk in enumerate(chunks):
                self.emit_event('chunk_start', {
                    'chunk_id': chunk.chunk_id,
                    'index': i + 1,
                    'total': len(chunks),
                    'source_code': chunk.source_code,
                    'estimated_tokens': chunk.estimated_tokens
                })

                try:
                    # Actual conversion would happen here via migrator
                    # For now, we'll simulate the event structure
                    chunk_result = {
                        'chunk_id': chunk.chunk_id,
                        'source_code': chunk.source_code
                    }
                    converted_chunks.append(chunk_result)

                    self.emit_event('chunk_complete', {
                        'chunk_id': chunk.chunk_id,
                        'success': True,
                        'index': i + 1,
                        'total': len(chunks)
                    })

                except Exception as e:
                    self.emit_event('chunk_error', {
                        'chunk_id': chunk.chunk_id,
                        'error': str(e)
                    })

            self._emit_phase_complete(4, time.time() - phase_start_times[4])

            # Phase 5: Reconciliation
            self._emit_phase_start(5, "Code Reconciliation", "Integrating chunks into final script")
            phase_start_times[5] = time.time()

            self.emit_event('reconciliation_start', {
                'total_chunks': len(converted_chunks)
            })

            # Call actual migrator
            result = self.migrator.migrate_file(
                sas_file_path=sas_file_path,
                output_dir=output_dir,
                visualize=visualize
            )

            self.emit_event('reconciliation_complete', {
                'final_code': result.pyspark_code[:500] + "..." if len(result.pyspark_code) > 500 else result.pyspark_code,
                'total_lines': len(result.pyspark_code.split('\n')) if result.pyspark_code else 0
            })

            self._emit_phase_complete(5, time.time() - phase_start_times[5])

            # Emit final result
            self.emit_event('migration_complete', {
                'result': result.to_dict()
            })

            return result

        except Exception as e:
            self.emit_event('migration_error', {
                'error': str(e),
                'phase': len(phase_start_times) + 1
            })
            raise

    def _emit_phase_start(self, phase: int, name: str, description: str):
        """Emit phase start event"""
        self.emit_event('phase_start', {
            'phase': phase,
            'name': name,
            'description': description
        })

    def _emit_phase_complete(self, phase: int, duration: float):
        """Emit phase complete event"""
        self.emit_event('phase_complete', {
            'phase': phase,
            'duration': duration
        })

    def _emit_schema_update(self, context: ExecutionContext):
        """Emit schema update event"""
        schemas = SchemaExporter.export_execution_context(context)
        self.emit_event('schema_update', {
            'schemas': schemas
        })

    def _export_chunks(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """Export chunks to JSON format"""
        chunks_data = []
        for chunk in chunks:
            chunk_data = {
                'chunk_id': chunk.chunk_id,
                'estimated_tokens': chunk.estimated_tokens,
                'layer': chunk.layer,
                'node_count': len(chunk.nodes),
                'has_macros': chunk.context.get('has_macros', False),
                'has_data_steps': chunk.context.get('has_data_steps', False),
                'has_procs': chunk.context.get('has_procs', False),
                'dependencies': list(chunk.dependencies),
                'source_preview': chunk.source_code[:200] + "..." if len(chunk.source_code) > 200 else chunk.source_code
            }
            chunks_data.append(chunk_data)
        return chunks_data
