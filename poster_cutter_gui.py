import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
import threading

# Добавляем путь к основному скрипту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'poster-cutter'))

# Импорт логики из основного скрипта
from poster_cutter import cut_image_into_tiles, calculate_layout, PAPER_SIZES_MM

class PosterCutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🖼️ Нарезка фото для плакатов")
        self.root.geometry("900x700")
        
        self.image_path = None
        self.preview_image = None
        self.is_processing = False
        
        # Настройки по умолчанию
        self.cols_var = tk.StringVar(value="4")
        self.rows_var = tk.StringVar(value="6")
        self.paper_var = tk.StringVar(value="a4")
        self.overlap_var = tk.StringVar(value="10")
        self.dpi_var = tk.StringVar(value="300")
        self.pattern_var = tk.StringVar(value="poster_page_{row:02d}_{col:02d}.png")
        self.auto_var = tk.BooleanVar(value=False)
        
        # Список форматов бумаги (верхний регистр для отображения)
        self.paper_formats = [size.upper() for size in PAPER_SIZES_MM.keys()]
        
        self.create_widgets()
        
    def create_widgets(self):
        # Левая панель (Превью)
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.preview_label = ttk.Label(left_frame, text="Изображение не загружено", background="#f0f0f0", anchor="center")
        self.preview_label.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)
        
        self.btn_load = ttk.Button(btn_frame, text="📂 Загрузить фото", command=self.load_image)
        self.btn_load.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = ttk.Button(btn_frame, text="❌ Очистить", command=self.clear_image, state=tk.DISABLED)
        self.btn_clear.pack(side=tk.LEFT, padx=5)
        
        # Правая панель (Настройки)
        right_frame = ttk.LabelFrame(self.root, text="⚙️ Параметры нарезки", padding="15")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        # Колонки
        ttk.Label(right_frame, text="Колонки (ширина):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_cols = ttk.Entry(right_frame, textvariable=self.cols_var, width=10)
        self.entry_cols.grid(row=0, column=1, pady=5, padx=5)
        
        # Ряды
        ttk.Label(right_frame, text="Ряды (высота):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_rows = ttk.Entry(right_frame, textvariable=self.rows_var, width=10)
        self.entry_rows.grid(row=1, column=1, pady=5, padx=5)
        
        # Авто-расчет
        self.chk_auto = ttk.Checkbutton(right_frame, text="🔄 Авто-расчет пропорций", variable=self.auto_var, command=self.toggle_auto)
        self.chk_auto.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Формат бумаги
        ttk.Label(right_frame, text="Формат бумаги:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.combo_paper = ttk.Combobox(right_frame, textvariable=self.paper_var, values=self.paper_formats, width=8, state="readonly")
        self.combo_paper.grid(row=3, column=1, pady=5, padx=5)
        self.combo_paper.set("A4")  # Устанавливаем значение по умолчанию
        
        # Перекрытие
        ttk.Label(right_frame, text="Перекрытие (мм):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.entry_overlap = ttk.Entry(right_frame, textvariable=self.overlap_var, width=10)
        self.entry_overlap.grid(row=4, column=1, pady=5, padx=5)
        
        # DPI
        ttk.Label(right_frame, text="DPI (качество):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.entry_dpi = ttk.Entry(right_frame, textvariable=self.dpi_var, width=10)
        self.entry_dpi.grid(row=5, column=1, pady=5, padx=5)
        
        # Шаблон имени
        ttk.Label(right_frame, text="Шаблон имени:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.entry_pattern = ttk.Entry(right_frame, textvariable=self.pattern_var, width=20)
        self.entry_pattern.grid(row=6, column=1, pady=5, padx=5)
        ttk.Label(right_frame, text="{row}, {col}", font=("TkDefaultFont", 8), foreground="gray").grid(row=7, column=1, sticky=tk.W)
        
        # Кнопка запуска
        self.btn_process = ttk.Button(right_frame, text="✂️ Нарезать и сохранить", command=self.start_processing)
        self.btn_process.grid(row=8, column=0, columnspan=2, pady=20, sticky=tk.EW)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(right_frame, mode='indeterminate')
        self.progress.grid(row=9, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        # Статус
        self.status_label = ttk.Label(right_frame, text="Готов к работе", foreground="green")
        self.status_label.grid(row=10, column=0, columnspan=2, pady=10)
        
    def toggle_auto(self):
        if self.auto_var.get():
            self.entry_rows.config(state=tk.DISABLED)
        else:
            self.entry_rows.config(state=tk.NORMAL)
            
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("All files", "*.*")]
        )
        if file_path:
            self.image_path = file_path
            self.show_preview(file_path)
            self.btn_clear.config(state=tk.NORMAL)
            self.status_label.config(text=f"Загружено: {os.path.basename(file_path)}", foreground="blue")
            
    def show_preview(self, path):
        try:
            img = Image.open(path)
            # Масштабирование для превью
            max_size = (500, 500)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.preview_image, text="")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {e}")
            
    def clear_image(self):
        self.image_path = None
        self.preview_label.config(image="", text="Изображение не загружено")
        self.preview_image = None
        self.btn_clear.config(state=tk.DISABLED)
        self.status_label.config(text="Очищено", foreground="black")
        
    def start_processing(self):
        if not self.image_path:
            messagebox.showwarning("Внимание", "Сначала загрузите изображение!")
            return
            
        try:
            cols = int(self.cols_var.get())
            if not self.auto_var.get():
                rows = int(self.rows_var.get())
            else:
                rows = None # Будет рассчитано
                
            overlap = int(self.overlap_var.get())
            dpi = int(self.dpi_var.get())
            paper = self.paper_var.get()
            pattern = self.pattern_var.get()
            
            if cols <= 0 or (rows is not None and rows <= 0):
                raise ValueError("Количество колонок и рядов должно быть больше 0")
                
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", f"Проверьте числовые значения:\n{e}")
            return
            
        # Выбор папки для сохранения
        output_dir = filedialog.askdirectory(title="Выберите папку для сохранения нарезанных частей")
        if not output_dir:
            return
            
        self.is_processing = True
        self.btn_process.config(state=tk.DISABLED)
        self.progress.start()
        self.status_label.config(text="Обработка...", foreground="orange")
        
        # Запуск в отдельном потоке, чтобы не замораживать интерфейс
        thread = threading.Thread(
            target=self.process_image, 
            args=(self.image_path, output_dir, cols, rows, paper, overlap, dpi, pattern, self.auto_var.get())
        )
        thread.daemon = True
        thread.start()
        
    def process_image(self, input_path, output_dir, cols, rows, paper, overlap, dpi, pattern, auto):
        try:
            # Если авто-режим, рассчитываем количество рядов
            if auto:
                cols, rows = calculate_layout(input_path, paper.lower(), target_cols=cols, dpi=dpi)
                self.root.after(0, lambda: self.status_label.config(text=f"Авто-расчет: {cols}x{rows} листов"))
            
            total_parts = cols * rows
            
            # Запускаем нарезку
            cut_image_into_tiles(
                image_path=input_path,
                output_dir=output_dir,
                cols=cols,
                rows=rows,
                paper_size=paper.lower(),
                dpi=dpi,
                overlap_mm=overlap,
                filename_pattern=pattern
            )
            
            self.root.after(0, self.finish_processing, output_dir)
            
        except Exception as e:
            self.root.after(0, self.finish_processing, None, str(e))
            
    def update_progress(self, current, total):
        self.status_label.config(text=f"Нарезка: {current}/{total}")
        
    def finish_processing(self, output_dir=None, error=None):
        self.is_processing = False
        self.btn_process.config(state=tk.NORMAL)
        self.progress.stop()
        
        if error:
            self.status_label.config(text="Ошибка!", foreground="red")
            messagebox.showerror("Ошибка при обработке", error)
        else:
            self.status_label.config(text="Готово! Проверьте папку.", foreground="green")
            messagebox.showinfo("Успех", f"Нарезка завершена!\nФайлы сохранены в:\n{output_dir}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PosterCutterApp(root)
    root.mainloop()
