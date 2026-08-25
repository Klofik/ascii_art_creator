"""ASCII art converter with GUI - a self-contained script (tkinter + Pillow).

Run:  python ascii_art_gui.py
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

from PIL import Image
from tkinter import filedialog, messagebox, ttk

# ---------- Converter ----------

DEFAULT_CHARSET = "@%#*+=-:. "

FULL_RAMP = (
    "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
)

CHAR_ASPECT = 0.5


def build_charset(count, ramp=FULL_RAMP):
    if count < 1:
        raise ValueError("count must be greater than 0")
    if count == 1:
        return ramp[0]
    if count >= len(ramp):
        return ramp
    step = (len(ramp) - 1) / (count - 1)
    indices = sorted({round(i * step) for i in range(count)})
    return "".join(ramp[i] for i in indices)


def to_ascii(image, width, *, charset=DEFAULT_CHARSET, invert=False):
    if width < 1:
        raise ValueError("width must be greater than 0")
    if not charset:
        raise ValueError("charset cannot be empty")

    gray = image.convert("L")
    height = max(1, round(gray.height / gray.width * width * CHAR_ASPECT))

    small = gray.resize((width, height), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())

    active_charset = charset[::-1] if invert else charset
    levels = len(active_charset)

    lines = []
    for row in range(height):
        start = row * width
        end = start + width
        line = "".join(
            active_charset[min(levels - 1, value * levels // 256)]
            for value in pixels[start:end]
        )
        lines.append(line)

    return lines


# ---------- GUI ----------

APP_TITLE = "ASCII Art"
BG = "#071a2c"
PANEL = "#0d2340"
ACCENT = "#3da5ff"
INK = "#eaf4ff"
FONT = ("Segoe UI", 11, "bold")


class AsciiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.configure(bg=BG)
        self.image_path = None
        self._build_ui()
        self._center_window(1180, 680)

    def _build_ui(self):
        container = tk.Frame(self, bg=BG, padx=16, pady=16)
        container.pack(fill="both", expand=True)
        self._build_header(container)
        self._build_toolbar(container)

        preview_frame = tk.Frame(container, bg=PANEL, highlightbackground="#1d4d8f", highlightthickness=3)
        preview_frame.pack(fill="both", expand=True)

        self.text = tk.Text(preview_frame, bg="#061827", fg="#dfefff", font=("Consolas", 10), wrap="none",
                            borderwidth=0, highlightthickness=0, padx=8, pady=8, undo=True,
                            insertbackground="#dfefff")
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(preview_frame, command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)

        self._build_footer(container)

    def _build_header(self, container):
        header = tk.Frame(container, bg=BG)
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="PHOTO -> ASCII ART", bg=BG, fg=INK, font=("Segoe UI", 20, "bold")).pack(side="left")
        tk.Label(header, text="Load an image and turn it into characters", bg=BG, fg=INK,
                 font=("Segoe UI", 11)).pack(side="left", padx=(12, 0), pady=(6, 0))

    def _build_toolbar(self, container):
        toolbar = tk.Frame(container, bg=PANEL, highlightbackground="#1d4d8f", highlightthickness=3, padx=12, pady=10)
        toolbar.pack(fill="x", pady=(0, 12))

        self.btn_open = self._fat_button(toolbar, "Open image", ACCENT, self.open_image)
        self.btn_open.pack(side="left")

        self.btn_save = self._fat_button(toolbar, "Save .txt", "#1b8cff", self.save_text)
        self.btn_save.pack(side="left", padx=(10, 0))
        self.btn_save.configure(state="disabled")

        tk.Label(toolbar, text="Width:", bg=PANEL, fg=INK, font=FONT).pack(side="left", padx=(24, 6))
        self.scale = tk.Scale(toolbar, from_=40, to=200, orient="horizontal", bg=PANEL, fg=INK,
                              highlightthickness=0, font=FONT, length=220, command=self._on_width_change)
        self.scale.set(90)
        self.scale.pack(side="left")

        tk.Label(toolbar, text="Detail:", bg=PANEL, fg=INK, font=FONT).pack(side="left", padx=(24, 6))
        self.accuracy = tk.Scale(toolbar, from_=2, to=len(FULL_RAMP), orient="horizontal", bg=PANEL, fg=INK,
                                 highlightthickness=0, font=FONT, length=160, command=self._on_accuracy_change)
        self.accuracy.set(10)
        self.accuracy.pack(side="left")

        self.invert_var = tk.BooleanVar(value=False)
        tk.Checkbutton(toolbar, text="Light background (invert)", variable=self.invert_var, bg=PANEL, fg=INK,
                       font=FONT, activebackground=PANEL, selectcolor="#1d4d8f", command=self.convert
                       ).pack(side="left", padx=(24, 0))

    def _build_footer(self, container):
        footer = tk.Frame(container, bg=BG)
        footer.pack(fill="x", pady=(10, 0))
        self.status = tk.Label(footer, text="Choose an image to get started", bg=BG, fg=INK, font=FONT, anchor="w")
        self.status.pack(fill="x")

    def _fat_button(self, parent, text, color, command):
        return tk.Button(parent, text=text, command=command, bg=color, fg="#f4fbff", font=FONT, relief="flat",
                         highlightbackground="#9dc9ff", highlightthickness=3, borderwidth=0, padx=18, pady=8,
                         activebackground="#1b8cff", activeforeground="#ffffff", cursor="hand2")

    def open_image(self):
        path = filedialog.askopenfilename(title="Open image", filetypes=[
            ("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("All files", "*.*")])
        if not path:
            return
        try:
            with Image.open(path) as img:
                img.verify()
        except Exception:
            messagebox.showerror(APP_TITLE, "Could not open the image. The file may be corrupted.")
            return
        self.image_path = Path(path)
        self.status.configure(text=f"Loaded: {self.image_path.name}")
        self.btn_save.configure(state="normal")
        self.convert()

    def convert(self, _event=None):
        if self.image_path is None:
            return
        try:
            with Image.open(self.image_path) as img:
                img.load()
                lines = to_ascii(img, self.scale.get(),
                                 charset=build_charset(self.accuracy.get()),
                                 invert=self.invert_var.get())
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Conversion error:\n{exc}")
            self.status.configure(text="Conversion error")
            return
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.status.configure(text=f"Ready: {len(lines[0])}x{len(lines)} characters  ·  {self.image_path.name}")

    def save_text(self):
        content = self.text.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo(APP_TITLE, "Convert an image first.")
            return
        default_name = f"ascii_{self.image_path.stem}.txt" if self.image_path else "ascii_art.txt"
        path = filedialog.asksaveasfilename(title="Save ASCII art", defaultextension=".txt",
                                            initialfile=default_name,
                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            Path(path).write_text(content, encoding="utf-8")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not save the file:\n{exc}")
            return
        self.status.configure(text=f"Saved: {path}")

    def _on_width_change(self, _value):
        self.convert()

    def _on_accuracy_change(self, _value):
        self.convert()

    def _center_window(self, width, height):
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"+{x}+{y}")
        self.minsize(720, 480)


def main():
    app = AsciiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
