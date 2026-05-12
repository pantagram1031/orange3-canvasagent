# Canvas Agent Roadmap

This checklist tracks the longer-term direction for a modern AI workflow panel
inside Orange Data Mining. The goal is to borrow the best interaction patterns
from tools like Codex, VS Code, Claude Code, and Pi without turning Orange into
a generic chat app.

## Product Direction

- [ ] Keep Orange's visual workflow canvas as the primary surface, with AI as a
      guided copilot rather than a replacement UI.
- [ ] Evolve **Canvas Agent** from a single widget into a broader workflow panel
      that still feels native to Orange.
- [ ] Preserve reversible, inspectable changes as a core trust feature for all
      AI-assisted edits.
- [ ] Design for data scientists, students, and researchers before optimizing
      for agent power users.

## Core AI Workflow Panel

- [ ] Add a dockable AI workflow panel that can stay open beside the Orange
      canvas.
- [ ] Support chat, plans, execution status, and recovery in one place.
- [ ] Show a step-by-step action timeline instead of a single opaque response.
- [ ] Separate "thinking", "planned actions", "warnings", and "applied changes"
      into clearly labeled sections.
- [ ] Allow the panel to focus on the current selection, current workflow, or a
      blank canvas.
- [ ] Let users pin useful prompts, workflows, and repair recipes.

## Orange-Native Authoring

- [ ] Teach the agent Orange concepts directly: widgets, signals, learner/eval
      loops, preprocessing, visualization, and reporting.
- [ ] Offer workflow recipes such as classification, clustering, text mining,
      explainability, and time series.
- [ ] Suggest valid next widgets based on the current graph.
- [ ] Explain why a widget or connection is recommended in Orange terms.
- [ ] Detect incompatible widget combinations before applying them.

## Trust, Safety, And Repair

- [ ] Keep every AI change previewable before apply.
- [ ] Expand undo from a single checkpoint into a navigable AI edit history.
- [ ] Add "repair my workflow" actions for broken signals, missing data roles,
      and incompatible widget parameters.
- [ ] Surface clear diagnostics when a widget is installed but not registered.
- [ ] Add one-click recovery for discovery issues and backend auth issues.
- [ ] Provide an audit log that users can export with prompts, plans, and
      applied actions.

## UX Patterns Inspired By Modern AI Tools

- [ ] Stream partial results with visible progress instead of blocking the UI.
- [ ] Add slash commands for common Orange tasks such as `/classify`,
      `/cluster`, `/explain`, and `/repair`.
- [ ] Support compact inline suggestions near the canvas, similar to editor
      quick actions.
- [ ] Offer conversational onboarding that feels calm and approachable, in the
      spirit of Pi, for first-time Orange users.
- [ ] Provide workspace-aware suggestions like modern coding agents, but scoped
      to the active Orange workflow and dataset metadata.
- [ ] Make the panel keyboard-friendly for advanced users without harming
      discoverability for beginners.

## Backend And Model Flexibility

- [ ] Keep Codex CLI support strong as the first polished backend.
- [ ] Add pluggable backends for LiteLLM, OpenAI, Anthropic, and local models.
- [ ] Let admins configure approved providers for lab or classroom deployments.
- [ ] Separate model selection from workflow prompts so users can switch
      backends without losing context.
- [ ] Add structured capability checks so UI features adapt to the selected
      backend.

## Dataset And Context Awareness

- [ ] Let the panel inspect dataset schema, feature roles, and sample rows with
      user approval.
- [ ] Generate workflow suggestions based on data type, target availability, and
      missing-value patterns.
- [ ] Summarize what changed in the workflow and why it matches the data.
- [ ] Remember recent workflow intent within a session.
- [ ] Support project notes so the agent can follow the user's analysis goals.

## Collaboration And Learning

- [ ] Turn AI-generated workflows into readable teaching moments for students.
- [ ] Add "explain this workflow" and "why this model" modes.
- [ ] Support sharable prompt-to-workflow recipes for teams and classrooms.
- [ ] Provide exportable session summaries for reports and reproducibility.
- [ ] Add beginner and expert interaction modes with different levels of UI
      detail.

## Delivery Milestones

- [ ] `v0.2.x`: polish installer, discovery repair, diagnostics, and first-run
      onboarding.
- [ ] `v0.3.x`: richer chat-plus-preview flow, action timeline, and stronger
      recovery tools.
- [ ] `v0.4.x`: docked AI workflow panel with dataset-aware suggestions.
- [ ] `v0.5.x`: multi-backend support and exportable AI session history.
- [ ] `v1.0`: trustworthy Orange-native AI workflow assistant with strong
      onboarding, recovery, and reproducibility.
