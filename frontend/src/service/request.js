import axios from 'axios'
import { ElNotification } from 'element-plus'
// 默认 message map
export const CodeMessage = {
  200: '服务器成功返回请求的数据。',
  201: '新建或修改数据成功。',
  202: '一个请求已经进入后台排队（异步任务）。',
  204: '删除数据成功。',
  400: '发出的请求有错误，服务器没有进行新建或修改数据的操作。',
  401: '用户凭证已过期，请退出后再进入',
  403: '用户得到授权，但是访问是被禁止的。',
  404: '发出的请求针对的是不存在的记录，服务器没有进行操作。',
  406: '请求的格式不可得。',
  410: '请求的资源被永久删除，且不会再得到的。',
  413: '请求发送的资源大小超过服务器限制',
  422: '当创建一个对象时，发生一个验证错误。',
  429: '操作过于频繁，请稍后再试',
  500: '服务器发生错误，请检查服务器。',
  502: '网关错误。',
  503: '服务不可用，服务器暂时过载或维护。',
  504: '网关超时。',
}

function showErrorNotification(title, msg) {
  console.log(title, msg)
  ElNotification.error(msg)
}

function errorHandler(error) {
  console.log('errorHandler', error, error.response)
  let response = error.response
  if (response) {
    const { skipErrorHandler } = response.config
    if (response.status === 401) {
      ElNotification.error('用户凭证已过期，请退出后再进入')
    } else {
      const msg =
        response?.data?.message ||
        response?.data?.msg ||
        CodeMessage[response.status] ||
        error?.message
      if (!skipErrorHandler) {
        showErrorNotification('操作失败', msg)
      }
    }
  } else if (!axios.isCancel(error)) {
    showErrorNotification('网络异常', '您的网络发生异常，无法连接服务器')
  }
  return Promise.reject(error)
}

function parseData(response) {
  const { config } = response
  if (config.getResponse) {
    return response
  }
  return response?.data || response
}

const generateAxiosInstance = (baseURL) => {
  const instance = axios.create({
    baseURL,
  })
  instance.interceptors.response.use(parseData)
  instance.interceptors.response.use(undefined, errorHandler)

  return instance
}

const baseURL1 = 'http://127.0.0.1:5100'
const baseURL5 = 'http://127.0.0.1:5500'

// const baseURL1 = 'http://192.168.11.102:5100'
// const baseURL5 = 'http://192.168.11.102:5500'

export const request1 = generateAxiosInstance(baseURL1)
export const request5 = generateAxiosInstance(baseURL5)
