#!/usr/bin/env zsh
# Base44 Hook Installer - Install pre-commit hooks for security enforcement
# Usage: ./tools/hooks/install-hooks.zsh

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOKS_DIR="$ROOT/tools/hooks"
GIT_HOOKS_DIR="$ROOT/.git/hooks"

echo "🔧 Base44 Hook Installer"
echo "📁 Project root: $ROOT"

# Check if we're in a git repository
if [[ ! -d "$ROOT/.git" ]]; then
    echo "❌ Not in a git repository. Please run from project root."
    exit 1
fi

# Check if our hooks exist
if [[ ! -f "$HOOKS_DIR/pre-commit" ]]; then
    echo "❌ Pre-commit hook not found at $HOOKS_DIR/pre-commit"
    exit 1
fi

# Create git hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Install pre-commit hook
echo "📋 Installing pre-commit hook..."
cp "$HOOKS_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
chmod +x "$GIT_HOOKS_DIR/pre-commit"

# Verify installation
if [[ -x "$GIT_HOOKS_DIR/pre-commit" ]]; then
    echo "✅ Pre-commit hook installed successfully!"
else
    echo "❌ Failed to install pre-commit hook"
    exit 1
fi

# Test the hook
echo "🧪 Testing hook installation..."
if "$GIT_HOOKS_DIR/pre-commit" --help >/dev/null 2>&1 || [[ $? -eq 1 ]]; then
    echo "✅ Hook is executable and ready"
else
    echo "⚠️ Hook installed but may have issues - check manually"
fi

echo ""
echo "🎉 Base44 pre-commit hooks installed!"
echo "📋 The hook will now run automatically before each commit"
echo "🛡️ It will enforce:"
echo "   • Forbidden vocabulary checks"
echo "   • Security audits"
echo "   • Code quality standards"
echo ""
echo "💡 To bypass the hook (emergency only): git commit --no-verify"
echo "📖 Hook logs: base44_guard.log"
echo "📊 Detailed reports: base44_guard_report.json"
