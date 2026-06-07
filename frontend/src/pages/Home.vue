<script setup>
import { ref } from 'vue'
import api from '@/plugins/axios'
import ChatBubble from '@/components/ChatBubble.vue'

const payload = ref(
    {
        message: '',
        state: {
            customer_name: null,
            customer_phone: null,
            service_needed: null,
            appointment_date: null,
            appointment_time: null
        }
    }
)
const messages = ref([])
const isLoading = ref(false) // add a loading tracker

const sendMessage = async () => {
    // prevent sending empty messages
    if (!payload.value.message.trim()) {
        alert("Empty Response")
        return
    }
    isLoading.value = true
    messages.value.push({
        role: 'user',
        text: payload.value.message
    })
    try {
        const response = await api.post('/chat/fetch-chat/', payload.value)
        messages.value.push({
            role: 'AI',
            text: response.data.reply
        })
        payload.value.state = response.data.state
    } catch (error) {
        console.log(error)
    } finally {
        payload.value.message = ''
        isLoading.value = false
    }
}
</script>

<template>
    <div class="grid grid-cols-12 py-8">
        <div class="col-span-12 md:col-span-6 md:col-start-4 lg:col-span-4 lg:col-start-5">
            <div class="rounded-lg bg-slate-100 p-4 shadow-xl/20">
                <ChatBubble v-for="(msg, index) in messages" :key="index" :msg="msg" />
                <form @submit.prevent="sendMessage">
                    <div>
                        <label for="message" class="block text-sm/6 font-medium">Message</label>
                        <div class="mt-2">
                            <textarea v-model="payload.message" id="message" name="message" rows="2" class="block w-full rounded-md px-3 py-1.5 text-base outline-1 -outline-offset-1 placeholder:text-gray-500 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-500 sm:text-sm/6" placeholder="Enter your message...">
                            </textarea>
                        </div>
                    </div>
                    <div class="mt-2 text-right">
                        <button type="submit" :disabled="isLoading" :class="isLoading ? 'cursor-wait bg-gray-500' : 'cursor-pointer bg-blue-600 hover:bg-blue-500'" class="shadow-sm text-white rounded-lg px-5 py-1 shadow-blue-500/50 transition-colors duration-200 ring">
                            {{ isLoading ? 'Sending...' : 'Send Chat'  }}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>