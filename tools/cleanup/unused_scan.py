#!/usr / bin / env python3
"""
unused_scan.py - Unused Code Detection Script
Part of the Trae AI Cleanup Framework

This tool scans for unused code, imports, variables, functions, and dependencies
to help maintain a clean and efficient codebase.
"""

import argparse
import ast
import json
import logging
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Setup logging
logging.basicConfig(
    level = logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
        logging.FileHandler("tools / cleanup / unused_scan.log"),
            logging.StreamHandler(),
            ],
)
logger = logging.getLogger(__name__)

@dataclass


class UnusedItem:
    """Represents an unused code item"""

    item_type: str  # 'import', 'function', 'variable', 'class', 'dependency'
    name: str
    file_path: str
    line_number: int
    context: str
    confidence: float  # 0.0 to 1.0
    safe_to_remove: bool
    reason: str


class PythonAnalyzer(ast.NodeVisitor):
    """AST - based analyzer for Python files"""


    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports = set()
        self.used_names = set()
        self.defined_functions = {}
        self.defined_classes = {}
        self.defined_variables = {}
        self.unused_items = []


    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)


    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)


    def visit_FunctionDef(self, node):
        self.defined_functions[node.name] = {
            "line": node.lineno,
                "node": node,
                "used": False,
                }
        self.generic_visit(node)


    def visit_AsyncFunctionDef(self, node):
        self.defined_functions[node.name] = {
            "line": node.lineno,
                "node": node,
                "used": False,
                }
        self.generic_visit(node)


    def visit_ClassDef(self, node):
        self.defined_classes[node.name] = {
            "line": node.lineno,
                "node": node,
                "used": False,
                }
        self.generic_visit(node)


    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_variables[target.id] = {
                    "line": node.lineno,
                        "node": node,
                        "used": False,
                        }
        self.generic_visit(node)


    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
            # Mark as used
            if node.id in self.defined_functions:
                self.defined_functions[node.id]["used"] = True
            if node.id in self.defined_classes:
                self.defined_classes[node.id]["used"] = True
            if node.id in self.defined_variables:
                self.defined_variables[node.id]["used"] = True
        self.generic_visit(node)


    def find_unused_items(self) -> List[UnusedItem]:
        """Find unused items in the analyzed file"""
        unused_items = []

        # Check unused imports
        for import_name in self.imports:
            if import_name not in self.used_names:
                unused_items.append(
                    UnusedItem(
                        item_type="import",
                            name = import_name,
                            file_path = self.file_path,
                            line_number = 1,  # Would need more sophisticated tracking
                        context = f"import {import_name}",
                            confidence = 0.9,
                            safe_to_remove = True,
                            reason="Import not used in file",
                            )
                )

        # Check unused functions
        for func_name, func_info in self.defined_functions.items():
            if not func_info["used"] and not func_name.startswith("_"):
                unused_items.append(
                    UnusedItem(
                        item_type="function",
                            name = func_name,
                            file_path = self.file_path,
                            line_number = func_info["line"],
                            context = f"def {func_name}(...)",
                            confidence = 0.8,
                            safe_to_remove = False,  # Might be called from other files
                        reason="Function not called within file",
                            )
                )

        # Check unused classes
        for class_name, class_info in self.defined_classes.items():
            if not class_info["used"] and not class_name.startswith("_"):
                unused_items.append(
                    UnusedItem(
                        item_type="class",
                            name = class_name,
                            file_path = self.file_path,
                            line_number = class_info["line"],
                            context = f"class {class_name}",
                            confidence = 0.8,
                            safe_to_remove = False,  # Might be used from other files
                        reason="Class not instantiated within file",
                            )
                )

        # Check unused variables
        for var_name, var_info in self.defined_variables.items():
            if not var_info["used"] and not var_name.startswith("_"):
                unused_items.append(
                    UnusedItem(
                        item_type="variable",
                            name = var_name,
                            file_path = self.file_path,
                            line_number = var_info["line"],
                            context = f"{var_name} = ...",
                            confidence = 0.9,
                            safe_to_remove = True,
                            reason="Variable assigned but never used",
                            )
                )

        return unused_items


