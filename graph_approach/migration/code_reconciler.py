"""
Code Reconciler

Reconciles multiple converted chunks into a single, coherent PySpark script.
Deduplicates imports, resolves variable conflicts, validates syntax,
and ensures proper execution order.
"""

import re
from typing import List, Dict, Set, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from graph_approach.migration.variable_tracker import VariableTracker, ValidationResult


@dataclass
class ReconciliationResult:
    """Result of code reconciliation"""
    code: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    fixes_applied: List[str] = field(default_factory=list)
    validation_report: str = ""


@dataclass
class CodeBlock:
    """Represents a block of code with metadata"""
    code: str
    chunk_id: str = ""
    defines: Set[str] = field(default_factory=set)  # Variables defined in this block
    uses: Set[str] = field(default_factory=set)     # Variables used in this block
    line_count: int = 0
    
    def __post_init__(self):
        self.line_count = len(self.code.split('\n'))


class CodeReconciler:
    """
    Reconcile converted chunks into clean, working PySpark code

    Handles:
    - Import deduplication
    - Variable name consistency
    - Removing placeholder/empty chunks
    - Data flow validation
    - Code cleanup
    - Variable lifecycle validation
    - Execution order optimization
    - Duplicate definition removal
    """

    def __init__(
        self,
        use_llm: bool = True,
        llm_client: Optional[Any] = None,
        llm_model: str = "gpt-4",
    ):
        """
        Initialize reconciler

        Args:
            use_llm: Whether to use LLM for final cleanup
            llm_client: OpenAI-compatible client for cleanup
            llm_model: Model name to use for cleanup
        """
        self.use_llm = use_llm
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.variable_tracker = VariableTracker()
        
        # Pattern for detecting DataFrame definitions
        self.df_definition_pattern = re.compile(
            r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*(?:_df)?)\s*=\s*\(',
            re.MULTILINE
        )

    def reconcile_chunks(
        self,
        converted_chunks: List[Dict[str, Any]],
        execution_context: Any,
        sas_macro_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Reconcile all chunks into single cohesive script

        Args:
            converted_chunks: List of converted chunk dictionaries
            execution_context: Execution context with variable mappings
            sas_macro_vars: Optional macro variable initialization code

        Returns:
            Clean, integrated PySpark code
        """
        # Step 0: Reassemble cAST sub-chunks before main reconciliation
        converted_chunks = self._reassemble_cast_chunks(converted_chunks)

        # Step 1: Filter out empty/placeholder chunks
        valid_chunks = self._filter_valid_chunks(converted_chunks)

        # Step 2: Extract and deduplicate imports
        all_imports = self._extract_imports(valid_chunks)
        unique_imports = self._deduplicate_imports(all_imports)

        # Step 3: Analyze variable usage and create mappings
        variable_map = self._build_variable_mapping(valid_chunks, execution_context)

        # Step 4: Extract code blocks (excluding imports)
        code_blocks = self._extract_code_blocks_with_metadata(valid_chunks)

        # Step 5: Apply variable name consistency
        code_blocks = self._apply_variable_mapping_to_blocks(code_blocks, variable_map)

        # Step 6: Remove duplicate definitions (keep most complete)
        code_blocks = self._remove_duplicate_definitions(code_blocks)

        # Step 7: Reorder blocks for proper execution order
        code_blocks = self._reorder_blocks(code_blocks)

        # Step 8: Assemble initial script
        initial_code = self._assemble_script(
            unique_imports, 
            [b.code for b in code_blocks],
            sas_macro_vars
        )

        # Step 9: Validate and fix variable issues
        validated_code, fixes = self._validate_and_fix_code(initial_code)

        # Step 10: Optional LLM-based cleanup (with chunking for large files)
        if self.use_llm and self.llm_client:
            validated_code = self._llm_cleanup_smart(validated_code)

        return validated_code

    def reconcile_chunks_with_report(
        self,
        converted_chunks: List[Dict[str, Any]],
        execution_context: Any,
        sas_macro_vars: Optional[Dict[str, str]] = None
    ) -> ReconciliationResult:
        """
        Reconcile chunks and return detailed report

        Args:
            converted_chunks: List of converted chunk dictionaries
            execution_context: Execution context with variable mappings
            sas_macro_vars: Optional macro variable initialization code

        Returns:
            ReconciliationResult with code and detailed report
        """
        result = ReconciliationResult(code="")
        
        try:
            # Step 0: Reassemble cAST sub-chunks
            original_count = len(converted_chunks)
            converted_chunks = self._reassemble_cast_chunks(converted_chunks)
            reassembled = original_count - len(converted_chunks)
            if reassembled > 0:
                result.fixes_applied.append(f"Reassembled {reassembled} cAST sub-chunks into parent chunks")

            # Step 1: Filter out empty/placeholder chunks
            valid_chunks = self._filter_valid_chunks(converted_chunks)
            result.fixes_applied.append(f"Filtered to {len(valid_chunks)} valid chunks from {len(converted_chunks)} total")

            # Step 2: Extract and deduplicate imports
            all_imports = self._extract_imports(valid_chunks)
            unique_imports = self._deduplicate_imports(all_imports)
            result.fixes_applied.append(f"Deduplicated imports: {len(all_imports)} -> {len(unique_imports)}")

            # Step 3: Analyze variable usage
            variable_map = self._build_variable_mapping(valid_chunks, execution_context)
            if variable_map:
                result.fixes_applied.append(f"Created {len(variable_map)} variable name mappings")

            # Step 4: Extract code blocks
            code_blocks = self._extract_code_blocks_with_metadata(valid_chunks)

            # Step 5: Apply variable name consistency
            code_blocks = self._apply_variable_mapping_to_blocks(code_blocks, variable_map)

            # Step 6: Remove duplicate definitions
            original_count = len(code_blocks)
            code_blocks = self._remove_duplicate_definitions(code_blocks)
            if len(code_blocks) < original_count:
                result.fixes_applied.append(f"Removed {original_count - len(code_blocks)} duplicate code blocks")

            # Step 7: Reorder blocks
            code_blocks = self._reorder_blocks(code_blocks)
            result.fixes_applied.append("Reordered code blocks for proper execution order")

            # Step 8: Assemble script
            initial_code = self._assemble_script(
                unique_imports,
                [b.code for b in code_blocks],
                sas_macro_vars
            )

            # Step 9: Validate and fix (may run multiple times)
            validated_code, fixes = self._validate_and_fix_code(initial_code)
            result.fixes_applied.extend(fixes)

            # Step 10: Get validation report (use fresh tracker to avoid duplicate issues)
            fresh_tracker = VariableTracker()
            validation_result = fresh_tracker.analyze_code(validated_code)
            result.validation_report = fresh_tracker.generate_validation_report()
            
            # Collect warnings and errors (only from second analysis)
            for issue in validation_result.issues:
                # Skip issues that we've already auto-fixed with placeholders
                if 'placeholder' in str(result.fixes_applied).lower() and issue.issue_type == 'undefined':
                    # Move to warnings instead of errors since we added placeholders
                    result.warnings.append(f"Line {issue.line_number}: {issue.message} (placeholder added)")
                elif issue.severity == 'error':
                    result.errors.append(f"Line {issue.line_number}: {issue.message}")
                elif issue.severity == 'warning':
                    result.warnings.append(f"Line {issue.line_number}: {issue.message}")

            # Step 11: LLM cleanup
            if self.use_llm and self.llm_client:
                validated_code = self._llm_cleanup_smart(validated_code)
                result.fixes_applied.append("Applied LLM-based code cleanup")

            result.code = validated_code

        except Exception as e:
            result.errors.append(f"Reconciliation failed: {str(e)}")
            import traceback
            result.errors.append(traceback.format_exc())

        return result

    def _reassemble_cast_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reassemble cAST sub-chunks back into their parent chunks.

        Groups sub-chunks by parent_node_id, orders by part_index,
        and merges their converted PySpark code. This prevents duplicate
        imports and inconsistent variable names across sub-chunks of the
        same construct.
        """
        regular_chunks = []
        cast_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for chunk in chunks:
            if chunk.get('cast_split'):
                parent_id = chunk.get('parent_node_id', '')
                if parent_id:
                    cast_groups[parent_id].append(chunk)
                else:
                    regular_chunks.append(chunk)
            else:
                regular_chunks.append(chunk)

        if not cast_groups:
            return chunks

        # Reassemble each group
        for parent_id, group in cast_groups.items():
            # Sort by part_index
            group.sort(key=lambda c: c.get('part_index', 0))

            # Merge PySpark code
            merged_code_parts = []
            merged_mapping_parts = []
            all_variables = []

            for part in group:
                code = part.get('pyspark_code', '').strip()
                if code:
                    merged_code_parts.append(code)
                mapping = part.get('mapping', '').strip()
                if mapping:
                    merged_mapping_parts.append(mapping)
                all_variables.extend(part.get('variables_created', []))

            # Deduplicate imports across sub-chunks
            merged_code = '\n\n'.join(merged_code_parts)
            lines = merged_code.split('\n')
            seen_imports = set()
            deduped_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    if stripped not in seen_imports:
                        seen_imports.add(stripped)
                        deduped_lines.append(line)
                else:
                    deduped_lines.append(line)

            reassembled = {
                'chunk_id': f"{parent_id}_reassembled",
                'pyspark_code': '\n'.join(deduped_lines),
                'mapping': '\n---\n'.join(merged_mapping_parts),
                'variables_created': list(dict.fromkeys(all_variables)),  # Dedupe preserving order
            }
            regular_chunks.append(reassembled)

        return regular_chunks

    def _filter_valid_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out empty or placeholder chunks"""
        valid = []

        for chunk in chunks:
            code = chunk.get('pyspark_code', '').strip()

            # Skip if empty
            if not code:
                continue

            # Skip if just comments or placeholders
            lines = [line.strip() for line in code.split('\n') if line.strip()]
            code_lines = [l for l in lines if not l.startswith('#')]

            if not code_lines:
                continue

            # Skip placeholder chunks
            placeholders = [
                'no sas code was provided',
                'please provide sas code',
                'no code to convert',
                'placeholder',
                'todo: implement'
            ]
            if any(p in code.lower() for p in placeholders):
                continue

            valid.append(chunk)

        return valid

    def _extract_imports(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract all import statements"""
        imports = []

        for chunk in chunks:
            code = chunk.get('pyspark_code', '')
            for line in code.split('\n'):
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line)

        return imports

    def _deduplicate_imports(self, imports: List[str]) -> List[str]:
        """Deduplicate and organize imports"""
        # Categorize imports
        from_imports = defaultdict(set)
        standard_imports = set()

        for imp in imports:
            imp = imp.strip()
            if imp.startswith('from '):
                # Parse: from X import Y, Z
                match = re.match(r'from\s+(\S+)\s+import\s+(.+)', imp)
                if match:
                    module = match.group(1)
                    items = match.group(2)
                    # Split on commas and clean
                    for item in items.split(','):
                        item = item.strip()
                        # Handle "as" aliases
                        from_imports[module].add(item)
            elif imp.startswith('import '):
                standard_imports.add(imp)

        # Reconstruct unique imports
        unique = []

        # Standard imports first (sorted)
        for imp in sorted(standard_imports):
            unique.append(imp)

        # From imports, combined (sorted by module)
        for module in sorted(from_imports.keys()):
            items = sorted(from_imports[module])
            items_str = ', '.join(items)
            unique.append(f"from {module} import {items_str}")

        return unique

    def _build_variable_mapping(
        self,
        chunks: List[Dict[str, Any]],
        execution_context: Any
    ) -> Dict[str, str]:
        """
        Build consistent variable naming mapping

        Strategy:
        1. Find most commonly used name for each dataset
        2. Prefer shorter, clearer names
        3. Use execution context mappings
        """
        # Track all variable assignments
        var_usage = defaultdict(lambda: defaultdict(int))

        for chunk in chunks:
            code = chunk.get('pyspark_code', '')

            # Find DataFrame assignments: var_name = ...
            assignments = re.findall(r'(\w+)\s*=\s*[^=]', code)
            for var in assignments:
                if '_df' in var or 'DataFrame' in var or var.endswith('_data'):
                    var_usage[var][var] += 1

            # Find DataFrame references
            for line in code.split('\n'):
                for var in list(var_usage.keys()):
                    if var in line:
                        var_usage[var][var] += 1

        # Build mapping: choose canonical name for related variables
        mapping = {}

        # Group similar variable names
        groups = self._group_similar_variables(list(var_usage.keys()))

        for group in groups:
            if len(group) <= 1:
                continue
            # Choose best name from group
            canonical = self._choose_canonical_name(group, var_usage)

            for var in group:
                if var != canonical:
                    mapping[var] = canonical

        # Add execution context mappings
        if hasattr(execution_context, 'variable_name_map'):
            for old, new in execution_context.variable_name_map.items():
                if old not in mapping:
                    mapping[old] = new

        return mapping

    def _group_similar_variables(self, variables: List[str]) -> List[List[str]]:
        """Group similar variable names"""
        groups = []
        processed = set()

        for var in variables:
            if var in processed:
                continue

            # Find similar variables
            group = [var]
            base = var.replace('_df', '').replace('_data', '').replace('_dataset', '')

            for other in variables:
                if other == var or other in processed:
                    continue

                other_base = other.replace('_df', '').replace('_data', '').replace('_dataset', '')

                # Similar if bases match
                if base == other_base or base in other_base or other_base in base:
                    group.append(other)
                    processed.add(other)

            groups.append(group)
            processed.add(var)

        return groups

    def _choose_canonical_name(
        self,
        group: List[str],
        usage: Dict[str, Dict[str, int]]
    ) -> str:
        """Choose the best canonical name from a group"""
        # Prefer names ending in _df
        df_names = [n for n in group if n.endswith('_df')]
        if df_names:
            # Choose most used
            return max(df_names, key=lambda n: sum(usage.get(n, {}).values()))

        # Otherwise, choose most used
        return max(group, key=lambda n: sum(usage.get(n, {}).values()))

    def _extract_code_blocks_with_metadata(self, chunks: List[Dict[str, Any]]) -> List[CodeBlock]:
        """Extract code blocks with variable usage metadata"""
        blocks = []

        for chunk in chunks:
            code = chunk.get('pyspark_code', '')
            chunk_id = chunk.get('chunk_id', '')
            lines = []

            for line in code.split('\n'):
                # Skip imports
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    continue
                # Skip chunk markers
                if line.strip().startswith('# Chunk:'):
                    continue
                lines.append(line)

            block_code = '\n'.join(lines).strip()
            if not block_code:
                continue

            # Analyze what this block defines and uses
            defines = set()
            uses = set()

            # Find definitions (var = ...)
            def_matches = re.findall(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=]', block_code, re.MULTILINE)
            for _, var in def_matches:
                if not var.startswith('_'):
                    defines.add(var)

            # Find usages (var.method() or func(var))
            use_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*(?:_df)?)\b'
            all_vars = set(re.findall(use_pattern, block_code))
            
            # Filter to likely DataFrame usages
            ignore_keywords = {
                'if', 'else', 'elif', 'for', 'while', 'in', 'and', 'or', 'not',
                'True', 'False', 'None', 'return', 'def', 'class', 'import', 'from',
                'as', 'with', 'try', 'except', 'finally', 'raise', 'pass', 'break',
                'continue', 'lambda', 'yield', 'global', 'nonlocal', 'assert', 'del',
                'spark', 'F', 'T', 'Window', 'Row', 'lit', 'col', 'when', 'otherwise',
                'agg', 'sum', 'count', 'mean', 'avg', 'min', 'max', 'first', 'last',
                'round', 'floor', 'ceil', 'abs', 'sqrt', 'log', 'exp', 'pow',
                'StructType', 'StructField', 'StringType', 'IntegerType', 'DoubleType',
                'DateType', 'TimestampType', 'BooleanType', 'ArrayType', 'MapType',
                'SparkSession', 'DataFrame', 'Column'
            }
            
            for var in all_vars:
                if var not in ignore_keywords and var not in defines:
                    uses.add(var)

            blocks.append(CodeBlock(
                code=block_code,
                chunk_id=chunk_id,
                defines=defines,
                uses=uses
            ))

        return blocks

    def _apply_variable_mapping_to_blocks(
        self,
        blocks: List[CodeBlock],
        mapping: Dict[str, str]
    ) -> List[CodeBlock]:
        """Apply variable name mapping to code blocks"""
        if not mapping:
            return blocks

        updated_blocks = []

        for block in blocks:
            updated_code = block.code

            # Replace variables (word boundaries to avoid partial matches)
            for old_name, new_name in mapping.items():
                pattern = r'\b' + re.escape(old_name) + r'\b'
                updated_code = re.sub(pattern, new_name, updated_code)

            # Update defines and uses
            new_defines = {mapping.get(v, v) for v in block.defines}
            new_uses = {mapping.get(v, v) for v in block.uses}

            updated_blocks.append(CodeBlock(
                code=updated_code,
                chunk_id=block.chunk_id,
                defines=new_defines,
                uses=new_uses
            ))

        return updated_blocks

    def _remove_duplicate_definitions(self, blocks: List[CodeBlock]) -> List[CodeBlock]:
        """
        Remove duplicate DataFrame definitions, keeping the most complete version
        """
        # Track definitions by variable name
        var_definitions: Dict[str, List[Tuple[int, CodeBlock]]] = defaultdict(list)
        
        for idx, block in enumerate(blocks):
            # Look for main DataFrame assignments
            df_pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*(?:_df)?)\s*=\s*\('
            matches = re.findall(df_pattern, block.code, re.MULTILINE)
            
            for var_name in matches:
                var_definitions[var_name].append((idx, block))

        # Find blocks to remove (duplicates)
        blocks_to_remove = set()
        
        for var_name, defs in var_definitions.items():
            if len(defs) <= 1:
                continue
            
            # Keep the longest/most complete definition
            sorted_defs = sorted(defs, key=lambda x: len(x[1].code), reverse=True)
            
            # Mark all but the longest for removal
            for idx, _ in sorted_defs[1:]:
                # Only remove if the block ONLY defines this variable
                if len(blocks[idx].defines) <= 1:
                    blocks_to_remove.add(idx)

        # Filter out duplicate blocks
        return [b for i, b in enumerate(blocks) if i not in blocks_to_remove]

    def _reorder_blocks(self, blocks: List[CodeBlock]) -> List[CodeBlock]:
        """
        Reorder code blocks to ensure variables are defined before use
        """
        if not blocks:
            return blocks

        # Build dependency graph
        # block index -> set of block indices it depends on
        dependencies: Dict[int, Set[int]] = {i: set() for i in range(len(blocks))}
        
        # Map variable -> block index that defines it
        var_to_block: Dict[str, int] = {}
        for idx, block in enumerate(blocks):
            for var in block.defines:
                if var not in var_to_block:  # First definition wins
                    var_to_block[var] = idx

        # Build dependencies based on variable usage
        for idx, block in enumerate(blocks):
            for var in block.uses:
                if var in var_to_block:
                    dep_idx = var_to_block[var]
                    if dep_idx != idx:  # Don't depend on self
                        dependencies[idx].add(dep_idx)

        # Topological sort
        ordered = []
        visited = set()
        temp_visited = set()

        def visit(idx: int) -> bool:
            """Visit node for topological sort. Returns False if cycle detected."""
            if idx in temp_visited:
                return False  # Cycle detected
            if idx in visited:
                return True
            
            temp_visited.add(idx)
            for dep_idx in dependencies[idx]:
                if not visit(dep_idx):
                    return False
            temp_visited.remove(idx)
            visited.add(idx)
            ordered.append(idx)
            return True

        # Visit all nodes
        for idx in range(len(blocks)):
            if idx not in visited:
                if not visit(idx):
                    # Cycle detected, fall back to original order
                    return blocks

        # Return blocks in topological order
        return [blocks[idx] for idx in ordered]

    def _validate_and_fix_code(self, code: str) -> Tuple[str, List[str]]:
        """
        Validate code and apply automatic fixes
        
        Returns:
            Tuple of (fixed_code, list_of_fixes_applied)
        """
        # Use variable tracker to analyze and fix
        validation_result = self.variable_tracker.analyze_code(code)
        
        if validation_result.is_valid and not validation_result.macro_variables:
            return code, ["Code validation passed - no fixes needed"]
        
        # Apply fixes
        fixed_code, fixes = self.variable_tracker.suggest_fixes(code)
        
        return fixed_code, fixes

    def _assemble_script(
        self, 
        imports: List[str], 
        code_blocks: List[str],
        macro_vars_init: Optional[str] = None
    ) -> str:
        """Assemble final script"""
        parts = []

        # Header
        parts.append("# Generated PySpark code from SAS migration")
        parts.append("# Generated by Graph-Based Migration Tool")
        parts.append("")

        # Imports
        if imports:
            parts.extend(imports)
            parts.append("")

        # Initialize SparkSession
        parts.append("# Initialize Spark session")
        parts.append('spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()')
        parts.append("")

        # Add macro variable initialization if provided
        if macro_vars_init:
            parts.append(macro_vars_init)
            parts.append("")

        # Code blocks
        for i, block in enumerate(code_blocks):
            if i > 0:
                parts.append("")  # Blank line between blocks
            parts.append(block)

        return '\n'.join(parts)

    def _llm_cleanup_smart(self, code: str) -> str:
        """
        Use LLM to clean up code, with smart chunking for large files
        """
        if not self.llm_client:
            return code

        # Check if code is too large for single LLM call
        lines = code.split('\n')
        if len(lines) > 500:
            # Split into chunks and clean each
            return self._llm_cleanup_chunked(code)
        else:
            return self._llm_cleanup(code)

    def _llm_cleanup(self, code: str) -> str:
        """Use LLM to clean up and validate final code"""
        if not self.llm_client:
            return code

        prompt = f"""You are a PySpark code cleanup expert. The following PySpark code was generated from SAS migration but needs cleanup.

CURRENT CODE:
```python
{code}
```

Please clean up this code:
1. Remove any remaining duplicates or redundant code
2. Ensure variable names are consistent throughout
3. Fix any syntax errors
4. Ensure proper data flow (variables defined before use)
5. Add brief comments for major sections
6. Keep all business logic intact
7. Remove any 'del' statements that delete variables that are used later

Return ONLY the cleaned Python code, no explanations.

CLEANED CODE:
```python"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=8000
            )

            cleaned = response.choices[0].message.content.strip()

            # Extract code from markdown if present
            if '```python' in cleaned:
                cleaned = cleaned.split('```python')[1].split('```')[0].strip()
            elif '```' in cleaned:
                cleaned = cleaned.split('```')[1].split('```')[0].strip()

            return cleaned

        except Exception as e:
            print(f"LLM cleanup failed: {e}, returning original code")
            return code

    def _llm_cleanup_chunked(self, code: str) -> str:
        """Clean up large code files by processing in chunks"""
        if not self.llm_client:
            return code

        lines = code.split('\n')
        
        # Find natural break points (blank lines between code blocks)
        chunks = []
        current_chunk = []
        
        for line in lines:
            current_chunk.append(line)
            if not line.strip() and len(current_chunk) > 50:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        # If still too few chunks, split evenly
        if len(chunks) < 3:
            chunk_size = len(lines) // 3
            chunks = [
                '\n'.join(lines[:chunk_size]),
                '\n'.join(lines[chunk_size:2*chunk_size]),
                '\n'.join(lines[2*chunk_size:])
            ]

        # Clean each chunk
        cleaned_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"  Cleaning chunk {i+1}/{len(chunks)}...")
            
            prompt = f"""You are a PySpark code cleanup expert. Clean up this code section (part {i+1} of {len(chunks)}).

CODE SECTION:
```python
{chunk}
```

Clean up:
1. Fix syntax errors
2. Remove redundant code
3. Ensure consistent variable names
4. Keep all business logic intact

Return ONLY the cleaned Python code for this section:"""

            try:
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000
                )

                cleaned = response.choices[0].message.content.strip()
                if '```python' in cleaned:
                    cleaned = cleaned.split('```python')[1].split('```')[0].strip()
                elif '```' in cleaned:
                    cleaned = cleaned.split('```')[1].split('```')[0].strip()
                
                cleaned_chunks.append(cleaned)
            except Exception as e:
                print(f"    Chunk {i+1} cleanup failed: {e}")
                cleaned_chunks.append(chunk)

        return '\n\n'.join(cleaned_chunks)

    # Legacy method for backwards compatibility
    def _extract_code_blocks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract code blocks without imports (legacy method)"""
        blocks = self._extract_code_blocks_with_metadata(chunks)
        return [b.code for b in blocks]

    def _apply_variable_mapping(
        self,
        code_blocks: List[str],
        mapping: Dict[str, str]
    ) -> List[str]:
        """Apply variable name mapping to code (legacy method)"""
        if not mapping:
            return code_blocks

        updated_blocks = []

        for block in code_blocks:
            updated = block
            for old_name, new_name in mapping.items():
                pattern = r'\b' + re.escape(old_name) + r'\b'
                updated = re.sub(pattern, new_name, updated)
            updated_blocks.append(updated)

        return updated_blocks

    def _remove_duplicates(self, code_blocks: List[str]) -> List[str]:
        """Remove duplicate or very similar code blocks (legacy method)"""
        unique_blocks = []
        seen_signatures = set()

        for block in code_blocks:
            signature = self._get_code_signature(block)
            if signature not in seen_signatures:
                unique_blocks.append(block)
                seen_signatures.add(signature)

        return unique_blocks

    def _get_code_signature(self, code: str) -> str:
        """Get normalized signature of code block"""
        lines = []
        for line in code.split('\n'):
            line = line.strip()
            if '#' in line:
                line = line[:line.index('#')].strip()
            if line:
                lines.append(line)
        return '||'.join(lines)
