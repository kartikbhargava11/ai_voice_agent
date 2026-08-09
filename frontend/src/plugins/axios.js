import axios from 'axios'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
})

api.interceptors.request.use(
    (config) => {
        const token = sessionStorage.getItem('auth_token')

        if (token) {
            config.headers.Authorization = `Token ${token}`
        }

        return config
    },
    (error) => Promise.reject(error)
)

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            sessionStorage.removeItem('auth_token')
            window.dispatchEvent(new Event('auth:unauthorized'))
        }
        return Promise.reject(error)
    }
)

export default api
