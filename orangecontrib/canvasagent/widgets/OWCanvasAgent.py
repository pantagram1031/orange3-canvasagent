from __future__ import annotations

import json
from orangecontrib.canvasagent.backend import AuthStatus
from orangecontrib.canvasagent.canvas import (
    CanvasActionExecutor,
    CanvasExecutionError,
    describe_canvas_state,
)
from orangecontrib.canvasagent.codex_backend import CodexCliBackend
from orangecontrib.canvasagent.commit import AiCommit, capture_scheme_snapshot, restore_scheme_snapshot
from orangecontrib.canvasagent.schema import CANVAS_PLAN_JSON_SCHEMA, CanvasPlan
from orangecontrib.canvasagent.setup_status import check_codex_status, diagnostic_report

NAME = "Canvas Agent"
DESCRIPTION = "Multi-LLM real-time canvas agent with reversible AI commits."
ICON = "../icons/agent.svg"
PRIORITY = 10
KEYWORDS = ["agent", "codex", "canvas", "ai"]

try:
    from Orange.widgets.widget import OWWidget
    from AnyQt.QtCore import QObject, QThread, Signal, Slot
    from AnyQt.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QLabel,
        QPushButton,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    ORANGE_AVAILABLE = True
except Exception:  # pragma: no cover - allows bare test imports without Orange3
    ORANGE_AVAILABLE = False

    class OWWidget:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

    class QObject:  # type: ignore[no-redef]
        pass

    class QThread:  # type: ignore[no-redef]
        pass

    class Signal:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

        def connect(self, *args, **kwargs):
            pass

        def emit(self, *args, **kwargs):
            pass

    def Slot(*args, **kwargs):  # type: ignore[no-redef]
        def decorator(func):
            return func

        return decorator


class AgentWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, backend, prompt: str, canvas_state: dict):
        super().__init__()
        self.backend = backend
        self.prompt = prompt
        self.canvas_state = canvas_state

    @Slot()
    def run(self) -> None:
        try:
            plan = self.backend.run(self.prompt, self.canvas_state, CANVAS_PLAN_JSON_SCHEMA)
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(plan)


