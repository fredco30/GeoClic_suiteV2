<template>
  <component :is="layout">
    <router-view />
  </component>
  <!-- Drawer d'aide global -->
  <HelpDrawer />
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DefaultLayout from '@/layouts/default.vue'
import AdminLayout from '@/layouts/admin.vue'
import HelpDrawer from '@/components/help/HelpDrawer.vue'

const route = useRoute()

const layouts: Record<string, any> = {
  default: DefaultLayout,
  admin: AdminLayout,
}

const layout = computed(() => {
  const layoutName = (route.meta?.layout as string) || 'default'
  return layouts[layoutName] || DefaultLayout
})
</script>
