<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const router = useRouter()

// Wizard state
const step = ref(1)
const totalSteps = 5

// Form data - Step 1
const name = ref('')
const domain = ref('')
const ip = ref('')
const email = ref('')
const sshUser = ref('ubuntu')
const sshPort = ref(22)

// Form data - Step 3 (Config admin)
const adminPassword = ref('')
const adminPasswordConfirm = ref('')
const collectivite = ref('')
const withDemo = ref(false)

// State
const sshKey = ref('')
const sshTestResult = ref<'idle' | 'testing' | 'ok' | 'failed'>('idle')
const provisioning = ref(false)
const initializing = ref(false)
const installPhase = ref<'provision' | 'init' | 'done' | 'failed'>('provision')
const taskId = ref('')
const taskStatus = ref<any>(null)
const taskLog = ref('')
const error = ref('')
let pollInterval: ReturnType<typeof setInterval>

// Auto-generate short name from domain
const autoName = computed(() => {
  if (name.value) return name.value
  if (domain.value) {
    return domain.value.replace(/\.geoclic\.fr$/, '').replace(/\./g, '-')
  }
  return ''
})

// Password validation
const passwordValid = computed(() => {
  return adminPassword.value.length >= 8 && adminPassword.value === adminPasswordConfirm.value
})

const passwordError = computed(() => {
  if (!adminPassword.value) return ''
  if (adminPassword.value.length < 8) return 'Minimum 8 caractères'
  if (adminPasswordConfirm.value && adminPassword.value !== adminPasswordConfirm.value) return 'Les mots de passe ne correspondent pas'
  return ''
})

// Step 1: Server info
function goStep2() {
  if (!domain.value || !ip.value || !email.value) {
    error.value = 'Tous les champs sont requis'
    return
  }
  if (!name.value) name.value = autoName.value
  error.value = ''
  step.value = 2
  loadSshKey()
}

// Step 2: SSH setup
async function loadSshKey() {
  try {
    const data = await api.getSshKey()
    sshKey.value = data.public_key
  } catch {
    try {
      const data = await api.generateSshKey()
      sshKey.value = data.public_key
    } catch (e: any) {
      error.value = `Impossible de charger la clé SSH: ${e.message}`
    }
  }
}

async function testSsh() {
  sshTestResult.value = 'testing'
  error.value = ''
  try {
    const result = await api.testSsh(ip.value, sshUser.value, sshPort.value)
    sshTestResult.value = result.status === 'ok' ? 'ok' : 'failed'
  } catch {
    sshTestResult.value = 'failed'
  }
}

function goStep3() {
  if (sshTestResult.value !== 'ok') {
    error.value = 'Testez la connexion SSH avant de continuer'
    return
  }
  error.value = ''
  step.value = 3
}

// Step 3: Admin config
function goStep4() {
  if (!adminPassword.value || !collectivite.value) {
    error.value = 'Le mot de passe et le nom de collectivité sont requis'
    return
  }
  if (!passwordValid.value) {
    error.value = passwordError.value || 'Vérifiez le mot de passe'
    return
  }
  error.value = ''
  step.value = 4
}

// Step 4: Confirm → Step 5: Install
async function startInstallation() {
  error.value = ''
  provisioning.value = true
  installPhase.value = 'provision'
  step.value = 5

  try {
    // Phase 1: Provisioning
    const result = await api.provisionServer({
      name: name.value,
      domain: domain.value,
      ip: ip.value,
      email: email.value,
      ssh_user: sshUser.value,
      ssh_port: sshPort.value,
    })
    taskId.value = result.task_id

    // Poll task status
    pollInterval = setInterval(async () => {
      try {
        const status = await api.getTask(taskId.value)
        taskStatus.value = status

        const logData = await api.getTaskLog(taskId.value)
        taskLog.value = logData.log

        if (status.status === 'completed') {
          clearInterval(pollInterval)
          provisioning.value = false
          // Auto-start init phase
          startInit()
        } else if (status.status === 'failed') {
          clearInterval(pollInterval)
          provisioning.value = false
          installPhase.value = 'failed'
        }
      } catch {
        // Ignore poll errors
      }
    }, 3000)
  } catch (e: any) {
    error.value = e.message
    provisioning.value = false
    installPhase.value = 'failed'
  }
}

