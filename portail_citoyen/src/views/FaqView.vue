<script setup lang="ts">
import { ref, computed } from 'vue'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()

interface FaqItem {
  question: string
  answer: string
  category: string
}

const faqItems: FaqItem[] = [
  // Signalement
  {
    category: 'Signalement',
    question: 'Comment signaler un problème dans ma commune ?',
    answer: 'Cliquez sur "Signaler" dans le menu, puis suivez les 4 étapes : choisissez une catégorie, décrivez le problème, indiquez la localisation sur la carte, et laissez vos coordonnées pour le suivi.'
  },
  {
    category: 'Signalement',
    question: 'Quels types de problèmes puis-je signaler ?',
    answer: 'Vous pouvez signaler tout problème touchant l\'espace public : voirie (nids-de-poule, trottoirs), propreté (dépôts sauvages, poubelles), éclairage (lampadaires), espaces verts (arbres, pelouses), mobilier urbain, etc. Les catégories disponibles sont configurées par votre collectivité.'
  },
  {
    category: 'Signalement',
    question: 'Dois-je créer un compte pour signaler ?',
    answer: 'Non, aucun compte n\'est nécessaire. Il vous suffit de fournir une adresse email valide pour recevoir votre numéro de suivi et les notifications de progression.'
  },
  {
    category: 'Signalement',
    question: 'Puis-je ajouter des photos à mon signalement ?',
    answer: 'Oui, vous pouvez ajouter jusqu\'à 3 photos. C\'est facultatif mais fortement recommandé : une photo aide les agents à mieux comprendre le problème et à préparer l\'intervention.'
  },
  {
    category: 'Signalement',
    question: 'Comment localiser le problème sur la carte ?',
    answer: 'Trois méthodes sont disponibles : 1) Cliquez sur le bouton GPS pour utiliser votre position actuelle, 2) Déplacez le marqueur sur la carte avec votre doigt ou souris, 3) Tapez une adresse dans la barre de recherche. Vous pouvez passer en plein écran pour plus de précision.'
  },

  // Suivi
  {
    category: 'Suivi',
    question: 'Comment suivre mon signalement ?',
    answer: 'Après votre signalement, vous recevez un numéro de suivi par email (format SIG-XXXX-XXXXXXXX). Allez sur la page "Suivi", entrez ce numéro, et consultez l\'état actuel de votre demande.'
  },
  {
    category: 'Suivi',
    question: 'Que signifient les différents statuts ?',
    answer: 'Nouveau : votre signalement vient d\'être reçu. Accepté : la collectivité l\'a pris en compte. En cours : un agent est assigné. Planifié : une date d\'intervention est fixée. Traité : le problème est résolu. Rejeté : le signalement n\'a pas été retenu (un motif est indiqué).'
  },
  {
    category: 'Suivi',
    question: 'Serai-je informé de l\'avancement ?',
    answer: 'Si la collectivité a configuré les notifications email, vous recevrez un email à chaque changement de statut important (acceptation, prise en charge, résolution, rejet).'
  },
  {
    category: 'Suivi',
    question: 'J\'ai perdu mon numéro de suivi, que faire ?',
    answer: 'Vérifiez votre boîte email (et les spams) : le numéro vous a été envoyé lors de la confirmation. Si vous ne le retrouvez pas, contactez directement votre mairie avec la date et le lieu approximatif de votre signalement.'
  },

  // Carte
  {
    category: 'Carte',
    question: 'À quoi sert la carte des signalements ?',
    answer: 'La carte publique affiche tous les signalements actifs dans votre commune. Vous pouvez visualiser les problèmes déjà signalés, voir leur statut, et vérifier si le problème que vous souhaitez signaler est déjà connu.'
  },
  {
    category: 'Carte',
    question: 'Pourquoi certains signalements n\'apparaissent-ils pas ?',
    answer: 'Seuls les signalements en cours de traitement sont visibles. Les signalements traités (résolus) ou rejetés sont retirés de la carte après un certain délai.'
  },

  // Données personnelles
  {
    category: 'Données personnelles',
    question: 'Mes données personnelles sont-elles protégées ?',
    answer: 'Votre email est utilisé uniquement pour le suivi de votre signalement. Vos coordonnées ne sont pas affichées publiquement sur la carte. Seuls les agents de la collectivité y ont accès dans le cadre du traitement de votre demande.'
  },
  {
    category: 'Données personnelles',
    question: 'Mon signalement est-il anonyme ?',
    answer: 'Votre signalement est visible sur la carte publique (description et localisation), mais votre identité n\'est jamais affichée. Les agents de la collectivité ont accès à votre email pour vous contacter si nécessaire.'
  },
]

