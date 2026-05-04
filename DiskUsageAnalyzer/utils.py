import os
import time

from plotly.graph_objs import Bar
from tqdm import tqdm
from plotly.graph_objects import Pie, Figure

def analyze_disk(disk_path, file_type=None, file_size_filter=None, date_filter=None):
    """Аналізує файли на диску з фільтрами."""
    data = {}
    top_files = []
    current_time = time.time()

    total_files = sum(len(files) for _, _, files in os.walk(disk_path))

    with tqdm(total=total_files, desc="Аналіз файлів", unit="файл") as progress_bar:
        for root, dirs, files in os.walk(disk_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path) / (1024 ** 3)  # Переводимо у ГБ
                    file_creation_time = os.path.getctime(file_path)

                    # Фільтр за типом файлів
                    if file_type and file_type != "all":
                        if not file.endswith(file_type):
                            continue

                    # Фільтр за розміром файлів
                    if file_size_filter:
                        if file_size_filter == ">10" and file_size <= 10:
                            continue
                        if file_size_filter == "<1" and file_size >= 1:
                            continue

                    # Фільтр за датою створення
                    if date_filter:
                        if date_filter == "recent" and current_time - file_creation_time > 30 * 24 * 3600:
                            continue
                        if date_filter == "old" and current_time - file_creation_time <= 365 * 24 * 3600:
                            continue

                    # Додавання результату
                    file_extension = os.path.splitext(file)[1] or "Без розширення"
                    data[file_extension] = data.get(file_extension, 0) + file_size

                    # Додавання файлу до топ 10
                    top_files.append({"name": file, "size": file_size})
                    top_files = sorted(top_files, key=lambda x: x["size"], reverse=True)[:10]

                except (OSError, PermissionError):
                    continue
                finally:
                    progress_bar.update(1)

    return data, top_files


from plotly.graph_objects import Pie, Figure, Bar

def generate_multiple_charts(data, top_files=None):
    """Генерує кілька графіків за фільтрами"""
    charts = []

    # Сортування даних для топ 10
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    top_10_data = sorted_data[:10]

    # Перший графік — топ 10 типів файлів
    fig1 = Figure(data=[Pie(labels=[x[0] for x in top_10_data], values=[x[1] for x in top_10_data], hole=0.3)])
    fig1.update_layout(title_text="Топ 10 типів файлів", width=1000, height=800)
    charts.append(fig1.to_html(full_html=False))

    # Другий графік — решта типів файлів
    remaining_data = sorted_data[10:]
    if remaining_data:
        fig2 = Figure(data=[Pie(labels=[x[0] for x in remaining_data], values=[x[1] for x in remaining_data], hole=0.3)])
        fig2.update_layout(title_text="Інші типи файлів", width=1000, height=800)
        charts.append(fig2.to_html(full_html=False))

    # Третій графік — загальний розподіл топ 10 типів файлів
    fig3 = Figure(data=[Bar(x=[x[0] for x in top_10_data], y=[x[1] for x in top_10_data])])
    fig3.update_layout(
        title_text="Розподіл топ 10 типів файлів",
        xaxis_title="Тип файлу",
        yaxis_title="Розмір (ГБ)",
        width=1200,
        height=800,
    )
    charts.append(fig3.to_html(full_html=False))

    # Четвертий і п'ятий графіки
    if top_files:
        file_names = [f["name"] for f in top_files]
        file_sizes = [f["size"] for f in top_files]
        fig4 = Figure(data=[Bar(x=file_names, y=file_sizes)])
        fig4.update_layout(
            title_text="Топ 10 найбільших файлів",
            xaxis_title="Назва файлу",
            yaxis_title="Розмір (ГБ)",
            width=1200,
            height=800,
        )
        charts.append(fig4.to_html(full_html=False))

    return charts