class OWCanvasAgent(OWWidget):
    name = NAME
    description = DESCRIPTION
    icon = ICON
    priority = PRIORITY
    want_main_area = True
    resizing_enabled = True

    def __init__(self):
        super().__init__()
        self.backends = {"Codex CLI": CodexCliBackend()}
        self.pending_commit: AiCommit | None = None
        self._pending_prompt = ""
        self._worker_thread = None
        self._worker = None
        self._backend_ready = False
        self._canvas_ready = False

        if not ORANGE_AVAILABLE:
            return

        self._build_controls()
        self._refresh_auth_status()
        self._set_commit_controls(False)

    def _build_controls(self) -> None:
        self.backend_selector = QComboBox()
        self.backend_selector.addItems(["Codex CLI", "LiteLLM/API (later)", "Local Ollama (later)"])
        self.backend_selector.currentTextChanged.connect(self._refresh_auth_status)

        self.model_selector = QComboBox()
        self.model_selector.addItems([model.label for model in self.backends["Codex CLI"].list_models()])

        self.auth_button = QPushButton("Sign in")
        self.auth_button.clicked.connect(self._login)
        self.auth_status = QLabel("")

        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(96)
        self.prompt_input.setPlaceholderText("Tell the agent what to change on the canvas...")

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._send_prompt)

        self.keep_button = QPushButton("Keep Changes")
        self.keep_button.clicked.connect(self._keep_commit)
        self.revert_button = QPushButton("Revert AI Commit")
        self.revert_button.clicked.connect(self._revert_commit)

        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(170)

        for widget in [
            QLabel("Backend"),
            self.backend_selector,
            QLabel("Model"),
            self.model_selector,
            self.auth_button,
            self.auth_status,
            self.keep_button,
            self.revert_button,
        ]:
            self.controlArea.layout().addWidget(widget)

        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.action_preview = QTextEdit()
        self.action_preview.setReadOnly(True)
        self.error_panel = QTextEdit()
        self.error_panel.setReadOnly(True)
        self.error_panel.setMaximumHeight(120)
        self.raw_json_toggle = QCheckBox("Show raw JSON")
        self.diagnostics_text = QTextEdit()
        self.diagnostics_text.setReadOnly(True)
        self.copy_diagnostics_button = QPushButton("Copy Diagnostic Report")
        self.copy_diagnostics_button.clicked.connect(self._copy_diagnostics)
        self.refresh_setup_button = QPushButton("Check Setup")
        self.refresh_setup_button.clicked.connect(self._refresh_auth_status)
        self.test_agent_button = QPushButton("Test Agent")
        self.test_agent_button.clicked.connect(self._test_agent_readiness)

        self.tabs = QTabWidget()
        self.setup_step_labels = [
            QLabel("1. Check Codex"),
            QLabel("2. Sign in"),
            QLabel("3. Test agent"),
            QLabel("4. Start"),
        ]
        self.codex_status_label = QLabel("")
        self.canvas_status_label = QLabel("")
        self.discovery_status_label = QLabel("")

        self.tabs.addTab(self._setup_tab(), "Setup")
        self.tabs.addTab(self._chat_tab(), "Chat")
        self.tabs.addTab(self._preview_tab(), "Preview")
        self.tabs.addTab(self._diagnostics_tab(), "Diagnostics")
        self.mainArea.layout().addWidget(self.tabs)

    def _setup_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.addWidget(QLabel("Canvas Agent Setup"))
        for label in self.setup_step_labels:
            layout.addWidget(label)
        layout.addWidget(self.codex_status_label)
        layout.addWidget(self.canvas_status_label)
        layout.addWidget(self.discovery_status_label)
        layout.addWidget(self.refresh_setup_button)
        layout.addWidget(self.test_agent_button)
        layout.addStretch(1)
        return tab

    def _chat_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.addWidget(QLabel("Conversation"))
        layout.addWidget(self.transcript)
        layout.addWidget(QLabel("Command"))
        layout.addWidget(self.prompt_input)
        layout.addWidget(self.send_button)
        layout.addWidget(QLabel("Status"))
        layout.addWidget(self.status_log)
        return tab

    def _preview_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.addWidget(QLabel("AI Commit Preview"))
        layout.addWidget(self.action_preview)
        layout.addWidget(self.raw_json_toggle)
        layout.addWidget(self.keep_button)
        layout.addWidget(self.revert_button)
        return tab

    def _diagnostics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.addWidget(QLabel("Diagnostics"))
        layout.addWidget(self.diagnostics_text)
        layout.addWidget(self.copy_diagnostics_button)
        return tab

    def _current_backend(self):
        name = self.backend_selector.currentText()
        if name not in self.backends:
            raise RuntimeError(f"{name} is not implemented yet.")
        return self.backends[name]

    def _refresh_auth_status(self) -> None:
        if not ORANGE_AVAILABLE:
            return
        try:
            status = self._current_backend().is_authenticated()
        except Exception as exc:
            status = AuthStatus(False, str(exc))
        codex_status = check_codex_status()
        self._backend_ready = status.authenticated
        self._canvas_ready = self._has_scheme()
        self.auth_status.setText(status.message)
        self.auth_button.setText("Reconnect" if status.authenticated else "Sign in")
        self.codex_status_label.setText(f"Codex: {codex_status.state} - {codex_status.message}")
        self.canvas_status_label.setText(
            "Canvas: ready" if self._canvas_ready else "Canvas: open this widget on an Orange canvas"
        )
        self.discovery_status_label.setText("Widget discovery: registered")
        self.diagnostics_text.setPlainText(diagnostic_report())
        self._update_send_enabled()

    def _login(self) -> None:
        try:
            status = self._current_backend().login()
        except Exception as exc:
            status = AuthStatus(False, str(exc))
        self._append_status(status.message)
        self._refresh_auth_status()

    def _send_prompt(self) -> None:
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            self._append_error("Enter a command before sending.")
            return
        try:
            scheme = self._scheme()
            backend = self._current_backend()
        except Exception as exc:
            self._append_error(str(exc))
            return

        self._pending_prompt = prompt
        self.send_button.setEnabled(False)
        self._append_transcript(f"User: {prompt}")
        self._append_status("Agent is planning canvas actions...")

        self._worker_thread = QThread()
        self._worker = AgentWorker(backend, prompt, describe_canvas_state(scheme))
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_plan_ready)
        self._worker.failed.connect(self._on_agent_error)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.failed.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.start()

    @Slot(object)
    def _on_plan_ready(self, plan: CanvasPlan) -> None:
        try:
            scheme = self._scheme()
            before_snapshot = capture_scheme_snapshot(scheme)
            executor = CanvasActionExecutor(
                scheme,
                resolve_widget_description=self._resolve_widget_description,
            )
            result = executor.apply(plan)
            backend_name = self.backend_selector.currentText()
            model = self.model_selector.currentText()
            self.pending_commit = AiCommit.create(
                prompt=self._pending_prompt,
                backend=backend_name,
                model=model,
                before_snapshot=before_snapshot,
                plan=plan,
                messages=result.messages,
            )
        except Exception as exc:
            if "before_snapshot" in locals():
                restore_scheme_snapshot(scheme, before_snapshot)
            self._on_agent_error(str(exc))
            return

        self.prompt_input.clear()
        self.send_button.setEnabled(True)
        self._update_send_enabled()
        self._set_commit_controls(True)
        self._append_transcript(f"Agent: {plan.summary}")
        self.action_preview.setPlainText(json.dumps(plan.to_dict(), indent=2))
        for warning in plan.warnings:
            self._append_status(f"Warning: {warning}")
        for message in result.messages:
            self._append_status(message)

    @Slot(str)
    def _on_agent_error(self, message: str) -> None:
        self._update_send_enabled()
        self._append_error(message)

    def _keep_commit(self) -> None:
        self.pending_commit = None
        self._set_commit_controls(False)
        self._append_status("AI commit kept.")

    def _revert_commit(self) -> None:
        if not self.pending_commit:
            self._append_error("No pending AI commit to revert.")
            return
        try:
            self.pending_commit.revert(self._scheme())
        except Exception as exc:
            self._append_error(str(exc))
            return
        self.pending_commit = None
        self._set_commit_controls(False)
        self._append_status("AI commit reverted.")

    def _set_commit_controls(self, enabled: bool) -> None:
        self.keep_button.setEnabled(enabled)
        self.revert_button.setEnabled(enabled)

    def _update_send_enabled(self) -> None:
        self.send_button.setEnabled(bool(self._backend_ready and self._canvas_ready))

    def _has_scheme(self) -> bool:
        try:
            self._scheme()
            return True
        except Exception:
            return False

    def _scheme(self):
        try:
            return self.workflowEnv().scheme()
        except Exception as exc:
            raise RuntimeError("Canvas scheme is not available from this widget.") from exc

    def _resolve_widget_description(self, qualified_name: str):
        registry = self._widget_registry()
        for description in self._iter_widget_descriptions(registry):
            if getattr(description, "qualified_name", None) == qualified_name:
                return description
        raise CanvasExecutionError(f"Widget is not registered in Orange: {qualified_name}")

    def _widget_registry(self):
        env = self.workflowEnv()
        for attr in ("widget_registry", "registry"):
            candidate = getattr(env, attr, None)
            if callable(candidate):
                return candidate()
            if candidate is not None:
                return candidate
        raise CanvasExecutionError("Could not access the Orange widget registry.")

    def _iter_widget_descriptions(self, registry):
        if hasattr(registry, "widgets"):
            yield from registry.widgets()
            return
        if hasattr(registry, "categories"):
            for category in registry.categories():
                yield from registry.widgets(category)

    def _append_status(self, text: str) -> None:
        self.status_log.append(text)

    def _append_error(self, text: str) -> None:
        self.error_panel.append(text)
        self._append_status(f"Error: {text}")

    def _append_transcript(self, text: str) -> None:
        self.transcript.append(text)

    def _copy_diagnostics(self) -> None:
        QApplication.clipboard().setText(self.diagnostics_text.toPlainText())
        self._append_status("Diagnostic report copied.")

    def _test_agent_readiness(self) -> None:
        self._refresh_auth_status()
        if self._backend_ready and self._canvas_ready:
            self._append_status("Agent is ready.")
        else:
            self._append_status("Agent is not ready yet. Check setup details.")
