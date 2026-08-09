<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'


const username = ref('')
const password = ref('')
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const submit = async () => {
    if (!username.value.trim() || !password.value) {
        auth.error = 'Username and password are required.'
        return
    }

    const loggedIn = await auth.login(username.value.trim(), password.value)
    if (loggedIn) {
        const destination = typeof route.query.redirect === 'string'
            ? route.query.redirect
            : '/dashboard'
        await router.replace(destination)
    }
}
</script>

<template>
    <div class="flex min-h-[calc(100vh-8rem)] items-center justify-center px-4 py-12">
        <div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl ring-1 ring-slate-200">
            <div class="mb-8 text-center">
                <p class="text-sm font-semibold uppercase tracking-wider text-indigo-600">
                    Staff access
                </p>
                <h1 class="mt-2 text-3xl font-bold text-slate-900">
                    Sign in to the dashboard
                </h1>
                <p class="mt-2 text-sm text-slate-500">
                    Use your Django staff username and password.
                </p>
            </div>

            <form class="space-y-5" @submit.prevent="submit">
                <div>
                    <label for="username" class="block text-sm font-medium text-slate-700">
                        Username
                    </label>
                    <input
                        id="username"
                        v-model="username"
                        name="username"
                        type="text"
                        autocomplete="username"
                        required
                        autofocus
                        class="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
                    />
                </div>

                <div>
                    <label for="password" class="block text-sm font-medium text-slate-700">
                        Password
                    </label>
                    <input
                        id="password"
                        v-model="password"
                        name="password"
                        type="password"
                        autocomplete="current-password"
                        required
                        class="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
                    />
                </div>

                <p
                    v-if="auth.error"
                    role="alert"
                    class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
                >
                    {{ auth.error }}
                </p>

                <button
                    type="submit"
                    :disabled="auth.isLoading"
                    class="w-full rounded-lg bg-indigo-600 px-4 py-2.5 font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                    {{ auth.isLoading ? 'Signing in…' : 'Sign in' }}
                </button>
            </form>
        </div>
    </div>
</template>
