<template>
  <div class="projet-detail">
    <!-- Header du projet -->
    <div class="d-flex align-center mb-4">
      <v-btn icon variant="text" @click="goBack" class="mr-2">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <div class="flex-grow-1">
        <div class="d-flex align-center">
          <h1 class="text-h4 font-weight-bold">
            {{ projet?.nom || 'Chargement...' }}
            <HelpButton page-key="projetDetail" size="sm" />
          </h1>
          <v-chip :color="projet?.actif ? 'success' : 'grey'" size="small" class="ml-3">
            {{ projet?.actif ? 'Actif' : 'Archivé' }}
          </v-chip>
        </div>
        <p class="text-body-2 text-grey mt-1">{{ projet?.description || 'Aucune description' }}</p>
      </div>
      <v-btn variant="outlined" class="mr-2" @click="showSettingsDialog = true">
        <v-icon start>mdi-cog</v-icon> Paramètres
      </v-btn>
    </div>

    <!-- Stats rapides -->
    <v-row class="mb-4">
      <v-col cols="12" md="3">
        <v-card variant="tonal" color="primary">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-folder-multiple</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ famillesCount }}</div>
              <div class="text-caption">Familles</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="tonal" color="secondary">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-shape</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ totalElements }}</div>
              <div class="text-caption">Éléments</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="tonal" color="info">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-form-textbox</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ totalChamps }}</div>
              <div class="text-caption">Champs</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="tonal" color="success">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-map-marker</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ projet?.points_count || 0 }}</div>
              <div class="text-caption">Points collectés</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Structure en colonnes -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-file-tree</v-icon>
        Structure du projet
        <v-spacer />
        <v-btn color="primary" size="small" @click="showAddFamilleDialog = true">
          <v-icon start>mdi-plus</v-icon> Ajouter une famille
        </v-btn>
      </v-card-title>
      <v-card-text>
        <!-- Colonnes dynamiques -->
        <div class="structure-columns" v-if="structure.length > 0">
          <div class="columns-container">
            <!-- Colonne pour chaque niveau utilisé -->
            <div
              v-for="(level, levelIndex) in visibleLevels"
              :key="levelIndex"
              class="structure-column"
            >
              <div class="column-header">
                {{ levelNames[levelIndex] || `Niveau ${levelIndex + 1}` }}
              </div>
              <div
                class="column-content"
                @dragover.prevent
                @drop="onDrop($event, levelIndex)"
              >
                <div
                  v-for="(item, itemIndex) in getItemsAtLevel(levelIndex)"
                  :key="item.code"
                  class="structure-item"
                  :class="{
                    'selected': selectedElement?.code === item.code,
                    'has-children': hasChildren(item.code),
                    'drag-over': dragOverItem === item.code
                  }"
                  draggable="true"
                  @click="selectElement(item)"
                  @dragstart="onDragStart($event, item, levelIndex)"
                  @dragend="onDragEnd"
                  @dragover.prevent="onDragOver(item.code)"
                  @dragleave="onDragLeave"
                >
                  <v-icon class="drag-handle mr-1" size="14" color="grey">mdi-drag-vertical</v-icon>
                  <v-icon
                    v-if="item.icone"
                    :color="formatColor(item.couleur)"
                    size="18"
                    class="mr-2"
                  >
                    {{ item.icone }}
                  </v-icon>
                  <span class="item-label">{{ item.libelle }}</span>
                  <v-chip size="x-small" class="ml-auto field-count-chip" v-if="getFieldCount(item.code) > 0">
                    {{ getFieldCount(item.code) }}
                  </v-chip>
                  <v-icon
                    v-if="hasChildren(item.code)"
                    size="16"
                    class="ml-1 chevron-icon"
                  >
                    mdi-chevron-right
                  </v-icon>
                  <!-- Boutons d'action (visible au hover) -->
                  <div class="item-actions">
                    <v-btn
                      icon
                      size="x-small"
                      variant="text"
                      @click.stop="editElement(item)"
                      title="Modifier"
                    >
                      <v-icon size="14">mdi-pencil</v-icon>
                    </v-btn>
                    <v-btn
                      icon
                      size="x-small"
                      variant="text"
                      color="error"
                      @click.stop="confirmDeleteElement(item)"
                      title="Supprimer"
                    >
                      <v-icon size="14">mdi-delete</v-icon>
                    </v-btn>
                  </div>
                </div>
                <!-- Bouton ajouter sous-élément -->
                <div
                  v-if="canAddChildAtLevel(levelIndex)"
                  class="add-child-btn"
                  @click="addChildAtLevel(levelIndex)"
                >
                  <v-icon size="16">mdi-plus</v-icon>
                  <span>Ajouter</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- État vide -->
        <div v-else class="text-center pa-8">
          <v-icon size="64" color="grey" class="mb-4">mdi-folder-plus-outline</v-icon>
          <h3 class="text-h6 mb-2">Aucune structure définie</h3>
          <p class="text-body-2 text-grey mb-4">
            Commencez par ajouter une famille pour structurer votre collecte
          </p>
          <v-btn color="primary" @click="showAddFamilleDialog = true">
            <v-icon start>mdi-plus</v-icon>
            Ajouter une famille
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- Panneau des champs + Preview Mobile -->
    <v-row v-if="selectedElement">
      <!-- Panneau des champs -->
      <v-col cols="12" md="7">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-form-textbox</v-icon>
            Champs de : {{ selectedPath }}
            <v-spacer />
            <v-btn color="primary" size="small" @click="showAddChampDialog = true" class="mr-2">
              <v-icon start>mdi-plus</v-icon> Ajouter un champ
            </v-btn>
            <v-btn
              color="error"
              size="small"
              variant="outlined"
              @click="confirmDeleteFamily()"
              :loading="checkingDelete"
            >
              <v-icon start>mdi-delete</v-icon> Supprimer
            </v-btn>
          </v-card-title>
          <v-card-text>
            <!-- Champs hérités -->
            <div class="mb-4">
              <div class="d-flex align-center mb-2">
                <div class="text-subtitle-2 text-grey">
                  <v-icon size="16" class="mr-1">mdi-arrow-down</v-icon>
                  Champs hérités ({{ inheritedChamps.length }})
                </div>
                <v-spacer />
                <v-btn
                  v-if="selectedElement && selectedElement.niveau === 0"
                  size="x-small"
                  variant="text"
                  color="primary"
                  @click="showManageInheritedFieldsDialog = true"
                >
                  <v-icon start size="14">mdi-pencil</v-icon>
                  Gérer
                </v-btn>
              </div>
              <v-chip-group v-if="inheritedChamps.length > 0">
                <v-chip
                  v-for="champ in inheritedChamps"
                  :key="champ.id"
                  size="small"
                  variant="outlined"
                  :prepend-icon="getChampIcon(champ.type)"
                  @click="editInheritedChamp(champ)"
                  class="cursor-pointer"
                >
                  {{ champ.nom }}
                  <span v-if="champ.obligatoire" class="ml-1 text-error">*</span>
                </v-chip>
              </v-chip-group>
              <div v-else class="text-caption text-grey pa-2">
                Aucun champ hérité.
                <a v-if="selectedElement && selectedElement.niveau === 0" href="#" class="text-primary" @click.prevent="showManageInheritedFieldsDialog = true">
                  Ajouter depuis un template
                </a>
              </div>
            </div>

            <!-- Champs propres -->
            <div class="text-subtitle-2 mb-2">
              <v-icon size="16" class="mr-1">mdi-form-textbox</v-icon>
              Champs propres ({{ ownChamps.length }})
            </div>

            <v-list v-if="ownChamps.length > 0" density="compact">
              <v-list-item
                v-for="champ in ownChamps"
                :key="champ.id"
                :prepend-icon="getChampIcon(champ.type)"
                @click="editChamp(champ)"
              >
                <v-list-item-title>
                  {{ champ.nom }}
                  <v-chip v-if="champ.obligatoire" size="x-small" color="error" class="ml-2">
                    Obligatoire
                  </v-chip>
                  <v-chip v-if="champ.condition_field" size="x-small" color="info" class="ml-2">
                    <v-icon start size="12">mdi-filter</v-icon>
                    Conditionnel
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ getChampTypeLabel(champ.type) }}
                  <span v-if="champ.options?.length"> - {{ champ.options.length }} options</span>
                  <span v-if="champ.condition_field" class="text-info"> | Si {{ champ.condition_field }} {{ champ.condition_operator }} "{{ champ.condition_value }}"</span>
                </v-list-item-subtitle>
                <template #append>
                  <v-btn icon size="small" variant="text" @click.stop="deleteChamp(champ)">
                    <v-icon size="18" color="error">mdi-delete</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>

            <div v-else class="text-center pa-4 text-grey">
              <v-icon size="32" class="mb-2">mdi-form-textbox</v-icon>
              <p>Aucun champ propre défini</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Preview Mobile -->
      <v-col cols="12" md="5">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-cellphone</v-icon>
            Aperçu Mobile
          </v-card-title>
          <v-card-text class="d-flex justify-center">
            <div class="mobile-preview">
              <!-- Cadre mobile -->
              <div class="mobile-frame">
                <!-- Header -->
                <div class="mobile-header">
                  <v-icon size="16" color="white">mdi-arrow-left</v-icon>
                  <span class="mobile-title">{{ selectedElement?.libelle }}</span>
                  <v-icon size="16" color="white">mdi-check</v-icon>
                </div>

                <!-- Contenu du formulaire -->
                <div class="mobile-content">
                  <!-- Catégorie sélectionnée -->
                  <div class="mobile-category">
                    <v-icon :color="formatColor(selectedElement?.couleur)" size="20">
                      {{ selectedElement?.icone }}
                    </v-icon>
                    <span>{{ selectedPath }}</span>
                  </div>

                  <!-- Champs du formulaire -->
                  <div class="mobile-form">
                    <div
                      v-for="champ in allChampsForPreview"
                      :key="champ.id || champ.nom"
                      class="mobile-field"
                    >
                      <label class="mobile-label">
                        {{ champ.nom }}
                        <span v-if="champ.obligatoire" class="text-error">*</span>
                      </label>
                      <!-- Différents types de champs -->
                      <div v-if="champ.type === 'text'" class="mobile-input">
                        <span class="placeholder">Saisir...</span>
                      </div>
                      <div v-else-if="champ.type === 'number'" class="mobile-input">
                        <span class="placeholder">0</span>
                      </div>
                      <div v-else-if="champ.type === 'select'" class="mobile-select">
                        <span class="placeholder">Choisir...</span>
                        <v-icon size="14">mdi-chevron-down</v-icon>
                      </div>
                      <div v-else-if="champ.type === 'date'" class="mobile-input">
                        <v-icon size="14" class="mr-1">mdi-calendar</v-icon>
                        <span class="placeholder">jj/mm/aaaa</span>
                      </div>
                      <div v-else-if="champ.type === 'photo'" class="mobile-photo">
                        <v-icon size="24" color="grey">mdi-camera-plus</v-icon>
                        <span class="text-caption">Ajouter photo</span>
                      </div>
                    </div>

                    <!-- Message si aucun champ -->
                    <div v-if="allChampsForPreview.length === 0" class="text-center pa-4 text-grey">
                      <v-icon size="24">mdi-form-textbox</v-icon>
                      <p class="text-caption mt-2">Aucun champ configuré</p>
                    </div>
                  </div>
                </div>

                <!-- Footer -->
                <div class="mobile-footer">
                  <v-btn size="small" variant="flat" color="primary" block>
                    Enregistrer
                  </v-btn>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog Paramètres projet -->
    <v-dialog v-model="showSettingsDialog" max-width="500">
      <v-card>
        <v-card-title>Paramètres du projet</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="projetForm.nom"
            label="Nom du projet *"
            :rules="[v => !!v || 'Nom requis']"
          />
          <v-textarea
            v-model="projetForm.description"
            label="Description"
            rows="3"
            class="mt-4"
          />
          <v-switch
            v-model="projetForm.actif"
            label="Projet actif"
            color="success"
            class="mt-4"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showSettingsDialog = false">Annuler</v-btn>
          <v-btn color="primary" @click="saveProjetSettings">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog Modifier élément -->
    <v-dialog v-model="showEditElementDialog" max-width="600" persistent>
      <v-card>
        <v-card-title>
          <v-icon start>mdi-pencil</v-icon>
          Modifier "{{ editingElement?.libelle }}"
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editElementForm.libelle"
            label="Nom *"
            :rules="[v => !!v || 'Nom requis']"
          />

          <v-text-field
            v-model="editElementForm.code"
            label="Code (identifiant)"
            disabled
            hint="Le code ne peut pas être modifié"
            persistent-hint
            class="mt-4"
          />

          <div class="mt-4">
            <div class="text-subtitle-2 mb-2">
              Icône
              <v-chip v-if="editElementForm.icone" size="x-small" class="ml-2">
                <v-icon size="14" class="mr-1">{{ editElementForm.icone }}</v-icon>
                {{ getIconLabel(editElementForm.icone) }}
              </v-chip>
            </div>
            <v-expansion-panels variant="accordion" class="icon-categories">
              <v-expansion-panel
                v-for="category in iconCategories"
                :key="category.name"
              >
                <v-expansion-panel-title class="py-2">
                  <v-icon size="18" class="mr-2">{{ category.icons[0]?.value }}</v-icon>
                  {{ category.name }}
                  <span class="text-caption text-grey ml-2">({{ category.icons.length }})</span>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <div class="icon-grid">
                    <v-tooltip
                      v-for="icon in category.icons"
                      :key="icon.value"
                      :text="icon.label"
                      location="top"
                    >
                      <template #activator="{ props }">
                        <v-btn
                          v-bind="props"
                          :variant="editElementForm.icone === icon.value ? 'flat' : 'outlined'"
                          :color="editElementForm.icone === icon.value ? 'primary' : undefined"
                          size="small"
                          icon
                          @click="editElementForm.icone = icon.value"
                        >
                          <v-icon>{{ icon.value }}</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

          <div class="mt-4">
            <div class="text-subtitle-2 mb-2">Couleur</div>
            <v-color-picker
              v-model="editElementForm.couleur"
              mode="hexa"
              hide-inputs
              show-swatches
              swatches-max-height="100"
            />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeEditElementDialog">Annuler</v-btn>
          <v-btn color="primary" @click="saveEditedElement" :disabled="!editElementForm.libelle">
            Enregistrer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog Ajouter famille/élément -->
    <v-dialog v-model="showAddFamilleDialog" max-width="600" persistent>
      <v-card>
        <v-card-title>
          {{ addElementParent ? `Ajouter un élément dans "${addElementParent.libelle}"` : 'Ajouter une famille' }}
        </v-card-title>
        <v-card-text>
          <!-- Sélection de template (uniquement pour les familles racines) -->
          <div v-if="!addElementParent" class="mb-4">
            <v-btn-toggle v-model="useTemplateMode" mandatory class="mb-3">
              <v-btn :value="false" size="small">
                <v-icon start>mdi-pencil</v-icon>
                Personnalisé
              </v-btn>
              <v-btn :value="true" size="small">
                <v-icon start>mdi-file-document-multiple</v-icon>
                Depuis template
              </v-btn>
            </v-btn-toggle>

            <!-- Templates disponibles -->
            <div v-if="useTemplateMode">
              <div class="text-subtitle-2 mb-2">Choisir un template</div>
              <v-row dense>
                <v-col
                  v-for="template in projectTemplates"
                  :key="template.id"
                  cols="6"
                  sm="4"
                >
                  <v-card
                    v-for="family in template.families"
                    :key="family.code"
                    :variant="selectedTemplateFamily?.code === family.code ? 'tonal' : 'outlined'"
                    :color="selectedTemplateFamily?.code === family.code ? 'primary' : undefined"
                    class="template-card mb-2"
                    @click="selectTemplateFamily(family)"
                  >
                    <v-card-text class="text-center pa-2">
                      <v-icon :color="family.color" size="28">{{ family.icon }}</v-icon>
                      <div class="text-caption font-weight-medium mt-1">{{ family.label }}</div>
                      <div class="text-caption text-grey">
                        {{ countTotalElements(family) }} éléments
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <!-- Aperçu du template sélectionné -->
              <v-expand-transition>
                <div v-if="selectedTemplateFamily" class="mt-3">
                  <v-alert type="info" variant="tonal" density="compact" class="mb-3">
                    <div class="text-subtitle-2 mb-1">Structure "{{ selectedTemplateFamily.label }}"</div>
                    <div class="template-preview-tree text-caption">
                      <div v-for="child in selectedTemplateFamily.children" :key="child.code" class="ml-2">
                        <v-icon size="12">{{ child.icon }}</v-icon> {{ child.label }}
                        <span v-if="child.children" class="text-grey">
                          ({{ child.children.length }} sous-types)
                        </span>
                      </div>
                    </div>
                  </v-alert>

                  <!-- Sélection des champs du template -->
                  <div class="template-fields-selection">
                    <div class="d-flex align-center mb-2">
                      <div class="text-subtitle-2">
                        <v-icon size="16" class="mr-1">mdi-form-textbox</v-icon>
                        Champs à créer
                      </div>
                      <v-spacer />
                      <v-btn size="x-small" variant="text" @click="selectAllTemplateFields">
                        Tout sélectionner
                      </v-btn>
                      <v-btn size="x-small" variant="text" @click="deselectAllTemplateFields">
                        Tout désélectionner
                      </v-btn>
                    </div>
                    <v-list density="compact" class="border rounded" max-height="200" style="overflow-y: auto;">
                      <v-list-item
                        v-for="field in selectedTemplateFamily.fields"
                        :key="field.nom"
                        class="py-1"
                      >
                        <template #prepend>
                          <v-checkbox
                            v-model="templateFieldsToApply"
                            :value="field.nom"
                            density="compact"
                            hide-details
                          />
                        </template>
                        <v-list-item-title class="text-body-2">
                          <v-icon size="14" class="mr-1">{{ getChampIcon(field.type) }}</v-icon>
                          {{ field.nom }}
                          <v-chip v-if="field.obligatoire" size="x-small" color="error" class="ml-1">*</v-chip>
                        </v-list-item-title>
                        <v-list-item-subtitle class="text-caption">
                          {{ getChampTypeLabel(field.type) }}
                        </v-list-item-subtitle>
                      </v-list-item>
                    </v-list>
                    <div class="text-caption text-grey mt-1">
                      {{ templateFieldsToApply.length }} / {{ selectedTemplateFamily.fields.length }} champs sélectionnés
                    </div>
                  </div>
                </div>
              </v-expand-transition>
            </div>
          </div>

          <!-- Formulaire personnalisé (mode normal) -->
          <div v-if="!useTemplateMode || addElementParent">
            <v-text-field
              v-model="elementForm.libelle"
              label="Nom *"
              :rules="[v => !!v || 'Nom requis']"
              @input="onElementNameChange"
            />

          <v-text-field
            v-model="elementForm.code"
            label="Code (identifiant unique)"
            hint="Généré automatiquement si vide"
            persistent-hint
            class="mt-4"
          />

          <div class="mt-4">
            <div class="text-subtitle-2 mb-2">
              Icône
              <v-chip v-if="elementForm.icone" size="x-small" class="ml-2">
                <v-icon size="14" class="mr-1">{{ elementForm.icone }}</v-icon>
                {{ getIconLabel(elementForm.icone) }}
              </v-chip>
            </div>
            <v-expansion-panels variant="accordion" class="icon-categories">
              <v-expansion-panel
                v-for="category in iconCategories"
                :key="category.name"
              >
                <v-expansion-panel-title class="py-2">
                  <v-icon size="18" class="mr-2">{{ category.icons[0]?.value }}</v-icon>
                  {{ category.name }}
                  <span class="text-caption text-grey ml-2">({{ category.icons.length }})</span>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <div class="icon-grid">
                    <v-tooltip
                      v-for="icon in category.icons"
                      :key="icon.value"
                      :text="icon.label"
                      location="top"
                    >
                      <template #activator="{ props }">
                        <v-btn
                          v-bind="props"
                          :variant="elementForm.icone === icon.value ? 'flat' : 'outlined'"
                          :color="elementForm.icone === icon.value ? 'primary' : undefined"
                          size="small"
                          icon
                          @click="elementForm.icone = icon.value"
                        >
                          <v-icon>{{ icon.value }}</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

          <div class="mt-4">
            <div class="text-subtitle-2 mb-2">Couleur</div>
            <v-color-picker
              v-model="elementForm.couleur"
              mode="hexa"
              hide-inputs
              show-swatches
              swatches-max-height="100"
            />
          </div>

            <!-- Suggestions de champs -->
            <div class="mt-6" v-if="suggestedFields.length > 0">
              <div class="text-subtitle-2 mb-2">
                <v-icon size="16" class="mr-1">mdi-lightbulb</v-icon>
                Champs suggérés
              </div>
              <v-chip-group v-model="selectedSuggestedFields" multiple column>
                <v-chip
                  v-for="field in suggestedFields"
                  :key="field.nom"
                  :value="field"
                  filter
                  variant="outlined"
                  :prepend-icon="getChampIcon(field.type)"
                >
                  {{ field.nom }}
                </v-chip>
              </v-chip-group>
            </div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeAddElementDialog">Annuler</v-btn>
          <v-btn
            color="primary"
            @click="useTemplateMode && !addElementParent ? applyTemplateFamily() : saveElement()"
            :disabled="(useTemplateMode && !addElementParent) ? !selectedTemplateFamily : !elementForm.libelle"
          >
            {{ useTemplateMode && !addElementParent ? 'Appliquer template' : 'Créer' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog Confirmer suppression famille -->
    <v-dialog v-model="showDeleteConfirmDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="text-error">
          <v-icon start color="error">mdi-alert</v-icon>
          Supprimer "{{ deleteInfo?.entry?.label }}"
        </v-card-title>
        <v-card-text>
          <div v-if="deleteInfo?.can_delete">
            <p class="mb-3">Êtes-vous sûr de vouloir supprimer cette famille ?</p>
            <v-alert type="warning" variant="tonal" density="compact" class="mb-3">
              Cette action est irréversible et supprimera :
              <ul class="mt-2">
                <li v-if="deleteInfo.descendants_count > 0">
                  {{ deleteInfo.descendants_count }} sous-élément(s) (types, sous-types)
                </li>
                <li v-if="deleteInfo.fields_count > 0">
                  {{ deleteInfo.fields_count }} champ(s) dynamique(s)
                </li>
                <li v-if="deleteInfo.descendants_count === 0 && deleteInfo.fields_count === 0">
                  L'entrée "{{ deleteInfo.entry?.label }}"
                </li>
              </ul>
            </v-alert>
          </div>
          <div v-else>
            <v-alert type="error" variant="tonal">
              <strong>Suppression impossible</strong>
              <p class="mt-2 mb-0">
                {{ deleteInfo?.reason }}
              </p>
              <p class="mt-2 mb-0 text-caption">
                Supprimez d'abord les points associés avant de supprimer cette famille.
              </p>
            </v-alert>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteConfirmDialog = false">
            Annuler
          </v-btn>
          <v-btn
            v-if="deleteInfo?.can_delete"
            color="error"
            @click="deleteFamily()"
            :loading="deletingFamily"
          >
            Supprimer définitivement
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog Gérer les champs hérités -->
    <v-dialog v-model="showManageInheritedFieldsDialog" max-width="700">
      <v-card v-if="selectedElement">
        <v-card-title class="d-flex align-center">
          <v-icon start>mdi-form-textbox-password</v-icon>
          Gérer les champs de "{{ selectedElement?.libelle }}"
        </v-card-title>
        <v-card-text>
          <!-- Champs actuels -->
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">Champs actuels</div>
            <v-list v-if="inheritedChamps.length > 0 || ownChamps.length > 0" density="compact" class="border rounded">
              <v-list-item
                v-for="champ in [...inheritedChamps, ...ownChamps]"
                :key="champ.id"
                :prepend-icon="getChampIcon(champ.type)"
              >
                <v-list-item-title>
                  {{ champ.nom }}
                  <v-chip v-if="champ.obligatoire" size="x-small" color="error" class="ml-2">*</v-chip>
                </v-list-item-title>
                <v-list-item-subtitle>{{ getChampTypeLabel(champ.type) }}</v-list-item-subtitle>
                <template #append>
                  <v-btn icon size="small" variant="text" @click="editChamp(champ)">
                    <v-icon size="18">mdi-pencil</v-icon>
                  </v-btn>
                  <v-btn icon size="small" variant="text" color="error" @click="deleteChamp(champ)">
                    <v-icon size="18">mdi-delete</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-center pa-4 text-grey border rounded">
              Aucun champ défini
            </div>
          </div>

          <!-- Ajouter depuis template -->
          <v-divider class="mb-4" />
          <div class="text-subtitle-2 mb-2">
            <v-icon size="16" class="mr-1">mdi-file-document-multiple</v-icon>
            Ajouter des champs depuis un template
          </div>

          <v-select
            v-model="selectedTemplateForFields"
            :items="availableTemplatesForFields"
            item-title="label"
            item-value="code"
            return-object
            label="Choisir un template"
            variant="outlined"
            density="compact"
            clearable
            class="mb-3"
          >
            <template #item="{ item, props }">
              <v-list-item v-bind="props">
                <template #prepend>
                  <v-icon :color="item.raw.color">{{ item.raw.icon }}</v-icon>
                </template>
                <v-list-item-subtitle>
                  {{ item.raw.fields.length }} champs prédéfinis
                </v-list-item-subtitle>
              </v-list-item>
            </template>
          </v-select>

          <!-- Liste des champs du template sélectionné -->
          <div v-if="selectedTemplateForFields" class="template-fields-list">
            <v-list density="compact" class="border rounded">
              <v-list-item
                v-for="field in selectedTemplateForFields.fields"
                :key="field.nom"
              >
                <template #prepend>
                  <v-checkbox
                    v-model="selectedTemplateFields"
                    :value="field.nom"
                    density="compact"
                    hide-details
                  />
                </template>
                <v-list-item-title>
                  <v-icon size="14" class="mr-1">{{ getChampIcon(field.type) }}</v-icon>
                  {{ field.nom }}
                  <v-chip v-if="field.obligatoire" size="x-small" color="error" class="ml-2">*</v-chip>
                  <v-chip v-if="isFieldAlreadyExists(field.nom)" size="x-small" color="warning" class="ml-2">
                    Existant
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ getChampTypeLabel(field.type) }}
                  <span v-if="field.options?.length"> - {{ field.options.length }} options</span>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>

            <v-btn
              color="primary"
              class="mt-3"
              :disabled="selectedTemplateFields.length === 0"
              @click="addFieldsFromTemplate"
              :loading="addingTemplateFields"
            >
              <v-icon start>mdi-plus</v-icon>
              Ajouter {{ selectedTemplateFields.length }} champ(s)
            </v-btn>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeManageInheritedFieldsDialog">Fermer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog Ajouter/Modifier champ -->
    <v-dialog v-model="showAddChampDialog" max-width="600" persistent>
      <v-card>
        <v-card-title>
          {{ editingChamp ? 'Modifier le champ' : 'Ajouter un champ' }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="champForm.nom"
            label="Nom du champ *"
            :rules="[v => !!v || 'Nom requis']"
          />

          <div class="mt-4">
            <div class="text-subtitle-2 mb-2">Type de champ</div>
            <v-btn-toggle v-model="champForm.type" mandatory class="flex-wrap">
              <v-btn
                v-for="type in champTypes"
                :key="type.value"
                :value="type.value"
                size="small"
              >
                <v-icon start>{{ type.icon }}</v-icon>
                {{ type.label }}
              </v-btn>
            </v-btn-toggle>
          </div>

          <!-- Options selon le type -->
          <div class="mt-4" v-if="champForm.type === 'select' || champForm.type === 'multiselect'">
            <v-combobox
              v-model="champForm.options"
              label="Options (appuyez Entrée pour ajouter)"
              multiple
              chips
              closable-chips
            />
          </div>

          <div class="mt-4" v-if="champForm.type === 'number' || champForm.type === 'slider'">
            <v-row>
              <v-col cols="6">
                <v-text-field v-model.number="champForm.min" label="Min" type="number" />
              </v-col>
              <v-col cols="6">
                <v-text-field v-model.number="champForm.max" label="Max" type="number" />
              </v-col>
            </v-row>
          </div>

          <v-switch
            v-model="champForm.obligatoire"
            label="Champ obligatoire"
            color="error"
            class="mt-4"
          />

          <!-- Section champ conditionnel -->
          <v-divider class="my-4" />
          <v-switch
            v-model="champForm.isConditional"
            label="Champ conditionnel (visible selon une condition)"
            color="primary"
            class="mt-2"
          />

          <div v-if="champForm.isConditional" class="conditional-config pa-3 rounded bg-grey-lighten-4">
            <div class="text-subtitle-2 mb-3">
              <v-icon start size="small">mdi-filter</v-icon>
              Afficher ce champ seulement si...
            </div>

            <v-select
              v-model="champForm.condition_field"
              :items="availableConditionFields"
              item-title="nom"
              item-value="nom"
              label="Champ déclencheur *"
              density="compact"
              :rules="[v => !!v || 'Sélectionnez un champ']"
            />

            <v-row class="mt-2">
              <v-col cols="4">
                <v-select
                  v-model="champForm.condition_operator"
                  :items="conditionOperators"
                  item-title="label"
                  item-value="value"
                  label="Opérateur"
                  density="compact"
                />
              </v-col>
              <v-col cols="8">
                <v-combobox
                  v-if="selectedConditionFieldOptions.length > 0"
                  v-model="champForm.condition_value"
                  :items="selectedConditionFieldOptions"
                  label="Valeur *"
                  density="compact"
                />
                <v-text-field
                  v-else
                  v-model="champForm.condition_value"
                  label="Valeur *"
                  density="compact"
                />
              </v-col>
            </v-row>

            <v-alert type="info" density="compact" variant="tonal" class="mt-3">
              <small>
                Exemple : Si "Modèle" = "Glasdon", alors afficher ce champ.
              </small>
            </v-alert>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeChampDialog">Annuler</v-btn>
          <v-btn color="primary" @click="saveChamp" :disabled="!champForm.nom">
            {{ editingChamp ? 'Modifier' : 'Créer' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projetsAPI, lexiqueAPI, champsAPI } from '@/services/api'
import { projectTemplates, countTotalElements, type TemplateFamily } from '@/constants/templates'
import HelpButton from '@/components/help/HelpButton.vue'

const route = useRoute()
const router = useRouter()

// Data
const projet = ref<any>(null)
const structure = ref<any[]>([])
const allChamps = ref<Map<string, any[]>>(new Map())
const selectedElement = ref<any>(null)
const selectedPath = ref('')

// Dialogs
const showSettingsDialog = ref(false)
const showAddFamilleDialog = ref(false)
const showAddChampDialog = ref(false)
const showEditElementDialog = ref(false)
const addElementParent = ref<any>(null)
const editingElement = ref<any>(null)
const editingChamp = ref<any>(null)
const selectedTemplateFamily = ref<TemplateFamily | null>(null)
const useTemplateMode = ref(false)
const templateFieldsToApply = ref<string[]>([])

// Delete family
const showDeleteConfirmDialog = ref(false)
const checkingDelete = ref(false)
const deletingFamily = ref(false)
const deleteInfo = ref<any>(null)

// Manage inherited fields
const showManageInheritedFieldsDialog = ref(false)
const selectedTemplateForFields = ref<TemplateFamily | null>(null)
const selectedTemplateFields = ref<string[]>([])
const addingTemplateFields = ref(false)

// Drag & Drop
const draggedItem = ref<any>(null)
const draggedFromLevel = ref<number>(-1)
const dragOverItem = ref<string | null>(null)

// Forms
const projetForm = ref({ nom: '', description: '', actif: true })
const elementForm = ref({
  libelle: '',
  code: '',
  icone: 'mdi-folder',
  couleur: '#1976D2',
  parent_id: null as string | null,
  niveau: 0
})
const editElementForm = ref({
  libelle: '',
  code: '',
  icone: 'mdi-folder',
  couleur: '#1976D2'
})
const champForm = ref({
  nom: '',
  type: 'text',
  obligatoire: false,
  options: [] as string[],
  min: undefined as number | undefined,
  max: undefined as number | undefined,
  // Champs conditionnels
  isConditional: false,
  condition_field: '' as string,
  condition_operator: '=' as string,
  condition_value: '' as string
})

const selectedSuggestedFields = ref<any[]>([])

// Constants
const levelNames = ['Famille', 'Type', 'Sous-type', 'Variante', 'Détail', 'Précision']

// Icônes organisées par catégorie pour faciliter la sélection
const iconCategories = [
  {
    name: 'Éclairage',
    icons: [
      { value: 'mdi-lightbulb', label: 'Ampoule' },
      { value: 'mdi-lightbulb-on', label: 'Éclairage' },
      { value: 'mdi-lamp', label: 'Lampe' },
      { value: 'mdi-ceiling-light', label: 'Plafonnier' },
      { value: 'mdi-floor-lamp', label: 'Lampadaire' },
      { value: 'mdi-wall-sconce', label: 'Applique' },
      { value: 'mdi-spotlight', label: 'Projecteur' },
      { value: 'mdi-spotlight-beam', label: 'Faisceau' },
      { value: 'mdi-led-strip', label: 'LED' },
    ]
  },
  {
    name: 'Aires de jeux',
    icons: [
      { value: 'mdi-seesaw', label: 'Balançoire' },
      { value: 'mdi-slide', label: 'Toboggan' },
      { value: 'mdi-ferris-wheel', label: 'Manège' },
      { value: 'mdi-human-child', label: 'Enfants' },
      { value: 'mdi-toy-brick', label: 'Jeux' },
      { value: 'mdi-castle', label: 'Structure' },
      { value: 'mdi-baby-carriage', label: 'Petite enfance' },
      { value: 'mdi-sandbox', label: 'Bac à sable' },
    ]
  },
  {
    name: 'Sport',
    icons: [
      { value: 'mdi-soccer', label: 'Football' },
      { value: 'mdi-soccer-field', label: 'Terrain foot' },
      { value: 'mdi-basketball', label: 'Basket' },
      { value: 'mdi-tennis', label: 'Tennis' },
      { value: 'mdi-tennis-ball', label: 'Balle tennis' },
      { value: 'mdi-volleyball', label: 'Volley' },
      { value: 'mdi-rugby', label: 'Rugby' },
      { value: 'mdi-baseball', label: 'Baseball' },
      { value: 'mdi-golf', label: 'Golf' },
      { value: 'mdi-bike', label: 'Vélo' },
      { value: 'mdi-run', label: 'Course' },
      { value: 'mdi-swim', label: 'Piscine' },
      { value: 'mdi-weight-lifter', label: 'Fitness' },
      { value: 'mdi-skateboard', label: 'Skate' },
      { value: 'mdi-roller-skate', label: 'Roller' },
      { value: 'mdi-table-tennis', label: 'Ping-pong' },
      { value: 'mdi-billiards', label: 'Pétanque' },
    ]
  },
  {
    name: 'Mobilier urbain',
    icons: [
      { value: 'mdi-bench', label: 'Banc' },
      { value: 'mdi-seat', label: 'Siège' },
      { value: 'mdi-table-picnic', label: 'Table pique-nique' },
      { value: 'mdi-table-furniture', label: 'Table' },
      { value: 'mdi-delete-outline', label: 'Poubelle' },
      { value: 'mdi-recycle', label: 'Tri sélectif' },
      { value: 'mdi-trash-can', label: 'Conteneur' },
      { value: 'mdi-fountain', label: 'Fontaine' },
      { value: 'mdi-fountain-pen', label: 'Point d\'eau' },
      { value: 'mdi-pot', label: 'Jardinière' },
      { value: 'mdi-fence', label: 'Clôture' },
      { value: 'mdi-gate', label: 'Portail' },
      { value: 'mdi-boom-gate', label: 'Barrière' },
      { value: 'mdi-bollard', label: 'Borne' },
    ]
  },
  {
    name: 'Signalisation',
    icons: [
      { value: 'mdi-sign-direction', label: 'Direction' },
      { value: 'mdi-sign-caution', label: 'Attention' },
      { value: 'mdi-sign-text', label: 'Panneau texte' },
      { value: 'mdi-sign-pole', label: 'Mât panneau' },
      { value: 'mdi-traffic-light', label: 'Feu tricolore' },
      { value: 'mdi-traffic-cone', label: 'Cône' },
      { value: 'mdi-alert-octagon', label: 'Stop' },
      { value: 'mdi-alert', label: 'Danger' },
      { value: 'mdi-information', label: 'Information' },
      { value: 'mdi-crosswalk', label: 'Passage piéton' },
      { value: 'mdi-road', label: 'Route' },
    ]
  },
  {
    name: 'Végétation',
    icons: [
      { value: 'mdi-tree', label: 'Arbre' },
      { value: 'mdi-tree-outline', label: 'Arbre (contour)' },
      { value: 'mdi-pine-tree', label: 'Conifère' },
      { value: 'mdi-palm-tree', label: 'Palmier' },
      { value: 'mdi-flower', label: 'Fleur' },
      { value: 'mdi-flower-tulip', label: 'Tulipe' },
      { value: 'mdi-grass', label: 'Gazon' },
      { value: 'mdi-sprout', label: 'Plante' },
      { value: 'mdi-leaf', label: 'Feuille' },
      { value: 'mdi-nature', label: 'Nature' },
      { value: 'mdi-forest', label: 'Forêt' },
      { value: 'mdi-mushroom', label: 'Champignon' },
    ]
  },
  {
    name: 'Réseaux',
    icons: [
      { value: 'mdi-water', label: 'Eau' },
      { value: 'mdi-water-pump', label: 'Pompe' },
      { value: 'mdi-pipe', label: 'Canalisation' },
      { value: 'mdi-valve', label: 'Vanne' },
      { value: 'mdi-meter-gas', label: 'Compteur gaz' },
      { value: 'mdi-meter-electric', label: 'Compteur élec' },
      { value: 'mdi-flash', label: 'Électricité' },
      { value: 'mdi-flash-triangle', label: 'Haute tension' },
      { value: 'mdi-fire', label: 'Gaz' },
      { value: 'mdi-antenna', label: 'Télécom' },
      { value: 'mdi-access-point', label: 'WiFi' },
      { value: 'mdi-fiber-manual-record', label: 'Fibre' },
      { value: 'mdi-transmission-tower', label: 'Pylône' },
      { value: 'mdi-ev-station', label: 'Borne recharge' },
    ]
  },
  {
    name: 'Bâtiments',
    icons: [
      { value: 'mdi-home', label: 'Maison' },
      { value: 'mdi-home-city', label: 'Immeuble' },
      { value: 'mdi-office-building', label: 'Bureau' },
      { value: 'mdi-domain', label: 'Mairie' },
      { value: 'mdi-school', label: 'École' },
      { value: 'mdi-hospital-building', label: 'Hôpital' },
      { value: 'mdi-medical-bag', label: 'Santé' },
      { value: 'mdi-church', label: 'Église' },
      { value: 'mdi-mosque', label: 'Mosquée' },
      { value: 'mdi-bank', label: 'Banque' },
      { value: 'mdi-store', label: 'Commerce' },
      { value: 'mdi-shopping', label: 'Centre commercial' },
      { value: 'mdi-warehouse', label: 'Entrepôt' },
      { value: 'mdi-factory', label: 'Usine' },
      { value: 'mdi-stadium', label: 'Stade' },
      { value: 'mdi-theater', label: 'Théâtre' },
      { value: 'mdi-library', label: 'Bibliothèque' },
      { value: 'mdi-museum', label: 'Musée' },
    ]
  },
  {
    name: 'Transport',
    icons: [
      { value: 'mdi-parking', label: 'Parking' },
      { value: 'mdi-bus-stop', label: 'Arrêt bus' },
      { value: 'mdi-bus', label: 'Bus' },
      { value: 'mdi-train', label: 'Train' },
      { value: 'mdi-tram', label: 'Tramway' },
      { value: 'mdi-subway', label: 'Métro' },
      { value: 'mdi-bicycle', label: 'Vélo' },
      { value: 'mdi-bike-fast', label: 'Piste cyclable' },
      { value: 'mdi-car', label: 'Voiture' },
      { value: 'mdi-taxi', label: 'Taxi' },
      { value: 'mdi-walk', label: 'Piéton' },
      { value: 'mdi-wheelchair-accessibility', label: 'Accessibilité' },
      { value: 'mdi-ferry', label: 'Bateau' },
      { value: 'mdi-airplane', label: 'Avion' },
    ]
  },
  {
    name: 'Sécurité',
    icons: [
      { value: 'mdi-cctv', label: 'Caméra' },
      { value: 'mdi-shield', label: 'Sécurité' },
      { value: 'mdi-fire-extinguisher', label: 'Extincteur' },
      { value: 'mdi-fire-hydrant', label: 'Bouche incendie' },
      { value: 'mdi-alarm-light', label: 'Alarme' },
      { value: 'mdi-siren', label: 'Sirène' },
      { value: 'mdi-lifebuoy', label: 'Bouée' },
      { value: 'mdi-police-badge', label: 'Police' },
      { value: 'mdi-ambulance', label: 'Ambulance' },
      { value: 'mdi-fire-truck', label: 'Pompiers' },
      { value: 'mdi-hard-hat', label: 'Chantier' },
    ]
  },
  {
    name: 'Divers',
    icons: [
      { value: 'mdi-map-marker', label: 'Point' },
      { value: 'mdi-map-marker-radius', label: 'Zone' },
      { value: 'mdi-pin', label: 'Épingle' },
      { value: 'mdi-flag', label: 'Drapeau' },
      { value: 'mdi-star', label: 'Étoile' },
      { value: 'mdi-heart', label: 'Favori' },
      { value: 'mdi-camera', label: 'Photo' },
      { value: 'mdi-image', label: 'Image' },
      { value: 'mdi-wrench', label: 'Maintenance' },
      { value: 'mdi-tools', label: 'Outils' },
      { value: 'mdi-cog', label: 'Paramètres' },
      { value: 'mdi-folder', label: 'Dossier' },
      { value: 'mdi-file-document', label: 'Document' },
      { value: 'mdi-tag', label: 'Étiquette' },
      { value: 'mdi-qrcode', label: 'QR Code' },
      { value: 'mdi-barcode', label: 'Code-barres' },
      { value: 'mdi-clock', label: 'Horloge' },
      { value: 'mdi-calendar', label: 'Calendrier' },
      { value: 'mdi-account', label: 'Personne' },
      { value: 'mdi-account-group', label: 'Groupe' },
    ]
  },
]

// Liste plate de toutes les icônes (pour compatibilité)
const availableIcons = iconCategories.flatMap(cat => cat.icons)

const champTypes = [
  { value: 'text', label: 'Texte', icon: 'mdi-format-text' },
  { value: 'number', label: 'Nombre', icon: 'mdi-numeric' },
  { value: 'select', label: 'Choix', icon: 'mdi-format-list-bulleted' },
  { value: 'date', label: 'Date', icon: 'mdi-calendar' },
  { value: 'photo', label: 'Photo', icon: 'mdi-camera' },
  { value: 'etat', label: 'État', icon: 'mdi-traffic-light' },
]

const suggestedFields = ref<any[]>([])

// Computed
const famillesCount = computed(() => {
  return structure.value.filter(s => s.niveau === 0).length
})

const totalElements = computed(() => structure.value.length)

const totalChamps = computed(() => {
  let count = 0
  allChamps.value.forEach((champs) => {
    count += champs.length
  })
  return count
})

const visibleLevels = computed(() => {
  if (structure.value.length === 0) return []
  const maxLevel = Math.max(...structure.value.map(s => s.niveau))
  return Array.from({ length: maxLevel + 1 }, (_, i) => i)
})

const inheritedChamps = computed(() => {
  if (!selectedElement.value) return []
  const inherited: any[] = []
  let current = selectedElement.value

  while (current.parent_id) {
    const parent = structure.value.find(s => s.code === current.parent_id)
    if (parent) {
      const parentChamps = allChamps.value.get(parent.code) || []
      inherited.unshift(...parentChamps)
      current = parent
    } else {
      break
    }
  }

  return inherited
})

const ownChamps = computed(() => {
  if (!selectedElement.value) return []
  return allChamps.value.get(selectedElement.value.code) || []
})

// Opérateurs disponibles pour les conditions
const conditionOperators = [
  { value: '=', label: 'égal à' },
  { value: '!=', label: 'différent de' },
  { value: 'contains', label: 'contient' },
  { value: 'not_empty', label: 'non vide' }
]

// Champs disponibles pour servir de déclencheur (tous les champs sauf celui en cours d'édition)
const availableConditionFields = computed(() => {
  const allFields = [...inheritedChamps.value, ...ownChamps.value]
  // Exclure le champ en cours d'édition
  if (editingChamp.value) {
    return allFields.filter(f => f.id !== editingChamp.value.id)
  }
  return allFields
})

// Options du champ sélectionné comme déclencheur (si c'est un select)
const selectedConditionFieldOptions = computed(() => {
  if (!champForm.value.condition_field) return []
  const field = availableConditionFields.value.find(f => f.nom === champForm.value.condition_field)
  if (field && (field.type === 'select' || field.type === 'multiselect') && field.options) {
    return field.options
  }
  return []
})

const allChampsForPreview = computed(() => {
  // Combine inherited and own champs for the mobile preview
  return [...inheritedChamps.value, ...ownChamps.value]
})

// Computed: all templates available for adding fields
const availableTemplatesForFields = computed(() => {
  const templates: TemplateFamily[] = []
  if (projectTemplates && Array.isArray(projectTemplates)) {
    projectTemplates.forEach(template => {
      if (template.families) {
        template.families.forEach(family => {
          if (family.fields && family.fields.length > 0) {
            templates.push(family)
          }
        })
      }
    })
  }
  return templates
})

// Check if a field already exists
function isFieldAlreadyExists(fieldName: string): boolean {
  const allCurrentFields = [...inheritedChamps.value, ...ownChamps.value]
  return allCurrentFields.some(f => f.nom.toLowerCase() === fieldName.toLowerCase())
}

// Methods
function goBack() {
  router.push('/projets')
}

async function loadProjet() {
  const id = route.params.id as string
  try {
    projet.value = await projetsAPI.getById(id)
    projetForm.value = { ...projet.value }
  } catch (e) {
    console.error('Erreur chargement projet:', e)
    router.push('/projets')
  }
}

async function loadStructure() {
  try {
    const projectId = route.params.id as string
    const data = await lexiqueAPI.getAll(projectId)
    structure.value = data

    // Charger les champs pour chaque élément
    for (const item of data) {
      try {
        const champs = await champsAPI.getByLexique(item.code)
        allChamps.value.set(item.code, champs)
      } catch (e) {
        allChamps.value.set(item.code, [])
      }
    }
  } catch (e) {
    console.error('Erreur chargement structure:', e)
  }
}

function getItemsAtLevel(level: number) {
  // Si niveau 0, retourner toutes les familles
  if (level === 0) {
    return structure.value.filter(s => s.niveau === 0)
  }

  // Sinon, retourner les enfants de l'élément sélectionné au niveau précédent
  const selectedAtPrevLevel = getSelectedAtLevel(level - 1)
  if (!selectedAtPrevLevel) return []

  return structure.value.filter(s => s.parent_id === selectedAtPrevLevel.code)
}

function getSelectedAtLevel(level: number): any {
  if (!selectedElement.value) return null

  // Remonter la chaîne des parents jusqu'au niveau demandé
  let current = selectedElement.value
  const path: any[] = [current]

  while (current.parent_id) {
    const parent = structure.value.find(s => s.code === current.parent_id)
    if (parent) {
      path.unshift(parent)
      current = parent
    } else {
      break
    }
  }

  return path[level] || null
}

function hasChildren(code: string) {
  return structure.value.some(s => s.parent_id === code)
}

function getFieldCount(code: string) {
  return allChamps.value.get(code)?.length || 0
}

function canAddChildAtLevel(level: number) {
  if (level === 0) return false
  return getSelectedAtLevel(level - 1) !== null
}

function selectElement(item: any) {
  selectedElement.value = item
  updateSelectedPath()
}

function updateSelectedPath() {
  if (!selectedElement.value) {
    selectedPath.value = ''
    return
  }

  const path: string[] = [selectedElement.value.libelle]
  let current = selectedElement.value

  while (current.parent_id) {
    const parent = structure.value.find(s => s.code === current.parent_id)
    if (parent) {
      path.unshift(parent.libelle)
      current = parent
    } else {
      break
    }
  }

  selectedPath.value = path.join(' > ')
}

function addChildAtLevel(level: number) {
  const parent = getSelectedAtLevel(level - 1)
  if (parent) {
    addElementParent.value = parent
    elementForm.value.parent_id = parent.code
    elementForm.value.niveau = level
    showAddFamilleDialog.value = true
  }
}

// Edit element
function editElement(item: any) {
  editingElement.value = item
  editElementForm.value = {
    libelle: item.libelle,
    code: item.code,
    icone: item.icone || 'mdi-folder',
    couleur: formatColor(item.couleur) || '#1976D2'
  }
  showEditElementDialog.value = true
}

function closeEditElementDialog() {
  showEditElementDialog.value = false
  editingElement.value = null
  editElementForm.value = {
    libelle: '',
    code: '',
    icone: 'mdi-folder',
    couleur: '#1976D2'
  }
}

async function saveEditedElement() {
  if (!editingElement.value) return

  // Sauvegarder le code avant de fermer le dialogue
  const elementCode = editingElement.value.code

  try {
    const projectId = route.params.id as string

    // Convertir la couleur hex en entier
    let couleurHex = editElementForm.value.couleur
    if (typeof couleurHex === 'object' && couleurHex !== null) {
      couleurHex = (couleurHex as any).hex || (couleurHex as any).hexa || '#1976D2'
    }
    if (!couleurHex || !couleurHex.startsWith('#')) {
      couleurHex = '#1976D2'
    }
    const colorValue = parseInt(couleurHex.replace('#', ''), 16)

    const data = {
      label: editElementForm.value.libelle,
      icon_name: editElementForm.value.icone,
      color_value: colorValue
    }

    await lexiqueAPI.update(elementCode, data, projectId)

    closeEditElementDialog()
    await loadStructure()

    // Re-sélectionner l'élément mis à jour
    const updated = structure.value.find(s => s.code === elementCode)
    if (updated) {
      selectElement(updated)
    }
  } catch (e: any) {
    console.error('Erreur modification élément:', e)
    alert(e.response?.data?.detail || 'Erreur lors de la modification')
  }
}

// Delete element from structure list
function confirmDeleteElement(item: any) {
  selectedElement.value = item
  confirmDeleteFamily()
}

// Drag & Drop functions
function onDragStart(event: DragEvent, item: any, level: number) {
  draggedItem.value = item
  draggedFromLevel.value = level
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', item.code)
  }
}

function onDragEnd() {
  draggedItem.value = null
  draggedFromLevel.value = -1
  dragOverItem.value = null
}

function onDragOver(itemCode: string) {
  if (draggedItem.value && draggedItem.value.code !== itemCode) {
    dragOverItem.value = itemCode
  }
}

function onDragLeave() {
  dragOverItem.value = null
}

async function onDrop(event: DragEvent, targetLevel: number) {
  event.preventDefault()

  if (!draggedItem.value || draggedFromLevel.value !== targetLevel) {
    // Ne peut réordonner que dans le même niveau
    onDragEnd()
    return
  }

  const targetCode = dragOverItem.value
  if (!targetCode || targetCode === draggedItem.value.code) {
    onDragEnd()
    return
  }

  // Trouver les items au niveau actuel
  const items = getItemsAtLevel(targetLevel)
  const draggedIndex = items.findIndex(i => i.code === draggedItem.value.code)
  const targetIndex = items.findIndex(i => i.code === targetCode)

  if (draggedIndex === -1 || targetIndex === -1) {
    onDragEnd()
    return
  }

  // Réordonner localement
  const [movedItem] = items.splice(draggedIndex, 1)
  items.splice(targetIndex, 0, movedItem)

  // Mettre à jour les ordres
  const reorderData = items.map((item, index) => ({
    id: item.code,
    ordre: index
  }))

  try {
    await lexiqueAPI.reorder(reorderData)
    // Recharger la structure pour refléter le nouvel ordre
    await loadStructure()
  } catch (e) {
    console.error('Erreur réorganisation:', e)
  }

  onDragEnd()
}

function onElementNameChange() {
  // Générer code à partir du libellé
  if (!elementForm.value.code || elementForm.value.code === '') {
    elementForm.value.code = elementForm.value.libelle
      .toUpperCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^A-Z0-9]/g, '_')
      .substring(0, 20)
  }

  // Suggérer des champs basés sur le nom
  generateFieldSuggestions()
}

