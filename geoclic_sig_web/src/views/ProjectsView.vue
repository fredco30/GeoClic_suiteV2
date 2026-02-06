<template>
  <div class="projects-view">
    <div class="projects-header">
      <h2>Projets</h2>
      <p>Sélectionnez un projet pour charger ses données sur la carte</p>
    </div>

    <div v-if="mapStore.loading" class="loading">
      Chargement des projets...
    </div>

    <div v-else-if="mapStore.projects.length === 0" class="empty-state">
      <span class="empty-icon">📁</span>
      <p>Aucun projet disponible</p>
    </div>

    <div v-else class="projects-grid">
      <div
        v-for="project in mapStore.projects"
        :key="project.id"
        class="project-card"
        :class="{ active: mapStore.currentProject?.id === project.id }"
        @click="selectProject(project)"
      >
        <div class="project-icon">📊</div>
        <div class="project-info">
          <h3>{{ project.name }}</h3>
          <p v-if="project.description">{{ project.description }}</p>
          <span class="project-date">
            Créé le {{ formatDate(project.created_at) }}
          </span>
        </div>
        <div v-if="mapStore.currentProject?.id === project.id" class="active-badge">
          Actif
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMapStore, type Project } from '../stores/map'

const router = useRouter()
const mapStore = useMapStore()

onMounted(() => {
  mapStore.loadProjects()
})

async function selectProject(project: Project) {
  await mapStore.selectProject(project)
  router.push('/')
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR')
}
</script>

<style scoped>
.projects-view {
  padding: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.projects-header {
  margin-bottom: 30px;
}

.projects-header h2 {
  margin: 0 0 5px 0;
  color: #1a1a2e;
}

.projects-header p {
  margin: 0;
  color: #666;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 60px;
  color: #999;
}

.empty-icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 15px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.project-card {
  background: white;
  border: 2px solid #eee;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  gap: 15px;
  align-items: flex-start;
  position: relative;
}

.project-card:hover {
  border-color: #3498db;
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.2);
}

.project-card.active {
  border-color: #3498db;
  background: #f0f8ff;
}

.project-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.project-info {
  flex: 1;
}

.project-info h3 {
  margin: 0 0 5px 0;
  font-size: 1.1rem;
  color: #1a1a2e;
}

.project-info p {
  margin: 0 0 8px 0;
  font-size: 0.9rem;
  color: #666;
}

.project-date {
  font-size: 0.8rem;
  color: #999;
}

.active-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #3498db;
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
}
</style>
