# Multi-AI Agent Lab Workflow

This workflow outlines how the lab coordinates local and cloud models to drive reconnaissance, analysis, and operator support across the mesh and TUI tooling.

- Local OSS model (Ollama) handles quick answers and offline summarization.
- Cloud LLM model provides richer analysis and long-form synthesis when connectivity allows.
- Routing logic selects the backend per task to balance speed, cost, and privacy.
- Mesh agents share context and hand off tasks between CLI, TUI, and recon modules.