function generateFieldSuggestions() {
  const name = elementForm.value.libelle.toLowerCase()
  const suggestions: any[] = []

  // Suggestions universelles
  suggestions.push({ nom: 'Photo', type: 'photo', obligatoire: false })
  suggestions.push({ nom: 'État', type: 'etat', obligatoire: true })
  suggestions.push({ nom: 'Remarques', type: 'text', obligatoire: false })

  // Suggestions contextuelles
  if (name.includes('luminaire') || name.includes('éclairage') || name.includes('lampe')) {
    suggestions.push({ nom: 'Puissance (W)', type: 'number', obligatoire: true })
    suggestions.push({ nom: 'Type de lampe', type: 'select', obligatoire: false, options: ['LED', 'Sodium', 'Halogène', 'Fluorescent'] })
    suggestions.push({ nom: 'Date installation', type: 'date', obligatoire: false })
  }

  if (name.includes('arbre') || name.includes('végéta')) {
    suggestions.push({ nom: 'Espèce', type: 'text', obligatoire: true })
    suggestions.push({ nom: 'Hauteur (m)', type: 'number', obligatoire: false })
    suggestions.push({ nom: 'Circonférence (cm)', type: 'number', obligatoire: false })
  }

  if (name.includes('banc') || name.includes('mobilier')) {
    suggestions.push({ nom: 'Matériau', type: 'select', obligatoire: false, options: ['Bois', 'Métal', 'Béton', 'Plastique'] })
    suggestions.push({ nom: 'Nombre de places', type: 'number', obligatoire: false })
  }

  if (name.includes('jeux') || name.includes('sport')) {
    suggestions.push({ nom: 'Type équipement', type: 'text', obligatoire: true })
    suggestions.push({ nom: 'Tranche âge', type: 'select', obligatoire: false, options: ['0-3 ans', '3-6 ans', '6-12 ans', 'Adultes'] })
    suggestions.push({ nom: 'Date contrôle', type: 'date', obligatoire: true })
  }

  suggestedFields.value = suggestions
}

