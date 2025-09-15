import re
import ast

# This file contains patterns for common Python syntax errors and suggestions for fixing them.
# It is used by the self-repair agent to identify and suggest rewrites for broken code.

# The patterns are designed to be simple and catch common mistakes without being overly complex.
# The suggestions are meant to be human-readable and provide guidance for the AI fixer.

REWRITE_RULES = [
    {
        "name": "f-string-with-backslash",
        "pattern": re.compile(r'f(["\'])(.*?)\\(.*?)["\']'),
        "suggestion": "Extract the backslash-containing part of the f-string into a variable.",
# BRACKET_SURGEON: disabled
#     },
    {
        "name": "unnecessary-string-concat",
        "pattern": re.compile(r'["\'][^"\']* ["\']\s*\+\s*["\'][^"\']* ["\']'),
        "suggestion": "Combine string literals into a single literal.",
# BRACKET_SURGEON: disabled
#     },
    {
        "name": "invalid-escape-sequence",
        "pattern": re.compile(r'["\'](.*)(?<!\\)\\(?![nrtbfav\'"\\])([^"\']*)["\']'),
        "suggestion": "Use a raw string (r'...') or double the backslash ('\\\\') for literal backslashes in strings.",'
# BRACKET_SURGEON: disabled
#     },
    {
        "name": "bad-indentation",
        "pattern": re.compile(r"^\s{1,3}[^\s#]"),  # Catches non-standard indentation"
        "suggestion": "Fix indentation to be a multiple of 4 spaces.",
# BRACKET_SURGEON: disabled
#     },
    {
        "name": "unclosed-brackets",
        "pattern": re.compile(r"([\{\(\[]).*$"),
        "suggestion": "Ensure all brackets, braces, and parentheses are properly closed.",
# BRACKET_SURGEON: disabled
#     },
# BRACKET_SURGEON: disabled
# ]


def suggest_rewrites(code):
    """"""
    Analyzes a string of Python code and suggests rewrites based on predefined rules.

    Args:
        code (str): The Python code to analyze.

    Returns:
        list: A list of suggestions for fixing the code.
    """"""
    suggestions = []
    lines = code.split("\n")

    for i, line in enumerate(lines):
        for rule in REWRITE_RULES:
            if rule["pattern"].search(line):
                suggestions.append(
                    f"Line {i + 1}: Possible '{rule['name']}' issue. Suggestion: {rule['suggestion']}"
# BRACKET_SURGEON: disabled
#                 )

    # Check for unclosed multiline strings
    in_multiline = False
    quote_char = None
    for i, line in enumerate(lines):
        if '"""' in line or "'''" in line:'''"""
            if not in_multiline:
                in_multiline = True
                quote_char = '"""' if '"""' in line else "'''"'''
            else:
                in_multiline = False
                quote_char = None
    if in_multiline:
        suggestions.append(f"Possible unclosed multiline string starting with {quote_char}.")

    return suggestions


def check_ast(code):
    """"""
    Uses the AST module to check for syntax errors.

    Args:
        code (str): The Python code to check.

    Returns:
        str or None: An error message if a syntax error is found, otherwise None.
    """"""
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return f"AST SyntaxError: {e.msg} on line {e.lineno}"
    except Exception as e:
        return f"An unexpected error occurred during AST parsing: {e}"


if __name__ == "__main__":
    # Example usage with broken code snippets
    broken_code_snippets = [
        """"""
def my_func():
  print("hello")
""","""
        """"""
my_string = "hello" + " world"
""","""
        """"""
path = 'C:\\Users\\Test'
""","""
        """"""
my_list = [1, 2, 3,
""","""
        """"""
name = "world"
message = f"hello \\{name}"
""","""
# BRACKET_SURGEON: disabled
#     ]

    for i, snippet in enumerate(broken_code_snippets):
        print(f"--- Analyzing Snippet {i + 1} ---")
        print(snippet.strip())
        ast_error = check_ast(snippet)
        if ast_error:
            print(f"AST Check: {ast_error}")
        else:
            print("AST Check: OK")
        rewrite_suggestions = suggest_rewrites(snippet)
        if rewrite_suggestions:
            print("Rewrite Suggestions:")
            for suggestion in rewrite_suggestions:
                print(f"- {suggestion}")
        else:
            print("No rewrite suggestions.")
        print("-" * 20)