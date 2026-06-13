<script setup>
import VoiceChat from '@/components/VoiceChat.vue';

</script>

<template>
    <div class="grid grid-cols-12 py-8">
        <div class="col-span-12 md:col-span-6 md:col-start-4 lg:col-span-4 lg:col-start-5">
            <div class="rounded-lg bg-slate-100 p-4 shadow-sm/20">
                <VoiceChat />
            </div>
        </div>
    </div>
</template>