function closeAddElementDialog() {
  showAddFamilleDialog.value = false
  addElementParent.value = null
  elementForm.value = {
    libelle: '',
    code: '',
    icone: 'mdi-folder',
    couleur: '#1976D2',
    parent_id: null,
    niveau: 0
  }
  selectedSuggestedFields.value = []
  suggestedFields.value = []
  // Reset template selection
  selectedTemplateFamily.value = null
  useTemplateMode.value = false
  templateFieldsToApply.value = []
}

function selectTemplateFamily(family: TemplateFamily) {
  if (selectedTemplateFamily.value?.code === family.code) {
    selectedTemplateFamily.value = null
    templateFieldsToApply.value = []
  } else {
    selectedTemplateFamily.value = family
    // Sélectionner tous les champs par défaut
    templateFieldsToApply.value = family.fields.map(f => f.nom)
  }
}

function selectAllTemplateFields() {
  if (selectedTemplateFamily.value) {
    templateFieldsToApply.value = selectedTemplateFamily.value.fields.map(f => f.nom)
  }
}

function deselectAllTemplateFields() {
  templateFieldsToApply.value = []
}

// Manage inherited fields dialog
function closeManageInheritedFieldsDialog() {
  showManageInheritedFieldsDialog.value = false
  selectedTemplateForFields.value = null
  selectedTemplateFields.value = []
}

