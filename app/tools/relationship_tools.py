"""
Relationship validation and dependency analysis tools.
These tools analyze foreign keys, relationships, and table dependencies.
"""

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.core.logger import get_logger
from app.schemas.input_schema import ColumnType, ProjectSchema
from app.schemas.validation_schema import (
    DependencyAnalysis,
    DependencyNode,
    ForeignKeyValidation,
    ValidationIssue,
    ValidationSeverity,
)

logger = get_logger(__name__)


class ForeignKeyCheckerInput(BaseModel):
    """Input schema for foreign key checker tool."""

    project_schema: dict = Field(..., description="Project schema as dictionary")


class ForeignKeyCheckerTool(BaseTool):
    """
    Tool for validating foreign key references.

    This tool checks:
    - Foreign key targets exist
    - Target columns exist
    - Target columns are valid references
    - Bidirectional relationships are consistent
    """

    name: str = "foreign_key_checker"
    description: str = """
    Validates all foreign key references in the schema.
    Checks that foreign key targets exist and are properly configured.

    Input: ProjectSchema as dictionary
    Output: ForeignKeyValidation report
    """
    args_schema: type[BaseModel] = ForeignKeyCheckerInput

    def _run(self, project_schema: dict) -> dict[str, Any]:
        """
        Validate foreign keys in the schema.

        Args:
            project_schema: ProjectSchema as dictionary

        Returns:
            dict: ForeignKeyValidation report
        """
        logger.info("Starting foreign key validation")

        try:
            schema = ProjectSchema.model_validate(project_schema)
            issues: list[ValidationIssue] = []
            foreign_keys: dict[str, list[str]] = {}

            # Build table and column lookup
            table_lookup = {table.table_name: table for table in schema.schema}
            column_lookup: dict[str, dict[str, Any]] = {}
            for table in schema.schema:
                column_lookup[table.table_name] = {
                    col.name: col for col in table.columns
                }

            # Check each table's foreign keys
            for table in schema.schema:
                table_fks: list[str] = []

                for column in table.columns:
                    if column.type == ColumnType.FOREIGN_KEY:
                        if not column.target:
                            continue  # Should be caught by Pydantic validation

                        # Parse target (format: table_name.column_name)
                        try:
                            target_table, target_column = column.target.split(".")
                        except ValueError:
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    message=f"Invalid foreign key target format: {column.target}",
                                    location=f"table: {table.table_name}, column: {column.name}",
                                    code="INVALID_FK_FORMAT",
                                )
                            )
                            continue

                        # Check if target table exists
                        if target_table not in table_lookup:
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    message=f"Foreign key references non-existent table: {target_table}",
                                    location=f"table: {table.table_name}, column: {column.name}",
                                    code="FK_TABLE_NOT_FOUND",
                                )
                            )
                            continue

                        # Check if target column exists
                        if target_column not in column_lookup[target_table]:
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.ERROR,
                                    message=f"Foreign key references non-existent column: {target_column}",
                                    location=f"table: {table.table_name}, column: {column.name} -> {target_table}.{target_column}",
                                    code="FK_COLUMN_NOT_FOUND",
                                )
                            )
                            continue

                        # Check if target column is a primary key or unique
                        target_col = column_lookup[target_table][target_column]
                        if not target_col.primary_key and not target_col.unique:
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.WARNING,
                                    message=f"Foreign key references column that is not primary key or unique",
                                    location=f"table: {table.table_name}, column: {column.name} -> {target_table}.{target_column}",
                                    code="FK_NOT_PK_OR_UNIQUE",
                                )
                            )

                        # Record valid foreign key
                        fk_ref = f"{column.name} -> {target_table}.{target_column}"
                        table_fks.append(fk_ref)

                if table_fks:
                    foreign_keys[table.table_name] = table_fks

            # Check relationship consistency
            self._check_relationship_consistency(schema, issues, table_lookup)

            # Determine validity
            has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)

            report = ForeignKeyValidation(
                valid=not has_errors,
                foreign_keys=foreign_keys,
                issues=issues,
            )

            logger.info(f"Foreign key validation complete: {'valid' if report.valid else 'invalid'}")
            return report.model_dump()

        except Exception as e:
            logger.error(f"Unexpected error during foreign key validation: {e}", exc_info=True)
            return ForeignKeyValidation(
                valid=False,
                foreign_keys={},
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Unexpected error: {str(e)}",
                        code="UNEXPECTED_ERROR",
                    )
                ],
            ).model_dump()

    async def _arun(self, project_schema: dict) -> dict[str, Any]:
        """Async version of _run."""
        return self._run(project_schema)

    def _check_relationship_consistency(
        self,
        schema: ProjectSchema,
        issues: list[ValidationIssue],
        table_lookup: dict[str, Any],
    ) -> None:
        """Check that relationships are bidirectional and consistent."""

        for table in schema.schema:
            for rel in table.relationships:
                # Check if target table exists
                if rel.target_table not in table_lookup:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Relationship references non-existent table: {rel.target_table}",
                            location=f"table: {table.table_name}, relationship: {rel.target_table}",
                            code="REL_TABLE_NOT_FOUND",
                        )
                    )
                    continue

                # Check if back_populates exists on target
                target_table = table_lookup[rel.target_table]
                back_rel = None
                for target_rel in target_table.relationships:
                    if (
                        target_rel.target_table == table.table_name
                        and target_rel.back_populates == table.table_name.lower()
                    ):
                        back_rel = target_rel
                        break

                if not back_rel:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Relationship may be missing back_populates on target table",
                            location=f"table: {table.table_name} -> {rel.target_table}",
                            code="MISSING_BACK_POPULATES",
                        )
                    )


