import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
from crewai import LLM
from latest_ai_development.secrets_manager import SecretsManager

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

secrets_manager = SecretsManager()


def build_llm(
    provider: str,
    model_name: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> LLM:
    """
    Factory function to build a CrewAI LLM instance.

    IMPORTANT FOR AI / FUTURE EDITS:
    - PROVIDER is a COMMON env var for the whole app (OPENAI / AZURE / OLLAMA).
    - model_name is allowed to differ PER AGENT (read from env per agent).
    - temperature/top_p/max_tokens are HARD-CODED PER AGENT in this file
      (do NOT read these from env, per requirement).
    - For Azure OpenAI: model_name should typically be the AZURE DEPLOYMENT NAME.
    """

    provider = (provider or "OLLAMA").upper()

    # If PROVIDER=OPENAI, use OpenAI models (requires API key secret).
    if provider == "OPENAI":
        # Prefer a generic secret env var name. Fallback to OPENAI_API_KEY_SECRET for backward compatibility.
        api_key_secret = os.getenv("API_KEY_SECRET", os.getenv("OPENAI_API_KEY_SECRET"))

        api_key = secrets_manager.get_secret(api_key_secret) if api_key_secret else None

        if not api_key:
            raise ValueError(
                "PROVIDER is set to OPENAI but API_KEY_SECRET/OPENAI_API_KEY_SECRET is not set or secret not found."
            )

        return LLM(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

    # If PROVIDER=AZURE, use Azure OpenAI endpoint (requires API key secret + URL + version).
    if provider == "AZURE":
        # Secret name is taken from env.
        api_key_secret = os.getenv("API_KEY_SECRET", "azure-openai-api-key-secret")
        api_key = secrets_manager.get_secret(api_key_secret)

        if not api_key:
            raise ValueError(
                "PROVIDER is set to AZURE but API_KEY_SECRET is not set or secret not found."
            )

        # Azure OpenAI endpoint information.
        # Keep these configurable via env, they are environment-specific).
        azure_base_url = os.getenv("AZURE_OPENAI_URL", "https://ap-azureopenai.openai.azure.com/")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

        return LLM(
            provider="azure",
            model=model_name,  # NOTE: This should be your Azure deployment name.
            base_url=azure_base_url,
            api_key=api_key,
            api_version=azure_api_version,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

    # Default: Ollama configuration (no API key required).
    # If PROVIDER=OLLAMA or not set, use Ollama with a local or remote base URL.
    return LLM(
        model=model_name or "ollama/llama3.2",
        base_url=os.getenv("OLLAMA_BASE_URL"),
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )


@CrewBase
class LatestAiDevelopment():
    """LatestAiDevelopment crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools

    # Code for defining your LLM(s) goes here.
    # LLM provider selection based on PROVIDER environment variable
    # Supported PROVIDER values in this file:
    # - PROVIDER=OPENAI  -> OpenAI API
    # - PROVIDER=AZURE   -> Azure OpenAI API
    # - PROVIDER=OLLAMA  -> Ollama (default)
    #
    # IMPORTANT FOR AI / FUTURE EDITS:
    # - PROVIDER is common (one env var for entire crew).
    # - MODEL is configured PER AGENT via env vars:
    #     RESEARCHER_MODEL_NAME, WRITER_MODEL_NAME, EDITOR_MODEL_NAME
    # - Generation params are HARD-CODED PER AGENT in this file:
    #     temperature/top_p/max_tokens
    provider = os.getenv("PROVIDER", "OLLAMA").upper()

    # -------------------------------------------------------------------------
    # Add proper comments to understand by llm
    # These values directly map to your requirement:
    #
    # Researcher:   temperature=0, top_p=0.3, max_tokens=1024
    # Reporting Analyst:    temperature=0.2, top_p=0.8, max_tokens=1500
    # -------------------------------------------------------------------------
    AGENT_LLM_SETTINGS: Dict[str, Dict[str, Any]] = {
        "researcher": {
            "model": "gpt-4.1-mini",
            "temperature": 0.1,
            "top_p": 0.3,
            "max_tokens": 1024,
        },
        "reporting_analyst": {
            "model": "gpt-4.1-mini",
            "temperature": 0.2,
            "top_p": 0.8,
            "max_tokens": 1500,
        }
    }

    def _get_generation_param(
        self,
        cfg: Dict[str, Any],
        key: str,
        env_key: str,
        default: Any,
        cast_type,
    ):
        """
        Resolve generation parameter with fallback priority:

        1. Agent config (AGENT_LLM_SETTINGS)
        2. Environment variable (.env)
        3. Hardcoded safe default
        """
        if key in cfg and cfg[key] is not None:
            return cast_type(cfg[key])

        env_value = os.getenv(env_key)
        if env_value is not None:
            return cast_type(env_value)

        return default

    def _llm_for_agent(self, agent_key: str) -> LLM:
        if agent_key not in self.AGENT_LLM_SETTINGS:
            raise ValueError(f"Unknown agent_key '{agent_key}' in AGENT_LLM_SETTINGS.")

        cfg = self.AGENT_LLM_SETTINGS[agent_key]

        model_name = cfg.get("model")

        temperature = self._get_generation_param(
            cfg, "temperature", "DEFAULT_TEMPERATURE", 0.1, float
        )

        top_p = self._get_generation_param(
            cfg, "top_p", "DEFAULT_TOP_P", 0.9, float
        )

        max_tokens = self._get_generation_param(
            cfg, "max_tokens", "DEFAULT_MAX_TOKENS", 1024, int
        )

        return build_llm(
            provider=self.provider,
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],  # type: ignore[index]
            verbose=True,
            llm=self._llm_for_agent("researcher"),
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],  # type: ignore[index]
            verbose=True,
            llm=self._llm_for_agent("reporting_analyst"),
        )


    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],  # type: ignore[index]
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],  # type: ignore[index]
            output_file='report.md'
        )


    @crew
    def crew(self) -> Crew:
        """Creates the LatestAiDevelopment crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            tracing=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
 