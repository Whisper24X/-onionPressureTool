import { request1, request5 } from './request'

/** 获取所有历史记录 */
export const deviceHistroyList = (params) => {
  return request5.get('/latest_ids', params)
}

/** 获取所有设备列表 */
export const deviceList = () => {
  return request5.post('/get_devices_details', {})
}

/** 开始运行接口
 * {
    deviceId: 'device_id',
    tcpPort: 'tcp_port',
   }
 */
export const deviceStart = (data = {}) => {
  return request1.post('/api/start_monkey', data, {
    headers: {
      'Content-Type': 'application/json',
    },
  })
}

/** 停止运行接口
 * {
    deviceId: 'device_id',
    tcpPort: 'tcp_port',
   }
 */
export const deviceStop = (params) => {
  return request1.post('/api/stop_monkey', params)
}

/** 获取CPU信息
 * {device_name, other_field}
 */
export const getCpuInfo = (data) => {
  return request5.post('/get_cpu_info', data)
}

/** 获取内存信息
 * {device_name, other_field}
 */
export const getMemInfo = (data) => {
  return request5.post('/get_mem_info', data)
}

/** 获取FPS信息
 * {device_name, other_field}
 */
export const getFpsInfo = (data) => {
  return request5.post('/get_fps_info', data)
}
