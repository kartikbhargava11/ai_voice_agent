<script setup>
import VoiceChat from '@/components/VoiceChat.vue';

</script>

<template>
    <main class="relative min-h-[calc(100vh-4rem)] overflow-hidden bg-slate-50 px-4 py-8 sm:px-6 sm:py-12">
        <div class="pointer-events-none absolute -left-32 top-20 size-80 rounded-full bg-indigo-200/40 blur-3xl"></div>
        <div class="pointer-events-none absolute -right-32 bottom-10 size-96 rounded-full bg-violet-200/40 blur-3xl"></div>
        <div class="relative mx-auto max-w-4xl">
            <VoiceChat />
        </div>
    </main>
</template>