function editInheritedChamp(champ: any) {
  // Open the edit dialog with the inherited champ
  editingChamp.value = champ
  champForm.value = {
    nom: champ.nom,
    type: champ.type,
    obligatoire: champ.obligatoire,
    options: champ.options || [],
    min: champ.min,
    max: champ.max
  }
  showAddChampDialog.value = true
}

async function addFieldsFromTemplate() {
  if (!selectedTemplateForFields.value || selectedTemplateFields.value.length === 0 || !selectedElement.value) return

  addingTemplateFields.value = true
  const projectId = route.params.id as string

  try {
    const fieldsToAdd = selectedTemplateForFields.value.fields.filter(
      f => selectedTemplateFields.value.includes(f.nom) && !isFieldAlreadyExists(f.nom)
    )

    for (const field of fieldsToAdd) {
      try {
        await champsAPI.create({
          lexique_id: selectedElement.value.code,
          nom: field.nom,
          type: field.type as any,
          obligatoire: field.obligatoire,
          ordre: field.ordre,
          options: field.options,
          min: field.min,
          max: field.max,
          project_id: projectId
        })
      } catch (e) {
        console.warn(`Erreur création champ ${field.nom}:`, e)
      }
    }

    // Recharger les champs
    const champs = await champsAPI.getByLexique(selectedElement.value.code)
    allChamps.value.set(selectedElement.value.code, champs)

    // Réinitialiser la sélection
    selectedTemplateFields.value = []
    selectedTemplateForFields.value = null

  } catch (e) {
    console.error('Erreur ajout champs:', e)
    alert('Erreur lors de l\'ajout des champs')
  } finally {
    addingTemplateFields.value = false
  }
}