async function startInit() {
  initializing.value = true
  installPhase.value = 'init'
  taskLog.value += '\n\n━━━ Phase 2 : Initialisation de la base de données ━━━\n\n'

  try {
    const result = await api.initServer(name.value, {
      email: email.value,
      password: adminPassword.value,
      collectivite: collectivite.value,
      with_demo: withDemo.value,
    })
    taskId.value = result.task_id

    // Poll init task
    pollInterval = setInterval(async () => {
      try {
        const status = await api.getTask(taskId.value)
        taskStatus.value = status

        const logData = await api.getTaskLog(taskId.value)
        // Append init logs after provision logs
        const provisionEnd = taskLog.value.indexOf('━━━ Phase 2')
        if (provisionEnd >= 0) {
          taskLog.value = taskLog.value.substring(0, provisionEnd) +
            '━━━ Phase 2 : Initialisation de la base de données ━━━\n\n' +
            logData.log
        }

        if (status.status === 'completed') {
          clearInterval(pollInterval)
          initializing.value = false
          installPhase.value = 'done'
        } else if (status.status === 'failed') {
          clearInterval(pollInterval)
          initializing.value = false
          installPhase.value = 'failed'
        }
      } catch {
        // Ignore poll errors
      }
    }, 3000)
  } catch (e: any) {
    error.value = e.message
    initializing.value = false
    installPhase.value = 'failed'
  }
}

function copyKey() {
  navigator.clipboard.writeText(sshKey.value)
}

function goBack() {
  if (step.value > 1 && step.value < 5) step.value -= 1
}

const isInstalling = computed(() => provisioning.value || initializing.value)
</script>

