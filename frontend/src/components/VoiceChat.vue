<script setup>
import { ref } from 'vue'
import api from '@/plugins/axios'

const transcript = ref('')
const aiReply = ref('')
const isListening = ref(false)
const isLoading = ref(false)
const conversationEnded = ref(false)

const state = ref({
    customer_name: null,
    customer_phone: null,
    service_needed: null,
    appointment_date: null,
    appointment_time: null
})

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

let recognition = null

if (SpeechRecognition) {
    recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.interimResults = false
    recognition.continuous = false

    recognition.onstart = () => {
        isListening.value = true
    }

    recognition.onend = () => {
        isListening.value = false
    }

    recognition.onresult = async (event) => {
        transcript.value = event.results[0][0].transcript
        await sendToBackend(transcript.value)
    }
}

const startListening = () => {
    if (!recognition) {
        alert('Speech Recognition is not supported')
        return
    }
    recognition.start()
}

const sendToBackend = async (message) => {
    isLoading.value = true
    try {
        const response = await api.post('/chat/fetch-chat/', { // post request to django endpoint to send the user message and state for backend logic purposes
            message,
            state: state.value
        })
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
        
        speak(aiReply.value) // send the AI reply to WebSpeech API
    } catch (error) {
        aiReply.value = 'Something went wrong'
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
<h1 class="text-lg font-bold text-slate-900">
    Talk to Bonnie
</h1>

<p class="mt-2 text-slate-500">
    Speak to book a dental appointment
</p>

<div class="mt-6">
    <button @click="startListening" :disabled="isListening || isLoading || conversationEnded"
    :class="isListening || isLoading || conversationEnded ? 'bg-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 cursor-pointer'"
    class="rounded-xl px-6 py-3 font-semibold text-white">
        {{  conversationEnded 
            ? 'Conversation Ended'
            : isListening
                ? 'Listening...'
                : 'Start Speaking' }}
    </button>
</div>

<div class="mt-6 rounded-xl bg-slate-100">
    <p class="text-sm font-semibold text-slate-500">You said:</p>
    <p class="mt-1 text-slate-800">
        {{  transcript || 'Nothing yet' }}
    </p>
</div>

<div class="mt-4 rounded-xl bg-blue-50 p-4">
    <p class="text-sm font-semibold text-blue-600">Receptionist:</p>
    <p class="mt-1 text-slate-800">
        {{  aiReply || 'Waiting for your message...' }}
    </p>
</div>
</template>