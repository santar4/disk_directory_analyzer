from flask import Flask, render_template, request
from utils import generate_multiple_charts, analyze_disk

app = Flask(__name__)

@app.route('/')
def select_disk():
    return render_template('select_disk.html')

@app.route('/analyze', methods=['POST'])
def analyze_disk_route():
    disk_path = request.form.get('disk_path')
    file_type = request.form.get('file_type')
    file_size_filter = request.form.get('file_size_filter')
    date_filter = request.form.get('date_filter')

    # Аналізуємо диск
    data, top_files = analyze_disk(disk_path, file_type, file_size_filter, date_filter)

    # Генеруємо кілька графіків
    charts = generate_multiple_charts(data, top_files)

    return render_template('analysis_results.html', charts=charts, disk_path=disk_path)

if __name__ == "__main__":
    app.run(debug=True)







