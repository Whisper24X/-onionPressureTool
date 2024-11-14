from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import pandas as pd
import random
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 读取示例 CSV 文件
data = pd.read_csv('/Users/yangcong/Downloads/mobileperf-master/results/com.yangcong345.android.phone/2023_12_28_11_31_53/cpuinfo.csv')

def background_task():
    while True:
        socketio.sleep(1)  # 模拟每秒生成一次数据
        index = random.randint(0, len(data)-1)  # 从数据中随机选择一行
        realtime_data = data.iloc[index].to_dict()
        socketio.emit('realtime_data', realtime_data, namespace='/test')

@socketio.on('connect', namespace='/test')
def test_connect():
    print('Client connected')
    if not socketio.async_tasks() and 'task' not in globals():
        global task
        task = socketio.start_background_task(target=background_task)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app)
