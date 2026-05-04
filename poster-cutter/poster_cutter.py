#!/usr/bin/env python3
"""
Poster Cutter - Приложение для нарезки изображений на плитки для печати больших плакатов.

Этот скрипт принимает изображение и разбивает его на части указанного размера (например, А4),
чтобы можно было распечатать их на обычном принтере и собрать в большой плакат.
"""

import argparse
import os
import sys
from pathlib import Path
from PIL import Image

# Размеры листов в миллирах (стандарт ISO 216)
PAPER_SIZES_MM = {
    'a0': (841, 1189),
    'a1': (594, 841),
    'a2': (420, 594),
    'a3': (297, 420),
    'a4': (210, 297),
    'a5': (148, 210),
    'a6': (105, 148),
}

# DPI для печати (стандартное качество)
DEFAULT_DPI = 300


def mm_to_pixels(mm, dpi):
    """Конвертирует миллиметры в пиксели при заданном DPI."""
    inches = mm / 25.4
    return int(inches * dpi)


def get_paper_size_pixels(paper_size, dpi):
    """Получает размер листа в пикселях для заданного формата и DPI."""
    paper_size = paper_size.lower()
    if paper_size not in PAPER_SIZES_MM:
        raise ValueError(f"Неизвестный формат бумаги: {paper_size}. Доступные: {', '.join(PAPER_SIZES_MM.keys())}")
    
    width_mm, height_mm = PAPER_SIZES_MM[paper_size]
    width_px = mm_to_pixels(width_mm, dpi)
    height_px = mm_to_pixels(height_mm, dpi)
    
    return width_px, height_px