class DependencyAnalyzerInput(BaseModel):
    """Input schema for dependency analyzer tool."""

    project_schema: dict = Field(..., description="Project schema as dictionary")


class DependencyAnalyzerTool(BaseTool):
    """
    Tool for analyzing table dependencies and determining build order.

    This tool:
    - Analyzes foreign key dependencies
    - Detects circular dependencies
    - Determines correct table creation order
    - Builds dependency graph
    """

    name: str = "dependency_analyzer"
    description: str = """
    Analyzes table dependencies based on foreign keys and determines the correct
    order for creating tables. Detects circular dependencies.

    Input: ProjectSchema as dictionary
    Output: DependencyAnalysis with build order and dependency graph
    """
    args_schema: type[BaseModel] = DependencyAnalyzerInput

    def _run(self, project_schema: dict) -> dict[str, Any]:
        """
        Analyze dependencies and determine build order.

        Args:
            project_schema: ProjectSchema as dictionary

        Returns:
            dict: DependencyAnalysis report
        """
        logger.info("Starting dependency analysis")

        try:
            schema = ProjectSchema.model_validate(project_schema)
            issues: list[ValidationIssue] = []

            # Build dependency graph
            dependency_graph: dict[str, list[str]] = {}
            table_names = [table.table_name for table in schema.schema]

            for table in schema.schema:
                dependencies = set()

                # Get dependencies from foreign keys
                for column in table.columns:
                    if column.type == ColumnType.FOREIGN_KEY and column.target:
                        target_table = column.target.split(".")[0]
                        # Don't add self-references to dependencies
                        if target_table != table.table_name:
                            dependencies.add(target_table)

                dependency_graph[table.table_name] = list(dependencies)

            logger.debug(f"Dependency graph: {dependency_graph}")

            # Detect cycles
            cycles = self._find_cycles(dependency_graph)

            if cycles:
                for cycle in cycles:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Circular dependency detected: {' -> '.join(cycle)} -> {cycle[0]}",
                            code="CIRCULAR_DEPENDENCY",
                        )
                    )

            # Determine build order (topological sort)
            build_order: list[str] = []
            if not cycles:
                build_order = self._topological_sort(dependency_graph, table_names)

                # Verify all tables are included
                if len(build_order) != len(table_names):
                    missing = set(table_names) - set(build_order)
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"Could not determine build order for tables: {', '.join(missing)}",
                            code="BUILD_ORDER_INCOMPLETE",
                        )
                    )

            report = DependencyAnalysis(
                valid=len(cycles) == 0,
                build_order=build_order,
                dependency_graph=dependency_graph,
                cycles=cycles,
                issues=issues,
            )

            logger.info(f"Dependency analysis complete: {'valid' if report.valid else 'invalid (cycles detected)'}")
            return report.model_dump()

        except Exception as e:
            logger.error(f"Unexpected error during dependency analysis: {e}", exc_info=True)
            return DependencyAnalysis(
                valid=False,
                build_order=[],
                dependency_graph={},
                cycles=[],
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Unexpected error: {str(e)}",
                        code="UNEXPECTED_ERROR",
                    )
                ],
            ).model_dump()

    async def _arun(self, project_schema: dict) -> dict[str, Any]:
        """Async version of _run."""
        return self._run(project_schema)

    def _find_cycles(self, graph: dict[str, list[str]]) -> list[list[str]]:
        """
        Find all cycles in the dependency graph using DFS.

        Args:
            graph: Dependency graph

        Returns:
            list: List of cycles found
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def _topological_sort(
        self, graph: dict[str, list[str]], all_nodes: list[str]
    ) -> list[str]:
        """
        Perform topological sort to determine build order.

        Args:
            graph: Dependency graph
            all_nodes: All table names

        Returns:
            list: Sorted list of table names in build order
        """
        # Calculate in-degree for each node
        in_degree = {node: 0 for node in all_nodes}
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1

        # Queue of nodes with no dependencies
        queue = [node for node in all_nodes if in_degree[node] == 0]
        result = []

        while queue:
            # Sort for deterministic output
            queue.sort()
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree for neighbors
            for neighbor in graph.get(node, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return result
