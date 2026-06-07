<template>
  <div class="relative">
    <img
      :src="isUser ? '/images/user.avif' : '/images/robot.png'"
      class="w-8 h-8 rounded-full object-cover absolute -top-5 border-2 border-white"
      :class="isUser ? 'right-2' : 'left-2'"/>

    <div
      class="text-sm leading-relaxed my-8"
      :class="isUser
      ? 'text-right'
      : 'text-left'">
      <div
        class="px-4 py-3 rounded-2xl shadow-sm text-pretty inline-block"
        :class="isUser
        ? 'bg-blue-600 text-white rounded-tr-sm'
        : 'bg-white text-gray-800 rounded-tl-sm border border-gray-200'">
        {{ msg.text }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  msg: {
    type: Object,
    required: true,
  },
})

const isUser = computed(() => props.msg.role === "user");
</script>