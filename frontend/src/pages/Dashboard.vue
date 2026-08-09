<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/plugins/axios'

const stats = ref({
    total_leads: 0,
    total_appointments: 0,
    upcoming_appointments: 0,
    average_lead_score: 0
})

const leads = ref([])
const appointments = ref([])
const isLoading = ref(false)
const errorMessage = ref('')

const formatDate = (value) => {
    if (!value) return '—'

    const [year, month, day] = value.split('-').map(Number)
    if (!year || !month || !day) return value

    return new Intl.DateTimeFormat('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    }).format(new Date(year, month - 1, day))
}

const formatTime = (value) => {
    if (!value) return '—'
    return value.slice(0, 5)
}

const sourceLabels = {
    WEB_VOICE: 'Voice assistant',
    WEB_CHAT: 'Web chat',
    PHONE: 'Phone call',
    MANUAL: 'Manual'
}

const statusClasses = {
    NEW: 'bg-blue-100 text-blue-700',
    CONVERTED: 'bg-green-100 text-green-700',
    LOST: 'bg-red-100 text-red-700'
}

const updatingLeadId = ref(null)
const updatingAppointmentId = ref(null)

const updateLeadStatus = async (lead, status) => {
    updatingLeadId.value = lead.id
    errorMessage.value = ''
    try {
        const response = await api.patch(`/lead/${lead.id}/`, { status })
        Object.assign(lead, response.data)
    } catch (error) {
        if (error.response?.status !== 401) {
            errorMessage.value = error.response?.data?.status?.[0]
                || 'The lead status could not be updated.'
        }
    } finally {
        updatingLeadId.value = null
    }
}

const appointmentStatusClasses = {
    SCHEDULED: 'bg-blue-100 text-blue-700',
    ATTENDED: 'bg-green-100 text-green-700',
    MISSED: 'bg-red-100 text-red-700'
}

const updateAppointmentStatus = async (appointment, status) => {
    updatingAppointmentId.value = appointment.id
    errorMessage.value = ''
    try {
        const response = await api.patch(
            `/book-appointment/${appointment.id}/`,
            { status }
        )
        Object.assign(appointment, response.data)
    } catch (error) {
        if (error.response?.status !== 401) {
            errorMessage.value = error.response?.data?.status?.[0]
                || 'The appointment status could not be updated.'
        }
    } finally {
        updatingAppointmentId.value = null
    }
}

const fetchDashboard = async () => {
    isLoading.value = true
    errorMessage.value = ''

    try {
        const leadsResponse = await api.get('/lead/')
        const appointmentsResponse = await api.get('/book-appointment/')

        leads.value = leadsResponse.data
        appointments.value = appointmentsResponse.data

        stats.value.total_leads = leads.value.length
        stats.value.total_appointments = appointments.value.length
        const today = new Date().toISOString().slice(0, 10)
        stats.value.upcoming_appointments = appointments.value.filter(
            appointment => appointment.status === 'SCHEDULED'
                && appointment.appointment_date >= today
        ).length

        const totalScore = leads.value.reduce((sum, lead) => {
            return sum + (lead.lead_score || 0)
        }, 0)

        stats.value.average_lead_score = leads.value.length ? (totalScore / leads.value.length).toFixed(1) : 0

    } catch (error) {
        if (error.response?.status !== 401) {
            errorMessage.value = 'The dashboard could not be loaded. Please try again.'
        }
    } finally {
        isLoading.value = false
    }
}
onMounted(fetchDashboard)
</script>

<template>
    <div class="min-h-screen bg-slate-100 p-6">
        <div class="mx-auto max-w-7xl">
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-slate-900">
                    AI Receptionist Dashboard
                </h1>
                <p class="mt-1 text-slate-500">
                    Monitor Leads, Bookings, and Appointment Automation
                </p>
            </div>
            <div v-if="isLoading" class="text-slate-600">
                Loading Dashboard...
            </div>
            <div v-else-if="errorMessage" class="rounded-lg bg-red-50 p-4 text-red-700">
                {{ errorMessage }}
                <button type="button" class="ml-2 font-semibold underline" @click="fetchDashboard">
                    Try again
                </button>
            </div>
            <div v-else>
                <!-- KPIs -->
                <div class="grid lg:grid-cols-4 gap-4 lg:grid-rows-1 md:grid-rows-2 md:grid-cols-2 xs:grid-cols-1" xs:grid-rows-4>
                    <div class="rounded-xl bg-white p-5 shadow">
                        <p class="text-sm text-slate-500">Total Leads</p>
                        <h2 class="mt-2 text-3xl font-bold text-slate-900">
                            {{ stats.total_leads }}
                        </h2>
                    </div>
                    <div class="rounded-xl bg-white p-5 shadow">
                        <p class="text-sm text-slate-500">Total Appointments</p>
                        <h2 class="mt-2 text-3xl font-bold text-slate-900">
                            {{ stats.total_appointments }}
                        </h2>
                    </div>
                    <div class="rounded-xl bg-white p-5 shadow">
                        <p class="text-sm text-slate-500">Upcoming Appointments</p>
                        <h2 class="mt-2 text-3xl font-bold text-slate-900">
                            {{ stats.upcoming_appointments }}
                        </h2>
                    </div>
                    <div class="rounded-xl bg-white p-5 shadow">
                        <p class="text-sm text-slate-500">Avg Lead Score</p>
                        <h2 class="mt-2 text-3xl font-bold text-slate-900">
                            {{ stats.average_lead_score }}
                        </h2>
                    </div>
                </div>
                <!-- Tables -->
                <div class="mt-8 grid grid-cols-1 gap-6">
                    <!-- Leads Table -->
                    <div class="rounded-xl bg-white p-5 shadow">
                        <h2 class="mb-4 text-lg font-semibold text-slate-900">
                            Recent Leads
                        </h2>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-sm">
                                <thead>
                                    <tr class="border-b text-slate-500">
                                        <th class="py-2">Name</th>
                                        <th class="py-2">Phone</th>
                                        <th class="py-2">Service</th>
                                        <th class="py-2">Source</th>
                                        <th class="py-2">Status</th>
                                        <th class="py-2">Score</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="lead in leads.slice(0,8)" :key="lead.id" class="border-b last:border-0">
                                        <td class="py-3 font-medium text-slate-800">
                                            {{  lead.customer_name }}
                                        </td>
                                        <td class="py-3 font-medium text-slate-800">
                                            {{  lead.customer_phone }}
                                        </td>
                                        <td class="py-3 font-medium text-slate-800">
                                            {{  lead.service_needed }}
                                        </td>
                                        <td class="py-3 text-slate-700">
                                            {{ sourceLabels[lead.lead_source] || lead.lead_source }}
                                        </td>
                                        <td class="py-3">
                                            <div class="flex items-center gap-2">
                                                <span
                                                    class="rounded-full px-2 py-1 text-xs font-semibold"
                                                    :class="statusClasses[lead.status] || statusClasses.NEW"
                                                >
                                                    {{ lead.status === 'CONVERTED' ? 'Converted' : lead.status === 'LOST' ? 'Lost' : 'New' }}
                                                </span>
                                                <button
                                                    v-if="lead.status !== 'CONVERTED'"
                                                    type="button"
                                                    :disabled="updatingLeadId === lead.id"
                                                    class="text-xs font-medium text-indigo-600 hover:underline disabled:text-slate-400"
                                                    @click="updateLeadStatus(lead, lead.status === 'LOST' ? 'NEW' : 'LOST')"
                                                >
                                                    {{ updatingLeadId === lead.id ? 'Saving…' : lead.status === 'LOST' ? 'Reopen' : 'Mark lost' }}
                                                </button>
                                            </div>
                                        </td>
                                        <td class="py-3 font-medium text-slate-800">
                                            <span
                                            :class="lead.lead_score >= 8 ? 'bg-orange-400 text-orange-100': 'bg-blue-100 text-blue-700'"
                                            class="rounded-full px-2 py-1 text-xs font-semibold">
                                                {{  lead.lead_score || 0 }}
                                            </span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <!-- Appointment Table -->
                    <div class="rounded-xl bg-white p-5 shadow">
                        <h2 class="mb-4 text-lg font-semibold text-slate-900">
                            Recent Appointments
                        </h2>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-sm">
                                <thead>
                                    <tr class="border-b text-slate-500">
                                        <th class="py-2">Lead</th>
                                        <th class="py-2">Date</th>
                                        <th class="py-2">Time</th>
                                        <th class="py-2">Status</th>
                                        <th class="py-2">Calendar</th>
                                        <th class="py-2">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="appointment in appointments.slice(0,8)" :key="appointment.id" class="border-b last:border-0">
                                        <td class="py-3 font-medium text-slate-800">
                                            {{  appointment.lead }}
                                        </td>
                                        <td class="py-3 font-medium text-slate-800">
                                            {{ formatDate(appointment.appointment_date) }}
                                        </td>
                                        <td class="py-3 font-medium text-slate-800">
                                            {{ formatTime(appointment.appointment_time) }}
                                        </td>
                                        <td class="py-3">
                                            <span
                                                class="rounded-full px-2 py-1 text-xs font-semibold"
                                                :class="appointmentStatusClasses[appointment.status] || appointmentStatusClasses.SCHEDULED"
                                            >
                                                {{ appointment.status === 'ATTENDED' ? 'Attended' : appointment.status === 'MISSED' ? 'Missed' : 'Scheduled' }}
                                            </span>
                                        </td>
                                        <td class="py-3">
                                            <span
                                                class="rounded-full px-2 py-1 text-xs font-semibold"
                                                :class="appointment.calendar_event_id ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                                                {{ appointment.calendar_event_id ? 'Synced' : 'Pending' }}
                                            </span>
                                        </td>
                                        <td class="py-3">
                                            <div class="flex flex-wrap gap-2">
                                                <button
                                                    type="button"
                                                    :disabled="updatingAppointmentId === appointment.id || appointment.status === 'ATTENDED'"
                                                    class="text-xs font-semibold text-green-700 hover:underline disabled:text-slate-400 disabled:no-underline"
                                                    @click="updateAppointmentStatus(appointment, 'ATTENDED')"
                                                >
                                                    Attended
                                                </button>
                                                <button
                                                    type="button"
                                                    :disabled="updatingAppointmentId === appointment.id || appointment.status === 'MISSED'"
                                                    class="text-xs font-semibold text-red-700 hover:underline disabled:text-slate-400 disabled:no-underline"
                                                    @click="updateAppointmentStatus(appointment, 'MISSED')"
                                                >
                                                    Missed
                                                </button>
                                                <button
                                                    v-if="appointment.status !== 'SCHEDULED'"
                                                    type="button"
                                                    :disabled="updatingAppointmentId === appointment.id"
                                                    class="text-xs font-semibold text-blue-700 hover:underline disabled:text-slate-400"
                                                    @click="updateAppointmentStatus(appointment, 'SCHEDULED')"
                                                >
                                                    Reset
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>

</style>