async function applyTemplateFamily() {
  const projectId = route.params.id as string
  if (!selectedTemplateFamily.value || !projectId) return

  // Convertit une couleur hex (#FF9800) en entier
  const hexToInt = (hex: string): number | null => {
    if (!hex) return null
    const clean = hex.replace('#', '')
    return parseInt(clean, 16)
  }

  try {
    const family = selectedTemplateFamily.value

    // Créer la famille racine (niveau 0)
    const familyData = {
      label: family.label,
      code: family.code,
      icon_name: family.icon,
      color_value: hexToInt(family.color),
      parent_code: null,
      level: 0,
      project_id: projectId
    }
    const createdFamily = await lexiqueAPI.create(familyData)

    // Créer les types (niveau 1)
    for (const type of family.children) {
      const typeData = {
        label: type.label,
        code: type.code,
        icon_name: type.icon,
        color_value: hexToInt(family.color),
        parent_code: createdFamily.code,  // Utiliser le code, pas l'id
        level: 1,
        project_id: projectId
      }
      const createdType = await lexiqueAPI.create(typeData)

      // Créer les sous-types (niveau 2)
      if (type.children) {
        for (const subtype of type.children) {
          const subtypeData = {
            label: subtype.label,
            code: subtype.code,
            icon_name: subtype.icon,
            color_value: hexToInt(family.color),
            parent_code: createdType.code,  // Utiliser le code, pas l'id
            level: 2,
            project_id: projectId
          }
          await lexiqueAPI.create(subtypeData)
        }
      }
    }

    // Créer uniquement les champs sélectionnés
    const fieldsToCreate = family.fields.filter(f => templateFieldsToApply.value.includes(f.nom))
    for (const field of fieldsToCreate) {
      try {
        await champsAPI.create({
          lexique_id: family.code,
          nom: field.nom,
          type: field.type as any,
          obligatoire: field.obligatoire,
          ordre: field.ordre,
          options: field.options,
          min: field.min,
          max: field.max,
          project_id: projectId
        })
      } catch (e) {
        console.warn(`Erreur création champ ${field.nom}:`, e)
      }
    }

    // Recharger la structure
    await loadStructure()
    closeAddElementDialog()
    // Réinitialiser les champs sélectionnés
    templateFieldsToApply.value = []

  } catch (e) {
    console.error('Erreur application template:', e)
    alert('Erreur lors de l\'application du template')
  }
}

