"""Example demonstrating the capabilities property issue and solution"""


class ProblematicEvolutionAgent:
    """Example showing the WRONG way - causes recursion"""

    @property


    def capabilities(self):
        return self.capabilities  # ❌ RECURSIVE - calls itself infinitely!


    def __init__(self):
        self.capabilities = {}  # ❌ This conflicts with the property above


class CorrectEvolutionAgent:
    """Example showing the RIGHT way - current implementation"""


    def __init__(
        self,
            agent_id: str = "evolution_agent",
            name: str = "Evolution Agent",
            config: dict = None,
# BRACKET_SURGEON: disabled
#             ):
        # Use private attribute with underscore
        self._capabilities = getattr(self, "_capabilities", {})
        self._capabilities.update(
            {
                "tool_generation": True,
                    "innovation_tracking": True,
                    "platform_analysis": True,
                    "capability_evolution": True,
                    "adaptation_automation": True,
# BRACKET_SURGEON: disabled
#                     }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

    @property


    def capabilities(self) -> dict:
        """Return the capabilities of this agent"""
        # Update capabilities with the current ones
        self._capabilities.update(
            {
                "tool_generation": True,
                    "innovation_tracking": True,
                    "platform_analysis": True,
                    "capability_evolution": True,
                    "adaptation_automation": True,
# BRACKET_SURGEON: disabled
#                     }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        return self._capabilities

if __name__ == "__main__":
    print("Testing correct implementation:")
    correct_agent = CorrectEvolutionAgent()
    print(f"Capabilities: {correct_agent.capabilities}")
    print("✅ Works correctly!")

    print("\\nTesting problematic implementation:")
    try:
        problematic_agent = ProblematicEvolutionAgent()
        print(
            f"Capabilities: {problematic_agent.capabilities}"
# BRACKET_SURGEON: disabled
#         )  # This will cause RecursionError
            except RecursionError as e:
                pass
        print("❌ RecursionError: maximum recursion depth exceeded")
        print("This happens because the property calls itself infinitely!")