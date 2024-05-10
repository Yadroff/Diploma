import fitz  # PyMuPDF

import os


def extract_text_containers_with_bbox(pdf_path):
    # Открываем PDF с помощью PyMuPDF
    pdf_document = fitz.open(pdf_path)

    # Итерируем по страницам PDF
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)

        # Получаем контейнеры текста
        text_containers = page.get_text("dict")["blocks"]

        # Итерируем по контейнерам текста и рисуем ограничивающие прямоугольники
        for block in text_containers:
            bbox = block["bbox"]
            page.draw_rect(bbox)

        # Сохраняем изменения в файле PDF
    pdf_document.save(f'{os.path.splitext(pdf_path)[0]}_paragraphs.pdf')


def main():
    # Путь к PDF-файлу
    pdf_path = 'example.pdf'

    # Извлекаем контейнеры текста с Bounding box из PDF и сохраняем измененные страницы
    extract_text_containers_with_bbox(pdf_path)


if __name__ == "__main__":
    main()
