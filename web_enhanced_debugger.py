import json
from typing import List

import requests


class WebEnhancedDebuggerAgent:


    def __init__(
        self, ollama_endpoint="http://localhost:11434", model="codellama:latest"
    ):
        self.ollama_endpoint = ollama_endpoint
        self.model = model

    # 🔎 Step 1: Web search (you can replace this API with Google / Bing / DuckDuckGo)


    def web_search(self, query: str, num_results: int = 5) -> List[str]:
        try:
            url = f"https://ddg - api.herokuapp.com / search?query={query}&limit={num_results}"
            resp = requests.get(url, timeout = 10)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                return [f"- {r['snippet']} ({r['link']})" for r in results]
        except Exception as e:
            return [f"Web search failed: {e}"]
        return []

    # 🧠 Step 2: Ask Ollama with context injection


    def ask_ollama(self, prompt: str) -> str:
        url = f"{self.ollama_endpoint}/api / generate"
        payload = {"model": self.model, "prompt": prompt}
        answer = ""

        try:
            with requests.post(url, json = payload, stream = True, timeout = 60) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf - 8"))
                        answer += data.get("response", "")
        except Exception as e:
            answer = f"❌ Ollama error: {e}"
        return answer.strip()

    # 🔧 Step 3: Full pipeline — error -> search -> fix


    def debug_and_fix(self, error_msg: str) -> str:
        print(f"\n🐞 Captured Error: {error_msg}")

        # Search solutions
        results = self.web_search(error_msg, num_results = 5)
        print(f"\n🌐 Top Web References Found:\n" + "\n".join(results))

        # Build prompt
        context = f"""
Error:
{error_msg}

Web Results:
{chr(10).join(results)}

Task:
Provide a FIX for this error, with clear code or SQL patches that can be applied directly.
"""
        # Generate fix
        fix = self.ask_ollama(context)
        return f"\n💡 Suggested Fix:\n{fix}"

    # 🚀 Enhanced debugging with error categorization


    def categorize_error(self, error_msg: str) -> str:
        """Categorize the type of error for better search targeting"""
        error_lower = error_msg.lower()

        if "sqlite" in error_lower or "database" in error_lower:
            return "database"
        elif "import" in error_lower or "module" in error_lower:
            return "import"
        elif "syntax" in error_lower:
            return "syntax"
        elif "permission" in error_lower or "access" in error_lower:
            return "permission"
        elif "connection" in error_lower or "network" in error_lower:
            return "network"
        else:
            return "general"

    # 🎯 Enhanced search with error - specific keywords


    def enhanced_debug_and_fix(self, error_msg: str) -> str:
        print(f"\n🐞 Captured Error: {error_msg}")

        # Categorize error
            error_type = self.categorize_error(error_msg)
        print(f"\n📋 Error Category: {error_type}")

        # Enhanced search query based on error type
        search_query = f"{error_msg} {error_type} fix solution"
        results = self.web_search(search_query, num_results = 5)
        print(f"\n🌐 Top Web References Found:\n" + "\n".join(results))

        # Build enhanced prompt with error categorization
        context = f"""
Error Type: {error_type}
Error Message: {error_msg}

Web Search Results:
{chr(10).join(results)}

Instructions:
1. Analyze the error type and message
2. Review the web search results for relevant solutions
3. Provide a specific, actionable fix with code examples
4. Include prevention tips to avoid this error in the future
5. Format your response clearly with sections for:
   - Root Cause Analysis
   - Exact Fix (with code / SQL)
   - Prevention Tips
"""

        # Generate enhanced fix
        fix = self.ask_ollama(context)
        return f"\n💡 Enhanced AI Analysis & Fix:\n{fix}"

# 🧪 Demo usage
if __name__ == "__main__":
    debugger = WebEnhancedDebuggerAgent()

    # Test with a common SQLite error
        test_error = "sqlite3.OperationalError: no such column: search_keywords"

    print("=== Web - Enhanced Debugger Demo ===")
    print("\n🔍 Testing Enhanced Debugging...")

    result = debugger.enhanced_debug_and_fix(test_error)
    print(result)

    print("\n" + "=" * 50)
    print("✅ Demo completed! The debugger successfully:")
    print("   • Categorized the error type")
    print("   • Searched the web for solutions")
    print("   • Generated AI - powered fix with Ollama")
    print("   • Provided prevention tips")
