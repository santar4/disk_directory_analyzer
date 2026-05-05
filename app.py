
import threading
import uuid
from flask import Response, render_template, request
from DiskUsageAnalyzer import SCAN_RESULTS, SCAN_ERRORS, socketio, app
from DiskUsageAnalyzer.utils import (
    analyze_disk,
    generate_multiple_charts,
    parse_filters,
    scan_result_to_csv,
    scan_result_to_json,
)



@app.route("/")
def select_disk():
    return render_template("select_disk.html")


@app.route("/results/<scan_id>")
def analysis_results(scan_id):
    scan_result = SCAN_RESULTS.get(scan_id)
    error = SCAN_ERRORS.get(scan_id)

    if not scan_result:
        return render_template("analysis_results.html", error=error or "Результат сканування не знайдено.")

    charts = generate_multiple_charts(scan_result)
    return render_template(
        "analysis_results.html",
        charts=charts,
        scan_id=scan_id,
        scan_result=scan_result,
        disk_path=scan_result["disk_path"],
    )


@app.route("/export/<scan_id>.csv")
def export_csv(scan_id):
    scan_result = SCAN_RESULTS.get(scan_id)
    if not scan_result:
        return Response("Результат сканування не знайдено.", status=404)

    return Response(
        scan_result_to_csv(scan_result),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=disk-analysis.csv"},
    )


@app.route("/export/<scan_id>.json")
def export_json(scan_id):
    scan_result = SCAN_RESULTS.get(scan_id)
    if not scan_result:
        return Response("Результат сканування не знайдено.", status=404)

    return Response(
        scan_result_to_json(scan_result),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=disk-analysis.json"},
    )


@socketio.on("start_scan")
def start_scan(form_data):
    scan_id = str(uuid.uuid4())
    socketio.emit("scan_started", {"scan_id": scan_id}, to=request.sid)

    thread = threading.Thread(target=_run_scan, args=(scan_id, request.sid, form_data), daemon=True)
    thread.start()


def _run_scan(scan_id, sid, form_data):
    try:
        filters = parse_filters(form_data)

        def progress_callback(progress):
            socketio.emit("scan_progress", {"scan_id": scan_id, **progress}, to=sid)

        scan_result = analyze_disk(form_data.get("disk_path", ""), filters, progress_callback)
        SCAN_RESULTS[scan_id] = scan_result
        socketio.emit("scan_finished", {"scan_id": scan_id, "summary": scan_result["summary"]}, to=sid)
    except Exception as exc:
        SCAN_ERRORS[scan_id] = str(exc)
        socketio.emit("scan_error", {"scan_id": scan_id, "message": str(exc)}, to=sid)



if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=False, allow_unsafe_werkzeug=True)