<template>
  <div class="add-server">
    <div class="page-header">
      <div>
        <h1>Ajouter un serveur</h1>
        <p class="subtitle">Provisionnement et configuration automatique d'un nouveau VPS</p>
      </div>
    </div>

    <!-- Progress bar -->
    <div class="progress-bar">
      <div
        v-for="s in totalSteps"
        :key="s"
        class="progress-step"
        :class="{ active: s === step, done: s < step }"
      >
        <div class="step-dot">{{ s < step ? '✓' : s }}</div>
        <span class="step-label">
          {{
            s === 1 ? 'Informations' :
            s === 2 ? 'Connexion SSH' :
            s === 3 ? 'Configuration' :
            s === 4 ? 'Confirmation' :
            'Installation'
          }}
        </span>
      </div>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>

    <!-- STEP 1: Informations serveur -->
    <div v-if="step === 1" class="card step-card">
      <h2>Informations du serveur</h2>
      <p class="step-desc">Entrez les informations de votre nouveau VPS OVH.</p>

      <div class="form-group">
        <label>Nom de domaine *</label>
        <input v-model="domain" class="input" placeholder="ville-lyon.geoclic.fr" />
        <p class="form-hint">Le domaine doit pointer vers l'IP du VPS (enregistrement DNS A)</p>
      </div>

      <div class="form-group">
        <label>Adresse IP du VPS *</label>
        <input v-model="ip" class="input" placeholder="51.210.42.100" />
        <p class="form-hint">Visible dans votre espace client OVH</p>
      </div>

      <div class="form-group">
        <label>Email administrateur *</label>
        <input v-model="email" type="email" class="input" placeholder="admin@ville-lyon.fr" />
        <p class="form-hint">Pour le certificat SSL, le compte super admin et les notifications</p>
      </div>

      <div class="form-group">
        <label>Identifiant court</label>
        <input v-model="name" class="input" :placeholder="autoName || 'ville-lyon'" />
        <p class="form-hint">Nom unique pour identifier ce serveur (auto-généré si vide)</p>
      </div>

      <div class="form-row">
        <div class="form-group" style="flex:2">
          <label>Utilisateur SSH</label>
          <input v-model="sshUser" class="input" placeholder="ubuntu" />
        </div>
        <div class="form-group" style="flex:1">
          <label>Port SSH</label>
          <input v-model.number="sshPort" type="number" class="input" placeholder="22" />
        </div>
      </div>

      <div class="step-actions">
        <router-link to="/" class="btn btn-outline">Annuler</router-link>
        <button class="btn btn-primary" @click="goStep2">Suivant</button>
      </div>
    </div>

    <!-- STEP 2: Connexion SSH -->
    <div v-if="step === 2" class="card step-card">
      <h2>Configuration SSH</h2>
      <p class="step-desc">
        Copiez cette clé publique et ajoutez-la sur votre VPS OVH.
      </p>

      <div class="ssh-key-box" v-if="sshKey">
        <div class="ssh-key-header">
          <strong>Clé publique à copier :</strong>
          <button class="btn btn-sm btn-outline" @click="copyKey">Copier</button>
        </div>
        <code class="ssh-key-value">{{ sshKey }}</code>
      </div>

      <div class="instructions">
        <h3>Comment faire ?</h3>
        <ol>
          <li>Connectez-vous à l'<a href="https://www.ovh.com/manager/" target="_blank">espace client OVH</a></li>
          <li>Allez dans <strong>Bare Metal Cloud &gt; Clés SSH</strong></li>
          <li>Cliquez <strong>Ajouter une clé SSH</strong></li>
          <li>Collez la clé ci-dessus et donnez-lui le nom <strong>geoclic-fleet</strong></li>
          <li>Si le VPS est déjà créé, connectez-vous en SSH et ajoutez la clé manuellement :<br>
            <code>echo "{{ sshKey }}" >> ~/.ssh/authorized_keys</code>
          </li>
        </ol>
      </div>

      <div class="ssh-test">
        <button
          class="btn"
          :class="{
            'btn-primary': sshTestResult === 'idle',
            'btn-outline': sshTestResult === 'testing',
            'btn-accent': sshTestResult === 'ok',
            'btn-danger': sshTestResult === 'failed',
          }"
          :disabled="sshTestResult === 'testing'"
          @click="testSsh"
        >
          {{
            sshTestResult === 'idle' ? 'Tester la connexion SSH' :
            sshTestResult === 'testing' ? 'Test en cours...' :
            sshTestResult === 'ok' ? 'Connexion OK !' :
            'Connexion échouée - Réessayer'
          }}
        </button>
      </div>

      <div class="step-actions">
        <button class="btn btn-outline" @click="goBack">Précédent</button>
        <button class="btn btn-primary" @click="goStep3">Suivant</button>
      </div>
    </div>

    <!-- STEP 3: Configuration admin et collectivité -->
    <div v-if="step === 3" class="card step-card">
      <h2>Configuration initiale</h2>
      <p class="step-desc">
        Ces informations seront utilisées pour créer le compte super administrateur
        et configurer la plateforme GéoClic.
      </p>

      <div class="form-group">
        <label>Nom de la collectivité *</label>
        <input v-model="collectivite" class="input" placeholder="Mairie de Lyon" />
        <p class="form-hint">Affiché sur toutes les applications (portail citoyen, back-office, etc.)</p>
      </div>

      <div class="form-group">
        <label>Mot de passe administrateur *</label>
        <input v-model="adminPassword" type="password" class="input" placeholder="Minimum 8 caractères" />
        <p class="form-hint" v-if="!passwordError">Le compte admin utilisera l'email : <strong>{{ email }}</strong></p>
        <p class="form-hint form-error" v-else>{{ passwordError }}</p>
      </div>

      <div class="form-group">
        <label>Confirmer le mot de passe *</label>
        <input v-model="adminPasswordConfirm" type="password" class="input" placeholder="Retapez le mot de passe" />
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="withDemo" />
          <span>Charger les données de démonstration</span>
        </label>
        <p class="form-hint">
          12 signalements fictifs, 4 services municipaux, 3 comptes agents.
          Utile pour tester la plateforme avant de la configurer.
        </p>
      </div>

      <div class="step-actions">
        <button class="btn btn-outline" @click="goBack">Précédent</button>
        <button class="btn btn-primary" @click="goStep4">Suivant</button>
      </div>
    </div>

    <!-- STEP 4: Confirmation -->
    <div v-if="step === 4" class="card step-card">
      <h2>Confirmation</h2>
      <p class="step-desc">Vérifiez les informations avant de lancer l'installation complète.</p>

      <div class="recap">
        <div class="recap-row">
          <span>Identifiant</span><strong>{{ name }}</strong>
        </div>
        <div class="recap-row">
          <span>Domaine</span><strong>{{ domain }}</strong>
        </div>
        <div class="recap-row">
          <span>IP</span><strong>{{ ip }}</strong>
        </div>
        <div class="recap-row">
          <span>SSH</span><strong>{{ sshUser }}@{{ ip }}:{{ sshPort }}</strong>
        </div>
        <div class="recap-row">
          <span>Email admin</span><strong>{{ email }}</strong>
        </div>
        <div class="recap-row">
          <span>Collectivité</span><strong>{{ collectivite }}</strong>
        </div>
        <div class="recap-row">
          <span>Données démo</span><strong>{{ withDemo ? 'Oui' : 'Non' }}</strong>
        </div>
      </div>

      <div class="recap-info">
        <h3>Ce qui va se passer :</h3>
        <div class="install-phases">
          <div class="phase">
            <div class="phase-icon">1</div>
            <div>
              <strong>Provisioning</strong> (~10-15 min)
              <p>Installation Docker, copie du code, génération du .env, certificat SSL, construction et démarrage des 10 conteneurs.</p>
            </div>
          </div>
          <div class="phase">
            <div class="phase-icon">2</div>
            <div>
              <strong>Initialisation BDD</strong> (~2-3 min)
              <p>Application des 25 migrations SQL (toutes les tables et fonctionnalités), création du super admin, configuration du branding{{ withDemo ? ', chargement des données démo' : '' }}.</p>
            </div>
          </div>
          <div class="phase">
            <div class="phase-icon">3</div>
            <div>
              <strong>Prêt à l'emploi</strong>
              <p>Le client se connecte et le wizard d'onboarding le guide (catégories, services, email SMTP).</p>
            </div>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button class="btn btn-outline" @click="goBack">Précédent</button>
        <button class="btn btn-accent" @click="startInstallation">
          Lancer l'installation complète
        </button>
      </div>
    </div>

    <!-- STEP 5: Installation en cours -->
    <div v-if="step === 5" class="card step-card">
      <h2>
        {{
          installPhase === 'provision' ? 'Phase 1 : Provisioning en cours...' :
          installPhase === 'init' ? 'Phase 2 : Initialisation de la base de données...' :
          installPhase === 'done' ? 'Installation terminée !' :
          'Installation échouée'
        }}
      </h2>

      <!-- Phase indicator -->
      <div class="phase-indicator">
        <div class="phase-step" :class="{ active: installPhase === 'provision', done: installPhase !== 'provision' && installPhase !== 'failed' }">
          <div class="phase-dot">{{ installPhase === 'provision' ? '⏳' : (installPhase === 'failed' && !initializing ? '✗' : '✓') }}</div>
          <span>Provisioning</span>
        </div>
        <div class="phase-line" :class="{ done: installPhase !== 'provision' }"></div>
        <div class="phase-step" :class="{ active: installPhase === 'init', done: installPhase === 'done' }">
          <div class="phase-dot">{{ installPhase === 'init' ? '⏳' : (installPhase === 'done' ? '✓' : (installPhase === 'failed' && !provisioning ? '✗' : '·')) }}</div>
          <span>Initialisation BDD</span>
        </div>
        <div class="phase-line" :class="{ done: installPhase === 'done' }"></div>
        <div class="phase-step" :class="{ done: installPhase === 'done' }">
          <div class="phase-dot">{{ installPhase === 'done' ? '✓' : '·' }}</div>
          <span>Prêt</span>
        </div>
      </div>

      <!-- Provision progress steps -->
      <div v-if="taskStatus && installPhase === 'provision'" class="provision-progress">
        <div class="provision-steps">
          <div
            v-for="s in (taskStatus.total || 7)"
            :key="s"
            class="provision-step"
            :class="{
              done: s < (taskStatus.step || 0),
              active: s === (taskStatus.step || 0),
              pending: s > (taskStatus.step || 0),
            }"
          >
            <div class="pstep-icon">
              {{ s < (taskStatus.step || 0) ? '✓' : s === (taskStatus.step || 0) && provisioning ? '⏳' : s }}
            </div>
            <span v-if="s === (taskStatus.step || 0)">{{ taskStatus.label }}</span>
          </div>
        </div>
      </div>

      <!-- Logs -->
      <div class="log-box" v-if="taskLog">
        <pre>{{ taskLog }}</pre>
      </div>

      <!-- Success message -->
      <div v-if="installPhase === 'done'" class="success-box">
        <div class="success-icon">🎉</div>
        <h3>Serveur opérationnel !</h3>
        <p>
          <strong>{{ collectivite }}</strong> est maintenant en ligne sur
          <a :href="`https://${domain}`" target="_blank">{{ domain }}</a>.
        </p>
        <p class="success-detail">
          Le compte administrateur <strong>{{ email }}</strong> peut se connecter
          et lancer le wizard d'onboarding pour configurer les catégories, services et email.
        </p>
      </div>

      <!-- Actions post-install -->
      <div v-if="!isInstalling" class="step-actions">
        <router-link to="/" class="btn btn-primary">Retour au dashboard</router-link>
        <a v-if="installPhase === 'done'" :href="`https://${domain}/data/`" target="_blank" class="btn btn-accent">
          Ouvrir GéoClic Admin
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.add-server {
  max-width: 700px;
  margin: 0 auto;
}

