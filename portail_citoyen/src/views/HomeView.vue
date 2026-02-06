<script setup lang="ts">
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()
</script>

<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>Bienvenue sur le Portail Citoyen</h1>
        <p class="hero-subtitle">
          Signalez un problème, suivez vos demandes et participez à l'amélioration de votre cadre de vie.
        </p>
        <div class="hero-actions">
          <router-link to="/signaler" class="btn btn-primary btn-large">
            <span class="btn-icon">&#128679;</span>
            Signaler un problème
          </router-link>
          <router-link to="/suivi" class="btn btn-secondary btn-large">
            <span class="btn-icon">&#128269;</span>
            Suivre ma demande
          </router-link>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features">
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">&#128205;</div>
          <h3>Localisez</h3>
          <p>Indiquez précisément l'emplacement du problème sur la carte ou scannez un QR code.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">&#128247;</div>
          <h3>Photographiez</h3>
          <p>Ajoutez des photos pour illustrer le problème et aider les services techniques.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">&#128232;</div>
          <h3>Soyez informé</h3>
          <p>Recevez des notifications par email à chaque étape du traitement de votre demande.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">&#128200;</div>
          <h3>Suivez</h3>
          <p>Consultez l'avancement de votre signalement en temps réel avec votre numéro de suivi.</p>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="how-it-works">
      <h2>Comment ça marche ?</h2>
      <div class="steps">
        <div class="step">
          <div class="step-number">1</div>
          <h4>Décrivez le problème</h4>
          <p>Choisissez une catégorie et décrivez le problème rencontré.</p>
        </div>
        <div class="step-arrow">&#10140;</div>
        <div class="step">
          <div class="step-number">2</div>
          <h4>Localisez-le</h4>
          <p>Pointez l'emplacement sur la carte ou utilisez votre position GPS.</p>
        </div>
        <div class="step-arrow">&#10140;</div>
        <div class="step">
          <div class="step-number">3</div>
          <h4>Envoyez</h4>
          <p>Validez votre signalement et recevez un numéro de suivi.</p>
        </div>
        <div class="step-arrow">&#10140;</div>
        <div class="step">
          <div class="step-number">4</div>
          <h4>Suivez</h4>
          <p>Recevez des notifications à chaque étape du traitement.</p>
        </div>
      </div>
    </section>

    <!-- Categories Preview -->
    <section class="categories-preview" v-if="configStore.categories.length">
      <h2>Types de signalements</h2>
      <div class="categories-grid">
        <div
          v-for="category in configStore.categories.slice(0, 6)"
          :key="category.id"
          class="category-card"
          :style="{ '--category-color': category.couleur || '#2563eb' }"
        >
          <span class="category-icon">{{ category.icone || '&#128204;' }}</span>
          <span class="category-name">{{ category.nom }}</span>
        </div>
      </div>
      <router-link to="/signaler" class="btn btn-outline">Voir toutes les catégories</router-link>
    </section>
  </div>
</template>

<style scoped>
.home {
  min-height: 100%;
}

/* Hero */
.hero {
  background: linear-gradient(135deg, var(--primary-color, #2563eb) 0%, #1d4ed8 100%);
  color: white;
  padding: 4rem 2rem;
  text-align: center;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero h1 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.hero-subtitle {
  font-size: 1.25rem;
  opacity: 0.9;
  margin-bottom: 2rem;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.1rem;
}

.btn-primary {
  background: white;
  color: var(--primary-color, #2563eb);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid white;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.3);
}

.btn-outline {
  background: transparent;
  color: var(--primary-color, #2563eb);
  border: 2px solid var(--primary-color, #2563eb);
}

.btn-outline:hover {
  background: var(--primary-color, #2563eb);
  color: white;
}

.btn-icon {
  font-size: 1.25rem;
}

/* Features */
.features {
  padding: 4rem 2rem;
  background: white;
}

.features-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.feature-card {
  text-align: center;
  padding: 2rem;
  border-radius: 12px;
  background: #f9fafb;
  transition: transform 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.feature-card h3 {
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.feature-card p {
  color: #6b7280;
  font-size: 0.95rem;
}

/* How it works */
.how-it-works {
  padding: 4rem 2rem;
  background: #f9fafb;
  text-align: center;
}

.how-it-works h2 {
  color: #1f2937;
  margin-bottom: 3rem;
  font-size: 2rem;
}

.steps {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.step {
  flex: 1;
  min-width: 180px;
  max-width: 220px;
  padding: 1.5rem;
}

.step-number {
  width: 50px;
  height: 50px;
  background: var(--primary-color, #2563eb);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 auto 1rem;
}

.step h4 {
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.step p {
  color: #6b7280;
  font-size: 0.9rem;
}

.step-arrow {
  font-size: 1.5rem;
  color: var(--primary-color, #2563eb);
}

/* Categories */
.categories-preview {
  padding: 4rem 2rem;
  background: white;
  text-align: center;
}

.categories-preview h2 {
  color: #1f2937;
  margin-bottom: 2rem;
}

.categories-grid {
  max-width: 800px;
  margin: 0 auto 2rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.category-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1.5rem;
  border-radius: 12px;
  background: #f9fafb;
  border: 2px solid transparent;
  transition: all 0.2s;
  cursor: pointer;
}

.category-card:hover {
  border-color: var(--category-color);
  transform: translateY(-2px);
}

.category-icon {
  font-size: 2rem;
}

.category-name {
  font-weight: 500;
  color: #374151;
}

@media (max-width: 768px) {
  .hero h1 {
    font-size: 1.75rem;
  }

  .hero-subtitle {
    font-size: 1rem;
  }

  .step-arrow {
    display: none;
  }

  .steps {
    flex-direction: column;
  }
}
</style>
