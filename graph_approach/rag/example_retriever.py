"""
Example Retriever

Retrieves and formats relevant migration examples for LLM prompts.
"""

from typing import List, Dict, Any, Optional
from graph_approach.rag.pattern_store import PatternStore, MigrationPattern
from graph_approach.core.chunk_optimizer import Chunk
from graph_approach.core.dependency_graph import NodeType


class ExampleRetriever:
    """
    Retrieve relevant migration examples based on chunk characteristics

    Uses pattern store to find similar SAS code and format examples
    for inclusion in LLM prompts.
    """

    def __init__(self, pattern_store: PatternStore):
        """
        Initialize example retriever

        Args:
            pattern_store: Pattern store to retrieve from
        """
        self.pattern_store = pattern_store

    def get_relevant_examples(
        self,
        chunk: Chunk,
        max_examples: int = 3,
        min_similarity: float = 0.5
    ) -> List[MigrationPattern]:
        """
        Get relevant migration examples for a chunk

        Args:
            chunk: Chunk to find examples for
            max_examples: Maximum number of examples to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of relevant migration patterns
        """
        # Find similar patterns based on chunk source code
        patterns = self.pattern_store.find_similar_patterns(
            sas_code=chunk.source_code,
            n_results=max_examples,
            min_similarity=min_similarity
        )

        # Filter by chunk characteristics if available
        filtered_patterns = self._filter_by_chunk_type(chunk, patterns)

        return filtered_patterns[:max_examples]

    def _filter_by_chunk_type(
        self,
        chunk: Chunk,
        patterns: List[MigrationPattern]
    ) -> List[MigrationPattern]:
        """
        Filter patterns by chunk type relevance

        Args:
            chunk: Chunk context
            patterns: Candidate patterns

        Returns:
            Filtered and re-ranked patterns
        """
        # Determine chunk characteristics
        has_macros = chunk.context.get('has_macros', False)
        has_data_steps = chunk.context.get('has_data_steps', False)
        has_procs = chunk.context.get('has_procs', False)

        scored_patterns = []
        for pattern in patterns:
            relevance_score = pattern.similarity_score

            # Boost score if pattern category matches chunk type
            category = pattern.metadata.get('category', '')

            if has_macros and category == 'macro':
                relevance_score *= 1.2
            elif has_data_steps and category == 'data_step':
                relevance_score *= 1.2
            elif has_procs and category in ['proc', 'proc_sql']:
                relevance_score *= 1.2

            pattern.similarity_score = relevance_score
            scored_patterns.append(pattern)

        # Re-sort by updated scores
        scored_patterns.sort(key=lambda p: p.similarity_score, reverse=True)
        return scored_patterns

    def format_examples_for_prompt(
        self,
        examples: List[MigrationPattern],
        include_metadata: bool = False
    ) -> str:
        """
        Format examples for inclusion in LLM prompt

        Args:
            examples: List of migration patterns
            include_metadata: Whether to include metadata

        Returns:
            Formatted string for prompt
        """
        if not examples:
            return "No similar examples found."

        formatted = "## Similar Migration Examples\n\n"

        for i, example in enumerate(examples, 1):
            formatted += f"### Example {i} (Similarity: {example.similarity_score:.2f})\n\n"

            formatted += "**SAS Code:**\n```sas\n"
            formatted += example.sas_code
            formatted += "\n```\n\n"

            formatted += "**PySpark Code:**\n```python\n"
            formatted += example.pyspark_code
            formatted += "\n```\n\n"

            if include_metadata and example.metadata:
                formatted += f"**Metadata:** {example.metadata}\n\n"

            formatted += "---\n\n"

        return formatted

    def get_category_examples(
        self,
        category: str,
        max_examples: int = 2
    ) -> List[MigrationPattern]:
        """
        Get examples for a specific category (macro, data_step, proc, etc.)

        Args:
            category: Category to get examples for
            max_examples: Maximum number of examples

        Returns:
            List of patterns in that category
        """
        # For now, this requires iterating through all patterns
        # In production, could maintain category indexes
        all_patterns = []

        # Simple approach: try to find patterns with category in metadata
        # This is a placeholder - actual implementation depends on pattern_store structure
        # Could be enhanced with category indexes

        return all_patterns[:max_examples]

    def get_examples_by_complexity(
        self,
        chunk: Chunk,
        complexity_level: str = "similar",
        max_examples: int = 3
    ) -> List[MigrationPattern]:
        """
        Get examples based on complexity level

        Args:
            chunk: Chunk to compare
            complexity_level: "simple", "similar", or "complex"
            max_examples: Maximum examples

        Returns:
            List of patterns
        """
        # Estimate chunk complexity
        chunk_complexity = self._estimate_complexity(chunk)

        # Get similar patterns
        patterns = self.pattern_store.find_similar_patterns(
            sas_code=chunk.source_code,
            n_results=max_examples * 2  # Get more to filter
        )

        # Filter by complexity
        filtered = []
        for pattern in patterns:
            pattern_complexity = pattern.metadata.get('complexity', 'medium')

            if complexity_level == "simple" and pattern_complexity in ["low", "simple"]:
                filtered.append(pattern)
            elif complexity_level == "similar":
                filtered.append(pattern)  # Include all
            elif complexity_level == "complex" and pattern_complexity in ["high", "complex"]:
                filtered.append(pattern)

        return filtered[:max_examples]

    def _estimate_complexity(self, chunk: Chunk) -> str:
        """
        Estimate complexity of a chunk

        Args:
            chunk: Chunk to analyze

        Returns:
            Complexity level: "low", "medium", or "high"
        """
        # Simple heuristic based on token count and node types
        tokens = chunk.estimated_tokens
        node_types = chunk.context.get('node_types', [])

        if tokens < 200 and len(node_types) <= 2:
            return "low"
        elif tokens > 800 or len(node_types) > 5:
            return "high"
        else:
            return "medium"

    def create_example_context(
        self,
        chunk: Chunk,
        max_examples: int = 3
    ) -> Dict[str, Any]:
        """
        Create comprehensive example context for a chunk

        Args:
            chunk: Chunk to create context for
            max_examples: Maximum examples to include

        Returns:
            Dictionary with examples and metadata
        """
        examples = self.get_relevant_examples(
            chunk=chunk,
            max_examples=max_examples
        )

        formatted_examples = self.format_examples_for_prompt(examples)

        return {
            "examples": [e.to_dict() for e in examples],
            "formatted_text": formatted_examples,
            "num_examples": len(examples),
            "avg_similarity": (
                sum(e.similarity_score for e in examples) / len(examples)
                if examples else 0.0
            )
        }
