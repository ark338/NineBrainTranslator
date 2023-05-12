from flask import Flask, render_template, request, jsonify, send_file, session
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
import trans  # 导入您自定义的翻译模块
import os
from werkzeug.utils import secure_filename
import time
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SECRET_KEY'] = app.secret_key
socketio = SocketIO(app, cors_allowed_origins='*')
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

sid_mapping = {}

@app.route('/translate')
def index():
    return render_template('index.html')

@socketio.on('translate_text')
@app.route('/translate/text', methods=['POST'])
def translate_text():
    text = request.form['text']
    languages = request.form.getlist('languages')
    target_languages = jsonify(eval(languages[0])).json
    user_id = request.form['user_id']
    enable_gpt4 = request.form['enable_gpt4']

    # 这里对应了trans代码中的process_row函数的定义：text需要是一个元组，其中第四个元素是要翻译的文本
    transrow = ('', '', '', text)

    def report_progress(lang):
        socketio.emit('translation_progress', {'user_id': user_id, 'progress':lang})
    translations = trans.process_row(1, transrow, target_languages, report_progress, enable_gpt4=enable_gpt4)  # 使用您提供的翻译函数

    print(f" text {text} target_languages {target_languages} user_id {user_id} enable_gpt4 {enable_gpt4}")

    result = ""
    for i in range(len(target_languages)):
        result += "\n\n" + target_languages[i] + ": " + translations[i+4]
        #result.append({"language": languages[i], "translation": translations[i+4]})

    #print (jsonify(result))

    return jsonify({"success":result})

@app.route('/translate/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if file:
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4()
        file_save_name = str(unique_id) + '_' + filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_save_name))
    else:
        return jsonify({"error": "File upload failed"}), 400

    languages = request.form.getlist('languages')
    target_languages = jsonify(eval(languages[0])).json
    user_id = request.form['user_id']
    enable_gpt4 = request.form['enable_gpt4']
    
    print(f"languages: {target_languages} user_id {user_id} enable_gpt4 {enable_gpt4}")

    def report_progress(lang):
        socketio.emit('file_progress', {'user_id': user_id, 'progress':lang})
    
    upload_filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_save_name)
    download_filename = 'translated_' + file_save_name
    download_filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], download_filename)

    session['upload_filepath'] = upload_filepath
    session['download_filepath'] = download_filepath
    session['download_filename'] = download_filename

    trans.process_excel(upload_filepath, download_filepath, target_languages = target_languages, progress_callback=report_progress, enable_gpt4=enable_gpt4)  # 使用您提供的翻译函数

    return jsonify({"success": "Translation Success!", "filename": filename}), 200

@app.route('/translate/download/<filename>', methods=['GET'])
def download_file(filename):
    if 'download_filepath' not in session or 'download_filename' not in session:
        return jsonify({"error": "No file selected"}), 400

    download_filepath = session['download_filepath']
    download_filename = session['download_filename']
    return send_file(download_filepath, download_name=download_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
