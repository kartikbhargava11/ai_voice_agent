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
const activeTab = ref('leads')

const localDateValue = () => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
}

const upcomingAppointments = computed(() => {
    const today = localDateValue()
    return appointments.value.filter(
        appointment => appointment.appointment_date >= today
    )
})

const pastAppointments = computed(() => {
    const today = localDateValue()
    return appointments.value.filter(
        appointment => appointment.appointment_date < today
    )
})

const visibleAppointments = computed(() => (
    activeTab.value === 'past-appointments'
        ? pastAppointments.value
        : upcomingAppointments.value
))

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

const handleLeadAction = (event, lead) => {
    const status = event.target.value
    event.target.value = ''
    if (status) updateLeadStatus(lead, status)
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

const handleAppointmentAction = (event, appointment) => {
    const status = event.target.value
    event.target.value = ''
    if (status) updateAppointmentStatus(appointment, status)
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
        const today = localDateValue()
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
                        <p class="text-sm text-slate-500">Avg Service Priority</p>
                        <h2 class="mt-2 text-3xl font-bold text-slate-900">
                            {{ stats.average_lead_score }}
                        </h2>
                    </div>
                </div>
                <!-- Tabbed tables -->
                <div class="mt-8 overflow-hidden rounded-2xl bg-white shadow ring-1 ring-slate-200">
                    <div class="flex overflow-x-auto border-b border-slate-200 bg-slate-50 px-4 pt-3 sm:px-6">
                        <button
                            type="button"
                            class="relative shrink-0 px-4 py-3 text-sm font-semibold transition"
                            :class="activeTab === 'leads' ? 'text-indigo-700' : 'text-slate-500 hover:text-slate-800'"
                            @click="activeTab = 'leads'"
                        >
                            Recent Leads
                            <span class="ml-2 rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700">
                                {{ leads.length }}
                            </span>
                            <span v-if="activeTab === 'leads'" class="absolute inset-x-2 bottom-0 h-0.5 bg-indigo-600"></span>
                        </button>
                        <button
                            type="button"
                            class="relative shrink-0 px-4 py-3 text-sm font-semibold transition"
                            :class="activeTab === 'appointments' ? 'text-indigo-700' : 'text-slate-500 hover:text-slate-800'"
                            @click="activeTab = 'appointments'"
                        >
                            Upcoming Appointments
                            <span class="ml-2 rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700">
                                {{ upcomingAppointments.length }}
                            </span>
                            <span v-if="activeTab === 'appointments'" class="absolute inset-x-2 bottom-0 h-0.5 bg-indigo-600"></span>
                        </button>
                        <button
                            type="button"
                            class="relative shrink-0 px-4 py-3 text-sm font-semibold transition"
                            :class="activeTab === 'past-appointments' ? 'text-indigo-700' : 'text-slate-500 hover:text-slate-800'"
                            @click="activeTab = 'past-appointments'"
                        >
                            Past Appointments
                            <span class="ml-2 rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700">
                                {{ pastAppointments.length }}
                            </span>
                            <span v-if="activeTab === 'past-appointments'" class="absolute inset-x-2 bottom-0 h-0.5 bg-indigo-600"></span>
                        </button>
                    </div>

                    <!-- Leads Table -->
                    <div v-if="activeTab === 'leads'" class="p-5 sm:p-6">
                        <div class="mb-5">
                            <h2 class="text-lg font-semibold text-slate-900">Recent Leads</h2>
                            <p class="mt-1 text-sm text-slate-500">Review lead sources, service priorities, and conversion outcomes.</p>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-sm">
                                <thead>
                                    <tr class="border-b text-slate-500">
                                        <th class="py-2">Name</th>
                                        <th class="py-2">Phone</th>
                                        <th class="py-2">Service</th>
                                        <th class="py-2">Source</th>
                                        <th class="py-2">Status</th>
                                        <th class="py-2">Service Priority</th>
                                        <th class="py-2 text-right">Actions</th>
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
                                            <span
                                                class="rounded-full px-2 py-1 text-xs font-semibold"
                                                :class="statusClasses[lead.status] || statusClasses.NEW"
                                            >
                                                {{ lead.status === 'CONVERTED' ? 'Converted' : lead.status === 'LOST' ? 'Lost' : 'New' }}
                                            </span>
                                        </td>
                                        <td class="py-3 font-medium text-slate-800">
                                            <span
                                            :class="lead.lead_score >= 8 ? 'bg-orange-400 text-orange-100': 'bg-blue-100 text-blue-700'"
                                            class="rounded-full px-2 py-1 text-xs font-semibold">
                                                {{  lead.lead_score || 0 }}
                                            </span>
                                        </td>
                                        <td class="py-3 text-right">
                                            <select
                                                value=""
                                                :disabled="updatingLeadId === lead.id || lead.status === 'CONVERTED'"
                                                class="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
                                                aria-label="Lead actions"
                                                @change="handleLeadAction($event, lead)"
                                            >
                                                <option value="" disabled>
                                                    {{ updatingLeadId === lead.id ? 'Saving…' : lead.status === 'CONVERTED' ? 'No actions' : 'Actions' }}
                                                </option>
                                                <option v-if="lead.status === 'NEW'" value="LOST">Mark as lost</option>
                                                <option v-if="lead.status === 'LOST'" value="NEW">Reopen lead</option>
                                            </select>
                                        </td>
                                    </tr>
                                    <tr v-if="leads.length === 0">
                                        <td colspan="7" class="py-10 text-center text-slate-500">No leads found.</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <!-- Appointment Table -->
                    <div v-else class="p-5 sm:p-6">
                        <div class="mb-5">
                            <div>
                                <h2 class="text-lg font-semibold text-slate-900">
                                    {{ activeTab === 'past-appointments' ? 'Past Appointments' : 'Upcoming Appointments' }}
                                </h2>
                                <p class="mt-1 text-sm text-slate-500">
                                    {{ activeTab === 'past-appointments'
                                        ? 'Review previous appointments and their attendance status.'
                                        : 'Track future bookings, attendance, and calendar sync status.' }}
                                </p>
                            </div>
                        </div>
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
                                    <tr v-for="appointment in visibleAppointments" :key="appointment.id" class="border-b last:border-0">
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
                                            <select
                                                value=""
                                                :disabled="updatingAppointmentId === appointment.id"
                                                class="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-indigo-500 disabled:cursor-wait disabled:bg-slate-100"
                                                aria-label="Appointment actions"
                                                @change="handleAppointmentAction($event, appointment)"
                                            >
                                                <option value="" disabled>{{ updatingAppointmentId === appointment.id ? 'Saving…' : 'Actions' }}</option>
                                                <option v-if="appointment.status !== 'ATTENDED'" value="ATTENDED">Mark attended</option>
                                                <option v-if="appointment.status !== 'MISSED'" value="MISSED">Mark missed</option>
                                                <option v-if="appointment.status !== 'SCHEDULED'" value="SCHEDULED">Reset to scheduled</option>
                                            </select>
                                        </td>
                                    </tr>
                                    <tr v-if="visibleAppointments.length === 0">
                                        <td colspan="6" class="py-10 text-center text-slate-500">
                                            {{ activeTab === 'past-appointments' ? 'No past appointments.' : 'No upcoming appointments.' }}
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
