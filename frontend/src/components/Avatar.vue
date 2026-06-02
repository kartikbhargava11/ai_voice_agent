<script setup>
defineProps(['role'])
</script>

<template>
    <div class="flex h-8 w-8 items-center justify-center rounded-full text-sm">
        <span v-if="role == 'AI'">
            👩🏻‍🦰
        </span>
        <span v-else>
            🫵🏻
        </span>
    </div>
</template>