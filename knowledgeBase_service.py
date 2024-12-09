import time
import win32serviceutil
import win32service
import win32event
import threading
from flask import Flask, request, jsonify
import os
from API_list import Get_List, Delete_all_data, Delete_one_data, FuzzySystemParser, FuzzySystemDatabase

app = Flask(__name__)

@app.route('/get_fml_file/<system_name>', methods=['GET'])
def get_fml_file(system_name):
    try:
        db = FuzzySystemDatabase("knowledgeBase", "postgres", "Zhenik_14", "localhost", "5432")
        system = db.Get_file(system_name)
        
        if not system:
            return jsonify({"message": "No systems found"}), 200
        
        return jsonify({"system": system}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_systems_list', methods=['GET'])
def get_systems_list():
    try:
        systems = Get_List("knowledgeBase", "postgres", "Zhenik_14", "localhost", "5432")
        count = len(systems)
        if count == 0:
            return jsonify({"message": "No systems found"}), 204
        return jsonify({"systems": systems, "count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/put_fml_file', methods=['PUT'])
def put_fml_file():
    try:
        data = request.get_json()

        file_path = data.get('file_path')

        print("File path received:", file_path)

        if not os.path.exists(file_path):
            return jsonify({"error": "File does not exist."}), 404

        parser = FuzzySystemParser(file_path)
        parser.Put_fml_file("knowledgeBase", "postgres", "Zhenik_14", "localhost", "5432")

        return jsonify({"message": f"File {os.path.basename(file_path)} was successfully added to the knowledge base"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_systems_list', methods=['DELETE'])
def delete_systems_list():
    try:
        result = Delete_all_data("knowledgeBase", "postgres", "Zhenik_14", "localhost", "5432")  
        if result:
            return jsonify({"message": "All data deleted successfully"}), 200 
        else:
            return jsonify({"message": "Failed to delete data"}), 500 
    except Exception as e:
        return jsonify({"error": str(e)}), 500  

@app.route('/delete_one_system/<system_name>', methods=['DELETE'])
def delete_one_system(system_name):
    try:
        result = Delete_one_data("knowledgeBase", "postgres", "Zhenik_14", "localhost", "5432", system_name)  
        if result:
            return jsonify({"message": f"System '{system_name}' deleted successfully"}), 200  
        else:
            return jsonify({"message": f"Failed to delete system '{system_name}'"}), 500  
    except Exception as e:
        return jsonify({"error": str(e)}), 500  

class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = "knowledgeBase_service"
    _svc_display_name_ = "knowledgeBase_service"
    _svc_description_ = "Service for storing fuzzy logic systems"

    def __init__(self, *args):
        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.flask_thread = None 

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        if self.flask_thread is not None:
            requests.get('http://localhost:5000/shutdown')

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.flask_thread = threading.Thread(target=self.run_flask)
        self.flask_thread.start()
        while self.running:
            time.sleep(1) 

    def run_flask(self):
        app.run(host='127.0.0.1', port=5000)

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(MyService)
