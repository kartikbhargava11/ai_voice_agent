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

const fetchDashboard = async () => {
    isLoading.value = true

    try {
        const leadsResponse = await api.get('/lead/')
        const appointmentsResponse = await api.get('/book-appointment/')

        leads.value = leadsResponse.data
        appointments.value = appointmentsResponse.data

        stats.value.total_leads = leads.value.length
        stats.value.total_appointments = appointments.value.length
        stats.value.upcoming_appointments = appointments.value.length

        const totalScore = leads.value.reduce((sum, lead) => {
            return sum + (lead.lead_score || 0)
        }, 0)

        stats.value.average_lead_score = leads.value.length ? (totalScore / leads.value.length).toFixed(1) : 0

    } catch (e) {

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
                <div class="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
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
                                        <th class="py-2">Calendar</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="appointment in appointments.slice(0,8)" :key="appointment.id" class="border-b last:border-0">
                                        <td class="py-3 font-medium text-slate-800">
                                            {{  appointment.lead }}
                                        </td>
                                        <td class="py-3 font-medium text-slate-800">
                                            {{  appointment.appointment_date }}
                                        </td>
                                        <td class="py-3 font-medium text-slate-800">
                                            {{  appointment.appointment_time }}
                                        </td>
                                        <td class="py-3">
                                            <span
                                                class="rounded-full px-2 py-1 text-xs font-semibold"
                                                :class="appointment.calendar_event_id ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                                                {{ appointment.calendar_event_id ? 'Synced' : 'Pending' }}
                                            </span>
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