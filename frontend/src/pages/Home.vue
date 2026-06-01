<script setup>
import { ref } from 'vue'
import api from '@/plugins/axios'

const payload = ref({ message: '' })
const isLoading = ref(false) // add a loading tracker

const sendMessage = async () => {
    // prevent sending empty messages
    if (!payload.value.message.trim()) {
        alert("Empty error message")
        return
    }


    isLoading.value = true
    try {
        const response = await api.post('/chat/fetch-chat/', payload.value)
        alert(`Message sent successfully`);

        // clear input on success
        payload.value.message = ''
    } catch (error) {
        console.log(error)
    } finally {
        isLoading.value = false
    }
}
</script>

<template>
    <div class="grid grid-cols-12 py-8">
        <div class="col-span-12 md:col-span-6 md:col-start-4 lg:col-span-4 lg:col-start-5">
            <div class="rounded-lg bg-slate-100 p-4 shadow-xl/20">
                <form @submit.prevent="sendMessage">
                    <div>
                        <label for="message" class="block text-sm/6 font-medium">Message</label>
                        <div class="mt-2">
                            <textarea v-model="payload.message" id="message" name="message" rows="3" class="block w-full rounded-md px-3 py-1.5 text-base outline-1 -outline-offset-1 placeholder:text-grey-500 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-500 sm:text-sm/6">
                            </textarea>
                        </div>
                    </div>
                    <div class="mt-2">
                        <button type="submit" :disabled="isLoading" :class="isLoading ? 'cursor-wait bg-grey-400' : 'cursor-pointer bg-blue-600 hover:bg-blue-500'" class="shadow-sm text-white rounded-lg px-5 py-1 shadow-blue-500/50 transition-colors duration-200 ring">
                            {{ isLoading ? 'Sending...' : 'Send Chat'  }}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>