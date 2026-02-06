<template>
  <div>
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          Gestion des Projets
          <HelpButton page-key="projets" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          Créez et gérez vos projets de collecte
        </p>
      </div>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-plus" @click="showDialog = true">
        Nouveau projet
      </v-btn>
    </div>

    <v-row>
      <v-col v-for="projet in projets" :key="projet.id" cols="12" md="4">
        <v-card
          class="projet-card"
          @click="openProjet(projet)"
          :style="{ cursor: 'pointer' }"
        >
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="primary">mdi-folder</v-icon>
            {{ projet.nom }}
            <v-spacer />
            <v-chip :color="projet.actif ? 'success' : 'grey'" size="small">
              {{ projet.actif ? 'Actif' : 'Archivé' }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <p class="text-body-2">{{ projet.description || 'Aucune description' }}</p>
            <v-divider class="my-3" />
            <div class="d-flex justify-space-between text-caption">
              <span>{{ projet.points_count || 0 }} points</span>
              <span>{{ projet.users_count || 0 }} utilisateurs</span>
            </div>
          </v-card-text>
          <v-card-actions @click.stop>
            <v-btn variant="text" size="small" color="primary" @click="openProjet(projet)">
              <v-icon start>mdi-cog</v-icon> Configurer
            </v-btn>
            <v-btn variant="text" size="small" @click="editProjet(projet)">
              <v-icon start>mdi-pencil</v-icon> Infos
            </v-btn>
            <v-spacer />
            <v-btn icon size="small" variant="text" color="error" @click="deleteProjet(projet)">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col v-if="!projets.length" cols="12">
        <v-card class="text-center pa-8">
          <v-icon size="64" color="grey" class="mb-4">mdi-folder-plus</v-icon>
          <h3 class="text-h6 mb-2">Aucun projet</h3>
          <p class="text-body-2 text-grey mb-4">Créez votre premier projet pour commencer</p>
          <v-btn color="primary" @click="showDialog = true">
            <v-icon start>mdi-plus</v-icon>
            Créer un projet
          </v-btn>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog création/édition -->
    <v-dialog v-model="showDialog" max-width="700" persistent>
      <v-card>
        <v-card-title>{{ editMode ? 'Modifier le projet' : 'Nouveau projet' }}</v-card-title>
        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <v-text-field
              v-model="formData.nom"
              label="Nom du projet *"
              :rules="[v => !!v || 'Nom requis']"
            />
            <v-textarea
              v-model="formData.description"
              label="Description"
              rows="2"
              class="mt-4"
            />
            <v-switch
              v-model="formData.actif"
              label="Projet actif"
              color="success"
              class="mt-2"
            />

            <!-- Templates (seulement en création) -->
            <div v-if="!editMode" class="mt-4">
              <div class="text-subtitle-2 mb-3">
                <v-icon size="18" class="mr-1">mdi-file-document-multiple</v-icon>
                Démarrer avec un template (optionnel)
              </div>
              <v-row>
                <v-col
                  v-for="template in projectTemplates"
                  :key="template.id"
                  cols="12"
                  sm="6"
                  md="4"
                >
                  <v-card
                    :variant="selectedTemplate?.id === template.id ? 'tonal' : 'outlined'"
                    :color="selectedTemplate?.id === template.id ? 'primary' : undefined"
                    class="template-card"
                    @click="selectTemplate(template)"
                  >
                    <v-card-text class="text-center pa-3">
                      <v-icon :color="template.color" size="32">{{ template.icon }}</v-icon>
                      <div class="text-subtitle-2 mt-2">{{ template.name }}</div>
                      <div class="text-caption text-grey">
                        {{ template.families.length }} familles
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
              <v-btn
                v-if="selectedTemplate"
                variant="text"
                size="small"
                class="mt-2"
                @click="selectedTemplate = null"
              >
                <v-icon start>mdi-close</v-icon>
                Projet vide (sans template)
              </v-btn>
            </div>

            <!-- Aperçu du template sélectionné -->
            <v-expand-transition>
              <div v-if="selectedTemplate" class="mt-4">
                <v-alert type="info" variant="tonal" density="compact">
                  <div class="text-subtitle-2 mb-2">
                    Structure du template "{{ selectedTemplate.name }}"
                  </div>
                  <div class="template-preview-tree">
                    <div
                      v-for="family in selectedTemplate.families"
                      :key="family.code"
                      class="family-block mb-2"
                    >
                      <div class="family-header d-flex align-center">
                        <v-icon size="18" :color="family.color" class="mr-1">{{ family.icon }}</v-icon>
                        <strong>{{ family.label }}</strong>
                        <v-chip size="x-small" class="ml-2" variant="tonal">
                          {{ countTotalElements(family) }} éléments
                        </v-chip>
                      </div>
                      <div v-if="family.children?.length" class="types-list ml-4 mt-1">
                        <div
                          v-for="type in family.children.slice(0, 4)"
                          :key="type.code"
                          class="type-item text-caption"
                        >
                          <v-icon size="12" class="mr-1">{{ type.icon }}</v-icon>
                          {{ type.label }}
                          <span v-if="type.children?.length" class="text-grey">
                            ({{ type.children.length }} sous-types)
                          </span>
                        </div>
                        <div v-if="family.children.length > 4" class="text-caption text-grey">
                          ... et {{ family.children.length - 4 }} autres types
                        </div>
                      </div>
                      <div v-if="family.fields?.length" class="fields-info ml-4 text-caption text-grey">
                        <v-icon size="12" class="mr-1">mdi-form-textbox</v-icon>
                        {{ family.fields.length }} champs configurés
                      </div>
                    </div>
                  </div>
                </v-alert>
              </div>
            </v-expand-transition>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn color="primary" :disabled="!formValid" :loading="saving" @click="saveProjet">
            {{ editMode ? 'Modifier' : 'Créer' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { projetsAPI, lexiqueAPI, champsAPI } from '@/services/api'
import HelpButton from '@/components/help/HelpButton.vue'
import { projectTemplates, countTotalElements } from '@/constants/templates'

const router = useRouter()
const projets = ref<any[]>([])
const showDialog = ref(false)
const editMode = ref(false)
const formValid = ref(false)
const saving = ref(false)
const selectedProjet = ref<any>(null)
const selectedTemplate = ref<any>(null)

const formData = ref({
  nom: '',
  description: '',
  actif: true,
})

function selectTemplate(template: any) {
  selectedTemplate.value = selectedTemplate.value?.id === template.id ? null : template
}

async function loadProjets() {
  try {
    projets.value = await projetsAPI.getAll()
  } catch (e) {
    console.error('Erreur chargement projets:', e)
  }
}

function editProjet(projet: any) {
  editMode.value = true
  selectedProjet.value = projet
  formData.value = { ...projet }
  selectedTemplate.value = null
  showDialog.value = true
}

function closeDialog() {
  showDialog.value = false
  editMode.value = false
  selectedProjet.value = null
  selectedTemplate.value = null
  formData.value = { nom: '', description: '', actif: true }
}

async function applyTemplate(template: any, projectId: string) {
  // Créer la structure du template dans le lexique pour ce projet (3 niveaux)
  for (const family of template.families) {
    // Créer la famille (niveau 0)
    try {
      await lexiqueAPI.create({
        code: family.code,
        libelle: family.label,
        icone: family.icon,
        couleur: family.color,
        parent_id: null,
        niveau: 0,
        actif: true,
        ordre: 0,
        project_id: projectId
      })

      // Créer les champs de la famille (applicables à tous les descendants)
      if (family.fields) {
        for (let i = 0; i < family.fields.length; i++) {
          const field = family.fields[i]
          try {
            await champsAPI.create({
              lexique_id: family.code,
              nom: field.nom,
              type: field.type,
              obligatoire: field.obligatoire || false,
              options: field.options,
              min: field.min,
              max: field.max,
              ordre: field.ordre || i,
              actif: true,
              project_id: projectId
            })
          } catch (e) {
            console.warn(`Champ ${field.nom} existe peut-être déjà pour ${family.code}`)
          }
        }
      }

      // Créer les types (niveau 1)
      if (family.children) {
        for (let i = 0; i < family.children.length; i++) {
          const type = family.children[i]
          try {
            await lexiqueAPI.create({
              code: type.code,
              libelle: type.label,
              icone: type.icon || family.icon,
              couleur: family.color,
              parent_id: family.code,
              niveau: 1,
              actif: true,
              ordre: i,
              project_id: projectId
            })

            // Créer les sous-types (niveau 2)
            if (type.children) {
              for (let j = 0; j < type.children.length; j++) {
                const subtype = type.children[j]
                try {
                  await lexiqueAPI.create({
                    code: subtype.code,
                    libelle: subtype.label,
                    icone: subtype.icon || type.icon || family.icon,
                    couleur: family.color,
                    parent_id: type.code,
                    niveau: 2,
                    actif: true,
                    ordre: j,
                    project_id: projectId
                  })
                } catch (e) {
                  console.warn(`Sous-type ${subtype.code} existe peut-être déjà`)
                }
              }
            }
          } catch (e) {
            console.warn(`Type ${type.code} existe peut-être déjà`)
          }
        }
      }
    } catch (e) {
      console.warn(`Famille ${family.code} existe peut-être déjà`)
    }
  }
}

async function saveProjet() {
  saving.value = true
  try {
    if (editMode.value && selectedProjet.value) {
      await projetsAPI.update(selectedProjet.value.id, formData.value)
    } else {
      // Créer le projet
      const newProjet = await projetsAPI.create(formData.value)

      // Appliquer le template si sélectionné
      if (selectedTemplate.value && newProjet?.id) {
        await applyTemplate(selectedTemplate.value, newProjet.id)
      }

      // Rediriger vers la configuration du nouveau projet
      if (newProjet?.id) {
        closeDialog()
        router.push(`/projets/${newProjet.id}`)
        return
      }
    }
    closeDialog()
    await loadProjets()
  } catch (e) {
    console.error('Erreur sauvegarde projet:', e)
  } finally {
    saving.value = false
  }
}

async function deleteProjet(projet: any) {
  if (confirm(`Supprimer le projet "${projet.nom}" ?`)) {
    try {
      await projetsAPI.delete(projet.id)
      await loadProjets()
    } catch (e) {
      console.error('Erreur suppression projet:', e)
    }
  }
}

function openProjet(projet: any) {
  router.push(`/projets/${projet.id}`)
}

onMounted(loadProjets)
</script>

<style scoped>
.template-card {
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.template-preview-tree {
  max-height: 200px;
  overflow-y: auto;
}

.family-block {
  padding: 8px;
  background: rgba(255,255,255,0.5);
  border-radius: 4px;
}

.family-header {
  font-size: 0.9rem;
}

.types-list {
  border-left: 2px solid rgba(0,0,0,0.1);
  padding-left: 8px;
}

.type-item {
  display: flex;
  align-items: center;
  padding: 2px 0;
}

.fields-info {
  margin-top: 4px;
  font-style: italic;
}
</style>
