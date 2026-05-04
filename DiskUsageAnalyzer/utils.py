import csv
import io
import json
import os
from datetime import datetime

from plotly.graph_objects import Bar, Figure, Pie


BYTES_IN_GB = 1024 ** 3
BYTES_IN_MB = 1024 ** 2


def validate_disk_path(disk_path):
    if not disk_path or not disk_path.strip():
        raise ValueError("Вкажіть шлях до диска або папки.")

    normalized_path = os.path.abspath(os.path.expanduser(disk_path.strip()))

    if not os.path.exists(normalized_path):
        raise ValueError("Вказаний шлях не існує.")

    if not os.path.isdir(normalized_path):
        raise ValueError("Вказаний шлях не є папкою або диском.")

    return normalized_path


def parse_filters(form_data):
    extensions = _split_extensions(form_data.get("extensions") or form_data.get("file_type"))

    min_size_mb = _to_float(form_data.get("min_size_mb"))
    max_size_mb = _to_float(form_data.get("max_size_mb"))
    legacy_size_filter = form_data.get("file_size_filter")
    if legacy_size_filter == ">10":
        min_size_mb = 10 * 1024
    elif legacy_size_filter == "<1":
        max_size_mb = 1024

    filters = {
        "extensions": extensions,
        "name_query": (form_data.get("name_query") or "").strip().lower(),
        "min_size_mb": min_size_mb,
        "max_size_mb": max_size_mb,
        "date_from": _parse_date(form_data.get("date_from")),
        "date_to": _parse_date(form_data.get("date_to"), end_of_day=True),
        "date_filter": form_data.get("date_filter") or "",
    }
    return filters


def analyze_disk(disk_path, filters=None, progress_callback=None):
    filters = filters or {}
    normalized_path = validate_disk_path(disk_path)

    extension_sizes = {}
    top_files = []
    scanned_files = 0
    matched_files = 0
    skipped_files = 0
    total_size_bytes = 0

    for root, _, files in os.walk(normalized_path):
        for file_name in files:
            scanned_files += 1
            file_path = os.path.join(root, file_name)

            try:
                stat = os.stat(file_path)
            except OSError:
                skipped_files += 1
                continue

            file_info = _build_file_info(file_path, file_name, stat)

            if progress_callback and scanned_files % 100 == 0:
                progress_callback(
                    {
                        "scanned_files": scanned_files,
                        "matched_files": matched_files,
                        "current_path": file_path,
                    }
                )

            if not _matches_filters(file_info, filters):
                continue

            matched_files += 1
            total_size_bytes += file_info["size_bytes"]
            extension = file_info["extension"]
            extension_sizes[extension] = extension_sizes.get(extension, 0) + file_info["size_gb"]

            top_files.append(file_info)
            top_files = sorted(top_files, key=lambda item: item["size_bytes"], reverse=True)[:10]

    if progress_callback:
        progress_callback(
            {
                "scanned_files": scanned_files,
                "matched_files": matched_files,
                "current_path": "",
                "done": True,
            }
        )

    return {
        "disk_path": normalized_path,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filters": _serialize_filters(filters),
        "extension_sizes": extension_sizes,
        "top_files": top_files,
        "summary": {
            "scanned_files": scanned_files,
            "matched_files": matched_files,
            "skipped_files": skipped_files,
            "total_size_bytes": total_size_bytes,
            "total_size_gb": round(total_size_bytes / BYTES_IN_GB, 4),
        },
    }


def generate_multiple_charts(scan_result):
    charts = []
    extension_sizes = scan_result.get("extension_sizes", {})
    top_files = scan_result.get("top_files", [])

    sorted_data = sorted(extension_sizes.items(), key=lambda item: item[1], reverse=True)
    top_10_data = sorted_data[:10]

    if top_10_data:
        pie = Figure(data=[Pie(labels=[x[0] for x in top_10_data], values=[x[1] for x in top_10_data], hole=0.35)])
        pie.update_layout(title_text="Топ 10 типів файлів за розміром", height=520)
        charts.append(pie.to_html(full_html=False))

        bar = Figure(data=[Bar(x=[x[0] for x in top_10_data], y=[x[1] for x in top_10_data])])
        bar.update_layout(
            title_text="Розподіл розміру за типами файлів",
            xaxis_title="Тип файлу",
            yaxis_title="Розмір (ГБ)",
            height=520,
        )
        charts.append(bar.to_html(full_html=False))

    if top_files:
        file_names = [item["name"] for item in top_files]
        file_sizes = [item["size_gb"] for item in top_files]
        top_bar = Figure(data=[Bar(x=file_names, y=file_sizes)])
        top_bar.update_layout(
            title_text="Топ 10 найбільших файлів",
            xaxis_title="Назва файлу",
            yaxis_title="Розмір (ГБ)",
            height=520,
        )
        charts.append(top_bar.to_html(full_html=False))

    return charts


def scan_result_to_csv(scan_result):
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["name", "path", "extension", "size_mb", "size_gb", "modified_at", "created_at"],
    )
    writer.writeheader()
    writer.writerows(scan_result.get("top_files", []))
    return output.getvalue()


def scan_result_to_json(scan_result):
    return json.dumps(scan_result, ensure_ascii=False, indent=2)


def _build_file_info(file_path, file_name, stat):
    extension = os.path.splitext(file_name)[1].lower() or "Без розширення"
    modified_at = datetime.fromtimestamp(stat.st_mtime)
    created_at = datetime.fromtimestamp(stat.st_ctime)

    return {
        "name": file_name,
        "path": file_path,
        "extension": extension,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / BYTES_IN_MB, 3),
        "size_gb": round(stat.st_size / BYTES_IN_GB, 6),
        "modified_timestamp": stat.st_mtime,
        "modified_at": modified_at.strftime("%Y-%m-%d %H:%M:%S"),
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _matches_filters(file_info, filters):
    extensions = filters.get("extensions") or []
    if extensions and file_info["extension"] not in extensions:
        return False

    name_query = filters.get("name_query")
    if name_query and name_query not in file_info["name"].lower():
        return False

    min_size_mb = filters.get("min_size_mb")
    if min_size_mb is not None and file_info["size_mb"] < min_size_mb:
        return False

    max_size_mb = filters.get("max_size_mb")
    if max_size_mb is not None and file_info["size_mb"] > max_size_mb:
        return False

    modified_timestamp = file_info["modified_timestamp"]
    date_from = filters.get("date_from")
    if date_from and modified_timestamp < date_from.timestamp():
        return False

    date_to = filters.get("date_to")
    if date_to and modified_timestamp > date_to.timestamp():
        return False

    return True


def _split_extensions(raw_value):
    if not raw_value or raw_value == "all":
        return []

    extensions = []
    for item in raw_value.split(","):
        extension = item.strip().lower()
        if not extension:
            continue
        if not extension.startswith("."):
            extension = f".{extension}"
        extensions.append(extension)
    return extensions


def _to_float(raw_value):
    if raw_value in (None, ""):
        return None
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError("Розмір файлу має бути числом.") from exc


def _parse_date(raw_value, end_of_day=False):
    if not raw_value:
        return None

    parsed = datetime.strptime(raw_value, "%Y-%m-%d")
    if end_of_day:
        return parsed.replace(hour=23, minute=59, second=59)
    return parsed


def _serialize_filters(filters):
    serialized = dict(filters)
    for key in ("date_from", "date_to"):
        value = serialized.get(key)
        if isinstance(value, datetime):
            serialized[key] = value.strftime("%Y-%m-%d")
    return serialized
