from __future__ import annotations

import fnmatch
from pathlib import Path

BANNED = {
    "production", "simulation", "placeholder", "demo",
    "mock", "fake", "sample", "test",
}

def load_ignore_patterns(root: Path) -> list[str]:
    """Load ignore patterns from .rule1_ignore file."""
    ignore_file = root / ".rule1_ignore"
    if not ignore_file.exists():
        return []
    
    patterns = []
    try:
        for line in ignore_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    except Exception:
        pass
    return patterns

def should_ignore(path: Path, root: Path, patterns: list[str]) -> bool:
    """Check if a path should be ignored based on patterns."""
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        return False
        
    path_str = str(relative_path)
    
    for pattern in patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            dir_pattern = pattern.rstrip("/")
            # Check if any parent directory matches
            if any(part == dir_pattern for part in relative_path.parts):
                return True
            # Check if the path starts with this directory
            if path_str.startswith(dir_pattern + "/") or path_str == dir_pattern:
                return True
        # Handle file extension patterns
        elif pattern.startswith("*."):
            if fnmatch.fnmatch(path.name, pattern):
                return True
        # Handle wildcard patterns
        elif "*" in pattern:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
        # Handle exact file/directory name matches
        else:
            if pattern in relative_path.parts or path.name == pattern:
                return True
    
    return False

def enforce(root: Path) -> int:
    """
    Scan files under `root` and return the number of violations.
    Exit codes/returns:
      0 = clean
      N = number of files with violations
    """
    ignore_patterns = load_ignore_patterns(root)
    violations = 0
    
    for p in root.rglob("*"):
        if not p.is_file():
            continue
            
        # Skip ignored files
        if should_ignore(p, root, ignore_patterns):
            continue
            
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
            
        bad = [w for w in BANNED if w in text]
        if bad:
            violations += 1
            print(f"[RULE-1] {p}: {', '.join(sorted(bad))}")
    return violations

if __name__ == "__main__":
    import sys
    root_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    exit_code = enforce(root_path)
    sys.exit(exit_code)