from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, Button, Frame, Label, Listbox, Tk, filedialog, messagebox

from installer.core import (
    OrangeInstall,
    discover_orange_installs,
    install_wheel,
    smoke_check,
    validate_orange_folder,
)


class CanvasAgentInstaller:
    def __init__(self, wheel_path: Path | None = None):
        self.root = Tk()
        self.root.title("Canvas Agent Setup")
        self.root.geometry("720x460")
        self.wheel_path = wheel_path or self._default_wheel_path()
        self.installs: list[OrangeInstall] = []

        Label(
            self.root,
            text="Install Canvas Agent into Orange",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(16, 4))
        Label(
            self.root,
            text="Choose your Orange installation, then install the add-on.",
            font=("Segoe UI", 10),
        ).pack(pady=(0, 12))

        self.listbox = Listbox(self.root, height=8)
        self.listbox.pack(fill=BOTH, expand=True, padx=16)

        buttons = Frame(self.root)
        buttons.pack(fill=BOTH, padx=16, pady=12)
        Button(buttons, text="Rescan", command=self.scan).pack(side=LEFT)
        Button(buttons, text="Choose Folder...", command=self.choose_folder).pack(side=LEFT, padx=8)
        Button(buttons, text="Install", command=self.install).pack(side=RIGHT)

        self.status = Label(self.root, text="", anchor="w")
        self.status.pack(fill=BOTH, padx=16, pady=(0, 16))
        self.scan()

    def run(self) -> None:
        self.root.mainloop()

    def scan(self) -> None:
        self.installs = discover_orange_installs()
        self._refresh_list()
        if self.installs:
            self.status.config(text="Found Orange. Click Install to continue.")
        else:
            self.status.config(text="No Orange install found automatically. Click Choose Folder.")

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose your Orange installation folder")
        if not folder:
            return
        result = validate_orange_folder(folder)
        if not result.ok or result.python_executable is None:
            messagebox.showerror("Orange not found", result.message)
            return
        self.installs.append(
            OrangeInstall(
                root=Path(folder),
                python_executable=result.python_executable,
                source="manual",
                label="Orange",
            )
        )
        self._refresh_list()
        self.listbox.selection_clear(0, END)
        self.listbox.selection_set(END)

    def install(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Choose Orange", "Select an Orange installation first.")
            return
        if not self.wheel_path or not self.wheel_path.exists():
            messagebox.showerror("Wheel not found", f"Could not find installer wheel: {self.wheel_path}")
            return

        install = self.installs[selection[0]]
        self.status.config(text="Installing Canvas Agent...")
        self.root.update_idletasks()
        result = install_wheel(install.python_executable, self.wheel_path)
        if not result.ok:
            messagebox.showerror("Install failed", result.message)
            self.status.config(text="Install failed.")
            return
        smoke = smoke_check(install.python_executable)
        if not smoke.ok:
            messagebox.showerror("Smoke check failed", smoke.message)
            self.status.config(text="Installed, but smoke check failed.")
            return
        self.status.config(text="Canvas Agent is installed. Opening Orange...")
        subprocess.Popen([str(install.python_executable), "-m", "Orange.canvas", "--force-discovery"])
        messagebox.showinfo("Installed", "Canvas Agent was installed. Orange is opening now.")

    def _refresh_list(self) -> None:
        self.listbox.delete(0, END)
        for install in self.installs:
            self.listbox.insert(
                END,
                f"{install.label} ({install.source}) - {install.root}",
            )
        if self.installs:
            self.listbox.selection_set(0)

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

