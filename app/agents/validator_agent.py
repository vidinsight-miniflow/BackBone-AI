"""
Validator Agent.

This agent validates generated code for quality, style, and correctness.
It runs multiple validation tools and aggregates the results.
"""

import time
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel

from app.agents.base_agent import BaseAgent
from app.core.logger import get_logger
from app.schemas.validator_schema import (
    CodeQualityMetrics,
    FileValidationResult,
    ValidationIssue,
    ValidationSeverityLevel,
    ValidatorAgentOutput,
)
from app.tools.validation_tools import (
    CodeLinter,
    CodeMetricsAnalyzer,
    ImportAnalyzer,
    PythonSyntaxChecker,
    SecurityScanner,
    TypeChecker,
)

logger = get_logger(__name__)


class ValidatorAgent(BaseAgent):
    """
    Agent for validating generated code quality.

    This agent orchestrates multiple validation tools to provide
    comprehensive code quality analysis including:
    - Syntax checking
    - Type checking (mypy)
    - Linting (ruff)
    - Security scanning
    - Code metrics
    - Import analysis
    """

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        enable_type_checking: bool = True,
        enable_linting: bool = True,
        enable_security_scan: bool = True,
        strict_mode: bool = False,
    ):
        """
        Initialize Validator Agent.

        Args:
            llm: Language model instance (optional, not used for validation)
            enable_type_checking: Enable mypy type checking
            enable_linting: Enable ruff linting
            enable_security_scan: Enable security scanning
            strict_mode: If True, treat warnings as errors
        """
        super().__init__(
            name="validator",
            llm=llm if llm else self._create_dummy_llm(),
            system_prompt="Code Quality Validator Agent",
        )

        self.enable_type_checking = enable_type_checking
        self.enable_linting = enable_linting
        self.enable_security_scan = enable_security_scan
        self.strict_mode = strict_mode

        # Initialize validation tools
        self.syntax_checker = PythonSyntaxChecker()
        self.type_checker = TypeChecker() if enable_type_checking else None
        self.linter = CodeLinter() if enable_linting else None
        self.security_scanner = SecurityScanner() if enable_security_scan else None
        self.metrics_analyzer = CodeMetricsAnalyzer()
        self.import_analyzer = ImportAnalyzer()

        logger.info(
            f"Validator Agent initialized ("
            f"type_checking={enable_type_checking}, "
            f"linting={enable_linting}, "
            f"security={enable_security_scan}, "
            f"strict={strict_mode})"
        )

    def _create_dummy_llm(self) -> Any:
        """Create a dummy LLM for non-LLM mode."""

        class DummyLLM:
            pass

        return DummyLLM()  # type: ignore

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code validation.

        Args:
            input_data: Dict with:
                - generated_files: Dict[str, str] (file_path -> content)

        Returns:
            dict: ValidatorAgentOutput as dictionary
        """
        generated_files = input_data.get("generated_files", {})

        if not generated_files:
            raise ValueError("Input must contain 'generated_files'")

        logger.info(f"Starting validation of {len(generated_files)} files")

        # Validate each file
        file_results: List[FileValidationResult] = []
        all_issues: List[ValidationIssue] = []

        for file_path, content in generated_files.items():
            logger.info(f"Validating: {file_path}")
            result = await self._validate_file(file_path, content)
            file_results.append(result)
            all_issues.extend(result.issues)

        # Calculate metrics
        metrics = self._calculate_metrics(file_results, generated_files)

        # Categorize issues
        errors = [i for i in all_issues if i.severity == ValidationSeverityLevel.ERROR]
        warnings = [
            i for i in all_issues if i.severity == ValidationSeverityLevel.WARNING
        ]
        suggestions = [
            i for i in all_issues if i.severity == ValidationSeverityLevel.INFO
        ]

        # Determine overall status
        has_errors = len(errors) > 0
        has_warnings = len(warnings) > 0

        if has_errors or (self.strict_mode and has_warnings):
            status = "failed"
            overall_passed = False
            summary = self._create_failed_summary(errors, warnings)
        elif has_warnings:
            status = "passed_with_warnings"
            overall_passed = True
            summary = self._create_warning_summary(warnings)
        else:
            status = "passed"
            overall_passed = True
            summary = "All validations passed! Code quality is excellent."

        output = ValidatorAgentOutput(
            status=status,
            summary=summary,
            overall_passed=overall_passed,
            file_results=file_results,
            metrics=metrics,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

        logger.info(
            f"Validation complete: {status} "
            f"(errors={len(errors)}, warnings={len(warnings)}, info={len(suggestions)})"
        )

        return output.model_dump()

    async def _validate_file(
        self, file_path: str, content: str
    ) -> FileValidationResult:
        """
        Validate a single file.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            FileValidationResult
        """
        issues: List[ValidationIssue] = []

        # 1. Syntax checking (always enabled)
        logger.debug(f"Running syntax check: {file_path}")
        syntax_issues = self.syntax_checker.check(file_path, content)
        issues.extend(syntax_issues)

        # If syntax errors, skip other checks
        if any(i.severity == ValidationSeverityLevel.ERROR for i in syntax_issues):
            logger.warning(f"Syntax errors found in {file_path}, skipping other checks")
            return FileValidationResult(
                file_path=file_path,
                passed=False,
                issues=issues,
                metrics={},
            )

        # 2. Type checking
        if self.type_checker:
            logger.debug(f"Running type check: {file_path}")
            type_issues = self.type_checker.check(file_path, content)
            issues.extend(type_issues)

        # 3. Linting
        if self.linter:
            logger.debug(f"Running linter: {file_path}")
            lint_issues = self.linter.check(file_path, content)
            issues.extend(lint_issues)

        # 4. Security scanning
        if self.security_scanner:
            logger.debug(f"Running security scan: {file_path}")
            security_issues = self.security_scanner.check(file_path, content)
            issues.extend(security_issues)

        # 5. Import analysis
        logger.debug(f"Running import analysis: {file_path}")
        import_issues = self.import_analyzer.check(file_path, content)
        issues.extend(import_issues)

        # 6. Code metrics
        logger.debug(f"Analyzing metrics: {file_path}")
        metrics = self.metrics_analyzer.analyze(file_path, content)

        # Check for high complexity
        if metrics.get("complexity", 0) > 20:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverityLevel.WARNING,
                    category="complexity",
                    message=f"High complexity score: {metrics['complexity']}",
                    file_path=file_path,
                    code="C901",
                    suggestion="Consider refactoring to reduce complexity",
                )
            )

        # Determine if file passed
        has_errors = any(i.severity == ValidationSeverityLevel.ERROR for i in issues)
        has_warnings = any(
            i.severity == ValidationSeverityLevel.WARNING for i in issues
        )
        passed = not has_errors and not (self.strict_mode and has_warnings)

        return FileValidationResult(
            file_path=file_path,
            passed=passed,
            issues=issues,
            metrics=metrics,
        )

    def _calculate_metrics(
        self,
        file_results: List[FileValidationResult],
        generated_files: Dict[str, str],
    ) -> CodeQualityMetrics:
        """
        Calculate overall code quality metrics.

        Args:
            file_results: Validation results for all files
            generated_files: Generated files dict

        Returns:
            CodeQualityMetrics
        """
        total_lines = 0
        total_complexity = 0
        total_errors = 0
        total_warnings = 0
        total_info = 0
        files_with_issues = 0

        for result in file_results:
            # Count issues
            for issue in result.issues:
                if issue.severity == ValidationSeverityLevel.ERROR:
                    total_errors += 1
                elif issue.severity == ValidationSeverityLevel.WARNING:
                    total_warnings += 1
                elif issue.severity == ValidationSeverityLevel.INFO:
                    total_info += 1

            if result.issues:
                files_with_issues += 1

            # Aggregate metrics
            total_lines += result.metrics.get("lines_of_code", 0)
            total_complexity += result.metrics.get("complexity", 0)

        # Calculate quality scores (0-100)
        maintainability_score = self._calculate_maintainability_score(
            total_errors, total_warnings, len(file_results)
        )

        return CodeQualityMetrics(
            total_lines=total_lines,
            total_files=len(generated_files),
            files_with_issues=files_with_issues,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_info=total_info,
            complexity_score=total_complexity / len(file_results)
            if file_results
            else 0,
            maintainability_score=maintainability_score,
        )

    def _calculate_maintainability_score(
        self, errors: int, warnings: int, num_files: int
    ) -> float:
        """
        Calculate maintainability score (0-100).

        Args:
            errors: Number of errors
            warnings: Number of warnings
            num_files: Number of files

        Returns:
            Score between 0 and 100
        """
        if num_files == 0:
            return 100.0

        # Start with perfect score
        score = 100.0

        # Deduct points for issues
        score -= errors * 10  # 10 points per error
        score -= warnings * 2  # 2 points per warning

        # Normalize by number of files
        score = max(0.0, score / num_files * num_files)

        return round(min(100.0, max(0.0, score)), 2)

    def _create_failed_summary(
        self, errors: List[ValidationIssue], warnings: List[ValidationIssue]
    ) -> str:
        """Create summary for failed validation."""
        summary_parts = [
            f"Validation failed with {len(errors)} error(s)",
        ]

        if warnings:
            summary_parts.append(f" and {len(warnings)} warning(s)")

        summary_parts.append(". Issues found:\n")

        # List top 3 errors
        for i, error in enumerate(errors[:3], 1):
            summary_parts.append(
                f"  {i}. [{error.category.upper()}] {error.message} ({error.file_path}:{error.line_number})\n"
            )

        if len(errors) > 3:
            summary_parts.append(f"  ... and {len(errors) - 3} more error(s)\n")

        return "".join(summary_parts)

    def _create_warning_summary(self, warnings: List[ValidationIssue]) -> str:
        """Create summary for passed with warnings."""
        summary_parts = [
            f"Validation passed with {len(warnings)} warning(s). Consider addressing:\n"
        ]

        # List top 3 warnings
        for i, warning in enumerate(warnings[:3], 1):
            summary_parts.append(
                f"  {i}. [{warning.category.upper()}] {warning.message}\n"
            )

        if len(warnings) > 3:
            summary_parts.append(f"  ... and {len(warnings) - 3} more warning(s)\n")

        return "".join(summary_parts)
