from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from tkinter import END, StringVar, Text, Tk, Toplevel, filedialog, messagebox
from tkinter import ttk

from installer.core import (
    OrangeInstall,
    DetectionResult,
    discover_orange_installs,
    install_wheel,
    smoke_check,
    validate_orange_folder,
)


WINDOWS_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
WIZARD_STEPS = ("Welcome", "Detect Orange", "Install / Repair", "Verify", "Finish")
ACCENT = "#2563eb"
ACCENT_DARK = "#1d4ed8"
TEXT = "#111827"
MUTED = "#5b6472"
SURFACE = "#ffffff"
APP_BG = "#eef2f7"
SUCCESS = "#0f766e"
ERROR = "#b42318"


class CanvasAgentInstaller:
    def __init__(self, wheel_path: Path | None = None):
        self.root = Tk()
        self.root.title("Canvas Agent Setup")
        self.root.geometry("980x680")
        self.root.minsize(900, 620)
        self.root.configure(background=APP_BG)

        self.wheel_path = wheel_path or self._default_wheel_path()
        self.installs: list[OrangeInstall] = []
        self.selected_install: OrangeInstall | None = None
        self.current_step = 0
        self.is_busy = False
        self.current_action = ""
        self.last_install_result: DetectionResult | None = None
        self.last_smoke_result: DetectionResult | None = None
        self.detected_version: str | None = None
        self.install_mode = "Install"
        self.launch_error: str | None = None
        self.diagnostics_sections: list[tuple[str, str]] = []

        self.step_title = StringVar()
        self.step_subtitle = StringVar()
        self.helper_text = StringVar()
        self.detect_summary = StringVar(value="Searching for Orange installations...")
        self.selection_summary = StringVar(value="No Orange installation selected yet.")
        self.install_summary = StringVar(value="Select an Orange installation to continue.")
        self.verify_summary = StringVar(value="Run a smoke check after installation to confirm everything is ready.")
        self.finish_title = StringVar(value="Setup not started")
        self.finish_message = StringVar(value="Complete the installer steps to finish setup.")
        self.finish_path = StringVar(value="Orange path: Not available")
        self.finish_version = StringVar(value="Canvas Agent version: Unknown")
        self.wheel_summary = StringVar(value=f"Installer package: {self.wheel_path}")
        self.open_orange_label = StringVar(value="Open Orange")

        self._configure_style()
        self._build_shell()
        self._set_step(0)
        self._scan_installs(initial=True)

    def run(self) -> None:
        self.root.mainloop()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        themes = style.theme_names()
        if "vista" in themes:
            style.theme_use("vista")
        elif "clam" in themes:
            style.theme_use("clam")

        self.default_font = ("Segoe UI", 10)
        self.header_font = ("Segoe UI Semibold", 20)
        self.section_font = ("Segoe UI Semibold", 11)
        self.body_font = ("Segoe UI", 10)
        self.small_font = ("Segoe UI", 9)

        style.configure(".", font=self.default_font)
        style.configure("App.TFrame", background=APP_BG)
        style.configure("Surface.TFrame", background=SURFACE)
        style.configure("Sidebar.TFrame", background="#e7edf6")
        style.configure("Content.TFrame", background=SURFACE)
        style.configure("Card.TFrame", background=SURFACE, relief="solid", borderwidth=1)
        style.configure("InnerCard.TFrame", background="#f8fafc", relief="solid", borderwidth=1)
        style.configure("TLabel", background=SURFACE, foreground=TEXT, font=self.body_font)
        style.configure("Sidebar.TLabel", background="#e7edf6", foreground=MUTED, font=self.body_font)
        style.configure("StepActive.TLabel", background="#dbeafe", foreground=ACCENT_DARK, font=self.section_font)
        style.configure("StepDone.TLabel", background="#dcfce7", foreground="#166534", font=self.section_font)
        style.configure("HeroTitle.TLabel", background=SURFACE, foreground=TEXT, font=self.header_font)
        style.configure("HeroBody.TLabel", background=SURFACE, foreground=MUTED, font=self.body_font)
        style.configure("Section.TLabel", background=SURFACE, foreground=TEXT, font=self.section_font)
        style.configure("Muted.TLabel", background=SURFACE, foreground=MUTED, font=self.body_font)
        style.configure("Mini.TLabel", background=SURFACE, foreground=MUTED, font=self.small_font)
        style.configure("Banner.TLabel", background="#eff6ff", foreground=ACCENT_DARK, font=self.body_font)
        style.configure("Success.TLabel", background="#ecfdf3", foreground=SUCCESS, font=self.section_font)
        style.configure("Error.TLabel", background="#fef3f2", foreground=ERROR, font=self.section_font)
        style.configure("Primary.TButton", font=("Segoe UI Semibold", 10), padding=(18, 10))
        style.map(
            "Primary.TButton",
            background=[("pressed", ACCENT_DARK), ("active", ACCENT_DARK), ("!disabled", ACCENT)],
            foreground=[("disabled", "#d1d5db"), ("!disabled", "#ffffff")],
            relief=[("pressed", "flat"), ("!disabled", "flat")],
        )
        style.configure("Secondary.TButton", padding=(16, 10))
        style.configure("TButton", padding=(14, 9))
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=4)
        style.configure("Wizard.Treeview", rowheight=28, font=self.body_font)
        style.configure("Wizard.Treeview.Heading", font=("Segoe UI Semibold", 10))

    def _build_shell(self) -> None:
        container = ttk.Frame(self.root, style="App.TFrame", padding=18)
        container.pack(fill="both", expand=True)

        shell = ttk.Frame(container, style="Surface.TFrame")
        shell.pack(fill="both", expand=True)

        sidebar = ttk.Frame(shell, style="Sidebar.TFrame", width=230, padding=(18, 26))
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Canvas Agent", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            sidebar,
            text="Setup Wizard",
            style="Sidebar.TLabel",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(2, 20))
        ttk.Label(
            sidebar,
            text="Install the Orange add-on with the same kind of simple flow you expect from a Windows installer.",
            style="Sidebar.TLabel",
            wraplength=180,
            justify="left",
        ).pack(anchor="w", pady=(0, 22))

        self.step_labels: list[ttk.Label] = []
        for step in WIZARD_STEPS:
            label = ttk.Label(sidebar, text=step, style="Sidebar.TLabel", padding=(12, 10))
            label.pack(fill="x", pady=4)
            self.step_labels.append(label)

        ttk.Separator(sidebar).pack(fill="x", pady=20)
        ttk.Label(sidebar, text="Package", style="Sidebar.TLabel", font=("Segoe UI Semibold", 9)).pack(anchor="w")
        ttk.Label(sidebar, textvariable=self.wheel_summary, style="Sidebar.TLabel", wraplength=180, justify="left").pack(anchor="w", pady=(6, 0))

        main = ttk.Frame(shell, style="Content.TFrame", padding=(28, 24))
        main.pack(side="left", fill="both", expand=True)

        self.title_label = ttk.Label(main, textvariable=self.step_title, style="HeroTitle.TLabel")
        self.title_label.pack(anchor="w")
        ttk.Label(main, textvariable=self.step_subtitle, style="HeroBody.TLabel", wraplength=640, justify="left").pack(anchor="w", pady=(6, 18))
        ttk.Separator(main).pack(fill="x")

        self.content_host = ttk.Frame(main, style="Content.TFrame", padding=(0, 22, 0, 14))
        self.content_host.pack(fill="both", expand=True)

        self.pages = [ttk.Frame(self.content_host, style="Content.TFrame") for _ in WIZARD_STEPS]
        for page in self.pages:
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_welcome_page(self.pages[0])
        self._build_detect_page(self.pages[1])
        self._build_install_page(self.pages[2])
        self._build_verify_page(self.pages[3])
        self._build_finish_page(self.pages[4])

        footer = ttk.Frame(main, style="Content.TFrame")
        footer.pack(fill="x", side="bottom")
        ttk.Separator(footer).pack(fill="x")

        footer_inner = ttk.Frame(footer, style="Content.TFrame", padding=(0, 14, 0, 0))
        footer_inner.pack(fill="x")

        ttk.Label(footer_inner, textvariable=self.helper_text, style="Muted.TLabel").pack(side="left", anchor="w")

        nav = ttk.Frame(footer_inner, style="Content.TFrame")
        nav.pack(side="right")

        self.back_button = ttk.Button(nav, text="Back", command=self._go_back)
        self.back_button.pack(side="left", padx=(0, 8))
        self.next_button = ttk.Button(nav, text="Next", style="Primary.TButton", command=self._go_next)
        self.next_button.pack(side="left")

    def _build_welcome_page(self, page: ttk.Frame) -> None:
        card = self._card(page)
        ttk.Label(card, text="Welcome", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            card,
            text="This wizard will detect Orange, install or repair the Canvas Agent package, run a smoke check, and finish with a quick launch option.",
            style="Muted.TLabel",
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(8, 18))

        bullets = (
            "Detect installed Orange locations automatically or choose one manually.",
            "Install or repair the bundled wheel without changing the existing installer.core workflow.",
            "Verify the add-on registration before you open Orange.",
        )
        for bullet in bullets:
            ttk.Label(card, text=f"- {bullet}", style="Muted.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=3)

        note = self._info_banner(page)
        ttk.Label(
            note,
            text="The setup uses your selected Orange Python environment and keeps diagnostics available if anything fails.",
            style="Banner.TLabel",
            wraplength=620,
            justify="left",
        ).pack(anchor="w")

    def _build_detect_page(self, page: ttk.Frame) -> None:
        summary = self._card(page)
        ttk.Label(summary, textvariable=self.detect_summary, style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            summary,
            text="Choose the Orange installation that should receive the Canvas Agent add-on.",
            style="Muted.TLabel",
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        table_card = self._card(page, pady=(16, 0))
        columns = ("label", "source", "path")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", style="Wizard.Treeview", selectmode="browse", height=8)
        self.tree.heading("label", text="Orange")
        self.tree.heading("source", text="Found via")
        self.tree.heading("path", text="Path")
        self.tree.column("label", width=180, anchor="w")
        self.tree.column("source", width=120, anchor="w")
        self.tree.column("path", width=360, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        buttons = ttk.Frame(table_card, style="Surface.TFrame")
        buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(buttons, text="Rescan", command=self._scan_installs).pack(side="left")
        ttk.Button(buttons, text="Choose Folder...", command=self._choose_folder).pack(side="left", padx=(8, 0))

        selection = self._card(page, pady=(16, 0))
        ttk.Label(selection, text="Selected Orange", style="Section.TLabel").pack(anchor="w")
        ttk.Label(selection, textvariable=self.selection_summary, style="Muted.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(8, 0))

    def _build_install_page(self, page: ttk.Frame) -> None:
        card = self._card(page)
        ttk.Label(card, text="Install or repair Canvas Agent", style="Section.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=self.install_summary, style="Muted.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(8, 18))

        details = ttk.Frame(card, style="InnerCard.TFrame", padding=16)
        details.pack(fill="x")
        self.install_target_label = ttk.Label(details, text="Orange path: Not selected", style="Muted.TLabel", wraplength=600, justify="left")
        self.install_target_label.pack(anchor="w")
        self.install_version_label = ttk.Label(details, text="Current package version: Unknown", style="Muted.TLabel")
        self.install_version_label.pack(anchor="w", pady=(10, 0))
        ttk.Label(details, textvariable=self.wheel_summary, style="Mini.TLabel", wraplength=600, justify="left").pack(anchor="w", pady=(10, 0))

        action_row = ttk.Frame(card, style="Surface.TFrame")
        action_row.pack(fill="x", pady=(18, 0))
        self.install_button = ttk.Button(action_row, text="Install / Repair", style="Primary.TButton", command=self._begin_install)
        self.install_button.pack(side="left")
        ttk.Button(action_row, text="View Diagnostics", command=self._open_diagnostics_window).pack(side="left", padx=(10, 0))

        self.install_status = ttk.Label(card, text="", style="Muted.TLabel", wraplength=620, justify="left")
        self.install_status.pack(anchor="w", pady=(18, 0))

    def _build_verify_page(self, page: ttk.Frame) -> None:
        card = self._card(page)
        ttk.Label(card, text="Verify the installation", style="Section.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=self.verify_summary, style="Muted.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(8, 18))

        action_row = ttk.Frame(card, style="Surface.TFrame")
        action_row.pack(fill="x")
        self.verify_button = ttk.Button(action_row, text="Run Verification", style="Primary.TButton", command=self._begin_verify)
        self.verify_button.pack(side="left")
        ttk.Button(action_row, text="View Diagnostics", command=self._open_diagnostics_window).pack(side="left", padx=(10, 0))

        self.verify_state = ttk.Label(card, text="Verification has not run yet.", style="Muted.TLabel", wraplength=620, justify="left")
        self.verify_state.pack(anchor="w", pady=(18, 12))

        self.diag_toggle_text = StringVar(value="Show diagnostics")
        self.diag_toggle = ttk.Button(card, textvariable=self.diag_toggle_text, command=self._toggle_inline_diagnostics)
        self.diag_toggle.pack(anchor="w")

        self.inline_diag_frame = ttk.Frame(card, style="InnerCard.TFrame", padding=12)
        self.inline_diag_text = self._create_diagnostics_text(self.inline_diag_frame, height=11)
        self.inline_diag_text.pack(fill="both", expand=True)
        self.inline_diag_visible = False

    def _build_finish_page(self, page: ttk.Frame) -> None:
        hero = self._card(page)
        self.finish_banner = ttk.Label(hero, textvariable=self.finish_title, style="Success.TLabel", padding=(12, 10))
        self.finish_banner.pack(fill="x")
        ttk.Label(hero, textvariable=self.finish_message, style="Muted.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(16, 18))

        details = ttk.Frame(hero, style="InnerCard.TFrame", padding=16)
        details.pack(fill="x")
        ttk.Label(details, textvariable=self.finish_path, style="Muted.TLabel", wraplength=600, justify="left").pack(anchor="w")
        ttk.Label(details, textvariable=self.finish_version, style="Muted.TLabel", wraplength=600, justify="left").pack(anchor="w", pady=(10, 0))

        actions = ttk.Frame(hero, style="Surface.TFrame")
        actions.pack(fill="x", pady=(18, 0))
        self.open_orange_button = ttk.Button(actions, textvariable=self.open_orange_label, style="Primary.TButton", command=self._open_orange)
        self.open_orange_button.pack(side="left")
        ttk.Button(actions, text="View Diagnostics", command=self._open_diagnostics_window).pack(side="left", padx=(10, 0))
        ttk.Button(actions, text="Close", command=self.root.destroy).pack(side="left", padx=(10, 0))

    def _card(self, parent: ttk.Frame, pady: tuple[int, int] = (0, 0)) -> ttk.Frame:
        frame = ttk.Frame(parent, style="Card.TFrame", padding=20)
        frame.pack(fill="x", pady=pady)
        return frame

    def _info_banner(self, parent: ttk.Frame) -> ttk.Frame:
        frame = ttk.Frame(parent, style="InnerCard.TFrame", padding=16)
        frame.pack(fill="x", pady=(18, 0))
        return frame

    def _create_diagnostics_text(self, parent: ttk.Frame, height: int) -> Text:
        text = Text(
            parent,
            height=height,
            wrap="word",
            font=("Consolas", 9),
            bd=0,
            padx=8,
            pady=8,
            background="#f8fafc",
            foreground=TEXT,
        )
        return text

    def _set_step(self, step_index: int) -> None:
        self.current_step = step_index
        page = self.pages[step_index]
        page.tkraise()

        title_map = {
            0: ("Welcome", "A lightweight Windows-style wizard for installing Canvas Agent into Orange."),
            1: ("Detect Orange", "Choose the Orange installation you want to update or repair."),
            2: ("Install / Repair", "Install the bundled package into the selected Orange Python environment."),
            3: ("Verify", "Run a smoke check to confirm the add-on imports and registers correctly."),
            4: ("Finish", "Review the results, open Orange, or keep the diagnostics for reference."),
        }
        title, subtitle = title_map[step_index]
        self.step_title.set(title)
        self.step_subtitle.set(subtitle)
        self.helper_text.set(self._helper_text_for_step(step_index))
        self._refresh_step_labels()
        self._refresh_navigation()
        self._refresh_finish_page()

    def _helper_text_for_step(self, step_index: int) -> str:
        if self.is_busy:
            return self.current_action
        helpers = {
            0: "Press Next to start detection.",
            1: "Select one Orange installation to continue.",
            2: "Install or repair before you move on to verification.",
            3: "Successful verification unlocks the Finish step.",
            4: "Use Open Orange to launch without a console window.",
        }
        return helpers.get(step_index, "")

    def _refresh_step_labels(self) -> None:
        for index, label in enumerate(self.step_labels):
            if index < self.current_step:
                label.configure(style="StepDone.TLabel")
            elif index == self.current_step:
                label.configure(style="StepActive.TLabel")
            else:
                label.configure(style="Sidebar.TLabel")

    def _refresh_navigation(self) -> None:
        self.back_button.configure(state="disabled" if self.current_step == 0 or self.is_busy else "normal")

        if self.current_step == 0:
            next_state = "normal"
            next_text = "Next"
        elif self.current_step == 1:
            next_state = "disabled" if self.selected_install is None or self.is_busy else "normal"
            next_text = "Next"
        elif self.current_step == 2:
            next_state = "disabled" if not self.last_install_result or not self.last_install_result.ok or self.is_busy else "normal"
            next_text = "Next"
        elif self.current_step == 3:
            ready = self.last_smoke_result is not None and self.last_smoke_result.ok
            next_state = "disabled" if not ready or self.is_busy else "normal"
            next_text = "Finish"
        else:
            next_state = "disabled" if self.is_busy else "normal"
            next_text = "Close"

        if self.current_step == 4:
            self.next_button.configure(text=next_text, command=self.root.destroy, state=next_state)
        else:
            self.next_button.configure(text=next_text, command=self._go_next, state=next_state)

        install_ready = self.selected_install is not None and not self.is_busy
        self.install_button.configure(state="normal" if install_ready else "disabled")
        verify_ready = self.selected_install is not None and self.last_install_result is not None and self.last_install_result.ok and not self.is_busy
        self.verify_button.configure(state="normal" if verify_ready else "disabled")

    def _go_back(self) -> None:
        if self.current_step > 0 and not self.is_busy:
            self._set_step(self.current_step - 1)

    def _go_next(self) -> None:
        if self.is_busy:
            return
        if self.current_step == 0:
            self._set_step(1)
            return
        if self.current_step == 1:
            if self.selected_install is None:
                messagebox.showerror("Choose Orange", "Select an Orange installation first.")
                return
            self._refresh_install_details()
            self._set_step(2)
            return
        if self.current_step == 2:
            if not self.last_install_result or not self.last_install_result.ok:
                messagebox.showerror("Install required", "Install or repair Canvas Agent before continuing.")
                return
            self._set_step(3)
            return
        if self.current_step == 3:
            if not self.last_smoke_result or not self.last_smoke_result.ok:
                messagebox.showerror("Verification required", "Run verification successfully before finishing.")
                return
            self._set_step(4)

    def _scan_installs(self, initial: bool = False) -> None:
        self._run_background(
            action="Detecting Orange installations...",
            work=discover_orange_installs,
            on_success=lambda installs: self._finish_scan(installs, initial=initial),
            on_error=lambda exc: self._handle_scan_failure(exc, initial=initial),
        )

    def _finish_scan(self, installs: list[OrangeInstall], initial: bool = False) -> None:
        self.installs = installs
        self.tree.delete(*self.tree.get_children())
        for index, install in enumerate(installs):
            self.tree.insert("", END, iid=str(index), values=(install.label, install.source, str(install.root)))

        if installs:
            self.detect_summary.set(f"Found {len(installs)} Orange installation{'s' if len(installs) != 1 else ''}.")
            self.tree.selection_set("0")
            self.tree.focus("0")
            self._apply_selection(0)
            if not initial:
                self._append_diagnostic("Detection", f"Detected {len(installs)} Orange installation(s).")
        else:
            self.detect_summary.set("No Orange installations were detected automatically.")
            self.selected_install = None
            self.selection_summary.set("No Orange installation is selected. Use Choose Folder to point at an Orange install manually.")
        self._refresh_navigation()

    def _handle_scan_failure(self, exc: Exception, initial: bool = False) -> None:
        self.installs = []
        self.tree.delete(*self.tree.get_children())
        self.selected_install = None
        self.detect_summary.set("Orange detection failed.")
        self.selection_summary.set("Detection did not complete. Review diagnostics or choose a folder manually.")
        self._append_diagnostic("Detection failed", str(exc))
        if not initial:
            messagebox.showerror("Detection failed", str(exc))
        self._refresh_navigation()

    def _choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose your Orange installation folder")
        if not folder:
            return

        result = validate_orange_folder(folder)
        if not result.ok or result.python_executable is None:
            self._append_diagnostic("Manual folder validation", result.message)
            messagebox.showerror("Orange not found", result.message)
            return

        install = OrangeInstall(
            root=Path(folder),
            python_executable=result.python_executable,
            source="manual",
            label="Orange",
        )

        existing_index = next((i for i, item in enumerate(self.installs) if item.root.resolve() == install.root.resolve()), None)
        if existing_index is None:
            self.installs.append(install)
            index = len(self.installs) - 1
            self.tree.insert("", END, iid=str(index), values=(install.label, install.source, str(install.root)))
        else:
            self.installs[existing_index] = install
            index = existing_index
            self.tree.item(str(index), values=(install.label, install.source, str(install.root)))

        self.detect_summary.set(f"Orange was validated at {install.root}.")
        self.tree.selection_set(str(index))
        self.tree.focus(str(index))
        self._apply_selection(index)

    def _on_tree_select(self, _event: object) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        self._apply_selection(int(selection[0]))

    def _apply_selection(self, index: int) -> None:
        if index < 0 or index >= len(self.installs):
            return
        self.selected_install = self.installs[index]
        install = self.selected_install
        self.install_mode = "Install"
        self.selection_summary.set(
            f"{install.label} found via {install.source}.\nPath: {install.root}\nPython: {install.python_executable}"
        )
        self.install_target_label.configure(text=f"Orange path: {install.root}\nPython: {install.python_executable}")
        self.install_summary.set(f"{self.install_mode} Canvas Agent into the selected Orange environment.")
        self.verify_summary.set(f"Run verification for {install.root} after installation completes.")
        self.last_install_result = None
        self.last_smoke_result = None
        self.detected_version = None
        self.launch_error = None
        self.install_status.configure(text="")
        self.verify_state.configure(text="Verification has not run yet.", style="Muted.TLabel")
        self._append_diagnostic("Selection", f"Selected Orange installation at {install.root}")
        self._refresh_navigation()
        self._probe_existing_version()

    def _probe_existing_version(self) -> None:
        if self.selected_install is None:
            return
        python_executable = self.selected_install.python_executable

        def work() -> tuple[bool, str]:
            result = subprocess.run(
                [str(python_executable), "-c", self._package_version_code()],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=WINDOWS_NO_WINDOW,
            )
            return result.returncode == 0, (result.stdout or result.stderr).strip()

        self._run_background(
            action="Checking current Canvas Agent version...",
            work=work,
            on_success=self._finish_probe_version,
            on_error=lambda exc: self._append_diagnostic("Version probe failed", str(exc)),
        )

    def _finish_probe_version(self, result: tuple[bool, str]) -> None:
        ok, output = result
        if ok and output:
            self.detected_version = output
            self.install_mode = "Repair"
            self.install_version_label.configure(text=f"Current package version: {output}")
        else:
            self.detected_version = None
            self.install_mode = "Install"
            self.install_version_label.configure(text="Current package version: Not detected")
        self.install_summary.set(f"{self.install_mode} Canvas Agent into the selected Orange environment.")
        self._refresh_finish_page()

    def _refresh_install_details(self) -> None:
        if self.selected_install is None:
            self.install_target_label.configure(text="Orange path: Not selected")
            self.install_version_label.configure(text="Current package version: Unknown")
            return
        self.install_target_label.configure(
            text=f"Orange path: {self.selected_install.root}\nPython: {self.selected_install.python_executable}"
        )
        version_text = self.detected_version or "Not detected"
        self.install_version_label.configure(text=f"Current package version: {version_text}")
        self.install_summary.set(f"{self.install_mode} Canvas Agent into the selected Orange environment.")

    def _begin_install(self) -> None:
        if self.selected_install is None:
            messagebox.showerror("Choose Orange", "Select an Orange installation first.")
            return
        if not self.wheel_path.exists():
            messagebox.showerror("Wheel not found", f"Could not find installer wheel: {self.wheel_path}")
            return

        install = self.selected_install
        self.install_status.configure(text=f"{self.install_mode}ing Canvas Agent in {install.root}...")
        self.last_install_result = None
        self.last_smoke_result = None
        self.launch_error = None

        self._run_background(
            action=f"{self.install_mode}ing Canvas Agent...",
            work=lambda: install_wheel(install.python_executable, self.wheel_path),
            on_success=self._finish_install,
            on_error=lambda exc: self._finish_install(DetectionResult(False, str(exc))),
        )

    def _finish_install(self, result: DetectionResult) -> None:
        self.last_install_result = result
        self._append_diagnostic(f"{self.install_mode} result", result.message)
        if result.ok:
            self.install_status.configure(
                text=f"Canvas Agent {self.install_mode.lower()} complete. Continue to Verify when you're ready.",
                style="Success.TLabel",
            )
            self.verify_summary.set("Run the smoke check now to confirm import and Orange widget registration.")
        else:
            self.install_status.configure(text=result.message, style="Error.TLabel")
            self.verify_summary.set("Installation did not complete. Review diagnostics, then retry the install step.")
            self._show_inline_diagnostics(True)
            messagebox.showerror("Install failed", result.message)
        self._refresh_navigation()

    def _begin_verify(self) -> None:
        if self.selected_install is None:
            messagebox.showerror("Choose Orange", "Select an Orange installation first.")
            return
        self.verify_state.configure(text="Running smoke check...", style="Muted.TLabel")
        self.last_smoke_result = None

        install = self.selected_install
        self._run_background(
            action="Running Canvas Agent smoke check...",
            work=lambda: self._verify_and_capture_details(install.python_executable),
            on_success=self._finish_verify,
            on_error=lambda exc: self._finish_verify((DetectionResult(False, str(exc)), None, str(exc))),
        )

    def _verify_and_capture_details(self, python_executable: Path) -> tuple[DetectionResult, str | None, str]:
        smoke = smoke_check(python_executable)
        detail_lines = [f"Smoke check: {smoke.message}"]
        version = None

        result = subprocess.run(
            [str(python_executable), "-c", self._package_version_code()],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=WINDOWS_NO_WINDOW,
        )
        version_output = (result.stdout or "").strip()
        if result.returncode == 0 and version_output:
            version = version_output
            detail_lines.append(f"Package version: {version}")
        elif result.returncode != 0:
            detail_lines.append((result.stderr or result.stdout or "Version lookup failed.").strip())
        return smoke, version, "\n".join(detail_lines)

    def _finish_verify(self, payload: tuple[DetectionResult, str | None, str]) -> None:
        smoke, version, details = payload
        self.last_smoke_result = smoke
        if version:
            self.detected_version = version
        self._append_diagnostic("Verification", details)

        if smoke.ok:
            version_text = self.detected_version or self._fallback_version_from_wheel()
            self.verify_state.configure(
                text=f"Verification passed. Canvas Agent {version_text} is ready in Orange.",
                style="Success.TLabel",
            )
            self.verify_summary.set("Everything looks good. Move to Finish for launch options and diagnostics.")
            self._set_step(4)
        else:
            self.verify_state.configure(text=smoke.message, style="Error.TLabel")
            self.verify_summary.set("Verification failed. Review or copy diagnostics, then retry after fixing the issue.")
            self._show_inline_diagnostics(True)
            messagebox.showerror("Smoke check failed", smoke.message)
            self._refresh_navigation()

    def _refresh_finish_page(self) -> None:
        install = self.selected_install
        version_text = self.detected_version or self._fallback_version_from_wheel()
        self.finish_version.set(f"Canvas Agent version: {version_text}")
        if install is not None:
            self.finish_path.set(f"Orange path: {install.root}")
            self.open_orange_label.set(f"Open Orange from {install.label}")
        else:
            self.finish_path.set("Orange path: Not available")
            self.open_orange_label.set("Open Orange")

        if self.last_smoke_result and self.last_smoke_result.ok:
            self.finish_banner.configure(style="Success.TLabel")
            self.finish_title.set("Canvas Agent is ready")
            self.finish_message.set("Installation and verification completed successfully. You can open Orange now or keep the diagnostics for your records.")
        elif self.last_smoke_result and not self.last_smoke_result.ok:
            self.finish_banner.configure(style="Error.TLabel")
            self.finish_title.set("Verification needs attention")
            self.finish_message.set("The installer reached the verification stage, but the smoke check failed. Review diagnostics before launching Orange.")
        elif self.last_install_result and not self.last_install_result.ok:
            self.finish_banner.configure(style="Error.TLabel")
            self.finish_title.set("Installation needs attention")
            self.finish_message.set("The package install step failed. Review diagnostics and retry the install step.")
        else:
            self.finish_banner.configure(style="Success.TLabel")
            self.finish_title.set("Setup in progress")
            self.finish_message.set("Complete detection, installation, and verification to finish setup.")

    def _open_orange(self) -> None:
        if self.selected_install is None:
            messagebox.showerror("Choose Orange", "Select an Orange installation first.")
            return

        try:
            subprocess.Popen(
                [
                    str(self.selected_install.python_executable),
                    "-m",
                    "Orange.canvas",
                    "--force-discovery",
                ],
                creationflags=WINDOWS_NO_WINDOW,
            )
            self.launch_error = None
        except OSError as exc:
            self.launch_error = str(exc)
            self._append_diagnostic("Launch failed", self.launch_error)
            messagebox.showerror("Open Orange failed", self.launch_error)

    def _toggle_inline_diagnostics(self) -> None:
        self._show_inline_diagnostics(not self.inline_diag_visible)

    def _show_inline_diagnostics(self, visible: bool) -> None:
        self.inline_diag_visible = visible
        if visible:
            self.inline_diag_frame.pack(fill="both", expand=True, pady=(12, 0))
            self.diag_toggle_text.set("Hide diagnostics")
        else:
            self.inline_diag_frame.pack_forget()
            self.diag_toggle_text.set("Show diagnostics")

    def _open_diagnostics_window(self) -> None:
        window = self.root.winfo_toplevel()
        dialog = Toplevel(window)
        dialog.title("Diagnostics")
        dialog.geometry("760x520")
        dialog.minsize(680, 420)

        outer = ttk.Frame(dialog, style="Content.TFrame", padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Diagnostics", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Use Copy All if you need to share setup details or paste them into a support request.",
            style="Muted.TLabel",
            wraplength=680,
            justify="left",
        ).pack(anchor="w", pady=(6, 14))

        text = self._create_diagnostics_text(outer, height=22)
        text.pack(fill="both", expand=True)
        self._fill_diagnostics_text(text)

        buttons = ttk.Frame(outer, style="Content.TFrame")
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="Copy All", command=lambda: self._copy_diagnostics(text.get("1.0", END))).pack(side="left")
        ttk.Button(buttons, text="Close", command=dialog.destroy).pack(side="right")

        dialog.transient(self.root)
        dialog.grab_set()

    def _copy_diagnostics(self, content: str | None = None) -> None:
        text = (content or self._diagnostics_blob()).strip()
        if not text:
            text = "No diagnostics captured."
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _append_diagnostic(self, title: str, body: str) -> None:
        body = body.strip() or "No details."
        self.diagnostics_sections.append((title, body))
        self._fill_diagnostics_text(self.inline_diag_text)

    def _fill_diagnostics_text(self, text_widget) -> None:
        text_widget.configure(state="normal")
        text_widget.delete("1.0", END)
        text_widget.insert("1.0", self._diagnostics_blob())
        text_widget.configure(state="disabled")

    def _diagnostics_blob(self) -> str:
        lines = [
            "Canvas Agent Setup Diagnostics",
            f"Wheel: {self.wheel_path}",
            f"Selected Orange: {self.selected_install.root if self.selected_install else 'None'}",
        ]
        for title, body in self.diagnostics_sections:
            lines.append("")
            lines.append(f"[{title}]")
            lines.append(body)
        if len(lines) == 3:
            lines.append("")
            lines.append("No diagnostics captured yet.")
        return "\n".join(lines)

    def _run_background(self, *, action: str, work, on_success, on_error) -> None:
        if self.is_busy:
            return
        self.is_busy = True
        self.current_action = action
        self.helper_text.set(action)
        self._refresh_navigation()

        def runner() -> None:
            try:
                result = work()
            except Exception as exc:  # pragma: no cover - UI fallback
                self.root.after(0, lambda: self._finish_background_error(on_error, exc))
            else:
                self.root.after(0, lambda: self._finish_background_success(on_success, result))

        threading.Thread(target=runner, daemon=True).start()

    def _finish_background_success(self, callback, result) -> None:
        self.is_busy = False
        self.current_action = ""
        callback(result)
        self.helper_text.set(self._helper_text_for_step(self.current_step))
        self._refresh_navigation()

    def _finish_background_error(self, callback, error: Exception) -> None:
        self.is_busy = False
        self.current_action = ""
        callback(error)
        self.helper_text.set(self._helper_text_for_step(self.current_step))
        self._refresh_navigation()

    def _fallback_version_from_wheel(self) -> str:
        stem = self.wheel_path.stem
        for separator in ("-", "_"):
            if separator in stem:
                parts = stem.split(separator)
                for part in reversed(parts):
                    if part and part[0].isdigit():
                        return part
        return "Installed package version unavailable"

    def _package_version_code(self) -> str:
        return (
            "from importlib.metadata import PackageNotFoundError, version\n"
            "found = ''\n"
            "for name in ('Orange3-CanvasAgent', 'orange3-canvasagent'):\n"
            "    try:\n"
            "        found = version(name)\n"
            "        break\n"
            "    except PackageNotFoundError:\n"
            "        pass\n"
            "print(found)\n"
        )

    def _default_wheel_path(self) -> Path:
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        wheels = sorted(base.glob("Orange3_CanvasAgent-*.whl")) + sorted(base.glob("orange3_canvasagent-*.whl"))
        if wheels:
            return wheels[-1]
        project_dist = Path(__file__).resolve().parents[1] / "dist"
        wheels = sorted(project_dist.glob("*.whl"))
        return wheels[-1] if wheels else project_dist / "Orange3_CanvasAgent.whl"


def main() -> None:
    CanvasAgentInstaller().run()


if __name__ == "__main__":
    main()
