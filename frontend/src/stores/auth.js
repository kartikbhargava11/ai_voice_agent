import { defineStore } from 'pinia'

import api from '@/plugins/axios'


export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: sessionStorage.getItem('auth_token'),
        isLoading: false,
        error: '',
    }),

    getters: {
        isAuthenticated: (state) => Boolean(state.token),
    },

    actions: {
        async login(username, password) {
            this.isLoading = true
            this.error = ''
            try {
                const response = await api.post('/auth/token/', { username, password })
                this.token = response.data.token
                sessionStorage.setItem('auth_token', this.token)
                return true
            } catch (error) {
                const details = error.response?.data
                this.error = details?.non_field_errors?.[0]
                    || details?.detail
                    || 'Unable to sign in. Check your username and password.'
                return false
            } finally {
                this.isLoading = false
            }
        },

        logout() {
            this.token = null
            this.error = ''
            sessionStorage.removeItem('auth_token')
        },
    },
})
