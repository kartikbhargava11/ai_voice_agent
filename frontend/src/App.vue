<script setup>
import { onBeforeUnmount, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import AppBar from '@/components/AppBar.vue';
import Footer from '@/components/Footer.vue';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const handleUnauthorized = () => {
  auth.logout();
  if (route.meta.requiresAuth) {
    router.replace({ name: 'Login', query: { redirect: route.fullPath } });
  }
};

onMounted(() => window.addEventListener('auth:unauthorized', handleUnauthorized));
onBeforeUnmount(() => window.removeEventListener('auth:unauthorized', handleUnauthorized));
</script>

<template>
  <div class="flex flex-col min-h-screen">
    <AppBar />
    <main class="container mx-auto grow">
      <RouterView />
    </main>
    <Footer />
  </div>
</template>

<style scoped></style>
