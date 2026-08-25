"""GUI для конвертації зображень в ASCII-арт (tkinter)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

from PIL import Image
from tkinter import filedialog, messagebox, ttk

from ascii_art_gui import FULL_RAMP, build_charset, to_ascii

APP_TITLE = "ASCII-Арт"
BG = "#f4e8c1"  # кремовий фон
PANEL = "#ffd166"  # жовта панель
ACCENT = "#ef476f"  # рожево-червоний акцент
INK = "#1d1d1d"  # майже чорний
FONT = ("Segoe UI", 11, "bold")


class AsciiApp(tk.Tk):
    """Вікно застосунку."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.configure(bg=BG)

        self.image_path: Path | None = None

        self._build_ui()
        self._center_window(980, 680)

    # ---------- UI ----------

    def _build_ui(self) -> None:
        container = tk.Frame(self, bg=BG, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        self._build_header(container)
        self._build_toolbar(container)

        # Попередній перегляд
        preview_frame = tk.Frame(
            container,
            bg=PANEL,
            highlightbackground=INK,
            highlightthickness=3,
        )
        preview_frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            preview_frame,
            bg="#ffffff",
            fg=INK,
            font=("Consolas", 10),
            wrap="none",
            borderwidth=0,
            highlightthickness=0,
            padx=8,
            pady=8,
            undo=True,
        )
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(preview_frame, command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)

        self._build_footer(container)

    def _build_header(self, container: tk.Frame) -> None:
        header = tk.Frame(container, bg=BG)
        header.pack(fill="x", pady=(0, 12))

        title = tk.Label(
            header,
            text="ФОТО → ASCII-АРТ",
            bg=BG,
            fg=INK,
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(side="left")

        hint = tk.Label(
            header,
            text="Вантаж картинку і отримуй її з символів",
            bg=BG,
            fg=INK,
            font=("Segoe UI", 11),
        )
        hint.pack(side="left", padx=(12, 0), pady=(6, 0))

    def _build_toolbar(self, container: tk.Frame) -> None:
        toolbar = tk.Frame(
            container,
            bg=PANEL,
            highlightbackground=INK,
            highlightthickness=3,
            padx=12,
            pady=10,
        )
        toolbar.pack(fill="x", pady=(0, 12))

        self.btn_open = self._fat_button(
            toolbar, "Відкрити фото", ACCENT, self.open_image
        )
        self.btn_open.pack(side="left")

        self.btn_save = self._fat_button(
            toolbar, "Зберегти .txt", "#06d6a0", self.save_text
        )
        self.btn_save.pack(side="left", padx=(10, 0))
        self.btn_save.configure(state="disabled")

        tk.Label(
            toolbar, text="Ширина:", bg=PANEL, fg=INK, font=FONT
        ).pack(side="left", padx=(24, 6))

        self.scale = tk.Scale(
            toolbar,
            from_=40,
            to=200,
            orient="horizontal",
            bg=PANEL,
            fg=INK,
            highlightthickness=0,
            font=FONT,
            length=220,
            command=self._on_width_change,
        )
        self.scale.set(90)
        self.scale.pack(side="left")

        tk.Label(
            toolbar, text="Точність:", bg=PANEL, fg=INK, font=FONT
        ).pack(side="left", padx=(24, 6))

        self.accuracy = tk.Scale(
            toolbar,
            from_=2,
            to=len(FULL_RAMP),
            orient="horizontal",
            bg=PANEL,
            fg=INK,
            highlightthickness=0,
            font=FONT,
            length=160,
            command=self._on_accuracy_change,
        )
        self.accuracy.set(10)
        self.accuracy.pack(side="left")

        self.invert_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            toolbar,
            text="Світлий фон (інверсія)",
            variable=self.invert_var,
            bg=PANEL,
            fg=INK,
            font=FONT,
            activebackground=PANEL,
            selectcolor="#d4b85c",
            command=self.convert,
        ).pack(side="left", padx=(24, 0))

    def _build_footer(self, container: tk.Frame) -> None:
        footer = tk.Frame(container, bg=BG)
        footer.pack(fill="x", pady=(10, 0))

        self.status = tk.Label(
            footer,
            text="Обери фото, щоб почати",
            bg=BG,
            fg=INK,
            font=FONT,
            anchor="w",
        )
        self.status.pack(fill="x")

    def _fat_button(self, parent: tk.Widget, text: str, color: str, command):
        """Кнопка в картонно-бруталістичному стилі: товста рамка, плоский колір."""
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=INK,
            font=FONT,
            relief="flat",
            highlightbackground=INK,
            highlightthickness=3,
            borderwidth=0,
            padx=18,
            pady=8,
            activebackground=color,
            activeforeground="#ffffff",
            cursor="hand2",
        )

    # ---------- Дії ----------

    def open_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Відкрити зображення",
            filetypes=[
                ("Зображення", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                ("Всі файли", "*.*"),
            ],
        )
        if not path:
            return

        try:
            with Image.open(path) as img:
                img.verify()
        except Exception:
            messagebox.showerror(
                APP_TITLE, "Не вдалося відкрити зображення. Файл може бути пошкоджений."
            )
            return

        self.image_path = Path(path)
        self.status.configure(text=f"Завантажено: {self.image_path.name}")
        self.btn_save.configure(state="normal")
        self.convert()

    def convert(self, _event: str | None = None) -> None:
        if self.image_path is None:
            return

        try:
            with Image.open(self.image_path) as img:
                img.load()
                lines = to_ascii(
                    img,
                    self.scale.get(),
                    charset=build_charset(self.accuracy.get()),
                    invert=self.invert_var.get(),
                )
        except Exception as exc:
            messagebox.showerror(
                APP_TITLE, f"Помилка конвертації:\n{exc}"
            )
            self.status.configure(text="Помилка конвертації")
            return

        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.status.configure(
            text=f"Готово: {len(lines[0])}×{len(lines)} символів  ·  {self.image_path.name}"
        )

    def save_text(self) -> None:
        content = self.text.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo(APP_TITLE, "Спершу сконвертуй зображення.")
            return

        default_name = (
            f"ascii_{self.image_path.stem}.txt"
            if self.image_path
            else "ascii_art.txt"
        )
        path = filedialog.asksaveasfilename(
            title="Зберегти ASCII-арт",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Текстовий файл", "*.txt"), ("Всі файли", "*.*")],
        )
        if not path:
            return

        try:
            Path(path).write_text(content, encoding="utf-8")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Не вдалося зберегти:\n{exc}")
            return

        self.status.configure(text=f"Збережено: {path}")

    def _on_width_change(self, _value: str) -> None:
        self.convert()

    def _on_accuracy_change(self, _value: str) -> None:
        self.convert()

    # ---------- Службове ----------

    def _center_window(self, width: int, height: int) -> None:
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"+{x}+{y}")
        self.minsize(720, 480)


def main() -> None:
    app = AsciiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