def cut_image_into_tiles(image_path, output_dir, cols, rows, paper_size='a4', 
                          dpi=DEFAULT_DPI, overlap_mm=10, filename_pattern=None):
    """
    Нарезает изображение на плитки для печати.
    
    Args:
        image_path: Путь к исходному изображению
        output_dir: Директория для сохранения плиток
        cols: Количество колонок (листов по горизонтали)
        rows: Количество рядов (листов по вертикали)
        paper_size: Формат бумаги (a4, a3 и т.д.)
        dpi: Разрешение в точках на дюйм
        overlap_mm: Перекрытие в мм для склейки (поля)
        filename_pattern: Шаблон имени файла (по умолчанию: poster_page_{row}_{col}.png)
    """
    
    # Открываем изображение
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')  # Конвертируем в RGB для совместимости
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден: {image_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при открытии изображения: {e}")
        sys.exit(1)
    
    # Получаем размер листа в пикселях
    tile_width, tile_height = get_paper_size_pixels(paper_size, dpi)
    
    # Вычисляем размер перекрытия в пикселях
    overlap_px = mm_to_pixels(overlap_mm, dpi)
    
    # Создаем выходную директорию
    os.makedirs(output_dir, exist_ok=True)
    
    # Вычисляем размеры области обрезки с учетом перекрытий
    # Общая ширина и высота итогового плаката в пикселях
    total_width = cols * tile_width - (cols - 1) * overlap_px
    total_height = rows * tile_height - (rows - 1) * overlap_px
    
    # Масштабируем изображение под нужный размер
    img_resized = img.resize((total_width, total_height), Image.Resampling.LANCZOS)
    
    print(f"Исходное изображение: {img.size[0]}x{img.size[1]}")
    print(f"Размер плаката: {total_width}x{total_height} пикселей")
    print(f"Размер одного листа ({paper_size.upper()}): {tile_width}x{tile_height} пикселей")
    print(f"Перекрытие: {overlap_mm} мм ({overlap_px} пикселей)")
    print(f"Количество листов: {cols} x {rows} = {cols * rows} шт.")
    print(f"Сохранение в: {output_dir}")
    print("-" * 50)
    
    # Если шаблон имени не указан, используем стандартный
    if filename_pattern is None:
        filename_pattern = "poster_page_{row:02d}_{col:02d}.png"
    
    # Нарезаем изображение
    tiles_created = 0
    for row in range(rows):
        for col in range(cols):
            # Вычисляем координаты обрезки
            left = col * (tile_width - overlap_px)
            upper = row * (tile_height - overlap_px)
            right = left + tile_width
            lower = upper + tile_height
            
            # Обрезаем плитку
            tile = img_resized.crop((left, upper, right, lower))
            
            # Добавляем метки для удобства сборки (опционально)
            # Можно добавить текст с номером листа
            
            # Формируем имя файла
            filename = filename_pattern.format(row=row + 1, col=col + 1, total_rows=rows, total_cols=cols)
            output_path = os.path.join(output_dir, filename)
            
            # Сохраняем плитку
            tile.save(output_path, dpi=(dpi, dpi))
            tiles_created += 1
            
            print(f"Создан лист {row + 1}/{rows}, {col + 1}/{cols}: {filename}")
    
    print("-" * 50)
    print(f"Готово! Создано {tiles_created} листов для печати.")
    print(f"Распечатайте все листы в формате {paper_size.upper()} с масштабом 100% (без масштабирования)")
    print(f"Обрежьте поля с одной стороны каждого листа (кроме правого нижнего угла) и склейте внахлёст")
    
    return tiles_created


def calculate_layout(image_path, paper_size='a4', target_cols=None, target_rows=None, dpi=DEFAULT_DPI):
    """
    Рассчитывает оптимальную раскладку для изображения.
    
    Args:
        image_path: Путь к изображению
        paper_size: Формат бумаги
        target_cols: Желаемое количество колонок (если указано, рассчитывается rows)
        target_rows: Желаемое количество рядов (если указано, рассчитывается cols)
        dpi: Разрешение
    
    Returns:
        tuple: (cols, rows)
    """
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    tile_width, tile_height = get_paper_size_pixels(paper_size, dpi)
    
    aspect_ratio = img_width / img_height
    tile_aspect = tile_width / tile_height
    
    if target_cols:
        cols = target_cols
        # Рассчитываем необходимое количество рядов
        # Общая ширина плаката
        total_width = cols * tile_width
        # Высота плаката должна соответствовать пропорциям изображения
        total_height = total_width / aspect_ratio
        rows = int(total_height / tile_height + 0.5)
        rows = max(1, rows)
    elif target_rows:
        rows = target_rows
        # Рассчитываем необходимое количество колонок
        total_height = rows * tile_height
        total_width = total_height * aspect_ratio
        cols = int(total_width / tile_width + 0.5)
        cols = max(1, cols)
    else:
        # Если ничего не указано, используем минимальную раскладку 1x1
        cols = 1
        rows = 1
        print("Предупреждение: Не указано количество колонок или рядов. Используется 1x1")
    
    return cols, rows


def main():
    parser = argparse.ArgumentParser(
        description='Poster Cutter - Нарезка изображений для печати больших плакатов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s input.jpg -c 4 -r 6
      Нарезать изображение на 4x6 листов А4
  
  %(prog)s input.jpg -c 4 --paper a3
      Нарезать изображение на 4 колонки (ряды рассчитаются автоматически) на бумаге А3
  
  %(prog)s input.jpg -r 3 -o output_folder --overlap 15
      Нарезать на 3 ряда с перекрытием 15 мм
        """
    )
    
    parser.add_argument('input', help='Путь к входному изображению')
    parser.add_argument('-o', '--output', default='./output', 
                        help='Директория для сохранения плиток (по умолчанию: ./output)')
    parser.add_argument('-c', '--cols', type=int, 
                        help='Количество колонок (листов по горизонтали)')
    parser.add_argument('-r', '--rows', type=int, 
                        help='Количество рядов (листов по вертикали)')
    parser.add_argument('-p', '--paper', default='a4', 
                        help=f'Формат бумаги: {", ".join(PAPER_SIZES_MM.keys())} (по умолчанию: a4)')
    parser.add_argument('--dpi', type=int, default=DEFAULT_DPI, 
                        help=f'Resolution in DPI (по умолчанию: {DEFAULT_DPI})')
    parser.add_argument('--overlap', type=float, default=10, 
                        help='Размер перекрытия в мм для склейки (по умолчанию: 10)')
    parser.add_argument('--pattern', 
                        help='Шаблон имени файла (используйте {row}, {col}, {total_rows}, {total_cols})')
    parser.add_argument('--auto', action='store_true',
                        help='Автоматически рассчитать раскладку на основе пропорций изображения')
    
    args = parser.parse_args()
    
    # Проверяем существование входного файла
    if not os.path.exists(args.input):
        print(f"Ошибка: Файл не найден: {args.input}")
        sys.exit(1)
    
    # Проверяем корректность формата бумаги
    if args.paper.lower() not in PAPER_SIZES_MM:
        print(f"Ошибка: Неверный формат бумаги '{args.paper}'")
        print(f"Доступные форматы: {', '.join(PAPER_SIZES_MM.keys())}")
        sys.exit(1)
    
    # Если ни cols, ни rows не указаны, пробуем рассчитать автоматически
    if not args.cols and not args.rows:
        if args.auto:
            # Для авторасчета нужно хотя бы одно значение, иначе используем 2x3 как пример
            print("Автоматический расчет требует указания хотя бы --cols или --rows")
            print("Используется раскладка 4x6 как пример (как в описании проекта)")
            args.cols = 4
            args.rows = 6
        else:
            print("Ошибка: Необходимо указать хотя бы --cols или --rows")
            print("Используйте --help для получения справки")
            sys.exit(1)
    
    # Рассчитываем раскладку если указано только одно значение
    if args.cols and not args.rows:
        args.cols, args.rows = calculate_layout(args.input, args.paper, target_cols=args.cols, dpi=args.dpi)
        print(f"Автоматически рассчитано рядов: {args.rows}")
    elif args.rows and not args.cols:
        args.cols, args.rows = calculate_layout(args.input, args.paper, target_rows=args.rows, dpi=args.dpi)
        print(f"Автоматически рассчитано колонок: {args.cols}")
    
    # Запускаем нарезку
    cut_image_into_tiles(
        image_path=args.input,
        output_dir=args.output,
        cols=args.cols,
        rows=args.rows,
        paper_size=args.paper,
        dpi=args.dpi,
        overlap_mm=args.overlap,
        filename_pattern=args.pattern
    )


if __name__ == '__main__':
    main()
