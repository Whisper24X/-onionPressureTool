const express = require('express');
const app = express();
const bodyParser = require('body-parser');

// 使用 body-parser 中间件解析请求体
app.use(bodyParser.json());

app.post('/api/report', (req, res) => {
  const { deviceId, tcpPort } = req.body;  // 假设你接收到的数据包含设备ID和端口

  // 假设设备连接成功
  const response = {
    deviceId: deviceId,
    tcpPort: tcpPort,
    status: 'connected'
  };

  // 返回 JSON 响应
  res.json(response);
});

app.listen(5100, () => {
  console.log('Server is running on port 5100');
});