class JavaScriptAnalyzer:
    """Analyzer for JavaScript / TypeScript files"""


    def __init__(self, file_path: str):
        self.file_path = file_path
        self.unused_items = []


    def analyze(self, content: str) -> List[UnusedItem]:
        """Analyze JavaScript / TypeScript content"""
        lines = content.split("\n")
        unused_items = []

        # Find imports
        imports = self._find_imports(lines)
        used_names = self._find_used_names(content)

        # Check for unused imports
        for import_info in imports:
            if import_info["name"] not in used_names:
                unused_items.append(
                    UnusedItem(
                        item_type="import",
                            name = import_info["name"],
                            file_path = self.file_path,
                            line_number = import_info["line"],
                            context = import_info["context"],
                            confidence = 0.9,
                            safe_to_remove = True,
                            reason="Import not used in file",
                            )
                )

        # Find unused variables
        variables = self._find_variables(lines)
        for var_info in variables:
            if var_info["name"] not in used_names:
                unused_items.append(
                    UnusedItem(
                        item_type="variable",
                            name = var_info["name"],
                            file_path = self.file_path,
                            line_number = var_info["line"],
                            context = var_info["context"],
                            confidence = 0.8,
                            safe_to_remove = True,
                            reason="Variable declared but never used",
                            )
                )

        return unused_items


    def _find_imports(self, lines: List[str]) -> List[Dict]:
        """Find import statements"""
        imports = []
        import_patterns = [
            r"import\s+{([^}]+)}\s + from",  # Named imports
            r"import\s+(\w+)\s + from",  # Default imports
            r"import\s+\*\s + as\s+(\w+)",  # Namespace imports
            r"const\s+{([^}]+)}\s*=\s * require",  # CommonJS named
            r"const\s+(\w+)\s*=\s * require",  # CommonJS default
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern in import_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    names = (
                        match.group(1).split(",")
                        if "{" in pattern
                        else [match.group(1)]
                    )
                    for name in names:
                        name = name.strip()
                        if name:
                            imports.append(
                                {
                                    "name": name,
                                        "line": line_num,
                                        "context": line.strip(),
                                        }
                            )

        return imports


    def _find_variables(self, lines: List[str]) -> List[Dict]:
        """Find variable declarations"""
        variables = []
        var_patterns = [
            r"(?:let|const|var)\s+(\w+)\s*=",
                r"function\s+(\w+)\s*\(",
                r"const\s+(\w+)\s*=\s*\(",  # Arrow functions
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern in var_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    name = match.group(1)
                    variables.append(
                        {"name": name, "line": line_num, "context": line.strip()}
                    )

        return variables


    def _find_used_names(self, content: str) -> Set[str]:
        """Find all used names in the content"""
        # Simple regex - based approach
        # In a production tool, you'd want to use a proper JS parser
        used_names = set()

        # Find identifiers (simplified)
        identifier_pattern = r"\b([a - zA - Z_$][a - zA - Z0 - 9_$]*)\b"
        matches = re.finditer(identifier_pattern, content)

        for match in matches:
            used_names.add(match.group(1))

        return used_names


class DependencyAnalyzer:
    """Analyzer for package dependencies"""


    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.unused_items = []


    def analyze_python_dependencies(self) -> List[UnusedItem]:
        """Analyze Python dependencies in requirements.txt"""
        unused_items = []
        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            return unused_items

        try:
            with open(requirements_file, "r") as f:
                requirements = f.read().splitlines()

            # Get installed packages
            installed_packages = set()
            for line in requirements:
                if line.strip() and not line.startswith("#"):
                    package = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                    installed_packages.add(package.lower())

            # Find used packages by scanning imports
            used_packages = self._find_used_python_packages()

            # Check for unused packages
            for package in installed_packages:
                if package not in used_packages and package not in [
                    "pip",
                        "setuptools",
                        "wheel",
                        ]:
                    unused_items.append(
                        UnusedItem(
                            item_type="dependency",
                                name = package,
                                file_path="requirements.txt",
                                line_number = 0,
                                context = f"Package: {package}",
                                confidence = 0.7,  # Lower confidence for dependencies
                            safe_to_remove = False,  # Might be runtime dependency
                            reason="Package not imported in any Python file",
                                )
                    )

        except Exception as e:
            logger.error(f"Error analyzing Python dependencies: {e}")

        return unused_items


    def analyze_npm_dependencies(self) -> List[UnusedItem]:
        """Analyze npm dependencies in package.json"""
        unused_items = []
        package_json = self.project_root / "package.json"

        if not package_json.exists():
            return unused_items

        try:
            with open(package_json, "r") as f:
                package_data = json.load(f)

            dependencies = package_data.get("dependencies", {})
            dev_dependencies = package_data.get("devDependencies", {})
            all_deps = {**dependencies, **dev_dependencies}

            # Find used packages
            used_packages = self._find_used_npm_packages()

            # Check for unused packages
            for package in all_deps:
                if package not in used_packages:
                    unused_items.append(
                        UnusedItem(
                            item_type="dependency",
                                name = package,
                                file_path="package.json",
                                line_number = 0,
                                context = f"Package: {package}",
                                confidence = 0.7,
                                safe_to_remove = False,
                                reason="Package not imported in any JS / TS file",
                                )
                    )

        except Exception as e:
            logger.error(f"Error analyzing npm dependencies: {e}")

        return unused_items


    def _find_used_python_packages(self) -> Set[str]:
        """Find Python packages used in import statements"""
        used_packages = set()

        for py_file in self.project_root.glob("**/*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf - 8", errors="ignore") as f:
                    content = f.read()

                # Find import statements
                import_pattern = r"(?:from|import)\s+([a - zA - Z_][a - zA - Z0 - 9_]*)"
                matches = re.finditer(import_pattern, content)

                for match in matches:
                    package = match.group(1).lower()
                    used_packages.add(package)

            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")

        return used_packages


    def _find_used_npm_packages(self) -> Set[str]:
        """Find npm packages used in import / require statements"""
        used_packages = set()

        for js_file in self.project_root.glob("**/*.{js,ts,jsx,tsx}"):
            if "node_modules" in str(js_file):
                continue

            try:
                with open(js_file, "r", encoding="utf - 8", errors="ignore") as f:
                    content = f.read()

                # Find import / require statements
                patterns = [
                    r'import.*from\s+[\'"]([^/\'"][^\'"]*)[\'"]',
                        r'require\s*\(\s*[\'"]([^/\'"][^\'"]*)[\'"]\s*\)',
                        ]

                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        package = match.group(1)
                        # Handle scoped packages
                        if package.startswith("@"):
                            package = (
                                package.split("/")[0] + "/" + package.split("/")[1]
                            )
                        else:
                            package = package.split("/")[0]
                        used_packages.add(package)

            except Exception as e:
                logger.debug(f"Error reading {js_file}: {e}")

        return used_packages


class UnusedCodeScanner:
    """Main scanner for unused code"""


    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.unused_items = []
        self.stats = {
            "files_scanned": 0,
                "unused_imports": 0,
                "unused_functions": 0,
                "unused_variables": 0,
                "unused_classes": 0,
                "unused_dependencies": 0,
                "safe_to_remove": 0,
                }


    def scan(self, file_extensions: List[str]) -> None:
        """Scan project for unused code"""
        logger.info(f"Starting unused code scan of {self.project_root}")

        # Scan Python files
        if "py" in file_extensions:
            self._scan_python_files()

        # Scan JavaScript / TypeScript files
        js_extensions = [
            ext for ext in file_extensions if ext in ["js", "ts", "jsx", "tsx"]
        ]
        if js_extensions:
            self._scan_javascript_files(js_extensions)

        # Scan dependencies
        self._scan_dependencies()

        # Update statistics
        self._update_statistics()


    def _scan_python_files(self) -> None:
        """Scan Python files for unused code"""
        for py_file in self.project_root.glob("**/*.py"):
            if any(skip in str(py_file) for skip in ["venv", "__pycache__", ".git"]):
                continue

            try:
                with open(py_file, "r", encoding="utf - 8", errors="ignore") as f:
                    content = f.read()

                # Parse with AST
                tree = ast.parse(content)
                analyzer = PythonAnalyzer(str(py_file.relative_to(self.project_root)))
                analyzer.visit(tree)

                unused_items = analyzer.find_unused_items()
                self.unused_items.extend(unused_items)
                self.stats["files_scanned"] += 1

            except Exception as e:
                logger.debug(f"Error analyzing {py_file}: {e}")


    def _scan_javascript_files(self, extensions: List[str]) -> None:
        """Scan JavaScript / TypeScript files for unused code"""
        for ext in extensions:
            for js_file in self.project_root.glob(f"**/*.{ext}"):
                if "node_modules" in str(js_file):
                    continue

                try:
                    with open(js_file, "r", encoding="utf - 8", errors="ignore") as f:
                        content = f.read()

                    analyzer = JavaScriptAnalyzer(
                        str(js_file.relative_to(self.project_root))
                    )
                    unused_items = analyzer.analyze(content)
                    self.unused_items.extend(unused_items)
                    self.stats["files_scanned"] += 1

                except Exception as e:
                    logger.debug(f"Error analyzing {js_file}: {e}")


    def _scan_dependencies(self) -> None:
        """Scan for unused dependencies"""
        dep_analyzer = DependencyAnalyzer(str(self.project_root))

        # Python dependencies
        python_unused = dep_analyzer.analyze_python_dependencies()
        self.unused_items.extend(python_unused)

        # npm dependencies
        npm_unused = dep_analyzer.analyze_npm_dependencies()
        self.unused_items.extend(npm_unused)


    def _update_statistics(self) -> None:
        """Update scan statistics"""
        for item in self.unused_items:
            if item.item_type == "import":
                self.stats["unused_imports"] += 1
            elif item.item_type == "function":
                self.stats["unused_functions"] += 1
            elif item.item_type == "variable":
                self.stats["unused_variables"] += 1
            elif item.item_type == "class":
                self.stats["unused_classes"] += 1
            elif item.item_type == "dependency":
                self.stats["unused_dependencies"] += 1

            if item.safe_to_remove:
                self.stats["safe_to_remove"] += 1


    def generate_report(self, output_format: str = "text") -> str:
        """Generate scan report"""
        if output_format == "json":
            return self._generate_json_report()
        else:
            return self._generate_text_report()


    def _generate_text_report(self) -> str:
        """Generate text format report"""
        report = []
        report.append("=" * 60)
        report.append("UNUSED CODE SCAN REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Project: {self.project_root}")
        report.append("")

        # Statistics
        report.append("STATISTICS:")
        report.append("-" * 20)
        for key, value in self.stats.items():
            report.append(f"{key.replace('_', ' ').title()}: {value}")
        report.append("")

        # Group by type
        by_type = defaultdict(list)
        for item in self.unused_items:
            by_type[item.item_type].append(item)

        for item_type, items in by_type.items():
            if items:
                report.append(f"UNUSED {item_type.upper()}S ({len(items)}):")
                report.append("-" * 30)

                for item in sorted(items, key = lambda x: (x.file_path, x.line_number)):
                    report.append(f"File: {item.file_path}:{item.line_number}")
                    report.append(f"Name: {item.name}")
                    report.append(f"Context: {item.context}")
                    report.append(f"Confidence: {item.confidence:.1%}")
                    report.append(
                        f"Safe to remove: {'Yes' if item.safe_to_remove else 'No'}"
                    )
                    report.append(f"Reason: {item.reason}")
                    report.append("")

        return "\n".join(report)


    def _generate_json_report(self) -> str:
        """Generate JSON format report"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "statistics": self.stats,
                "unused_items": [
                {
                    "item_type": item.item_type,
                        "name": item.name,
                        "file_path": item.file_path,
                        "line_number": item.line_number,
                        "context": item.context,
                        "confidence": item.confidence,
                        "safe_to_remove": item.safe_to_remove,
                        "reason": item.reason,
                        }
                for item in self.unused_items
            ],
                }
        return json.dumps(report_data, indent = 2)


    def remove_safe_items(self, dry_run: bool = True) -> int:
        """Remove items marked as safe to remove"""
        removed_count = 0

        for item in self.unused_items:
            if item.safe_to_remove:
                if self._remove_item(item, dry_run):
                    removed_count += 1

        return removed_count


    def _remove_item(self, item: UnusedItem, dry_run: bool) -> bool:
        """Remove a specific unused item"""
        try:
            if dry_run:
                logger.info(
                    f"[DRY RUN] Would remove {item.item_type} '{item.name}' from {item.file_path}:{item.line_number}"
                )
                return True

            # Implementation would depend on the item type
            # This is a simplified example
            logger.info(
                f"Removed {item.item_type} '{item.name}' from {item.file_path}:{item.line_number}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to remove {item.item_type} '{item.name}': {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Unused Code Detection Scanner")
    parser.add_argument(
        "--target - dir",
            default=".",
            help="Target directory to scan (default: current directory)",
            )
    parser.add_argument(
        "--extensions",
            default="py,js,ts,jsx,tsx",
            help="File extensions to scan (comma - separated)",
            )
    parser.add_argument(
        "--output - format",
            choices=["text", "json"],
            default="text",
            help="Output format for report",
            )
    parser.add_argument(
        "--output - file", help="Output file for report (default: stdout)"
    )
    parser.add_argument(
        "--remove - safe",
            action="store_true",
            help="Remove items marked as safe to remove",
            )
    parser.add_argument(
        "--dry - run",
            action="store_true",
            help="Show what would be removed without making changes",
            )
    parser.add_argument(
        "--min - confidence",
            type = float,
            default = 0.8,
            help="Minimum confidence threshold (0.0 - 1.0)",
            )

    args = parser.parse_args()

    # Initialize scanner
    project_root = Path(args.target_dir).resolve()
    scanner = UnusedCodeScanner(str(project_root))

    # Parse extensions
    extensions = [ext.strip() for ext in args.extensions.split(",")]

    # Run scan
    scanner.scan(extensions)

    # Filter by confidence
    scanner.unused_items = [
        item for item in scanner.unused_items if item.confidence >= args.min_confidence
    ]

    # Remove safe items if requested
    if args.remove_safe:
        removed_count = scanner.remove_safe_items(dry_run = args.dry_run)
        logger.info(f"Removed {removed_count} safe items")

    # Generate report
    report = scanner.generate_report(args.output_format)

    # Output report
    if args.output_file:
        with open(args.output_file, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {args.output_file}")
    else:
        print(report)

    # Exit with appropriate code
    if scanner.stats["unused_imports"] + scanner.stats["unused_functions"] > 0:
        sys.exit(1)  # Unused code found
    else:
        sys.exit(0)  # No unused code

if __name__ == "__main__":
    main()