async function confirmDeleteFamily() {
  const projectId = route.params.id as string
  if (!selectedElement.value || !projectId) return

  checkingDelete.value = true
  try {
    // Vérifier si la suppression est possible
    const info = await lexiqueAPI.canDelete(selectedElement.value.code, projectId)
    deleteInfo.value = info
    showDeleteConfirmDialog.value = true
  } catch (e: any) {
    console.error('Erreur vérification suppression:', e)
    alert(e.response?.data?.detail || 'Erreur lors de la vérification')
  } finally {
    checkingDelete.value = false
  }
}

async function deleteFamily() {
  const projectId = route.params.id as string
  if (!selectedElement.value || !projectId || !deleteInfo.value?.can_delete) return

  deletingFamily.value = true
  try {
    await lexiqueAPI.delete(selectedElement.value.code, projectId)

    // Fermer le dialogue et réinitialiser
    showDeleteConfirmDialog.value = false
    deleteInfo.value = null
    selectedElement.value = null

    // Recharger la structure
    await loadStructure()
  } catch (e: any) {
    console.error('Erreur suppression famille:', e)
    alert(e.response?.data?.detail || 'Erreur lors de la suppression')
  } finally {
    deletingFamily.value = false
  }
}

async function saveElement() {
  try {
    // Préparer le code s'il n'est pas défini
    let code = elementForm.value.code
    if (!code || code.trim() === '') {
      code = elementForm.value.libelle
        .toUpperCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^A-Z0-9]/g, '_')
        .substring(0, 20)
    }

    // Convertir la couleur hex en entier pour l'API
    let couleurHex = elementForm.value.couleur
    if (typeof couleurHex === 'object' && couleurHex !== null) {
      // Si c'est un objet (certains color pickers retournent ça)
      couleurHex = couleurHex.hex || couleurHex.hexa || '#1976D2'
    }
    if (typeof couleurHex === 'number') {
      // Si c'est déjà un nombre, garder tel quel
      couleurHex = '#' + (couleurHex >>> 0).toString(16).padStart(6, '0')
    }
    if (!couleurHex || !couleurHex.startsWith('#')) {
      couleurHex = '#1976D2'
    }
    // Convertir en entier pour l'API
    const colorValue = parseInt(couleurHex.replace('#', ''), 16)

    // Créer l'élément avec le project_id (noms de champs API)
    const projectId = route.params.id as string
    const data = {
      code: code,
      label: elementForm.value.libelle,
      icon_name: elementForm.value.icone,
      color_value: colorValue,
      parent_code: elementForm.value.parent_id,  // parent_id contient le code du parent
      level: elementForm.value.niveau,
      is_active: true,
      display_order: structure.value.length,
      project_id: projectId
    }

    console.log('Création élément avec données:', data)

    const newElement = await lexiqueAPI.create(data)

    // Créer les champs suggérés sélectionnés
    for (const field of selectedSuggestedFields.value) {
      await champsAPI.create({
        lexique_id: newElement.code,
        nom: field.nom,
        type: field.type === 'etat' ? 'select' : field.type,
        obligatoire: field.obligatoire,
        options: field.type === 'etat' ? ['Bon', 'Moyen', 'Mauvais', 'Hors service'] : field.options,
        ordre: 0,
        actif: true
      })
    }

    closeAddElementDialog()
    await loadStructure()

    // Sélectionner le nouvel élément
    selectElement(newElement)
  } catch (e: any) {
    console.error('Erreur création élément:', e)
    console.error('Détails:', e.response?.data)
  }
}