.progress-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
}

.progress-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.step-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  background: var(--border);
  color: var(--text-secondary);
  transition: all 0.3s;
}

.progress-step.active .step-dot {
  background: var(--primary);
  color: white;
}

.progress-step.done .step-dot {
  background: var(--accent);
  color: white;
}

.step-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.progress-step.active .step-label {
  color: var(--primary);
  font-weight: 600;
}

.step-card {
  padding: 28px;
}

.step-card h2 {
  font-size: 20px;
  margin-bottom: 6px;
}

.step-desc {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 24px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.error-box {
  background: #ffebee;
  color: #c62828;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 16px;
}

/* SSH */
.ssh-key-box {
  background: #f5f5f5;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px;
  margin-bottom: 20px;
}

.ssh-key-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ssh-key-value {
  display: block;
  font-size: 12px;
  word-break: break-all;
  background: white;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid var(--border);
  max-height: 80px;
  overflow: auto;
}

.instructions {
  margin-bottom: 20px;
}

.instructions h3 {
  font-size: 15px;
  margin-bottom: 8px;
}

.instructions ol {
  padding-left: 20px;
  font-size: 14px;
}

.instructions li {
  margin-bottom: 8px;
}

.instructions code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}

.ssh-test {
  text-align: center;
  margin: 20px 0;
}

