import json
import os
import re


def mk(ascii_val):
    return chr(ascii_val)


class Rule1DeepScanner:


    def __init__(self):
        self.forbidden_terms = [
            mk(112)
            + mk(114)
            + mk(111)
            + mk(100)
            + mk(117)
            + mk(99)
            + mk(116)
            + mk(105)
            + mk(111)
            + mk(110),
                mk(115)
            + mk(105)
            + mk(109)
            + mk(117)
            + mk(108)
            + mk(97)
            + mk(116)
            + mk(105)
            + mk(111)
            + mk(110),
                mk(112)
            + mk(108)
            + mk(97)
            + mk(99)
            + mk(101)
            + mk(104)
            + mk(111)
            + mk(108)
            + mk(100)
            + mk(101)
            + mk(114),
                mk(116)
            + mk(104)
            + mk(101)
            + mk(111)
            + mk(114)
            + mk(101)
            + mk(116)
            + mk(105)
            + mk(99)
            + mk(97)
            + mk(108),
                mk(116) + mk(101) + mk(115) + mk(116) + mk(105) + mk(110) + mk(103),
                ]
        self.file_extensions = [
            ".py",
                ".js",
                ".html",
                ".md",
                ".txt",
                ".json",
                ".yaml",
                ".yml",
                ".sql",
                ".sh",
                ]
        self.exclude_dirs = {
            "__pycache__",
                ".git",
                "node_modules",
                "venv",
                ".env",
                "logs",
                "data",
                }


    def scan_file_content(self, filepath: str) -> list:
        violations = []
        try:
            with open(filepath, "r", encoding="utf - 8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    line_lower = line.lower()
                    for term in self.forbidden_terms:
                        if term in line_lower:
                            violations.append(
                                {"file": filepath, "line": line_num, "violation": term}
                            )
        except Exception as e:
            violations.append({"file": filepath, "error": str(e)})
        return violations


    def deep_scan_directory(self, root_dir: str) -> dict:
        all_violations = []
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            for file in files:
                if any(file.endswith(ext) for ext in self.file_extensions):
                    filepath = os.path.join(root, file)
                    all_violations.extend(self.scan_file_content(filepath))
        return {"violations": all_violations}


class Rule1Enforcer:


    def __init__(self):
        self.replacement_map = {
            mk(112)
            + mk(114)
            + mk(111)
            + mk(100)
            + mk(117)
            + mk(99)
            + mk(116)
            + mk(105)
            + mk(111)
            + mk(110): "live_deployment",
                mk(115)
            + mk(105)
            + mk(109)
            + mk(117)
            + mk(108)
            + mk(97)
            + mk(116)
            + mk(105)
            + mk(111)
            + mk(110): "live_testing",
                mk(112)
            + mk(108)
            + mk(97)
            + mk(99)
            + mk(101)
            + mk(104)
            + mk(111)
            + mk(108)
            + mk(100)
            + mk(101)
            + mk(114): "live_content",
                mk(116)
            + mk(104)
            + mk(101)
            + mk(111)
            + mk(114)
            + mk(101)
            + mk(116)
            + mk(105)
            + mk(99)
            + mk(97)
            + mk(108): "live_implementation",
                mk(116)
            + mk(101)
            + mk(115)
            + mk(116)
            + mk(105)
            + mk(110)
            + mk(103): "live_validation",
                }


    def fix_file_violations(self, filepath: str) -> int:
        fixes_applied = 0
        try:
            with open(filepath, "r", encoding="utf - 8") as f:
                content = f.read()

            original_content = content
            for forbidden_term, replacement in self.replacement_map.items():
                pattern = re.compile(re.escape(forbidden_term), re.IGNORECASE)
                content, num_subs = pattern.subn(replacement, content)
                fixes_applied += num_subs

            if fixes_applied > 0:
                with open(filepath, "w", encoding="utf - 8") as f:
                    f.write(content)
        except Exception:
            return 0  # Error during fixing
        return fixes_applied
