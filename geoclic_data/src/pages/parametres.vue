<template>
  <div>
    <div class="d-flex align-center mb-6">
      <h1 class="text-h4 font-weight-bold">
        Paramètres
        <HelpButton page-key="parametres" size="sm" />
      </h1>
    </div>

    <!-- Tabs de navigation -->
    <v-tabs v-model="activeTab" class="mb-6" color="primary">
      <v-tab value="general">
        <v-icon start>mdi-cog</v-icon>
        Général
      </v-tab>
      <v-tab value="branding" v-if="isAdmin">
        <v-icon start>mdi-palette-swatch</v-icon>
        Personnalisation
      </v-tab>
      <v-tab value="email" v-if="isAdmin">
        <v-icon start>mdi-email-outline</v-icon>
        Email
      </v-tab>
      <v-tab value="postgis" v-if="isAdmin">
        <v-icon start>mdi-database</v-icon>
        PostGIS
      </v-tab>
    </v-tabs>

    <!-- ==================== ONGLET GÉNÉRAL ==================== -->
    <div v-if="activeTab === 'general'">
      <v-row>
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title>
              <v-icon class="mr-2">mdi-palette</v-icon>
              Apparence
            </v-card-title>
            <v-card-text>
              <v-switch
                v-model="darkMode"
                label="Mode sombre"
                color="primary"
                @update:model-value="toggleDarkMode"
              />
              <v-select
                v-model="language"
                label="Langue"
                :items="languages"
                class="mt-4"
              />
            </v-card-text>
          </v-card>

          <v-card class="mt-4">
            <v-card-title>
              <v-icon class="mr-2">mdi-map</v-icon>
              Cartographie
            </v-card-title>
            <v-card-text>
              <v-select
                v-model="defaultMapStyle"
                label="Style de carte par defaut"
                :items="mapStyles"
              />
              <v-text-field
                v-model.number="defaultZoom"
                label="Niveau de zoom par defaut"
                type="number"
                :min="1"
                :max="18"
                class="mt-4"
              />
              <v-row class="mt-4">
                <v-col cols="6">
                  <v-text-field
                    v-model.number="defaultLat"
                    label="Latitude par defaut"
                    type="number"
                    step="0.0001"
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model.number="defaultLng"
                    label="Longitude par defaut"
                    type="number"
                    step="0.0001"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card>
            <v-card-title>
              <v-icon class="mr-2">mdi-shield-check</v-icon>
              Anti-doublon
            </v-card-title>
            <v-card-text>
              <v-slider
                v-model="duplicateRadius"
                label="Rayon de detection"
                :min="1"
                :max="50"
                :step="1"
                thumb-label="always"
              >
                <template v-slot:append>
                  <span class="text-body-2">{{ duplicateRadius }}m</span>
                </template>
              </v-slider>
              <p class="text-caption text-grey">
                Un avertissement sera affiche si un point existe dans ce rayon lors de la creation.
              </p>
              <v-switch
                v-model="blockDuplicates"
                label="Bloquer la creation de doublons"
                color="error"
                class="mt-4"
              />
            </v-card-text>
          </v-card>

          <v-card class="mt-4">
            <v-card-title>
              <v-icon class="mr-2">mdi-qrcode</v-icon>
              QR Codes
            </v-card-title>
            <v-card-text>
              <v-text-field
                v-model="qrBaseUrl"
                label="URL de base des QR codes"
                hint="L'URL qui sera encodee dans les QR codes"
                persistent-hint
              />
              <v-select
                v-model="qrDefaultSize"
                label="Taille par defaut"
                :items="qrSizes"
                class="mt-4"
              />
            </v-card-text>
          </v-card>

          <v-card class="mt-4">
            <v-card-title>
              <v-icon class="mr-2">mdi-information</v-icon>
              A propos
            </v-card-title>
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>Version</v-list-item-title>
                  <v-list-item-subtitle>GeoClic Data v1.0.0</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>API</v-list-item-title>
                  <v-list-item-subtitle>{{ apiUrl }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-btn color="primary" size="large" class="mt-6" @click="saveSettings">
        <v-icon start>mdi-content-save</v-icon>
        Enregistrer les parametres
      </v-btn>
    </div>

    <!-- ==================== ONGLET PERSONNALISATION ==================== -->
    <div v-if="activeTab === 'branding' && isAdmin">
      <v-row>
        <v-col cols="12" md="7">
          <v-card>
            <v-card-title>
              <v-icon class="mr-2">mdi-domain</v-icon>
              Identite de la collectivite
            </v-card-title>
            <v-card-text>
              <v-alert type="info" variant="tonal" density="compact" class="mb-4">
                Ces parametres s'appliquent a toutes les applications GéoClic : portail citoyen, back-office demandes, services terrain, SIG, etc.
              </v-alert>

              <v-text-field
                v-model="branding.nom_collectivite"
                label="Nom de la collectivite *"
                placeholder="Mairie de..."
                hint="Affiche dans le portail citoyen, les emails et toutes les applications"
                persistent-hint
              />

              <!-- Logo upload -->
              <div class="mt-4">
                <label class="text-subtitle-2 d-block mb-2">Logo</label>
                <div class="d-flex align-center gap-3">
                  <div v-if="brandingLogoPreview || branding.logo_url" class="logo-preview-box">
                    <img :src="brandingLogoPreview || branding.logo_url" alt="Logo" class="logo-preview-img" />
                    <v-btn icon size="x-small" color="error" variant="flat" class="logo-remove-btn" @click="removeBrandingLogo">
                      <v-icon size="small">mdi-close</v-icon>
                    </v-btn>
                  </div>
                  <label class="logo-upload-label">
                    <input type="file" accept=".png,.jpg,.jpeg,.svg,.webp,.gif" @change="onBrandingLogoSelected" hidden />
                    <v-btn variant="outlined" color="primary" tag="span">
                      <v-icon start>mdi-upload</v-icon>
                      {{ branding.logo_url ? 'Changer' : 'Choisir un fichier' }}
                    </v-btn>
                  </label>
                </div>
                <p class="text-caption text-grey mt-1">PNG ou SVG recommande (hauteur 40px, max 5 MB)</p>
              </div>

              <v-text-field
                v-model="branding.favicon_url"
                label="URL du favicon"
                placeholder="https://..."
                class="mt-4"
              />

              <v-divider class="my-4" />

              <h4 class="text-subtitle-1 font-weight-bold mb-3">Coordonnees</h4>

              <v-text-field
                v-model="branding.adresse"
                label="Adresse"
                placeholder="1 Place de la Mairie, 75000 Paris"
              />

              <v-row class="mt-1">
                <v-col cols="6">
                  <v-text-field
                    v-model="branding.email_contact"
                    label="Email de contact"
                    placeholder="contact@mairie.fr"
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="branding.telephone"
                    label="Telephone"
                    placeholder="01 23 45 67 89"
                  />
                </v-col>
              </v-row>

              <v-text-field
                v-model="branding.site_web"
                label="Site web"
                placeholder="https://www.mairie.fr"
              />
            </v-card-text>
          </v-card>

          <!-- Couleurs -->
          <v-card class="mt-4">
            <v-card-title>
              <v-icon class="mr-2">mdi-palette</v-icon>
              Couleurs
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="6">
                  <div class="d-flex align-center gap-2">
                    <input type="color" v-model="branding.primary_color" style="width:40px;height:40px;border:1px solid #ccc;border-radius:8px;cursor:pointer;" />
                    <v-text-field
                      v-model="branding.primary_color"
                      label="Couleur principale"
                      density="compact"
                      hide-details
                    />
                  </div>
                  <p class="text-caption text-grey mt-1">Boutons, liens, accents</p>
                </v-col>
                <v-col cols="6">
                  <div class="d-flex align-center gap-2">
                    <input type="color" v-model="branding.secondary_color" style="width:40px;height:40px;border:1px solid #ccc;border-radius:8px;cursor:pointer;" />
                    <v-text-field
                      v-model="branding.secondary_color"
                      label="Couleur secondaire"
                      density="compact"
                      hide-details
                    />
                  </div>
                  <p class="text-caption text-grey mt-1">Textes, titres</p>
                </v-col>
              </v-row>
              <v-row class="mt-2">
                <v-col cols="6">
                  <div class="d-flex align-center gap-2">
                    <input type="color" v-model="branding.accent_color" style="width:40px;height:40px;border:1px solid #ccc;border-radius:8px;cursor:pointer;" />
                    <v-text-field
                      v-model="branding.accent_color"
                      label="Couleur accent"
                      density="compact"
                      hide-details
                    />
                  </div>
                  <p class="text-caption text-grey mt-1">Succes, confirmations</p>
                </v-col>
                <v-col cols="6">
                  <div class="d-flex align-center gap-2">
                    <input type="color" v-model="branding.sidebar_color" style="width:40px;height:40px;border:1px solid #ccc;border-radius:8px;cursor:pointer;" />
                    <v-text-field
                      v-model="branding.sidebar_color"
                      label="Couleur sidebar"
                      density="compact"
                      hide-details
                    />
                  </div>
                  <p class="text-caption text-grey mt-1">Menu lateral back-office</p>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Aperçu -->
        <v-col cols="12" md="5">
          <v-card>
            <v-card-title>
              <v-icon class="mr-2">mdi-eye</v-icon>
              Apercu
            </v-card-title>
            <v-card-text>
              <div class="preview-box">
                <div class="preview-sidebar" :style="{ background: branding.sidebar_color }">
                  <div class="preview-logo">
                    <img v-if="brandingLogoPreview || branding.logo_url" :src="brandingLogoPreview || branding.logo_url" alt="Logo" class="preview-logo-img" />
                    <span v-else class="preview-logo-text" :style="{ color: 'white' }">{{ branding.nom_collectivite || 'GeoClic' }}</span>
                  </div>
                  <div class="preview-menu-item" :style="{ borderColor: branding.primary_color }">Tableau de bord</div>
                  <div class="preview-menu-item">Demandes</div>
                  <div class="preview-menu-item">Carte</div>
                </div>
                <div class="preview-content">
                  <div class="preview-btn" :style="{ background: branding.primary_color }">Bouton principal</div>
                  <div class="preview-btn" :style="{ background: branding.accent_color }">Succes</div>
                  <span class="preview-text" :style="{ color: branding.secondary_color }">Texte exemple</span>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <v-card class="mt-4">
            <v-card-title>
              <v-icon class="mr-2">mdi-information-outline</v-icon>
              Applications concernees
            </v-card-title>
            <v-card-text>
              <v-list density="compact">
                <v-list-item prepend-icon="mdi-web">Portail citoyen (couleurs, logo, nom, contact)</v-list-item>
                <v-list-item prepend-icon="mdi-clipboard-text">Back-office demandes (sidebar, logo)</v-list-item>
                <v-list-item prepend-icon="mdi-wrench">Services terrain desktop (header, couleur)</v-list-item>
                <v-list-item prepend-icon="mdi-cellphone">Services terrain mobile (header, couleur)</v-list-item>
                <v-list-item prepend-icon="mdi-map">SIG Web (sidebar, logo)</v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <div class="d-flex gap-2 mt-6">
        <v-btn
          color="primary"
          size="large"
          :loading="savingBranding"
          @click="saveBranding"
        >
          <v-icon start>mdi-content-save</v-icon>
          Enregistrer la personnalisation
        </v-btn>
      </div>

      <v-alert
        v-if="brandingResult"
        :type="brandingResult.success ? 'success' : 'error'"
        variant="tonal"
        class="mt-4"
        closable
        @click:close="brandingResult = null"
      >
        {{ brandingResult.message }}
      </v-alert>
    </div>

    <!-- ==================== ONGLET EMAIL ==================== -->
    <div v-if="activeTab === 'email' && isAdmin">
      <v-row>
        <v-col cols="12" md="8">
          <v-card>
            <v-card-title>
              <v-icon class="mr-2">mdi-email-outline</v-icon>
              Configuration SMTP
            </v-card-title>
            <v-card-text>
              <v-alert type="info" variant="tonal" density="compact" class="mb-4">
                Cette configuration est utilisee par toutes les applications GéoClic pour envoyer des emails aux citoyens et aux agents.
              </v-alert>

              <v-switch
                v-model="emailSettings.enabled"
                label="Activer l'envoi d'emails"
                color="primary"
                class="mb-4"
              />

              <template v-if="emailSettings.enabled">
                <v-row>
                  <v-col cols="8">
                    <v-text-field
                      v-model="emailSettings.smtp_host"
                      label="Serveur SMTP"
                      placeholder="smtp.office365.com"
                      hint="Outlook 365 : smtp.office365.com | Gmail : smtp.gmail.com"
                      persistent-hint
                    />
                  </v-col>
                  <v-col cols="4">
                    <v-text-field
                      v-model.number="emailSettings.smtp_port"
                      label="Port"
                      type="number"
                    />
                  </v-col>
                </v-row>

                <v-row class="mt-1">
                  <v-col cols="6">
                    <v-text-field
                      v-model="emailSettings.smtp_user"
                      label="Utilisateur"
                      placeholder="user@domain.com"
                    />
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model="emailSettings.smtp_password"
                      label="Mot de passe"
                      :type="showSmtpPassword ? 'text' : 'password'"
                      :append-inner-icon="showSmtpPassword ? 'mdi-eye-off' : 'mdi-eye'"
                      @click:append-inner="showSmtpPassword = !showSmtpPassword"
                      hint="Pour Office 365 avec MFA : utiliser un mot de passe d'application"
                      persistent-hint
                    />
                  </v-col>
                </v-row>

                <v-row class="mt-1">
                  <v-col cols="6">
                    <v-text-field
                      v-model="emailSettings.sender_name"
                      label="Nom expediteur"
                      placeholder="Mairie de..."
                    />
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model="emailSettings.sender_email"
                      label="Email expediteur"
                      placeholder="noreply@mairie.fr"
                    />
                  </v-col>
                </v-row>

                <v-switch
                  v-model="emailSettings.smtp_tls"
                  label="Utiliser TLS (recommande)"
                  color="primary"
                  class="mt-2"
                />
              </template>
            </v-card-text>
          </v-card>

          <v-card class="mt-4" v-if="emailSettings.enabled">
            <v-card-title>
              <v-icon class="mr-2">mdi-bell-outline</v-icon>
              Notifications
            </v-card-title>
            <v-card-text>
              <h4 class="text-subtitle-2 mb-2">Citoyens</h4>
              <v-switch
                v-model="emailSettings.notify_citizen_creation"
                label="Confirmation de reception du signalement"
                color="primary"
                density="compact"
                hide-details
              />
              <v-switch
                v-model="emailSettings.notify_citizen_status_change"
                label="Changement de statut (accepte, en cours, traite, rejete)"
                color="primary"
                density="compact"
                hide-details
                class="mt-1"
              />

              <v-divider class="my-3" />

              <h4 class="text-subtitle-2 mb-2">Agents terrain</h4>
              <v-switch
                v-model="emailSettings.notify_service_new_demande"
                label="Nouvelle demande assignee au service"
                color="primary"
                density="compact"
                hide-details
              />
              <v-switch
                v-model="emailSettings.notify_agent_new_message"
                label="Nouveau message tchat du back-office"
                color="primary"
                density="compact"
                hide-details
                class="mt-1"
              />
              <v-switch
                v-model="emailSettings.notify_agent_reminder"
                label="Rappel avant intervention planifiee"
                color="primary"
                density="compact"
                hide-details
                class="mt-1"
              />

              <v-select
                v-if="emailSettings.notify_agent_reminder"
                v-model="emailSettings.reminder_hours_before"
                label="Delai de rappel"
                :items="reminderDelays"
                class="mt-3"
                style="max-width: 300px"
              />
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>
              <v-icon class="mr-2">mdi-information-outline</v-icon>
              Aide
            </v-card-title>
            <v-card-text>
              <v-alert type="info" variant="tonal" density="compact" class="mb-3">
                <strong>Office 365</strong><br />
                Serveur : smtp.office365.com<br />
                Port : 587<br />
                TLS : Oui
              </v-alert>
              <v-alert type="info" variant="tonal" density="compact">
                <strong>Gmail</strong><br />
                Serveur : smtp.gmail.com<br />
                Port : 587<br />
                TLS : Oui<br />
                Mot de passe d'application requis
              </v-alert>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <div class="d-flex gap-2 mt-6">
        <v-btn
          color="primary"
          size="large"
          :loading="savingEmail"
          @click="saveEmailSettings"
        >
          <v-icon start>mdi-content-save</v-icon>
          Enregistrer
        </v-btn>
        <v-btn
          variant="outlined"
          size="large"
          :disabled="!emailSettings.enabled"
          :loading="testingEmail"
          @click="testEmail"
        >
          <v-icon start>mdi-email-fast</v-icon>
          Envoyer un test
        </v-btn>
      </div>

      <v-alert
        v-if="emailResult"
        :type="emailResult.success ? 'success' : 'error'"
        variant="tonal"
        class="mt-4"
        closable
        @click:close="emailResult = null"
      >
        {{ emailResult.message }}
      </v-alert>
    </div>

    <!-- ==================== ONGLET POSTGIS ==================== -->
    <div v-if="activeTab === 'postgis' && isAdmin">
      <v-row>
        <v-col cols="12" md="8">
          <v-card>
            <v-card-title>
              <v-icon class="mr-2">mdi-database</v-icon>
              Connexion PostGIS externe
              <v-chip
                :color="postgisConfigured ? 'success' : 'grey'"
                size="small"
                class="ml-2"
              >
                {{ postgisConfigured ? 'Configure' : 'Non configure' }}
              </v-chip>
            </v-card-title>
            <v-card-text>
              <v-alert type="info" variant="tonal" density="compact" class="mb-4">
                <v-icon class="mr-1" size="small">mdi-information</v-icon>
                Cette configuration permet d'importer des donnees depuis une base PostGIS externe.
                Reserve au service IT.
              </v-alert>

              <v-text-field
                v-model="pgConfig.host"
                label="Hote *"
                placeholder="localhost ou 192.168.1.10"
                :disabled="postgisConfigured && !editingPostgis"
              />
              <v-text-field
                v-model.number="pgConfig.port"
                label="Port *"
                type="number"
                :disabled="postgisConfigured && !editingPostgis"
                class="mt-3"
              />
              <v-text-field
                v-model="pgConfig.database"
                label="Base de donnees *"
                placeholder="nom_base"
                :disabled="postgisConfigured && !editingPostgis"
                class="mt-3"
              />
              <v-text-field
                v-model="pgConfig.schema_name"
                label="Schema"
                placeholder="public"
                :disabled="postgisConfigured && !editingPostgis"
                class="mt-3"
              />
              <v-text-field
                v-model="pgConfig.username"
                label="Utilisateur *"
                :disabled="postgisConfigured && !editingPostgis"
                class="mt-3"
              />
              <v-text-field
                v-model="pgConfig.password"
                label="Mot de passe *"
                :type="showPgPassword ? 'text' : 'password'"
                :append-inner-icon="showPgPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showPgPassword = !showPgPassword"
                :disabled="postgisConfigured && !editingPostgis"
                class="mt-3"
              />

              <div class="d-flex gap-2 mt-4">
                <v-btn
                  v-if="!postgisConfigured"
                  color="primary"
                  :loading="savingPostgis"
                  :disabled="!pgConfigValid"
                  @click="savePostGISConfig"
                >
                  <v-icon start>mdi-content-save</v-icon>
                  Enregistrer
                </v-btn>

                <v-btn
                  v-if="postgisConfigured && !editingPostgis"
                  color="warning"
                  variant="outlined"
                  @click="editingPostgis = true"
                >
                  <v-icon start>mdi-pencil</v-icon>
                  Modifier
                </v-btn>

                <v-btn
                  v-if="editingPostgis"
                  color="primary"
                  :loading="savingPostgis"
                  :disabled="!pgConfigValid"
                  @click="savePostGISConfig"
                >
                  <v-icon start>mdi-content-save</v-icon>
                  Mettre a jour
                </v-btn>

                <v-btn
                  v-if="editingPostgis"
                  variant="text"
                  @click="cancelEditPostgis"
                >
                  Annuler
                </v-btn>

                <v-btn
                  v-if="postgisConfigured"
                  color="info"
                  variant="outlined"
                  :loading="testingPostgis"
                  @click="testPostGISConnection"
                >
                  <v-icon start>mdi-connection</v-icon>
                  Tester
                </v-btn>

                <v-spacer />

                <v-btn
                  v-if="postgisConfigured"
                  color="error"
                  variant="text"
                  @click="confirmDeletePostgis = true"
                >
                  <v-icon start>mdi-delete</v-icon>
                  Supprimer
                </v-btn>
              </div>

              <!-- Resultat du test -->
              <v-alert
                v-if="pgTestResult"
                :type="pgTestResult.success ? 'success' : 'error'"
                variant="tonal"
                class="mt-4"
                closable
                @click:close="pgTestResult = null"
              >
                {{ pgTestResult.message }}
                <span v-if="pgTestResult.postgis_version">
                  (PostGIS {{ pgTestResult.postgis_version }})
                </span>
              </v-alert>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- Dialog de confirmation suppression PostGIS -->
    <v-dialog v-model="confirmDeletePostgis" max-width="400">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon class="mr-2" color="error">mdi-alert</v-icon>
          Confirmer la suppression
        </v-card-title>
        <v-card-text>
          Etes-vous sur de vouloir supprimer la configuration PostGIS ?
          L'import depuis PostGIS ne sera plus disponible.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDeletePostgis = false">
            Annuler
          </v-btn>
          <v-btn color="error" @click="deletePostGISConfig">
            Supprimer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'
import { postgisAPI } from '@/services/api'
import HelpButton from '@/components/help/HelpButton.vue'
import axios from 'axios'

const theme = useTheme()
const authStore = useAuthStore()

// Active tab
const activeTab = ref('general')

// Apparence
const darkMode = ref(theme.global.current.value.dark)
const language = ref('fr')
const languages = [
  { title: 'Francais', value: 'fr' },
  { title: 'English', value: 'en' },
]

// Carte
const defaultMapStyle = ref('streets')
const mapStyles = [
  { title: 'Plan', value: 'streets' },
  { title: 'Satellite', value: 'satellite' },
]
const defaultZoom = ref(13)
const defaultLat = ref(46.603354)
const defaultLng = ref(1.888334)

// Anti-doublon
const duplicateRadius = ref(5)
const blockDuplicates = ref(false)

// QR Codes
const qrBaseUrl = ref(window.location.origin)
const qrDefaultSize = ref('medium')
const qrSizes = [
  { title: 'Petit (2cm)', value: 'small' },
  { title: 'Moyen (4cm)', value: 'medium' },
  { title: 'Grand (6cm)', value: 'large' },
]

// API
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Branding
const isAdmin = computed(() => authStore.user?.is_super_admin || authStore.user?.role_data === 'admin')
const brandingConfigured = ref(false)
const savingBranding = ref(false)
const brandingResult = ref<{ success: boolean; message: string } | null>(null)
const brandingLogoFile = ref<File | null>(null)
const brandingLogoPreview = ref<string | null>(null)
const branding = ref({
  nom_collectivite: '',
  logo_url: '',
  primary_color: '#2563eb',
  secondary_color: '#1f2937',
  accent_color: '#10b981',
  sidebar_color: '#1f2937',
  email_contact: '',
  telephone: '',
  site_web: '',
  adresse: '',
  favicon_url: '',
})

function onBrandingLogoSelected(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!['png', 'jpg', 'jpeg', 'svg', 'webp', 'gif'].includes(ext || '')) {
      brandingResult.value = { success: false, message: 'Format non supporte. Utilisez PNG, JPG, SVG ou WebP.' }
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      brandingResult.value = { success: false, message: 'Fichier trop volumineux (max 5 MB).' }
      return
    }
    brandingLogoFile.value = file
    brandingLogoPreview.value = URL.createObjectURL(file)
  }
}

