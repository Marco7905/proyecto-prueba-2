"""Interfaz gráfica para reducir lotes de imágenes en Windows."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
from queue import Empty, Queue

from reduce_image import ResizeOptions, discover_images, reduce_image_in_place


class ReduceImagesApp(ttk.Frame):
    """Aplicación principal con una interfaz amigable."""

    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=24, style="Card.TFrame")
        self.master = master

        self.target_path = tk.StringVar()
        self.mode = tk.StringVar(value="scale")
        self.scale_value = tk.DoubleVar(value=50)
        self.width_value = tk.StringVar()
        self.height_value = tk.StringVar()
        self.status_text = tk.StringVar(value="Selecciona una carpeta o imagen para comenzar.")
        self.progress_value = tk.IntVar(value=0)

        self._queue: Queue[tuple] = Queue()
        self._is_running = False

        self._configure_styles()
        self._build_layout()
        self._process_queue()

    # ------------------------------------------------------------------ UI
    def _configure_styles(self) -> None:
        self.master.title("Reductor de Imágenes")
        self.master.configure(bg="#f5f7fb")
        self.master.minsize(780, 580)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Card.TFrame", background="#ffffff")
        style.configure(
            "Title.TLabel",
            background="#ffffff",
            font=("Segoe UI", 20, "bold"),
            foreground="#1f2937",
        )
        style.configure(
            "Subtitle.TLabel",
            background="#ffffff",
            font=("Segoe UI", 11),
            foreground="#4b5563",
            wraplength=640,
        )
        style.configure(
            "Section.TLabelframe",
            background="#ffffff",
            font=("Segoe UI", 11, "bold"),
            foreground="#1d4ed8",
        )
        style.configure("Section.TLabelframe.Label", background="#ffffff", foreground="#1d4ed8")
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 11, "bold"),
            foreground="#ffffff",
            background="#4f46e5",
            padding=10,
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#4338ca"), ("disabled", "#a5b4fc")],
            foreground=[("disabled", "#e2e8f0")],
        )
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="#4338ca",
            background="#e0e7ff",
            padding=8,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#c7d2fe")],
            foreground=[("disabled", "#94a3b8")],
        )
        style.configure("CardInner.TFrame", background="#ffffff")
        style.configure(
            "Status.TLabel",
            background="#ffffff",
            font=("Segoe UI", 10, "italic"),
            foreground="#334155",
        )

    def _build_layout(self) -> None:
        self.grid(column=0, row=0, sticky="nsew")
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        title = ttk.Label(
            self,
            text="Reductor inteligente de imágenes",
            style="Title.TLabel",
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(
            self,
            text=(
                "Reduce automáticamente todas las imágenes de una carpeta y sus subcarpetas,"
                " conservando cada formato original sin ampliar ninguna fotografía."
            ),
            style="Subtitle.TLabel",
            anchor="w",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 18))

        path_frame = ttk.Frame(self, style="CardInner.TFrame", padding=(18, 14))
        path_frame.grid(row=2, column=0, sticky="ew")
        path_frame.columnconfigure(1, weight=1)

        ttk.Label(
            path_frame,
            text="Destino a procesar",
            style="Subtitle.TLabel",
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        entry = ttk.Entry(path_frame, textvariable=self.target_path, state="readonly")
        entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 12))

        ttk.Button(
            path_frame,
            text="Elegir carpeta",
            style="Secondary.TButton",
            command=self._choose_directory,
        ).grid(row=2, column=0, sticky="w")
        ttk.Button(
            path_frame,
            text="Elegir imagen",
            style="Secondary.TButton",
            command=self._choose_file,
        ).grid(row=2, column=1, sticky="w", padx=(12, 0))
        ttk.Button(
            path_frame,
            text="Limpiar selección",
            style="Secondary.TButton",
            command=self._clear_selection,
        ).grid(row=2, column=2, sticky="e")

        options_frame = ttk.LabelFrame(
            self,
            text="Opciones de reducción",
            style="Section.TLabelframe",
            padding=(18, 14),
        )
        options_frame.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)

        ttk.Radiobutton(
            options_frame,
            text="Reducir por porcentaje",
            variable=self.mode,
            value="scale",
            command=self._on_mode_change,
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            options_frame,
            text="Limitar por ancho/alto",
            variable=self.mode,
            value="dimensions",
            command=self._on_mode_change,
        ).grid(row=0, column=1, sticky="w", pady=(0, 6))

        scale_frame = ttk.Frame(options_frame, style="CardInner.TFrame")
        scale_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 6))
        scale_frame.columnconfigure(0, weight=1)

        self.scale_indicator = ttk.Label(
            scale_frame,
            text=self._format_scale_label(self.scale_value.get()),
            style="Subtitle.TLabel",
            anchor="w",
        )
        self.scale_indicator.grid(row=0, column=0, sticky="w")

        self.scale_slider = ttk.Scale(
            scale_frame,
            from_=10,
            to=100,
            orient="horizontal",
            variable=self.scale_value,
            command=self._on_scale_change,
        )
        self.scale_slider.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        dims_frame = ttk.Frame(options_frame, style="CardInner.TFrame")
        dims_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        dims_frame.columnconfigure(0, weight=1)
        dims_frame.columnconfigure(1, weight=1)

        ttk.Label(
            dims_frame,
            text="Ancho (px)",
            style="Subtitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        self.width_entry = ttk.Entry(dims_frame, textvariable=self.width_value)
        self.width_entry.grid(row=1, column=0, sticky="ew", padx=(0, 12))

        ttk.Label(
            dims_frame,
            text="Alto (px)",
            style="Subtitle.TLabel",
        ).grid(row=0, column=1, sticky="w")
        self.height_entry = ttk.Entry(dims_frame, textvariable=self.height_value)
        self.height_entry.grid(row=1, column=1, sticky="ew")

        ttk.Label(
            dims_frame,
            text="Se toman como límites máximos; nunca se agrandan las imágenes.",
            style="Status.TLabel",
            wraplength=360,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        action_frame = ttk.Frame(self, style="CardInner.TFrame", padding=(18, 16))
        action_frame.grid(row=4, column=0, sticky="ew", pady=(18, 0))
        action_frame.columnconfigure(0, weight=1)

        self.start_button = ttk.Button(
            action_frame,
            text="Iniciar reducción",
            style="Accent.TButton",
            command=self._start_processing,
        )
        self.start_button.grid(row=0, column=0, sticky="ew")

        self.progress_bar = ttk.Progressbar(
            action_frame,
            variable=self.progress_value,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(16, 0))

        self.status_label = ttk.Label(
            action_frame,
            textvariable=self.status_text,
            style="Status.TLabel",
        )
        self.status_label.grid(row=2, column=0, sticky="w", pady=(8, 0))

        log_frame = ttk.LabelFrame(
            self,
            text="Registro del proceso",
            style="Section.TLabelframe",
            padding=(18, 12),
        )
        log_frame.grid(row=5, column=0, sticky="nsew", pady=(18, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        self.log_widget = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=("Cascadia Code", 10),
            bg="#0f172a",
            fg="#f1f5f9",
            insertbackground="#f1f5f9",
            relief="flat",
            borderwidth=8,
            wrap="word",
        )
        self.log_widget.grid(row=0, column=0, sticky="nsew")
        self.log_widget.configure(state="disabled")

        self._on_mode_change()

    # ----------------------------------------------------------------- Events
    def _choose_directory(self) -> None:
        path = filedialog.askdirectory(title="Selecciona la carpeta de imágenes")
        if path:
            self.target_path.set(path)

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecciona una imagen",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp *.ico"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if path:
            self.target_path.set(path)

    def _clear_selection(self) -> None:
        self.target_path.set("")

    def _on_mode_change(self) -> None:
        is_scale = self.mode.get() == "scale"
        state_slider = "!disabled" if is_scale else "disabled"
        state_entries = "disabled" if is_scale else "normal"

        if is_scale:
            self.width_value.set("")
            self.height_value.set("")

        self.scale_slider.state([state_slider])
        self.width_entry.configure(state=state_entries)
        self.height_entry.configure(state=state_entries)

    def _on_scale_change(self, _value: str) -> None:
        self.scale_indicator.configure(text=self._format_scale_label(self.scale_value.get()))

    @staticmethod
    def _format_scale_label(scale: float) -> str:
        return f"Reducción: {int(scale)} % del tamaño original"

    # --------------------------------------------------------------- Procesado
    def _start_processing(self) -> None:
        if self._is_running:
            return

        target = self.target_path.get().strip()
        if not target:
            messagebox.showwarning("Falta la ruta", "Selecciona primero una carpeta o imagen para procesar.")
            return

        path = Path(target)
        if not path.exists():
            messagebox.showerror("Ruta no válida", "La ruta seleccionada ya no existe.")
            return

        try:
            options = self._build_options()
        except ValueError as exc:
            messagebox.showerror("Opciones inválidas", str(exc))
            return

        images = discover_images(path)
        if not images:
            messagebox.showinfo(
                "Sin imágenes",
                "No se encontraron imágenes compatibles en la ruta seleccionada.",
            )
            return

        self._reset_log()
        self.progress_bar.configure(maximum=len(images))
        self.progress_value.set(0)
        self.status_text.set("Procesando imágenes...")
        self._log(f"Se encontraron {len(images)} imagen(es). Iniciando redimensionado...")
        self._is_running = True
        self.start_button.state(["disabled"])

        def worker() -> None:
            processed: list[Path] = []
            errors: list[tuple[Path, Exception]] = []
            for index, image_path in enumerate(images, start=1):
                try:
                    if reduce_image_in_place(image_path, options):
                        processed.append(image_path)
                        message = f"✔ Redimensionada: {image_path}"
                    else:
                        message = f"• Sin cambios: {image_path}"
                except Exception as exc:  # pragma: no cover - GUI feedback
                    errors.append((image_path, exc))
                    message = f"✖ Error con {image_path}: {exc}"
                finally:
                    self._queue.put(("progress", index, message))
            self._queue.put(("finished", processed, errors))

        threading.Thread(target=worker, daemon=True).start()

    def _build_options(self) -> ResizeOptions:
        if self.mode.get() == "scale":
            scale = round(self.scale_value.get()) / 100
            options = ResizeOptions(scale=scale)
        else:
            try:
                width = int(self.width_value.get()) if self.width_value.get().strip() else None
                height = int(self.height_value.get()) if self.height_value.get().strip() else None
            except ValueError as exc:  # pragma: no cover - validación en GUI
                raise ValueError("El ancho y el alto deben ser números enteros.") from exc
            options = ResizeOptions(width=width, height=height)
        options.validate()
        return options

    def _reset_log(self) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.delete("1.0", tk.END)
        self.log_widget.configure(state="disabled")

    def _log(self, message: str) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state="disabled")

    def _process_queue(self) -> None:
        try:
            while True:
                event = self._queue.get_nowait()
                kind = event[0]
                if kind == "progress":
                    _kind, value, text = event
                    self.progress_value.set(value)
                    self.progress_bar.configure(value=value)
                    self._log(text)
                elif kind == "finished":
                    _kind, processed, errors = event
                    self._finish_processing(processed, errors)
        except Empty:
            pass
        finally:
            self.after(100, self._process_queue)

    def _finish_processing(
        self,
        processed: list[Path],
        errors: list[tuple[Path, Exception]],
    ) -> None:
        if not self._is_running:
            return

        self._is_running = False
        self.start_button.state(["!disabled"])

        summary = f"Proceso completado. {len(processed)} imagen(es) modificadas."
        if errors:
            summary += f" {len(errors)} archivo(s) no se pudieron procesar."
        self.status_text.set(summary)
        self._log(summary)

        if errors:
            error_lines = "\n".join(f"- {path}: {exc}" for path, exc in errors)
            messagebox.showwarning(
                "Proceso finalizado con advertencias",
                "Algunas imágenes no pudieron procesarse:\n\n" + error_lines,
            )
        else:
            messagebox.showinfo("¡Todo listo!", "Las imágenes se redujeron exitosamente.")

    # ----------------------------------------------------------------- Utility
    def close(self) -> None:
        self.master.destroy()


def launch_app() -> None:
    root = tk.Tk()
    app = ReduceImagesApp(root)
    app.mainloop()


if __name__ == "__main__":
    launch_app()