async function saveProjetSettings() {
  try {
    await projetsAPI.update(projet.value.id, projetForm.value)
    projet.value = { ...projet.value, ...projetForm.value }
    showSettingsDialog.value = false
  } catch (e) {
    console.error('Erreur sauvegarde projet:', e)
  }
}

function formatColor(couleur: any): string {
  if (!couleur) return 'primary'
  if (typeof couleur === 'string') {
    if (couleur.startsWith('#')) return couleur
    return 'primary'
  }
  if (typeof couleur === 'number') {
    // Convertir nombre négatif en hex
    const hex = (couleur >>> 0).toString(16).padStart(8, '0')
    return '#' + hex.substring(2) // Enlever l'alpha
  }
  return 'primary'
}

function getChampIcon(type: string) {
  const found = champTypes.find(t => t.value === type)
  return found?.icon || 'mdi-form-textbox'
}

function getChampTypeLabel(type: string) {
  const found = champTypes.find(t => t.value === type)
  return found?.label || type
}

function getIconLabel(iconValue: string): string {
  const icon = availableIcons.find(i => i.value === iconValue)
  return icon?.label || iconValue.replace('mdi-', '')
}

function editChamp(champ: any) {
  editingChamp.value = champ
  champForm.value = {
    ...champ,
    isConditional: !!champ.condition_field,
    condition_field: champ.condition_field || '',
    condition_operator: champ.condition_operator || '=',
    condition_value: champ.condition_value || ''
  }
  showAddChampDialog.value = true
}

