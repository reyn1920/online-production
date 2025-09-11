from ollama_integration import ask_ollama
from web_search import web_search


def fix_sqlite_error_with_ai(error_msg):
    """Use web search and Ollama to get AI-powered fixes for SQLite errors.

    Args:
        error_msg (str): The SQLite error message

    Returns:
        str: AI-generated fix suggestion
    """
    print(f"🔍 Searching for solutions to: {error_msg}")

    # Search the web for solutions
    results = web_search(error_msg, num_results=3)

    # Create context for the AI
    context = f"Error:\n{error_msg}\n\nWeb Results:\n" + "\n".join(results)

    # Ask Ollama for a fix
    print("🤖 Asking CodeLlama for a solution...")
    fix = ask_ollama(
        "codellama:latest",
        f"Based on this SQLite error and web search results, provide a specific SQL fix:\n\n{context}",
    )

    return fix


# Example usage
if __name__ == "__main__":
    error_msg = "sqlite3.OperationalError: no such column: search_keywords"

    try:
        fix = fix_sqlite_error_with_ai(error_msg)
        print("💡 Suggested Fix:\n", fix)
    except Exception as e:
        print(f"❌ Error getting fix: {e}")
