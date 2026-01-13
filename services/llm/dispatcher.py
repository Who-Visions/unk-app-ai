from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from services.llm.gemini_agent import GeminiAgent


class AgentDispatcher:
    """
    RAPS "Parallel Agents" Orchestrator.
    Routes tasks to the specific sub-agent (Design Lead, Builder, Nerd, etc.)
    defined in antigravity.yaml.
    """

    def __init__(self, config_path: str = "antigravity.yaml"):
        self.config = self._load_config(config_path)
        self.team = {member['name']: member for member in self.config.get('team', [])}
        self.agents = {}  # Lazy load agents

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def get_agent(self, agent_name: str) -> GeminiAgent:
        if agent_name not in self.team:
            raise ValueError(f"Agent '{agent_name}' not found in Team config.")

        if agent_name not in self.agents:
            spec = self.team[agent_name]
            # Initialize GeminiAgent with specific model for this role
            self.agents[agent_name] = GeminiAgent(default_model=spec['model'])

        return self.agents[agent_name]

    def dispatch(self, agent_name: str, prompt: str) -> str:
        """
        Send a prompt to a specific specialized agent.
        """
        agent = self.get_agent(agent_name)
        spec = self.team[agent_name]

        # Inject Role Context
        system_context = f"""
        ROLE: {spec['role']}
        FOCUS: {spec['focus']}
        """
        full_prompt = f"{system_context}\n\nTASK: {prompt}"

        # Configure Thinking Level (Gemini 3.0)
        config = {}
        if 'thinking_level' in spec:
            config['thinking_config'] = {'thinking_level': spec['thinking_level']}

        return agent.run(full_prompt, config=config)

    def run_parallel(self, task_map: Dict[str, str]) -> Dict[str, str]:
        """
        Run tasks across multiple agents (mock parallel for now).
        task_map: {"Design Lead": "Style this...", "Nerd": "Audit this..."}
        """
        results = {}
        for name, task in task_map.items():
            results[name] = self.dispatch(name, task)
        return results
