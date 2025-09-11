from web_search import web_search
from ollama_integration import ask_ollama
import traceback
import sys

def ai_debug_sqlite_error(error_msg, num_results=3):
    """
    AI-powered SQLite error debugging using web search and Ollama.
    
    Args:
        error_msg (str): The SQLite error message
        num_results (int): Number of web search results to include
        
    Returns:
        str: AI-generated fix suggestion
    """
    print(f"🔍 Analyzing SQLite error: {error_msg}")
    
    # Search the web for solutions
    print("📡 Searching web for solutions...")
    results = web_search(error_msg, num_results=num_results)
    
    # Create comprehensive context for AI
    context = f"Error:\n{error_msg}\n\nWeb Results:\n" + "\n".join(results)
    
    # Enhanced prompt for better AI analysis
    prompt = f"""You are a SQLite database expert. Analyze this error and provide a specific, actionable fix.

{context}

Provide:
1. Root cause analysis
2. Exact SQL command to fix the issue
3. Prevention tips for the future

Be concise and practical."""
    
    print("🤖 Asking CodeLlama for expert analysis...")
    fix = ask_ollama("codellama:latest", prompt)
    
    return fix

def auto_debug_with_ai():
    """
    Demonstration of the AI debugging workflow.
    """
    # Example SQLite error
    error_msg = "sqlite3.OperationalError: no such column: search_keywords"
    
    try:
        # Get AI-powered fix
        fix = ai_debug_sqlite_error(error_msg)
        
        print("\n💡 AI-Generated Fix:")
        print("=" * 50)
        print(fix)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during AI debugging: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Run the AI debugging demonstration
    auto_debug_with_ai()
    
    print("\n🎯 AI Debug Assistant Ready!")
    print("Use ai_debug_sqlite_error(error_msg) for any SQLite issues.")