/* Step 3 - Config */
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 600;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--primary);
}

.form-error {
  color: #c62828 !important;
}

/* Recap */
.recap {
  background: #f5f5f5;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
}

.recap-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}

.recap-row:last-child {
  border-bottom: none;
}

.recap-info {
  background: #e8eaf6;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
}

.recap-info h3 {
  font-size: 15px;
  margin-bottom: 12px;
  color: var(--primary);
}

.install-phases {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.phase {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.phase-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.phase p {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

/* Phase indicator */
.phase-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin: 24px 0;
}

.phase-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.phase-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: var(--border);
  color: var(--text-secondary);
  transition: all 0.3s;
}

.phase-step.active .phase-dot {
  background: var(--primary);
  color: white;
  animation: pulse 1.5s infinite;
}

.phase-step.done .phase-dot {
  background: var(--accent);
  color: white;
}

.phase-step span {
  font-size: 12px;
  color: var(--text-secondary);
}

.phase-step.active span {
  color: var(--primary);
  font-weight: 600;
}

.phase-step.done span {
  color: var(--accent);
}

.phase-line {
  width: 60px;
  height: 3px;
  background: var(--border);
  margin: 0 8px;
  margin-bottom: 22px;
  transition: background 0.3s;
}

.phase-line.done {
  background: var(--accent);
}

/* Provisioning */
.provision-progress {
  margin: 20px 0;
}

.provision-steps {
  display: flex;
  gap: 4px;
}

.provision-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.pstep-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  background: var(--border);
  color: var(--text-secondary);
}

.provision-step.done .pstep-icon {
  background: var(--accent);
  color: white;
}

.provision-step.active .pstep-icon {
  background: var(--primary);
  color: white;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.log-box {
  background: #1a1a2e;
  color: #a4e400;
  border-radius: 6px;
  padding: 16px;
  margin: 20px 0;
  max-height: 300px;
  overflow: auto;
  font-family: 'Fira Code', 'Consolas', monospace;
}

.log-box pre {
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* Success */
.success-box {
  text-align: center;
  padding: 24px;
  background: #e8f5e9;
  border-radius: 8px;
  margin: 20px 0;
}

.success-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.success-box h3 {
  font-size: 20px;
  color: #2e7d32;
  margin-bottom: 8px;
}

.success-box a {
  color: var(--primary);
  font-weight: 600;
}

.success-detail {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
}
</style>
