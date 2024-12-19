from flask import Flask, request, jsonify
from flask_cors import CORS
from mobileperf.android.DB_utils import DatabaseOperations
from datetime import datetime
import pandas as pd

app = Flask(__name__)
CORS(app)
db_operations = DatabaseOperations()

# 添加自定义响应头
@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/get_devices_details', methods=['POST'])
def get_devices_details():
    details = db_operations.get_devices_details()

    # 假设数据库查询返回的是元组类型
    if details:
        column_names = [
            "id", "device_id", "model", "android_version", "device_ram",
            "online_time", "device_status", "tcp_port", "package_list"
        ]

        formatted_details = []

        for device in details:
            formatted_device = dict(zip(column_names, device))  # 将元组与字段名映射
            formatted_details.append(formatted_device)

        return jsonify(formatted_details)
    else:
        return jsonify({"message": "未找到相关设备详情数据"}), 409


# def get_devices_details():
#     details = db_operations.get_devices_details()
#     if details:
#         formatted_details = []
#         for device in details:
#             formatted_device = {
#                 "id": device[0],  # 假设 id 在元组的第一个位置
#                 "device_id": device[1],  # device_id 在第二个位置
#                 "model": device[2],  # model 在第三个位置
#                 "android_version": device[3],  # android_version 在第四个位置
#                 "device_ram": device[4],  # device_ram 在第五个位置
#                 "online_time": device[5],  # online_time 在第六个位置
#                 "device_status": device[6],  # device_status 在第七个位置
#                 "tcp_port": device[7],  # tcp_port 在第八个位置
#                 "package_list": device[8] # package_list 在第九个位置
#             }
#             formatted_details.append(formatted_device)
#
#         return jsonify(formatted_details)
#     else:
#         return jsonify({"message": "未找到相关设备详情数据"}), 409

# 查看所有设备信息
@app.route('/latest_ids', methods=['GET'])
def get_devices():
    devices = db_operations.get_all_devices()
    #print(devices)
    if devices:
        devices_sorted = sorted(devices, key=lambda x: x[3], reverse=True)
        devices_dict = [
            {
                "device_id": device[0],
                "device_name": device[1],
                "model": device[2],
                "created_at": device[3].strftime("%Y-%m-%d %H:%M:%S") if isinstance(device[3], datetime) else device[3],
                "other_field": device[4]
            }
            for device in devices_sorted
        ]
        return jsonify(devices_dict)
    else:
        return jsonify({"message": "未找到设备相关信息"}), 409

# 请求对应ids的设备所有性能数据
# @app.route('/view_device_perf_info', methods=['POST'])
# def view_device_perf_info():
#     data = request.json
#     sn = data.get('device_name')
#     ids = data.get('other_field')
#
#     perf_data = db_operations.get_devices_perf_info(sn, ids)
#
#     if perf_data is not None:
#         try:
#             df = pd.DataFrame(perf_data)
#             date_columns = ['created_at', 'fps_datetime', 'fps_recorded_at', 'cpu_datetime', 'cpu_recorded_at',
#                             'mem_datetime', 'mem_recorded_at']
#             for col in date_columns:
#                 if col in df.columns:
#                     df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
#
#             result = df.to_dict(orient='records')
#             return jsonify(result), 200
#         except Exception as e:
#             print(f"Error processing data: {e}")
#             return jsonify({"message": "Internal server error"}), 500
#     else:
#         return jsonify({"message": "未找到设备性能数据"}), 404

@app.route('/get_cpu_info', methods=['POST'])
def get_cpu_info():
    data = request.json
    sn = data.get('device_name')
    ids = data.get('other_field')

    cpu_info = db_operations.get_cpu_info(sn, ids)
    if cpu_info:
        return jsonify(cpu_info)
    else:
        return jsonify({"message": "未找到相关CPU数据"}), 409

@app.route('/get_mem_info', methods=['POST'])
def get_mem_info():
    data = request.json
    sn = data.get('device_name')
    ids = data.get('other_field')

    mem_info = db_operations.get_mem_info(sn, ids)
    if mem_info:
        return jsonify(mem_info)
    else:
        return jsonify({"message": "未找到相关内存数据"}), 409

@app.route('/get_fps_info', methods=['POST'])
def get_fps_info():
    data = request.json
    sn = data.get('device_name')
    ids = data.get('other_field')

    fps_info = db_operations.get_fps_info(sn, ids)
    if fps_info:
        return jsonify(fps_info)
    else:
        return jsonify({"message": "未找到相关fps数据"}), 409

@app.route('/get_all_tablet_report', methods=['GET'])
def get_all_tablet_report():

    all_tablet_report = db_operations.get_all_tablet_report()
    if all_tablet_report:
        return jsonify(all_tablet_report)
    else:
        return jsonify({"message": "未找到相关平板报告的数据"}), 409

@app.route('/get_tablet_report', methods=['POST'])
def get_tablet_report():
    data = request.json
    report_id = data.get('report_id')
    sn = data.get('sn')

    tablet_report = db_operations.get_fps_info(report_id, sn)
    if tablet_report:
        return jsonify(tablet_report)
    else:
        return jsonify({"message": "未找到相关指定平板报告的数据"}), 409

@app.route('/delete_device_data', methods=['POST'])
def delete_device_data():
    data = request.json
    sn = data.get('device_name')
    ids = data.get('other_field')

    delete_device_data = db_operations.delete_device_data(sn, ids)
    if delete_device_data:
        return jsonify(delete_device_data)
    else:
        return jsonify({"message": "未删除相关设备历史数据"}), 409

@app.route('/insert_tablet_report', methods=['POST'])
def insert_tablet_report():
    try:
        data = request.get_json()  # 获取 POST 请求的 JSON 数据

        sn = data.get('sn')
        details = data.get('details')

        insert_tablet_report = db_operations.insert_tablet_report(sn, details)
        print(insert_tablet_report)
        return jsonify({"message": "insert_tablet_report.Report inserted successfully"}), 200
    except Exception as e:
        return jsonify({"insert_tablet_report error": str(e)}), 500


    # if insert_tablet_report:
    #     return jsonify(insert_tablet_report)
    # else:
    #     return jsonify({"message": "平板报告未插入成功"}), 409

if __name__ == '__main__':
    #get_devices()
    #app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5500)