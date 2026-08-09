<script setup>
import { computed, ref } from 'vue'
import api from '@/plugins/axios'

const transcript = ref('')
const aiReply = ref('')
const isListening = ref(false)
const isLoading = ref(false)
const conversationEnded = ref(false)
const speechError = ref('')
const idempotencyKey = ref(crypto.randomUUID())

const state = ref({
    customer_name: null,
    customer_phone: null,
    service_needed: null,
    appointment_date: null,
    appointment_time: null
})

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
const speechSupported = Boolean(SpeechRecognition)

let recognition = null

if (SpeechRecognition) {
    recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.interimResults = false
    recognition.continuous = false

    recognition.onstart = () => {
        speechError.value = ''
        isListening.value = true
    }

    recognition.onend = () => {
        isListening.value = false
    }

    recognition.onresult = async (event) => {
        transcript.value = event.results[0][0].transcript
        await sendToBackend(transcript.value)
    }

    recognition.onerror = (event) => {
        isListening.value = false
        speechError.value = event.error === 'not-allowed'
            ? 'Microphone access was blocked. Allow microphone access and try again.'
            : 'I could not hear that clearly. Please try again.'
    }
}

const startListening = () => {
    if (!recognition) {
        speechError.value = 'Voice input is not supported in this browser. Try Google Chrome.'
        return
    }
    speechError.value = ''
    try {
        recognition.start()
    } catch {
        speechError.value = 'The microphone is already starting. Please wait a moment.'
    }
}

const collectedDetails = computed(() => [
    { label: 'Name', value: state.value.customer_name },
    { label: 'Phone', value: state.value.customer_phone },
    { label: 'Service', value: state.value.service_needed },
    { label: 'Date', value: state.value.appointment_date },
    { label: 'Time', value: state.value.appointment_time?.slice(0, 5) }
])

const detailsCollected = computed(() => collectedDetails.value.filter(item => item.value).length)

const resetConversation = () => {
    if (recognition && isListening.value) recognition.abort()
    window.speechSynthesis.cancel()
    transcript.value = ''
    aiReply.value = ''
    speechError.value = ''
    conversationEnded.value = false
    idempotencyKey.value = crypto.randomUUID()
    state.value = {
        customer_name: null,
        customer_phone: null,
        service_needed: null,
        appointment_date: null,
        appointment_time: null
    }
}

const sendToBackend = async (message) => {
    isLoading.value = true
    try {
        const response = await api.post(
            '/chat/fetch-chat/',
            { message, state: state.value },
            { headers: { 'Idempotency-Key': idempotencyKey.value } }
        )
        aiReply.value = response.data.reply // saving the reply from the AI to display it to the client
        

        if (response.data.next_step === "booking_completed") { // django sends 'booking_completed' flag when all the details have been filled
            conversationEnded.value = true // marking 'conversationEnded' to true for UI purposes
            if (recognition) {
                recognition.abort() // kills any active listening session
            }
        }

        if (response.data.state) { // save the state, to send it to later API calls. It is just for backend logic
            state.value = response.data.state
        }

        if (response.data.reset_idempotency_key) {
            idempotencyKey.value = crypto.randomUUID()
        }
        
        speak(aiReply.value) // send the AI reply to WebSpeech API
    } catch (error) {
        const errorData = error.response?.data
        aiReply.value = errorData?.reply || errorData?.error_message || 'Something went wrong'
        if (errorData?.state) {
            state.value = errorData.state
        }
        if (errorData?.reset_idempotency_key) {
            idempotencyKey.value = crypto.randomUUID()
        }
        speak(aiReply.value)
    } finally {
        isLoading.value = false
    }
}

const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text)
    const voices = speechSynthesis.getVoices()
    utterance.voice = voices.find(v => v.lang === 'en-IN') || voices[0]

    utterance.lang = 'en-IN'
    utterance.rate = 0.95
    utterance.pitch = 1.05
    utterance.volume = 1

    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)

    utterance.onend = () => {
        if (!conversationEnded.value && recognition && !isListening.value) {
            recognition.start() // only restarting listening if convo hasn't started
        }
    }
}

</script>

