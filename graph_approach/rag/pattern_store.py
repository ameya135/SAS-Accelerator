"""
Pattern Store

Stores and retrieves migration patterns using ChromaDB for RAG.
Learns from successful SAS to PySpark conversions.
"""

import os
import re
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: chromadb not installed. Pattern store will use fallback mode.")


@dataclass
class MigrationPattern:
    """
    A stored migration pattern

    Attributes:
        pattern_id: Unique identifier
        sas_code: Original SAS code
        pyspark_code: Converted PySpark code
        metadata: Additional metadata (complexity, category, etc.)
        similarity_score: Similarity score (when retrieved)
    """

    pattern_id: str
    sas_code: str
    pyspark_code: str
    metadata: Dict[str, Any]
    similarity_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "pattern_id": self.pattern_id,
            "sas_code": self.sas_code,
            "pyspark_code": self.pyspark_code,
            "metadata": self.metadata,
            "similarity_score": self.similarity_score,
        }


class PatternStore:
    """
    Store and retrieve migration patterns using ChromaDB

    Uses vector embeddings to find similar SAS code patterns
    and return their PySpark conversions.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize pattern store

        Args:
            db_path: Path to ChromaDB database directory
        """
        if db_path is None:
            # Default to data directory in graph_approach
            base_dir = Path(__file__).parent.parent
            db_path = str(base_dir / "data" / "chroma_db")

        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)

        if CHROMADB_AVAILABLE:
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(
                name="migration_patterns",
                metadata={"description": "SAS to PySpark migration patterns"},
            )
            self.fallback_mode = False
        else:
            # Fallback to simple in-memory storage
            self.collection = None
            self.patterns = {}
            self.fallback_mode = True
            print(f"PatternStore initialized in fallback mode (no ChromaDB)")

    def add_pattern(
        self,
        pattern_id: str,
        sas_code: str,
        pyspark_code: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a migration pattern to the store

        Args:
            pattern_id: Unique identifier for the pattern
            sas_code: Original SAS code
            pyspark_code: Converted PySpark code
            metadata: Additional metadata (category, complexity, etc.)
        """
        if metadata is None:
            metadata = {}

        if self.fallback_mode:
            self.patterns[pattern_id] = MigrationPattern(
                pattern_id=pattern_id,
                sas_code=sas_code,
                pyspark_code=pyspark_code,
                metadata=metadata,
            )
        else:
            # Add to ChromaDB
            self.collection.add(
                ids=[pattern_id],
                documents=[sas_code],
                metadatas=[{**metadata, "pyspark_code": pyspark_code}],
            )

    def find_similar_patterns(
        self, sas_code: str, n_results: int = 3, min_similarity: float = 0.5
    ) -> List[MigrationPattern]:
        """
        Find similar migration patterns

        Args:
            sas_code: SAS code to find similar patterns for
            n_results: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of similar patterns with similarity scores
        """
        if self.fallback_mode:
            return self._fallback_find_similar(sas_code, n_results)

        # Query ChromaDB
        results = self.collection.query(query_texts=[sas_code], n_results=n_results)

        patterns = []
        if results and results["ids"] and results["ids"][0]:
            for i, pattern_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if "distances" in results else 1.0
                # Convert distance to similarity (lower distance = higher similarity)
                similarity = 1.0 - min(distance, 1.0)

                if similarity >= min_similarity:
                    metadata = results["metadatas"][0][i]
                    pattern = MigrationPattern(
                        pattern_id=pattern_id,
                        sas_code=results["documents"][0][i],
                        pyspark_code=metadata.get("pyspark_code", ""),
                        metadata={
                            k: v for k, v in metadata.items() if k != "pyspark_code"
                        },
                        similarity_score=similarity,
                    )
                    patterns.append(pattern)

        return patterns

    def _fallback_find_similar(
        self, sas_code: str, n_results: int
    ) -> List[MigrationPattern]:
        """
        Fallback similarity search using simple string matching

        Args:
            sas_code: SAS code to match
            n_results: Number of results

        Returns:
            List of patterns (best effort)
        """
        # Simple keyword matching as fallback
        sas_lower = sas_code.lower()
        keywords = set(sas_lower.split())

        scored_patterns = []
        for pattern in self.patterns.values():
            pattern_keywords = set(pattern.sas_code.lower().split())
            # Jaccard similarity
            intersection = len(keywords & pattern_keywords)
            union = len(keywords | pattern_keywords)
            similarity = intersection / union if union > 0 else 0.0

            if similarity > 0:
                pattern.similarity_score = similarity
                scored_patterns.append(pattern)

        # Sort by similarity and return top N
        scored_patterns.sort(key=lambda p: p.similarity_score, reverse=True)
        return scored_patterns[:n_results]

    def initialize_with_examples(
        self, migration_guide_path: Optional[str] = None
    ) -> int:
        """
        Initialize pattern store with examples from migration guide

        Args:
            migration_guide_path: Path to migration guide file

        Returns:
            Number of patterns added
        """
        if migration_guide_path is None:
            # Try to find migration guide in parent directory
            base_dir = Path(__file__).parent.parent.parent
            migration_guide_path = str(base_dir / "SAS_to_pyspark_migration_guide.md")

        if not os.path.exists(migration_guide_path):
            print(f"Migration guide not found at {migration_guide_path}")
            return 0

        # Parse migration guide for examples
        patterns_added = self._parse_migration_guide(migration_guide_path)
        print(
            f"Initialized pattern store with {patterns_added} examples from migration guide"
        )
        return patterns_added

    def _parse_migration_guide(self, guide_path: str) -> int:
        """
        Parse migration guide to extract SAS/PySpark example pairs

        Args:
            guide_path: Path to migration guide

        Returns:
            Number of patterns extracted
        """
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract code blocks
        # Find SAS code blocks followed by PySpark code blocks
        sas_pattern = r"```sas\n(.*?)\n```"
        pyspark_pattern = r"```python\n(.*?)\n```"

        sas_blocks = re.findall(sas_pattern, content, re.DOTALL)
        pyspark_blocks = re.findall(pyspark_pattern, content, re.DOTALL)

        patterns_added = 0

        # Try to pair them up (simple heuristic: consecutive blocks)
        for i, sas_code in enumerate(sas_blocks):
            if i < len(pyspark_blocks):
                pyspark_code = pyspark_blocks[i]
                pattern_id = f"guide_example_{i + 1}"

                # Determine category from context
                category = "general"
                if "PROC SQL" in sas_code:
                    category = "proc_sql"
                elif "PROC" in sas_code:
                    category = "proc"
                elif "DATA" in sas_code:
                    category = "data_step"
                elif "%MACRO" in sas_code:
                    category = "macro"

                self.add_pattern(
                    pattern_id=pattern_id,
                    sas_code=sas_code.strip(),
                    pyspark_code=pyspark_code.strip(),
                    metadata={"source": "migration_guide", "category": category},
                )
                patterns_added += 1

        return patterns_added

    def get_pattern(self, pattern_id: str) -> Optional[MigrationPattern]:
        """
        Get a specific pattern by ID

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern if found, None otherwise
        """
        if self.fallback_mode:
            return self.patterns.get(pattern_id)

        result = self.collection.get(ids=[pattern_id])
        if result and result["ids"]:
            metadata = result["metadatas"][0]
            return MigrationPattern(
                pattern_id=pattern_id,
                sas_code=result["documents"][0],
                pyspark_code=metadata.get("pyspark_code", ""),
                metadata={k: v for k, v in metadata.items() if k != "pyspark_code"},
            )
        return None

    def count_patterns(self) -> int:
        """Get total number of patterns in store"""
        if self.fallback_mode:
            return len(self.patterns)
        return self.collection.count()

    def clear_patterns(self) -> None:
        """Clear all patterns (use with caution!)"""
        if self.fallback_mode:
            self.patterns.clear()
        else:
            # Delete and recreate collection
            self.client.delete_collection("migration_patterns")
            self.collection = self.client.create_collection("migration_patterns")

    def export_patterns(self, output_path: str) -> None:
        """
        Export patterns to JSON file

        Args:
            output_path: Path to output JSON file
        """

        if self.fallback_mode:
            patterns_dict = {pid: p.to_dict() for pid, p in self.patterns.items()}
        else:
            # Export from ChromaDB
            all_data = self.collection.get()
            patterns_dict = {}
            for i, pid in enumerate(all_data["ids"]):
                metadata = all_data["metadatas"][i]
                patterns_dict[pid] = {
                    "pattern_id": pid,
                    "sas_code": all_data["documents"][i],
                    "pyspark_code": metadata.get("pyspark_code", ""),
                    "metadata": {
                        k: v for k, v in metadata.items() if k != "pyspark_code"
                    },
                }

        with open(output_path, "w") as f:
            json.dump(patterns_dict, f, indent=2)

    def import_patterns(self, input_path: str) -> int:
        """
        Import patterns from JSON file

        Args:
            input_path: Path to JSON file

        Returns:
            Number of patterns imported
        """

        with open(input_path, "r") as f:
            patterns_dict = json.load(f)

        for pattern_data in patterns_dict.values():
            self.add_pattern(
                pattern_id=pattern_data["pattern_id"],
                sas_code=pattern_data["sas_code"],
                pyspark_code=pattern_data["pyspark_code"],
                metadata=pattern_data.get("metadata", {}),
            )

        return len(patterns_dict)

    def __str__(self) -> str:
        return f"PatternStore(patterns={self.count_patterns()}, mode={'fallback' if self.fallback_mode else 'chromadb'})"