const categories = computed(() => [...new Set(faqItems.map(f => f.category))])
const selectedCategory = ref<string | null>(null)
const searchQuery = ref('')
const expandedIndex = ref<number | null>(null)

const filteredFaq = computed(() => {
  let items = faqItems
  if (selectedCategory.value) {
    items = items.filter(f => f.category === selectedCategory.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    items = items.filter(f =>
      f.question.toLowerCase().includes(q) || f.answer.toLowerCase().includes(q)
    )
  }
  return items
})

function toggleItem(index: number) {
  expandedIndex.value = expandedIndex.value === index ? null : index
}

function selectCategory(cat: string | null) {
  selectedCategory.value = cat
  expandedIndex.value = null
}
</script>

<template>
  <div class="faq-page">
    <header class="faq-header">
      <h1>Questions fréquentes</h1>
      <p>Trouvez rapidement les réponses à vos questions sur le portail citoyen</p>
    </header>

    <div class="faq-search">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Rechercher une question..."
        class="search-input"
      />
    </div>

    <div class="faq-categories">
      <button
        class="cat-btn"
        :class="{ active: selectedCategory === null }"
        @click="selectCategory(null)"
      >
        Toutes
      </button>
      <button
        v-for="cat in categories"
        :key="cat"
        class="cat-btn"
        :class="{ active: selectedCategory === cat }"
        @click="selectCategory(cat)"
      >
        {{ cat }}
      </button>
    </div>

    <div class="faq-list">
      <div
        v-for="(item, index) in filteredFaq"
        :key="index"
        class="faq-item"
        :class="{ expanded: expandedIndex === index }"
      >
        <button class="faq-question" @click="toggleItem(index)">
          <span class="q-text">{{ item.question }}</span>
          <span class="q-icon">{{ expandedIndex === index ? '−' : '+' }}</span>
        </button>
        <div v-if="expandedIndex === index" class="faq-answer">
          <p>{{ item.answer }}</p>
        </div>
      </div>

      <div v-if="filteredFaq.length === 0" class="no-results">
        <p>Aucun résultat pour votre recherche.</p>
      </div>
    </div>

    <div class="faq-contact" v-if="configStore.contactEmail || configStore.contactTelephone">
      <h2>Vous n'avez pas trouvé votre réponse ?</h2>
      <p>Contactez directement votre collectivité :</p>
      <div class="contact-info">
        <a v-if="configStore.contactEmail" :href="'mailto:' + configStore.contactEmail" class="contact-link">
          {{ configStore.contactEmail }}
        </a>
        <a v-if="configStore.contactTelephone" :href="'tel:' + configStore.contactTelephone" class="contact-link">
          {{ configStore.contactTelephone }}
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.faq-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.faq-header {
  text-align: center;
  margin-bottom: 2rem;
}

.faq-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--primary-color, #2563eb);
  margin: 0 0 0.5rem;
}

.faq-header p {
  color: #6b7280;
  margin: 0;
}

.faq-search {
  margin-bottom: 1.5rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 1rem;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color, #2563eb);
}

.faq-categories {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}

.cat-btn {
  padding: 0.4rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  background: white;
  color: #4b5563;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.cat-btn:hover {
  border-color: var(--primary-color, #2563eb);
  color: var(--primary-color, #2563eb);
}

.cat-btn.active {
  background: var(--primary-color, #2563eb);
  color: white;
  border-color: var(--primary-color, #2563eb);
}

.faq-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 2rem;
}

.faq-item {
  background: white;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.faq-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.faq-item.expanded {
  border-color: var(--primary-color, #2563eb);
}

.faq-question {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  font-size: 0.95rem;
  font-weight: 500;
  color: #1f2937;
}

.q-icon {
  font-size: 1.25rem;
  font-weight: 300;
  color: #9ca3af;
  flex-shrink: 0;
  margin-left: 1rem;
}

.faq-answer {
  padding: 0 1.25rem 1rem;
  color: #4b5563;
  line-height: 1.6;
  font-size: 0.9rem;
}

.faq-answer p {
  margin: 0;
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}

.faq-contact {
  text-align: center;
  background: #f9fafb;
  border-radius: 12px;
  padding: 1.5rem;
}

.faq-contact h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem;
}

.faq-contact p {
  color: #6b7280;
  margin: 0 0 1rem;
  font-size: 0.9rem;
}

.contact-info {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.contact-link {
  color: var(--primary-color, #2563eb);
  text-decoration: none;
  font-weight: 500;
}

.contact-link:hover {
  text-decoration: underline;
}
</style>