<template>
    <div class="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl shadow-indigo-950/10">
        <div class="bg-gradient-to-br from-indigo-700 via-indigo-600 to-violet-600 px-6 py-6 text-white sm:px-8">
            <div class="flex items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <div class="flex size-12 items-center justify-center rounded-2xl bg-white/15 ring-1 ring-white/25">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="size-6" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-12 0v1.5a6 6 0 0 0 6 6m0 0v3m-3 0h6M12 15.75a3 3 0 0 0 3-3V5.25a3 3 0 0 0-6 0v7.5a3 3 0 0 0 3 3Z" />
                        </svg>
                    </div>
                    <div>
                        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-100">Voice receptionist</p>
                        <h1 class="mt-1 text-2xl font-bold">Talk to Bonnie</h1>
                    </div>
                </div>
                <span class="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-medium ring-1 ring-white/20">
                    <span class="size-2 rounded-full" :class="conversationEnded ? 'bg-emerald-300' : 'bg-green-300 animate-pulse'"></span>
                    {{ conversationEnded ? 'Complete' : 'Ready' }}
                </span>
            </div>
            <p class="mt-4 max-w-xl text-sm leading-6 text-indigo-100">
                Book a dental appointment naturally. Bonnie will collect your details and ask you to confirm before booking.
            </p>
        </div>

        <div class="grid lg:grid-cols-[1fr_220px]">
            <div class="p-5 sm:p-8">
                <div class="min-h-52 space-y-4 rounded-2xl bg-slate-50 p-4 ring-1 ring-slate-200 sm:p-5">
                    <div class="flex justify-end">
                        <div class="max-w-[88%] rounded-2xl rounded-br-md bg-indigo-600 px-4 py-3 text-sm leading-6 text-white shadow-sm">
                            <p class="mb-1 text-xs font-semibold text-indigo-100">You</p>
                            <p>{{ transcript || 'Your words will appear here…' }}</p>
                        </div>
                    </div>
                    <div class="flex items-start gap-3">
                        <div class="mt-1 flex size-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700">B</div>
                        <div class="max-w-[88%] rounded-2xl rounded-tl-md bg-white px-4 py-3 text-sm leading-6 text-slate-700 shadow-sm ring-1 ring-slate-200">
                            <p class="mb-1 text-xs font-semibold text-indigo-600">Bonnie</p>
                            <p v-if="isLoading" class="flex items-center gap-1.5 py-1" aria-label="Bonnie is thinking">
                                <span v-for="dot in 3" :key="dot" class="size-2 animate-bounce rounded-full bg-indigo-400" :style="{ animationDelay: `${dot * 120}ms` }"></span>
                            </p>
                            <p v-else>{{ aiReply || 'Hi! Tap the microphone and tell me how I can help.' }}</p>
                        </div>
                    </div>
                </div>

                <p v-if="speechError" class="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200" role="alert">
                    {{ speechError }}
                </p>

                <div class="mt-6 flex flex-col items-center">
                    <button
                        type="button"
                        :disabled="isListening || isLoading || conversationEnded || !speechSupported"
                        class="group flex size-20 items-center justify-center rounded-full text-white shadow-lg transition focus:outline-none focus:ring-4 focus:ring-indigo-200 disabled:cursor-not-allowed"
                        :class="isListening ? 'animate-pulse bg-red-500 shadow-red-200' : isLoading || conversationEnded || !speechSupported ? 'bg-slate-400 shadow-slate-200' : 'bg-indigo-600 shadow-indigo-200 hover:-translate-y-0.5 hover:bg-indigo-500'"
                        aria-label="Start speaking"
                        @click="startListening"
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="size-8" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-12 0v1.5a6 6 0 0 0 6 6m0 0v3m-3 0h6M12 15.75a3 3 0 0 0 3-3V5.25a3 3 0 0 0-6 0v7.5a3 3 0 0 0 3 3Z" />
                        </svg>
                    </button>
                    <p class="mt-3 text-sm font-semibold text-slate-700">
                        {{ conversationEnded ? 'Booking conversation complete' : isLoading ? 'Bonnie is thinking…' : isListening ? 'Listening… speak now' : 'Tap to speak' }}
                    </p>
                    <p v-if="!conversationEnded" class="mt-1 text-xs text-slate-500">Speak clearly and wait for Bonnie to reply</p>
                    <button v-else type="button" class="mt-3 text-sm font-semibold text-indigo-600 hover:text-indigo-500" @click="resetConversation">
                        Start a new conversation
                    </button>
                </div>
            </div>

            <aside class="border-t border-slate-200 bg-slate-50/80 p-5 lg:border-l lg:border-t-0">
                <div class="flex items-center justify-between">
                    <h2 class="text-sm font-semibold text-slate-900">Booking details</h2>
                    <span class="text-xs font-medium text-slate-500">{{ detailsCollected }}/5</span>
                </div>
                <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200">
                    <div class="h-full rounded-full bg-indigo-500 transition-all duration-500" :style="{ width: `${detailsCollected * 20}%` }"></div>
                </div>
                <dl class="mt-5 space-y-4">
                    <div v-for="item in collectedDetails" :key="item.label">
                        <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ item.label }}</dt>
                        <dd class="mt-1 break-words text-sm font-medium" :class="item.value ? 'text-slate-800' : 'text-slate-400'">
                            {{ item.value || 'Not provided' }}
                        </dd>
                    </div>
                </dl>
            </aside>
        </div>
    </div>
</template>