function closeChampDialog() {
  showAddChampDialog.value = false
  editingChamp.value = null
  champForm.value = {
    nom: '',
    type: 'text',
    obligatoire: false,
    options: [],
    min: undefined,
    max: undefined,
    isConditional: false,
    condition_field: '',
    condition_operator: '=',
    condition_value: ''
  }
}

async function saveChamp() {
  try {
    const data: any = {
      lexique_id: selectedElement.value.code,
      nom: champForm.value.nom,
      type: champForm.value.type === 'etat' ? 'select' : champForm.value.type,
      obligatoire: champForm.value.obligatoire,
      options: champForm.value.type === 'etat'
        ? ['Bon', 'Moyen', 'Mauvais', 'Hors service']
        : champForm.value.options,
      min: champForm.value.min,
      max: champForm.value.max,
      actif: true,
      ordre: ownChamps.value.length
    }

    // Ajouter les conditions si le champ est conditionnel
    if (champForm.value.isConditional && champForm.value.condition_field) {
      data.condition_field = champForm.value.condition_field
      data.condition_operator = champForm.value.condition_operator || '='
      data.condition_value = champForm.value.condition_value
    } else {
      data.condition_field = null
      data.condition_operator = null
      data.condition_value = null
    }

    if (editingChamp.value) {
      await champsAPI.update(editingChamp.value.id, data)
    } else {
      await champsAPI.create(data)
    }

    closeChampDialog()

    // Recharger les champs
    const champs = await champsAPI.getByLexique(selectedElement.value.code)
    allChamps.value.set(selectedElement.value.code, champs)
  } catch (e) {
    console.error('Erreur sauvegarde champ:', e)
  }
}

async function deleteChamp(champ: any) {
  if (confirm(`Supprimer le champ "${champ.nom}" ?`)) {
    try {
      await champsAPI.delete(champ.id)
      const champs = await champsAPI.getByLexique(selectedElement.value.code)
      allChamps.value.set(selectedElement.value.code, champs)
    } catch (e) {
      console.error('Erreur suppression champ:', e)
    }
  }
}

// Lifecycle
onMounted(async () => {
  await loadProjet()
  await loadStructure()
})

// Fermer le dialogue de gestion des champs si l'élément sélectionné change
watch(selectedElement, (newVal) => {
  if (!newVal) {
    showManageInheritedFieldsDialog.value = false
  }
})
</script>

<style scoped>
.projet-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.structure-columns {
  overflow-x: auto;
}

.columns-container {
  display: flex;
  gap: 16px;
  min-width: min-content;
}

.structure-column {
  min-width: 200px;
  max-width: 250px;
  flex-shrink: 0;
  background: rgb(var(--v-theme-surface-variant));
  border-radius: 8px;
  overflow: hidden;
}

.column-header {
  padding: 12px 16px;
  font-weight: 600;
  background: rgb(var(--v-theme-primary));
  color: white;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
}

.column-content {
  padding: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.structure-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  background: rgb(var(--v-theme-surface));
  transition: all 0.2s;
}

.structure-item:hover {
  background: rgb(var(--v-theme-primary), 0.1);
}

.structure-item:hover .item-actions {
  opacity: 1;
}

.structure-item:hover .field-count-chip,
.structure-item:hover .chevron-icon {
  opacity: 0;
}

.structure-item.selected {
  background: rgb(var(--v-theme-primary));
  color: white;
}

.structure-item.selected .v-icon {
  color: white !important;
}

.structure-item.selected .item-actions .v-btn {
  color: white !important;
}

.item-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
  position: absolute;
  right: 8px;
  background: inherit;
}

.structure-item {
  position: relative;
}

.field-count-chip,
.chevron-icon {
  transition: opacity 0.2s;
}

.add-child-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px dashed rgb(var(--v-theme-primary), 0.3);
  color: rgb(var(--v-theme-primary));
  font-size: 0.8rem;
  margin-top: 8px;
  transition: all 0.2s;
}

.add-child-btn:hover {
  border-color: rgb(var(--v-theme-primary));
  background: rgb(var(--v-theme-primary), 0.1);
}

.icon-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.icon-categories {
  max-height: 300px;
  overflow-y: auto;
}

.icon-categories :deep(.v-expansion-panel-title) {
  min-height: 40px;
  padding: 8px 16px;
}

.icon-categories :deep(.v-expansion-panel-text__wrapper) {
  padding: 8px;
}

/* Drag & Drop styles */
.structure-item {
  cursor: grab;
}

.structure-item:active {
  cursor: grabbing;
}

.structure-item.drag-over {
  border: 2px dashed rgb(var(--v-theme-primary));
  background: rgb(var(--v-theme-primary), 0.15);
}

.drag-handle {
  opacity: 0.4;
  cursor: grab;
}

.structure-item:hover .drag-handle {
  opacity: 1;
}

/* Mobile Preview styles */
.mobile-preview {
  width: 280px;
}

.mobile-frame {
  border: 3px solid #333;
  border-radius: 24px;
  overflow: hidden;
  background: #f5f5f5;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}

.mobile-header {
  background: rgb(var(--v-theme-primary));
  color: white;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mobile-title {
  font-weight: 600;
  font-size: 14px;
}

.mobile-content {
  padding: 12px;
  min-height: 350px;
  max-height: 350px;
  overflow-y: auto;
  background: white;
}

.mobile-category {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f0f0;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 12px;
  font-weight: 500;
}

.mobile-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mobile-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mobile-label {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
}

.mobile-input {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  background: white;
}

.mobile-input .placeholder {
  color: #999;
}

.mobile-select {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  background: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mobile-select .placeholder {
  color: #999;
}

.mobile-photo {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: #fafafa;
}

.mobile-footer {
  padding: 12px;
  background: white;
  border-top: 1px solid #eee;
}

.template-card {
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.template-preview-tree {
  max-height: 150px;
  overflow-y: auto;
}
</style>