function removeBrandingLogo() {
  brandingLogoFile.value = null
  brandingLogoPreview.value = null
  branding.value.logo_url = ''
}

async function loadBranding() {
  try {
    const response = await axios.get('/api/settings/branding')
    const data = response.data
    branding.value.nom_collectivite = data.nom_collectivite || ''
    branding.value.logo_url = data.logo_url || ''
    branding.value.primary_color = data.primary_color || '#2563eb'
    branding.value.secondary_color = data.secondary_color || '#1f2937'
    branding.value.accent_color = data.accent_color || '#10b981'
    branding.value.sidebar_color = data.sidebar_color || '#1f2937'
    branding.value.email_contact = data.email_contact || ''
    branding.value.telephone = data.telephone || ''
    branding.value.site_web = data.site_web || ''
    branding.value.favicon_url = data.favicon_url || ''
    brandingConfigured.value = !!data.nom_collectivite

    // Charger aussi l'adresse depuis general settings
    try {
      const genRes = await axios.get('/api/settings/general')
      branding.value.adresse = genRes.data.adresse || ''
    } catch { /* ignore */ }
  } catch (e) {
    console.error('Erreur chargement branding:', e)
  }
}

async function saveBranding() {
  savingBranding.value = true
  brandingResult.value = null
  try {
    // Uploader le logo s'il y en a un nouveau
    if (brandingLogoFile.value) {
      const formData = new FormData()
      formData.append('file', brandingLogoFile.value)
      const res = await axios.post('/api/settings/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      branding.value.logo_url = res.data.logo_url
      brandingLogoFile.value = null
      brandingLogoPreview.value = null
    }

    await axios.put('/api/settings/general', branding.value)
    brandingConfigured.value = true
    brandingResult.value = {
      success: true,
      message: 'Personnalisation enregistree. Les changements seront visibles au prochain chargement de toutes les applications.'
    }
  } catch (e: any) {
    brandingResult.value = {
      success: false,
      message: e.response?.data?.detail || 'Erreur lors de l\'enregistrement'
    }
  } finally {
    savingBranding.value = false
  }
}

// Email
const savingEmail = ref(false)
const testingEmail = ref(false)
const showSmtpPassword = ref(false)
const emailResult = ref<{ success: boolean; message: string } | null>(null)
const emailSettings = ref({
  enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
  smtp_tls: true,
  sender_name: '',
  sender_email: '',
  notify_citizen_creation: true,
  notify_citizen_status_change: true,
  notify_service_new_demande: true,
  notify_agent_new_message: true,
  notify_agent_reminder: true,
  reminder_hours_before: 24
})

const reminderDelays = [
  { title: '2 heures', value: 2 },
  { title: '6 heures', value: 6 },
  { title: '12 heures', value: 12 },
  { title: '24 heures (1 jour)', value: 24 },
  { title: '48 heures (2 jours)', value: 48 },
]

async function loadEmailSettings() {
  try {
    const response = await axios.get('/api/settings/email')
    emailSettings.value = { ...emailSettings.value, ...response.data }
  } catch (e) {
    console.error('Erreur chargement email:', e)
  }
}

async function saveEmailSettings() {
  savingEmail.value = true
  emailResult.value = null
  try {
    await axios.put('/api/settings/email', emailSettings.value)
    emailResult.value = { success: true, message: 'Parametres email enregistres' }
  } catch (e: any) {
    emailResult.value = { success: false, message: e.response?.data?.detail || 'Erreur lors de l\'enregistrement' }
  } finally {
    savingEmail.value = false
  }
}

async function testEmail() {
  testingEmail.value = true
  emailResult.value = null
  try {
    await axios.post('/api/settings/email/test')
    emailResult.value = { success: true, message: 'Email de test envoye avec succes' }
  } catch (e: any) {
    emailResult.value = { success: false, message: e.response?.data?.detail || 'Erreur lors de l\'envoi du test' }
  } finally {
    testingEmail.value = false
  }
}

// PostGIS
const postgisConfigured = ref(false)
const editingPostgis = ref(false)
const savingPostgis = ref(false)
const testingPostgis = ref(false)
const showPgPassword = ref(false)
const confirmDeletePostgis = ref(false)
const pgTestResult = ref<{ success: boolean; message: string; postgis_version?: string } | null>(null)

const pgConfig = ref({
  host: '',
  port: 5432,
  database: '',
  schema_name: 'public',
  username: '',
  password: '',
})

const pgConfigValid = computed(() => {
  return (
    pgConfig.value.host.trim() !== '' &&
    pgConfig.value.port > 0 &&
    pgConfig.value.database.trim() !== '' &&
    pgConfig.value.username.trim() !== '' &&
    pgConfig.value.password.trim() !== ''
  )
})

function toggleDarkMode(value: boolean | null) {
  theme.global.name.value = value ? 'geoclicDarkTheme' : 'geoclicTheme'
}

function saveSettings() {
  const settings = {
    darkMode: darkMode.value,
    language: language.value,
    defaultMapStyle: defaultMapStyle.value,
    defaultZoom: defaultZoom.value,
    defaultLat: defaultLat.value,
    defaultLng: defaultLng.value,
    duplicateRadius: duplicateRadius.value,
    blockDuplicates: blockDuplicates.value,
    qrBaseUrl: qrBaseUrl.value,
    qrDefaultSize: qrDefaultSize.value,
  }
  localStorage.setItem('geoclic_settings', JSON.stringify(settings))
}

// PostGIS functions
async function loadPostGISStatus() {
  try {
    const status = await postgisAPI.getStatus()
    postgisConfigured.value = status.configured

    if (status.configured) {
      pgConfig.value.host = status.host || ''
      pgConfig.value.database = status.database || ''
      pgConfig.value.schema_name = status.schema_name || 'public'
    }
  } catch (e) {
    console.error('Erreur chargement statut PostGIS:', e)
  }
}

async function savePostGISConfig() {
  savingPostgis.value = true
  pgTestResult.value = null

  try {
    await postgisAPI.configure(pgConfig.value)
    postgisConfigured.value = true
    editingPostgis.value = false
    pgTestResult.value = {
      success: true,
      message: 'Configuration enregistree avec succes',
    }
  } catch (e: any) {
    pgTestResult.value = {
      success: false,
      message: e.response?.data?.detail || "Erreur lors de l'enregistrement",
    }
  } finally {
    savingPostgis.value = false
  }
}

async function testPostGISConnection() {
  testingPostgis.value = true
  pgTestResult.value = null

  try {
    const result = await postgisAPI.testConnection()
    pgTestResult.value = {
      success: true,
      message: result.message,
      postgis_version: result.postgis_version,
    }
  } catch (e: any) {
    pgTestResult.value = {
      success: false,
      message: e.response?.data?.detail || 'Echec de la connexion',
    }
  } finally {
    testingPostgis.value = false
  }
}

async function deletePostGISConfig() {
  try {
    await postgisAPI.deleteConfig()
    postgisConfigured.value = false
    pgConfig.value = {
      host: '',
      port: 5432,
      database: '',
      schema_name: 'public',
      username: '',
      password: '',
    }
    confirmDeletePostgis.value = false
    pgTestResult.value = {
      success: true,
      message: 'Configuration supprimee',
    }
  } catch (e: any) {
    pgTestResult.value = {
      success: false,
      message: e.response?.data?.detail || 'Erreur lors de la suppression',
    }
  }
}

function cancelEditPostgis() {
  editingPostgis.value = false
  loadPostGISStatus()
}

onMounted(() => {
  if (isAdmin.value) {
    loadPostGISStatus()
    loadBranding()
    loadEmailSettings()
  }
})
</script>

<style scoped>
/* Logo upload */
.logo-preview-box {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.logo-preview-img {
  max-height: 40px;
  max-width: 160px;
  object-fit: contain;
}

.logo-remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
}

.logo-upload-label {
  cursor: pointer;
}

/* Preview */
.preview-box {
  display: flex;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  height: 160px;
}

.preview-sidebar {
  width: 160px;
  padding: 0.75rem;
  color: white;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.preview-logo {
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.15);
  margin-bottom: 0.25rem;
}

.preview-logo-img {
  height: 24px;
  width: auto;
}

.preview-logo-text {
  font-weight: 600;
  font-size: 0.85rem;
}

.preview-menu-item {
  font-size: 0.75rem;
  padding: 0.3rem 0.5rem;
  border-left: 3px solid transparent;
  border-radius: 0 4px 4px 0;
  color: rgba(255,255,255,0.7);
}

.preview-menu-item:first-of-type {
  background: rgba(255,255,255,0.1);
  color: white;
}

.preview-content {
  flex: 1;
  padding: 1rem;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 0.75rem;
  background: #f9fafb;
}

.preview-btn {
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  color: white;
  font-size: 0.8rem;
  font-weight: 500;
}

.preview-text {
  font-size: 0.85rem;
  font-weight: 500;
}
</style>
