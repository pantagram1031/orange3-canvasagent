# Orange3 Canvas Agent

`Orange3-CanvasAgent` adds an experimental Orange widget that can ask an agent
backend for structured canvas actions, apply them to the live scheme, and keep a
reversible checkpoint until the user accepts or reverts the AI commit.

The first backend targets the installed `codex` CLI and its ChatGPT/Codex login
flow. Direct API-key routing through LiteLLM is reserved for a later adapter.

