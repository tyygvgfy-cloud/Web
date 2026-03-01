from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import requests
import signal

app = Flask(__name__)
CORS(app)

SERVER_DIR = os.getcwd()
CONFIG_FILE = os.path.join(SERVER_DIR, "server.conf")
# Глобальная переменная для хранения процесса сервера
server_process = None

CORE_URLS = {
    "paper": "https://api.papermc.io/v2/projects/paper/versions/{v}/builds/",
    "purpur": "https://api.purpurmc.org/v2/purpur/{v}/latest/download",
    "vanilla": "https://piston-data.mojang.com/v1/objects/450698d1862ab5180c25d7c8040a5bc8d313d33e/server.jar",
    "spigot": "https://download.getbukkit.org/spigot/spigot-{v}.jar"
}

def ensure_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            f.write("jar=server.jar\n")
            f.write("ram=2G\n")
            f.write("java=java17\n")

@app.route('/ping', methods=['POST'])
def ping():
    return jsonify({"status": "online", "message": "VortexNode Bridge Active"})

@app.route('/server_control', methods=['POST'])
def control():
    global server_process
    data = request.json
    action = data.get('action')
    try:
        if action == 'start':
            if server_process and server_process.poll() is None:
                return jsonify({"status": "error", "message": "Сервер уже запущен"})
            
            # Запускаем сервер с перенаправлением stdin для приема команд
            server_process = subprocess.Popen(
                ['/bin/bash', f'{SERVER_DIR}/start_server.sh'],
                cwd=SERVER_DIR,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            return jsonify({"status": "success", "message": "Команда СТАРТ отправлена"})
        
        elif action == 'stop':
            if server_process and server_process.poll() is None:
                # Отправляем команду stop в консоль сервера
                server_process.stdin.write("stop\n")
                server_process.stdin.flush()
                return jsonify({"status": "success", "message": "Команда СТОП отправлена в консоль"})
            else:
                # Если процесс завис, пробуем скрипт
                subprocess.run(['/bin/bash', f'{SERVER_DIR}/stop_server.sh'], cwd=SERVER_DIR)
                return jsonify({"status": "success", "message": "Выполнен аварийный стоп"})
        
        return jsonify({"status": "error", "message": "Unknown action"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/save_config', methods=['POST'])
def save_config():
    data = request.json
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(f"jar={data.get('jar', 'server.jar')}\n")
            f.write(f"ram={data.get('ram', '2G')}\n")
            f.write(f"java={data.get('java', 'java17')}\n")
        return jsonify({"status": "success", "message": "Конфиг обновлен"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download_core', methods=['POST'])
def download_core():
    data = request.json
    core_type = str(data.get('type')).lower()
    version = data.get('version')
    target_path = os.path.join(SERVER_DIR, "server.jar")
    url = ""
    try:
        if core_type == "purpur": url = CORE_URLS["purpur"].format(v=version)
        elif core_type == "paper":
            api_url = CORE_URLS["paper"].format(v=version)
            builds_res = requests.get(api_url, timeout=15)
            data_json = builds_res.json()
            latest_build = data_json['builds'][-1]
            url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{latest_build}/downloads/paper-{version}-{latest_build}.jar"
        elif core_type == "vanilla": url = CORE_URLS["vanilla"]
        elif core_type == "spigot": url = f"https://cdn.getbukkit.org/spigot/spigot-{version}.jar"
        
        curl_cmd = ['curl', '-L', url, '-o', target_path]
        subprocess.run(curl_cmd)
        return jsonify({"status": "success", "message": "Ядро загружено"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/list_files', methods=['POST'])
def list_files():
    try:
        files = []
        for f in os.listdir(SERVER_DIR):
            path = os.path.join(SERVER_DIR, f)
            files.append({
                "name": f,
                "is_dir": os.path.isdir(path),
                "size": os.path.getsize(path) if not os.path.isdir(path) else 0
            })
        return jsonify({"status": "success", "files": files})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/read_file', methods=['POST'])
def read_file():
    filename = request.json.get('filename')
    try:
        path = os.path.join(SERVER_DIR, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"status": "success", "content": content})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/save_file', methods=['POST'])
def save_file():
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    try:
        path = os.path.join(SERVER_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({"status": "success", "message": f"Файл {filename} сохранен"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- ОБНОВЛЕННАЯ ФУНКЦИЯ ИСПОЛНЕНИЯ КОМАНД В ЯДРО ---

@app.route('/execute', methods=['POST'])
def execute():
    global server_process
    data = request.json
    command = data.get('command')
    
    try:
        # Проверяем, запущен ли процесс сервера
        if server_process and server_process.poll() is None:
            # Отправляем команду напрямую в stdin процесса Java
            server_process.stdin.write(command + "\n")
            server_process.stdin.flush()
            return jsonify({"status": "success", "output": f"Команда '{command}' отправлена в ядро"})
        else:
            # Если сервер не запущен, выполняем как системную команду (как было раньше)
            process = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
            return jsonify({"output": process})
    except Exception as e:
        return jsonify({"output": f"Ошибка: {str(e)}"})

@app.route('/get_logs', methods=['POST'])
def get_logs():
    log_path = os.path.join(SERVER_DIR, "logs", "latest.log")
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                content = "".join(lines[-200:])
                return jsonify({"status": "success", "full_log": content})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "error", "message": "Файл логов не найден"})

if __name__ == '__main__':
    ensure_config()
    app.run(host='0.0.0.0', port=5000)
