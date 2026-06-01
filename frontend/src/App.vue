<script setup>
import AppBar from '@/components/AppBar.vue';
import Footer from '@/components/Footer.vue';
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
