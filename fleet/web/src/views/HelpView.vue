<script setup lang="ts">
import { ref, computed } from 'vue'

const openSection = ref('quick-start')
const searchQuery = ref('')

function toggle(id: string) {
  openSection.value = openSection.value === id ? '' : id
}

function scrollToSection(id: string) {
  toggle(id)
  setTimeout(() => {
    const el = document.getElementById('section-' + id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, 100)
}

function copyCode(event: Event) {
  const btn = event.target as HTMLElement
  const block = btn.closest('.code-block')
  if (!block) return
  const codeEl = block.querySelector('code')
  if (!codeEl) return
  navigator.clipboard.writeText(codeEl.textContent || '').then(() => {
    btn.textContent = 'Copié !'
    btn.classList.add('copied')
    setTimeout(() => {
      btn.textContent = 'Copier'
      btn.classList.remove('copied')
    }, 2000)
  })
}

const allSections = [
  { id: 'quick-start', label: 'Démarrage rapide', icon: '🚀', group: 'accueil' },
  { id: 'prerequis', label: 'Prérequis', icon: '📋', group: 'accueil' },
  { id: 'new-vps', label: 'Acheter un VPS', icon: '🖥️', group: 'prerequis' },
  { id: 'dns', label: 'Configurer le DNS', icon: '🌐', group: 'prerequis' },
  { id: 'ssh', label: 'Configurer SSH', icon: '🔑', group: 'prerequis' },
  { id: 'provisioning', label: 'Provisionner un serveur', icon: '⚡', group: 'install' },
  { id: 'init-db', label: 'Initialiser la base de données', icon: '🗄️', group: 'install', badge: 'Automatique' },
  { id: 'update', label: 'Mettre à jour les serveurs', icon: '🔄', group: 'gestion' },
  { id: 'status', label: 'Voir l\'état des serveurs', icon: '📊', group: 'gestion' },
  { id: 'backup', label: 'Sauvegardes', icon: '💾', group: 'gestion' },
  { id: 'logs', label: 'Consulter les logs', icon: '📝', group: 'gestion' },
  { id: 'registry', label: 'Gérer le registre', icon: '📃', group: 'gestion' },
  { id: 'ssh-direct', label: 'Accès SSH direct', icon: '💻', group: 'gestion' },
  { id: 'reference', label: 'Référence des commandes', icon: '📖', group: 'reference' },
  { id: 'troubleshoot', label: 'Dépannage', icon: '🔧', group: 'reference' },
  { id: 'architecture', label: 'Architecture technique', icon: '🏗️', group: 'reference' },
  { id: 'glossaire', label: 'Glossaire', icon: '📚', group: 'reference', badge: 'Nouveau' },
  { id: 'faq', label: 'FAQ', icon: '❓', group: 'reference' },
]

const filteredSections = computed(() => {
  if (!searchQuery.value.trim()) return allSections
  const q = searchQuery.value.toLowerCase()
  return allSections.filter(s => s.label.toLowerCase().includes(q))
})
</script>

<template>
  <div class="help-page">
    <div class="page-header">
      <div>
        <h1>Aide - Fleet Manager</h1>
        <p class="subtitle">Guide complet pour gérer vos serveurs GéoClic</p>
      </div>
      <router-link to="/" class="btn btn-outline">&larr; Dashboard</router-link>
    </div>

    <!-- Recherche + Table des matières -->
    <div class="toc card">
      <div class="toc-header">
        <h3>Sommaire</h3>
        <div class="search-wrap">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Rechercher..."
            class="search-input"
          />
        </div>
      </div>
      <div class="toc-groups">
        <div class="toc-group" v-if="filteredSections.some(s => s.group === 'accueil')">
          <span class="toc-group-label">Accueil</span>
          <ul>
            <li v-for="s in filteredSections.filter(s => s.group === 'accueil')" :key="s.id">
              <a href="#" @click.prevent="scrollToSection(s.id)" :class="{ active: openSection === s.id }">
                <span class="toc-icon">{{ s.icon }}</span> {{ s.label }}
                <span v-if="s.badge" class="badge-new-sm">{{ s.badge }}</span>
              </a>
            </li>
          </ul>
        </div>
        <div class="toc-group" v-if="filteredSections.some(s => s.group === 'prerequis')">
          <span class="toc-group-label">Prérequis</span>
          <ul>
            <li v-for="s in filteredSections.filter(s => s.group === 'prerequis')" :key="s.id">
              <a href="#" @click.prevent="scrollToSection(s.id)" :class="{ active: openSection === s.id }">
                <span class="toc-icon">{{ s.icon }}</span> {{ s.label }}
              </a>
            </li>
          </ul>
        </div>
        <div class="toc-group" v-if="filteredSections.some(s => s.group === 'install')">
          <span class="toc-group-label">Installation</span>
          <ul>
            <li v-for="s in filteredSections.filter(s => s.group === 'install')" :key="s.id">
              <a href="#" @click.prevent="scrollToSection(s.id)" :class="{ active: openSection === s.id }">
                <span class="toc-icon">{{ s.icon }}</span> {{ s.label }}
                <span v-if="s.badge" class="badge-new-sm">{{ s.badge }}</span>
              </a>
            </li>
          </ul>
        </div>
        <div class="toc-group" v-if="filteredSections.some(s => s.group === 'gestion')">
          <span class="toc-group-label">Gestion quotidienne</span>
          <ul>
            <li v-for="s in filteredSections.filter(s => s.group === 'gestion')" :key="s.id">
              <a href="#" @click.prevent="scrollToSection(s.id)" :class="{ active: openSection === s.id }">
                <span class="toc-icon">{{ s.icon }}</span> {{ s.label }}
              </a>
            </li>
          </ul>
        </div>
        <div class="toc-group" v-if="filteredSections.some(s => s.group === 'reference')">
          <span class="toc-group-label">Référence</span>
          <ul>
            <li v-for="s in filteredSections.filter(s => s.group === 'reference')" :key="s.id">
              <a href="#" @click.prevent="scrollToSection(s.id)" :class="{ active: openSection === s.id }">
                <span class="toc-icon">{{ s.icon }}</span> {{ s.label }}
                <span v-if="s.badge" class="badge-new-sm">{{ s.badge }}</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Sections -->
    <div class="sections">

      <!-- ═══ DÉMARRAGE RAPIDE ═══ -->
      <div id="section-quick-start" class="section card" :class="{ open: openSection === 'quick-start' }">
        <h2 @click="toggle('quick-start')">
          <span class="section-icon">🚀</span> Démarrage rapide
          <span class="chevron">{{ openSection === 'quick-start' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'quick-start'" class="section-content">
          <p>Le Fleet Manager vous permet de déployer et gérer GéoClic Suite sur plusieurs serveurs clients. Voici le flux complet pour ajouter un nouveau client :</p>

          <!-- Workflow visuel -->
          <div class="workflow">
            <div class="wf-step">
              <span class="wf-icon">🖥️</span>
              <strong>1. Acheter un VPS</strong>
              <p>~5€/mois chez OVH</p>
            </div>
            <div class="wf-arrow">→</div>
            <div class="wf-step">
              <span class="wf-icon">🌐</span>
              <strong>2. Configurer DNS</strong>
              <p>ville.geoclic.fr → IP</p>
            </div>
            <div class="wf-arrow">→</div>
            <div class="wf-step">
              <span class="wf-icon">🔑</span>
              <strong>3. Clé SSH</strong>
              <p>Copier sur le VPS</p>
            </div>
            <div class="wf-arrow">→</div>
            <div class="wf-step wf-step-new">
              <span class="wf-icon">📦</span>
              <strong>4. Installer</strong>
              <p>Un clic = tout automatique</p>
            </div>
            <div class="wf-arrow">→</div>
            <div class="wf-step wf-step-done">
              <span class="wf-icon">✅</span>
              <strong>5. C'est prêt !</strong>
              <p>Le client se connecte</p>
            </div>
          </div>

          <div class="info-box">
            <strong>Temps total estimé :</strong> ~20 minutes dont ~15 min d'installation automatique.<br>
            L'étape 4 fait <strong>tout en un clic</strong> : Docker, code, SSL, 25 migrations SQL, compte admin, branding.
          </div>

          <h3>Commandes essentielles</h3>
          <div class="cmd-grid">
            <div class="cmd-card" @click="scrollToSection('provisioning')">
              <code>+ Ajouter</code>
              <p>Installer GéoClic sur un nouveau VPS (tout automatique)</p>
              <span class="cmd-badge badge-essential">Essentiel</span>
            </div>
            <div class="cmd-card" @click="scrollToSection('update')">
              <code>update</code>
              <p>Mettre à jour un ou tous les serveurs</p>
              <span class="cmd-badge badge-essential">Essentiel</span>
            </div>
            <div class="cmd-card" @click="scrollToSection('status')">
              <code>status</code>
              <p>Vérifier l'état des serveurs</p>
              <span class="cmd-badge badge-gestion">Gestion</span>
            </div>
            <div class="cmd-card" @click="scrollToSection('backup')">
              <code>backup</code>
              <p>Sauvegarder la base de données</p>
              <span class="cmd-badge badge-gestion">Gestion</span>
            </div>
            <div class="cmd-card" @click="scrollToSection('logs')">
              <code>logs</code>
              <p>Voir les logs Docker d'un client</p>
              <span class="cmd-badge badge-debug">Debug</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ PRÉREQUIS ═══ -->
      <div id="section-prerequis" class="section card" :class="{ open: openSection === 'prerequis' }">
        <h2 @click="toggle('prerequis')">
          <span class="section-icon">📋</span> Prérequis
          <span class="chevron">{{ openSection === 'prerequis' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'prerequis'" class="section-content">
          <p>Checklist de ce dont vous avez besoin avant de déployer un nouveau client :</p>

          <table class="help-table">
            <thead>
              <tr><th>Élément</th><th>Détail</th><th>Coût</th></tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Un VPS (serveur)</strong></td>
                <td>Ubuntu 22.04 ou 24.04, minimum 2 Go RAM, 20 Go disque</td>
                <td>~5-10€/mois</td>
              </tr>
              <tr>
                <td><strong>Un nom de domaine</strong></td>
                <td>Sous-domaine de geoclic.fr ou domaine du client</td>
                <td>Inclus ou ~10€/an</td>
              </tr>
              <tr>
                <td><strong>Accès SSH au serveur</strong></td>
                <td>L'IP du VPS + la clé SSH Fleet configurée</td>
                <td>Gratuit</td>
              </tr>
              <tr>
                <td><strong>Un email admin</strong></td>
                <td>Pour les certificats SSL et le compte super admin</td>
                <td>Gratuit</td>
              </tr>
            </tbody>
          </table>

          <div class="info-box">
            <strong>Rappel :</strong> Toutes les commandes Fleet s'exécutent depuis votre serveur principal (geoclic.fr). Vous n'avez jamais besoin de vous connecter manuellement au serveur du client.
          </div>
        </div>
      </div>

      <!-- ═══ NOUVEAU VPS ═══ -->
      <div id="section-new-vps" class="section card" :class="{ open: openSection === 'new-vps' }">
        <h2 @click="toggle('new-vps')">
          <span class="section-icon">🖥️</span> Acheter un VPS
          <span class="chevron">{{ openSection === 'new-vps' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'new-vps'" class="section-content">
          <p>Un <strong>VPS</strong> (Virtual Private Server) est un serveur virtuel chez un hébergeur. C'est comme un ordinateur qui tourne 24h/24 sur internet.</p>

          <h3>Fournisseurs recommandés</h3>
          <table class="help-table">
            <thead>
              <tr><th>Fournisseur</th><th>Offre</th><th>RAM</th><th>Prix/mois</th><th>Avantage</th></tr>
            </thead>
            <tbody>
              <tr><td><strong>OVH</strong></td><td>VPS Starter</td><td>2 Go</td><td>~6€</td><td>Hébergeur français, RGPD</td></tr>
              <tr><td><strong>Scaleway</strong></td><td>DEV1-S</td><td>2 Go</td><td>~5€</td><td>Interface moderne</td></tr>
              <tr><td><strong>Hetzner</strong></td><td>CX22</td><td>4 Go</td><td>~4€</td><td>Bon rapport qualité/prix</td></tr>
            </tbody>
          </table>

          <h3>Étape 1 : Commander le VPS</h3>
          <ol>
            <li>Allez sur <a href="https://www.ovhcloud.com/fr/vps/" target="_blank">OVH VPS</a></li>
            <li>Choisissez <strong>VPS Starter</strong> (2 Go RAM, 20 Go SSD) minimum</li>
            <li>Système : <strong>Ubuntu 24.04</strong> (ou 22.04)</li>
            <li>Localisation : <strong>France</strong> (Gravelines ou Strasbourg)</li>
          </ol>

          <h3>Étape 2 : Pré-installer la clé SSH chez OVH (recommandé)</h3>
          <p>Pour éviter de copier manuellement la clé SSH sur chaque nouveau VPS :</p>
          <ol>
            <li>Connectez-vous à l'<a href="https://www.ovh.com/manager/" target="_blank">espace client OVH</a></li>
            <li>Allez dans <strong>Public Cloud &gt; Clés SSH</strong></li>
            <li>Cliquez <strong>Ajouter une clé SSH</strong></li>
            <li>Nom : <strong>geoclic-fleet</strong></li>
            <li>Clé : collez la clé SSH affichée dans le <router-link to="/">Dashboard</router-link></li>
          </ol>
          <div class="info-box">
            <strong>Résultat :</strong> Lors de la commande d'un nouveau VPS, sélectionnez la clé "geoclic-fleet". Le VPS sera livré avec la clé déjà installée !
          </div>

          <h3>Étape 3 : Récupérer l'IP</h3>
          <p>Une fois le VPS livré (quelques minutes), notez l'adresse IP dans votre espace client OVH.</p>

          <h3>Recommandation par taille de commune</h3>
          <table class="help-table">
            <thead>
              <tr><th>Commune</th><th>VPS recommandé</th><th>RAM</th><th>Prix/mois</th></tr>
            </thead>
            <tbody>
              <tr><td>&lt; 5 000 hab.</td><td>Starter</td><td>2 Go</td><td>~5€</td></tr>
              <tr><td>5 000 - 20 000</td><td>Essential</td><td>4 Go</td><td>~10€</td></tr>
              <tr><td>20 000 - 50 000</td><td>Comfort</td><td>8 Go</td><td>~20€</td></tr>
              <tr><td>&gt; 50 000</td><td>Elite</td><td>16 Go</td><td>~40€</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ═══ DNS ═══ -->
      <div id="section-dns" class="section card" :class="{ open: openSection === 'dns' }">
        <h2 @click="toggle('dns')">
          <span class="section-icon">🌐</span> Configurer le nom de domaine (DNS)
          <span class="chevron">{{ openSection === 'dns' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'dns'" class="section-content">
          <p>Le <strong>DNS</strong> est l'annuaire d'internet. Il traduit un nom lisible (ex: <code>lyon.geoclic.fr</code>) en adresse IP (ex: <code>51.210.42.100</code>).</p>

          <h3>Option A : Sous-domaine de geoclic.fr (recommandé)</h3>
          <ol>
            <li>Connectez-vous à l'espace client OVH</li>
            <li>Allez dans <strong>Noms de domaine &gt; geoclic.fr &gt; Zone DNS</strong></li>
            <li>Cliquez <strong>Ajouter une entrée</strong></li>
          </ol>
          <table class="help-table">
            <tr><th>Champ</th><th>Valeur</th></tr>
            <tr><td>Type</td><td><code>A</code></td></tr>
            <tr><td>Sous-domaine</td><td><code>lyon</code> (pour lyon.geoclic.fr)</td></tr>
            <tr><td>IP cible</td><td><code>51.210.42.100</code> (IP du VPS)</td></tr>
            <tr><td>TTL</td><td><code>3600</code> (laisser par défaut)</td></tr>
          </table>

          <h3>Option B : Domaine du client</h3>
          <p>Si le client a son propre domaine (ex: <code>signalements.ville-lyon.fr</code>), demandez-lui de créer un enregistrement A pointant vers l'IP du VPS.</p>

          <h3>Vérifier la propagation</h3>
          <div class="code-block">
            <code>ping lyon.geoclic.fr</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>
          <p>Si vous voyez l'IP du VPS dans la réponse, c'est bon ! Sinon vérifiez sur <a href="https://dnschecker.org/" target="_blank">dnschecker.org</a>.</p>

          <div class="warn-box">
            <strong>Important :</strong> Le DNS doit être configuré AVANT le provisionnement car le certificat SSL a besoin que le domaine pointe déjà vers le serveur.
          </div>
        </div>
      </div>

      <!-- ═══ SSH ═══ -->
      <div id="section-ssh" class="section card" :class="{ open: openSection === 'ssh' }">
        <h2 @click="toggle('ssh')">
          <span class="section-icon">🔑</span> Configurer SSH
          <span class="chevron">{{ openSection === 'ssh' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'ssh'" class="section-content">
          <p><strong>SSH</strong> est un moyen sécurisé de se connecter à un serveur distant. La <strong>clé SSH</strong> remplace le mot de passe.</p>

          <h3>Générer la clé Fleet (une seule fois)</h3>
          <p>La clé SSH est visible dans le <router-link to="/">Dashboard</router-link> (section "Clé SSH Fleet"). Si elle n'est pas encore générée :</p>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh ssh-key generate</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <h3>Copier la clé sur un nouveau VPS</h3>
          <p>Si vous n'avez pas pré-installé la clé chez OVH, connectez-vous au VPS manuellement :</p>
          <div class="code-block">
            <code>ssh root@51.210.42.100</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>
          <p>Puis exécutez :</p>
          <div class="code-block">
            <code>adduser ubuntu --disabled-password --gecos ""
usermod -aG sudo docker ubuntu
echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu
mkdir -p /home/ubuntu/.ssh
echo "COLLEZ_LA_CLE_PUBLIQUE_ICI" >> /home/ubuntu/.ssh/authorized_keys
chown -R ubuntu:ubuntu /home/ubuntu/.ssh
chmod 700 /home/ubuntu/.ssh && chmod 600 /home/ubuntu/.ssh/authorized_keys</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <h3>Vérifier</h3>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh test-ssh 51.210.42.100 ubuntu</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>
          <p>Résultat attendu : <code>{"status":"ok"}</code></p>

          <div class="warn-box">
            <strong>Ne partagez JAMAIS la clé privée.</strong> Seule la clé publique (.pub) se copie sur les serveurs.
          </div>
        </div>
      </div>

      <!-- ═══ PROVISIONING ═══ -->
      <div id="section-provisioning" class="section card" :class="{ open: openSection === 'provisioning' }">
        <h2 @click="toggle('provisioning')">
          <span class="section-icon">⚡</span> Provisionner un serveur
          <span class="chevron">{{ openSection === 'provisioning' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'provisioning'" class="section-content">
          <div class="info-box">
            <strong>Prérequis :</strong> Le VPS est acheté, le DNS est configuré, la clé SSH est installée.
          </div>

          <h3>Via l'interface web (recommandé)</h3>
          <ol>
            <li>Cliquez <router-link to="/add"><strong>+ Ajouter un serveur</strong></router-link></li>
            <li><strong>Étape 1 :</strong> Remplissez domaine, IP, email</li>
            <li><strong>Étape 2 :</strong> Testez la connexion SSH (bouton vert = OK)</li>
            <li><strong>Étape 3 :</strong> Configurez le compte admin (mot de passe, nom de collectivité, option démo)</li>
            <li><strong>Étape 4 :</strong> Vérifiez le récapitulatif et lancez l'installation</li>
            <li><strong>Étape 5 :</strong> Le provisioning + l'initialisation BDD se lancent <strong>automatiquement</strong></li>
          </ol>
          <div class="success-box">
            <strong>Tout est automatique !</strong> Un seul clic sur "Lancer l'installation complète" fait tout : Docker, code, SSL, 25 migrations, compte admin, branding. Le serveur est prêt à l'emploi à la fin.
          </div>

          <h3>Via le terminal</h3>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh provision \
  --name ville-lyon \
  --domain lyon.geoclic.fr \
  --ip 51.210.42.100 \
  --email admin@lyon.fr</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <h3>Paramètres</h3>
          <table class="help-table">
            <thead>
              <tr><th>Paramètre</th><th>Obligatoire</th><th>Description</th><th>Exemple</th></tr>
            </thead>
            <tbody>
              <tr><td><code>--name</code></td><td>Oui</td><td>Nom unique du client (sans espaces)</td><td><code>ville-lyon</code></td></tr>
              <tr><td><code>--domain</code></td><td>Oui</td><td>Nom de domaine du client</td><td><code>lyon.geoclic.fr</code></td></tr>
              <tr><td><code>--ip</code></td><td>Oui</td><td>Adresse IP du VPS</td><td><code>51.210.42.100</code></td></tr>
              <tr><td><code>--email</code></td><td>Oui</td><td>Email pour SSL (Let's Encrypt)</td><td><code>admin@lyon.fr</code></td></tr>
              <tr><td><code>--ssh-user</code></td><td>Non</td><td>Utilisateur SSH (défaut: ubuntu)</td><td><code>ubuntu</code></td></tr>
              <tr><td><code>--ssh-port</code></td><td>Non</td><td>Port SSH (défaut: 22)</td><td><code>22</code></td></tr>
            </tbody>
          </table>

          <h3>Ce que l'installation fait automatiquement (7 étapes)</h3>
          <table class="help-table">
            <thead>
              <tr><th>Étape</th><th>Détail</th><th>Durée</th></tr>
            </thead>
            <tbody>
              <tr><td>1. Test SSH</td><td>Vérifie que le serveur est accessible</td><td>~5s</td></tr>
              <tr><td>2. Prérequis</td><td>Installe Docker, rsync, certbot</td><td>~2 min</td></tr>
              <tr><td>3. Code</td><td>Copie tout GéoClic sur le serveur</td><td>~1 min</td></tr>
              <tr><td>4. Configuration</td><td>Génère les secrets JWT, mot de passe DB</td><td>~5s</td></tr>
              <tr><td>5. SSL</td><td>Obtient un certificat Let's Encrypt (HTTPS)</td><td>~30s</td></tr>
              <tr><td>6. Docker</td><td>Construit et démarre 10 conteneurs</td><td>~10 min</td></tr>
              <tr><td>7. Finalisation</td><td>Configure backups auto, monitoring, démarrage auto</td><td>~30s</td></tr>
            </tbody>
          </table>

          <div class="warn-box">
            <strong>Important :</strong> Le domaine DOIT pointer vers l'IP du VPS AVANT l'installation (nécessaire pour le certificat SSL). Ne fermez pas le terminal pendant l'exécution.
          </div>

          <div class="info-box">
            <strong>Via l'interface web :</strong> L'initialisation de la base de données (25 migrations + compte admin) se lance <strong>automatiquement</strong> juste après le provisionnement. La commande CLI ci-dessus ne fait que le provisionnement — il faut ensuite lancer <code>init</code> séparément.
          </div>
        </div>
      </div>

      <!-- ═══ INITIALISER LA DB ═══ -->
      <div id="section-init-db" class="section card" :class="{ open: openSection === 'init-db' }">
        <h2 @click="toggle('init-db')">
          <span class="section-icon">🗄️</span> Initialiser la base de données
          <span class="badge-new">Automatique</span>
          <span class="chevron">{{ openSection === 'init-db' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'init-db'" class="section-content">

          <div class="success-box">
            <strong>C'est automatique !</strong> Quand vous ajoutez un serveur via
            <router-link to="/add">+ Ajouter</router-link>, l'initialisation de la base de données
            se lance automatiquement juste après le provisionnement. Vous n'avez <strong>rien à faire manuellement</strong>.
          </div>

          <h3>Ce qui se passe automatiquement (étape 5 du wizard)</h3>
          <p>Après que les 10 conteneurs Docker sont démarrés, le wizard enchaîne automatiquement l'initialisation :</p>

          <div class="steps">
            <div class="step-item">
              <span class="step-num">1</span>
              <div>
                <strong>Vérifie la base de données</strong>
                <p>S'assure que PostgreSQL et PostGIS fonctionnent</p>
              </div>
            </div>
            <div class="step-item">
              <span class="step-num">2</span>
              <div>
                <strong>Applique les 25 migrations SQL</strong>
                <p>Crée toutes les tables, fonctions, triggers — le client obtient TOUTES les fonctionnalités</p>
              </div>
            </div>
            <div class="step-item">
              <span class="step-num">3</span>
              <div>
                <strong>Crée le compte super admin</strong>
                <p>Avec l'email et le mot de passe que vous avez saisis à l'étape 3</p>
              </div>
            </div>
            <div class="step-item">
              <span class="step-num">4</span>
              <div>
                <strong>Configure le branding</strong>
                <p>Enregistre le nom de la collectivité et les couleurs par défaut</p>
              </div>
            </div>
            <div class="step-item" v-if="true">
              <span class="step-num">5</span>
              <div>
                <strong>Charge les données démo (optionnel)</strong>
                <p>Si vous avez coché l'option à l'étape 3 : 12 signalements, 4 services, 3 comptes agents</p>
              </div>
            </div>
          </div>

          <div class="info-box">
            <strong>C'est quoi les "25 migrations" ?</strong> Ce sont des fichiers SQL qui créent progressivement toutes les tables, vues, triggers et fonctions de GéoClic. Sans elles, le client n'aurait aucune fonctionnalité (pas de demandes, pas de services, pas d'auth...). Vous n'avez pas besoin de les connaître, elles s'appliquent automatiquement.
          </div>

          <h3>Alternative : commande CLI (avancé)</h3>
          <p>Si vous avez besoin de relancer l'initialisation manuellement (par exemple après un échec réseau), vous pouvez utiliser la commande CLI :</p>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh init \
  --client ville-lyon \
  --email admin@lyon.fr \
  --password MotDePasse2026! \
  --collectivite "Mairie de Lyon"</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>
          <p>Ajoutez <code>--with-demo</code> pour charger les données de démonstration.</p>

          <div class="success-box">
            <strong>Résultat :</strong> Le client peut se connecter sur <code>https://domaine/data/</code> avec son email et mot de passe. Le wizard d'onboarding le guidera pour configurer les catégories, services et email.
          </div>
        </div>
      </div>

      <!-- ═══ MISE À JOUR ═══ -->
      <div id="section-update" class="section card" :class="{ open: openSection === 'update' }">
        <h2 @click="toggle('update')">
          <span class="section-icon">🔄</span> Mettre à jour les serveurs
          <span class="chevron">{{ openSection === 'update' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'update'" class="section-content">
          <p>Quand vous modifiez le code de GéoClic (nouvelle fonctionnalité, correction de bug), poussez la mise à jour vers vos serveurs clients.</p>

          <h3>Via l'interface web</h3>
          <ol>
            <li>Cliquez sur le serveur dans le dashboard</li>
            <li>Cliquez <strong>Mettre à jour</strong></li>
            <li>Attendez la fin de l'opération (~5-10 min)</li>
          </ol>
          <p>Pour tout mettre à jour d'un coup : bouton <strong>"Tout mettre à jour"</strong> dans le dashboard.</p>

          <h3>Via le terminal</h3>
          <div class="code-block">
            <code># Un seul client
sudo /opt/geoclic/fleet/geoclic-fleet.sh update --client ville-lyon

# Tous les clients
sudo /opt/geoclic/fleet/geoclic-fleet.sh update --all

# Avec une migration SQL
sudo /opt/geoclic/fleet/geoclic-fleet.sh update --client ville-lyon \
  --migration 025_nouvelle_feature.sql

# Seulement certains services
sudo /opt/geoclic/fleet/geoclic-fleet.sh update --client ville-lyon \
  --services "api portail demandes"</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <h3>Ce que la mise à jour fait</h3>
          <div class="steps">
            <div class="step-item"><span class="step-num">1</span><div><strong>Sauvegarde automatique</strong><p>Backup de la base avant toute modification</p></div></div>
            <div class="step-item"><span class="step-num">2</span><div><strong>Copie du code</strong><p>Seuls les fichiers modifiés sont transférés (rsync)</p></div></div>
            <div class="step-item"><span class="step-num">3</span><div><strong>Migration SQL (si demandé)</strong><p>Applique le fichier SQL sur la base du client</p></div></div>
            <div class="step-item"><span class="step-num">4</span><div><strong>Reconstruction Docker</strong><p>Rebuild et redémarrage des conteneurs</p></div></div>
            <div class="step-item"><span class="step-num">5</span><div><strong>Vérification de santé</strong><p>Teste que l'API répond (HTTP 200)</p></div></div>
          </div>

          <div class="warn-box">
            <strong>Coupure :</strong> La mise à jour provoque une interruption de ~2-5 minutes pendant le rebuild Docker. Préférez les mises à jour en dehors des heures de bureau.
          </div>
        </div>
      </div>

      <!-- ═══ ÉTAT DES SERVEURS ═══ -->
      <div id="section-status" class="section card" :class="{ open: openSection === 'status' }">
        <h2 @click="toggle('status')">
          <span class="section-icon">📊</span> Voir l'état des serveurs
          <span class="chevron">{{ openSection === 'status' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'status'" class="section-content">
          <p>Le <router-link to="/">Dashboard</router-link> affiche l'état de tous vos serveurs en temps réel. Vous pouvez aussi utiliser le terminal :</p>

          <h3>État de tous les serveurs</h3>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh status</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>
          <p>Exemple de résultat :</p>
          <div class="code-block">
            <code>🟢 ville-lyon (lyon.geoclic.fr) - HTTP 200 - SSL: Mar 15 2027 - SSH: true
🟢 ville-nice (nice.geoclic.fr) - HTTP 200 - SSL: Jun 20 2027 - SSH: true
🔴 ville-test (test.geoclic.fr) - HTTP 000 - SSL:  - SSH: false</code>
          </div>

          <h3>Comprendre les indicateurs</h3>
          <table class="help-table">
            <tr><th>Indicateur</th><th>Signification</th></tr>
            <tr><td>🟢 HTTP 200</td><td>Le serveur fonctionne parfaitement</td></tr>
            <tr><td>🔴 HTTP 000</td><td>Le serveur ne répond pas (éteint ou DNS pas configuré)</td></tr>
            <tr><td>🔴 HTTP 502</td><td>Nginx fonctionne mais l'API est plantée</td></tr>
            <tr><td>SSL: date</td><td>Date d'expiration du certificat HTTPS</td></tr>
            <tr><td>SSH: true/false</td><td>Connexion SSH possible ou non</td></tr>
          </table>

          <h3>État détaillé d'un seul client</h3>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh status --client ville-lyon</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>
        </div>
      </div>

      <!-- ═══ BACKUP ═══ -->
      <div id="section-backup" class="section card" :class="{ open: openSection === 'backup' }">
        <h2 @click="toggle('backup')">
          <span class="section-icon">💾</span> Sauvegardes
          <span class="chevron">{{ openSection === 'backup' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'backup'" class="section-content">
          <div class="info-box">
            <strong>Automatique :</strong> Les sauvegardes sont configurées automatiquement tous les jours à 2h du matin sur chaque serveur.
          </div>

          <h3>Contenu des sauvegardes</h3>
          <ul>
            <li><strong>Base de données :</strong> dump SQL + format custom (restauration rapide)</li>
            <li><strong>Photos :</strong> archive tar.gz du volume Docker</li>
            <li><strong>Rétention :</strong> 7 jours quotidien + 4 semaines hebdomadaire</li>
          </ul>

          <h3>Sauvegarde manuelle (interface)</h3>
          <ol>
            <li>Ouvrez le détail du serveur</li>
            <li>Cliquez <strong>Sauvegarder</strong></li>
          </ol>

          <h3>Sauvegarde manuelle (terminal)</h3>
          <div class="code-block">
            <code># Un seul client
sudo /opt/geoclic/fleet/geoclic-fleet.sh backup --client ville-lyon

# Tous les clients
sudo /opt/geoclic/fleet/geoclic-fleet.sh backup --all</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <div class="warn-box">
            <strong>Conseil :</strong> Faites toujours un backup manuel AVANT une mise à jour importante. La commande <code>update</code> le fait automatiquement, mais mieux vaut être prudent.
          </div>
        </div>
      </div>

      <!-- ═══ LOGS ═══ -->
      <div id="section-logs" class="section card" :class="{ open: openSection === 'logs' }">
        <h2 @click="toggle('logs')">
          <span class="section-icon">📝</span> Consulter les logs
          <span class="chevron">{{ openSection === 'logs' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'logs'" class="section-content">
          <p>Les logs permettent de voir ce qu'il se passe dans les conteneurs Docker d'un client. Utile pour diagnostiquer les erreurs.</p>

          <h3>Voir les logs de l'API</h3>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh logs ville-lyon</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <h3>Logs d'un service spécifique</h3>
          <div class="code-block">
            <code># Logs du portail citoyen
sudo /opt/geoclic/fleet/geoclic-fleet.sh logs ville-lyon --service portail

# Logs de nginx (proxy web)
sudo /opt/geoclic/fleet/geoclic-fleet.sh logs ville-lyon --service nginx

# Logs de la base de données
sudo /opt/geoclic/fleet/geoclic-fleet.sh logs ville-lyon --service db

# Afficher les 200 dernières lignes
sudo /opt/geoclic/fleet/geoclic-fleet.sh logs ville-lyon --lines 200</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <h3>Services disponibles</h3>
          <table class="help-table">
            <tr><th>Service</th><th>Conteneur</th><th>Quand consulter</th></tr>
            <tr><td><code>api</code></td><td>geoclic_api</td><td>Erreurs 500, problèmes de login</td></tr>
            <tr><td><code>db</code></td><td>geoclic_db</td><td>Erreurs SQL, problèmes de connexion</td></tr>
            <tr><td><code>nginx</code></td><td>geoclic_nginx</td><td>Erreurs 502, 404, problèmes SSL</td></tr>
            <tr><td><code>portail</code></td><td>geoclic_portail</td><td>Portail citoyen</td></tr>
            <tr><td><code>demandes</code></td><td>geoclic_demandes</td><td>Back-office demandes</td></tr>
            <tr><td><code>admin</code></td><td>geoclic_admin</td><td>GéoClic Data (admin)</td></tr>
            <tr><td><code>sig</code></td><td>geoclic_sig</td><td>SIG Web cartographie</td></tr>
            <tr><td><code>services</code></td><td>geoclic_services</td><td>Services terrain (desktop)</td></tr>
            <tr><td><code>terrain</code></td><td>geoclic_terrain</td><td>PWA terrain (mobile)</td></tr>
          </table>
        </div>
      </div>

      <!-- ═══ REGISTRE ═══ -->
      <div id="section-registry" class="section card" :class="{ open: openSection === 'registry' }">
        <h2 @click="toggle('registry')">
          <span class="section-icon">📃</span> Gérer le registre des serveurs
          <span class="chevron">{{ openSection === 'registry' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'registry'" class="section-content">
          <p>Le registre (<code>clients.conf</code>) contient la liste de tous les serveurs gérés par Fleet.</p>

          <h3>Lister tous les serveurs</h3>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh list</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <h3>Ajouter un serveur manuellement</h3>
          <p>Utile si vous avez un serveur déjà existant que vous voulez gérer avec Fleet :</p>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh add \
  --name ville-nice \
  --domain nice.geoclic.fr \
  --ip 51.210.99.200</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <h3>Retirer un serveur du registre</h3>
          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh remove --name ville-test</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <div class="info-box">
            <strong>Note :</strong> Retirer un serveur du registre ne supprime rien sur le serveur distant. Cela supprime simplement l'entrée dans <code>clients.conf</code>.
          </div>
        </div>
      </div>

      <!-- ═══ SSH DIRECT ═══ -->
      <div id="section-ssh-direct" class="section card" :class="{ open: openSection === 'ssh-direct' }">
        <h2 @click="toggle('ssh-direct')">
          <span class="section-icon">💻</span> Accès SSH direct
          <span class="chevron">{{ openSection === 'ssh-direct' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'ssh-direct'" class="section-content">
          <p>Se connecter directement au terminal d'un serveur client pour exécuter des commandes manuelles.</p>

          <div class="code-block">
            <code>sudo /opt/geoclic/fleet/geoclic-fleet.sh ssh ville-lyon</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <p>Une fois connecté, commandes utiles :</p>
          <div class="code-block">
            <code># Voir l'état des conteneurs
cd /opt/geoclic/deploy && sudo docker-compose ps

# Redémarrer un service
sudo docker-compose restart api

# Accéder à la base de données
sudo docker exec -it geoclic_db psql -U geoclic -d geoclic_db

# Voir l'espace disque
df -h

# Quitter le serveur
exit</code>
            <button class="copy-btn" @click="copyCode($event)">Copier</button>
          </div>

          <div class="warn-box">
            <strong>Attention :</strong> Sur le serveur client, toutes les commandes doivent être préfixées par <code>sudo</code>. Pour quitter, tapez <code>exit</code>.
          </div>
        </div>
      </div>

      <!-- ═══ RÉFÉRENCE DES COMMANDES ═══ -->
      <div id="section-reference" class="section card" :class="{ open: openSection === 'reference' }">
        <h2 @click="toggle('reference')">
          <span class="section-icon">📖</span> Référence des commandes
          <span class="chevron">{{ openSection === 'reference' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'reference'" class="section-content">
          <p>Toutes les commandes disponibles dans <code>geoclic-fleet.sh</code> :</p>

          <div class="cmd-grid cmd-grid-ref">
            <div class="cmd-card"><code>provision</code><p>Installe GéoClic sur un nouveau VPS</p><span class="cmd-badge badge-essential">Essentiel</span></div>
            <div class="cmd-card"><code>init</code><p>Initialise la DB (migrations + admin)</p><span class="cmd-badge badge-essential">Essentiel</span></div>
            <div class="cmd-card"><code>update</code><p>Met à jour un ou tous les serveurs</p><span class="cmd-badge badge-essential">Essentiel</span></div>
            <div class="cmd-card"><code>status</code><p>Vérifie l'état de santé des serveurs</p><span class="cmd-badge badge-gestion">Gestion</span></div>
            <div class="cmd-card"><code>list</code><p>Liste les serveurs enregistrés</p><span class="cmd-badge badge-gestion">Gestion</span></div>
            <div class="cmd-card"><code>add</code><p>Ajoute un serveur au registre</p><span class="cmd-badge badge-gestion">Gestion</span></div>
            <div class="cmd-card"><code>remove</code><p>Retire un serveur du registre</p><span class="cmd-badge badge-gestion">Gestion</span></div>
            <div class="cmd-card"><code>ssh</code><p>Connexion SSH directe à un serveur</p><span class="cmd-badge badge-debug">Debug</span></div>
            <div class="cmd-card"><code>logs</code><p>Consulte les logs Docker d'un serveur</p><span class="cmd-badge badge-debug">Debug</span></div>
            <div class="cmd-card"><code>backup</code><p>Déclenche une sauvegarde manuelle</p><span class="cmd-badge badge-gestion">Gestion</span></div>
            <div class="cmd-card"><code>ssh-key</code><p>Génère ou affiche la clé SSH Fleet</p><span class="cmd-badge badge-gestion">Gestion</span></div>
            <div class="cmd-card"><code>test-ssh</code><p>Teste la connexion SSH vers une IP</p><span class="cmd-badge badge-debug">Debug</span></div>
            <div class="cmd-card"><code>task-status</code><p>Vérifie l'avancement d'une tâche</p><span class="cmd-badge badge-debug">Debug</span></div>
            <div class="cmd-card"><code>task-log</code><p>Consulte le log d'une tâche passée</p><span class="cmd-badge badge-debug">Debug</span></div>
            <div class="cmd-card"><code>aide</code><p>Ouvre le guide interactif HTML</p><span class="cmd-badge badge-gestion">Gestion</span></div>
            <div class="cmd-card"><code>help</code><p>Aide rapide dans le terminal</p><span class="cmd-badge badge-gestion">Gestion</span></div>
          </div>
        </div>
      </div>

      <!-- ═══ DÉPANNAGE ═══ -->
      <div id="section-troubleshoot" class="section card" :class="{ open: openSection === 'troubleshoot' }">
        <h2 @click="toggle('troubleshoot')">
          <span class="section-icon">🔧</span> Dépannage
          <span class="chevron">{{ openSection === 'troubleshoot' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'troubleshoot'" class="section-content">
          <div class="faq-item">
            <h3>Le provision échoue à l'étape SSH</h3>
            <p><strong>Cause :</strong> La clé SSH Fleet n'est pas autorisée sur le VPS.</p>
            <ol>
              <li>Vérifiez que la clé est générée : <code>geoclic-fleet.sh ssh-key show</code></li>
              <li>Connectez-vous au VPS et ajoutez la clé dans <code>/home/ubuntu/.ssh/authorized_keys</code></li>
              <li>Testez : <code>geoclic-fleet.sh test-ssh IP ubuntu</code></li>
            </ol>
          </div>

          <div class="faq-item">
            <h3>Le serveur est marqué 🔴 (hors ligne)</h3>
            <p><strong>Causes possibles :</strong></p>
            <ul>
              <li>Le VPS est éteint → Vérifier dans l'espace client OVH</li>
              <li>Docker est arrêté → Consulter les logs depuis le dashboard</li>
              <li>Le domaine ne pointe plus vers la bonne IP → Vérifier le DNS</li>
              <li>Le certificat SSL a expiré → Normalement renouvelé automatiquement</li>
            </ul>
          </div>

          <div class="faq-item">
            <h3>La connexion SSH échoue</h3>
            <ul>
              <li>Vérifiez que la clé SSH est dans <code>~/.ssh/authorized_keys</code> sur le VPS</li>
              <li>Vérifiez le port SSH (par défaut 22)</li>
              <li>Vérifiez que le pare-feu OVH ne bloque pas le port SSH</li>
            </ul>
          </div>

          <div class="faq-item">
            <h3>Erreur "KeyError: ContainerConfig"</h3>
            <p>Cache Docker corrompu. Connectez-vous en SSH et exécutez :</p>
            <div class="code-block">
              <code>cd /opt/geoclic/deploy
sudo docker-compose down
sudo docker container prune -f
sudo docker-compose up -d --build</code>
              <button class="copy-btn" @click="copyCode($event)">Copier</button>
            </div>
          </div>

          <div class="faq-item">
            <h3>Le site affiche "502 Bad Gateway"</h3>
            <ul>
              <li>Vérifiez les logs : <code>geoclic-fleet.sh logs NOM --service api</code></li>
              <li>Si l'API a planté : <code>sudo docker-compose restart api</code></li>
              <li>Si le problème persiste : <code>sudo docker-compose down && sudo docker-compose up -d</code></li>
            </ul>
          </div>

          <div class="faq-item">
            <h3>Le certificat SSL ne s'installe pas</h3>
            <ul>
              <li>Le domaine doit pointer vers l'IP du VPS (vérifier avec <code>nslookup</code>)</li>
              <li>Le port 80 doit être accessible</li>
              <li>Let's Encrypt a une limite de 5 certificats par domaine par semaine</li>
            </ul>
          </div>

          <div class="faq-item">
            <h3>L'init échoue sur une migration SQL</h3>
            <ul>
              <li>Si le message dit "already exists" → C'est OK, la migration est déjà passée</li>
              <li>Si c'est une autre erreur → Notez le numéro de migration et contactez le support</li>
            </ul>
          </div>

          <div class="faq-item">
            <h3>Les utilisateurs voient l'ancienne version après mise à jour</h3>
            <p>Le cache du navigateur garde l'ancienne version. Solution pour les utilisateurs :</p>
            <ul>
              <li>F12 → Application → Stockage → "Effacer les données du site"</li>
              <li>Ou ouvrir en navigation privée (Ctrl+Shift+N)</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- ═══ ARCHITECTURE ═══ -->
      <div id="section-architecture" class="section card" :class="{ open: openSection === 'architecture' }">
        <h2 @click="toggle('architecture')">
          <span class="section-icon">🏗️</span> Architecture technique
          <span class="chevron">{{ openSection === 'architecture' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'architecture'" class="section-content">
          <pre class="arch-diagram">
geoclic.fr (serveur maître)
│
├── GéoClic Suite (son propre client)
│   ├── API + 7 apps frontend
│   └── PostgreSQL + PostGIS
│
├── Fleet Manager
│   ├── Dashboard web (/fleet/)
│   ├── API Python (/api/fleet/)
│   └── Script bash (geoclic-fleet.sh)
│       ├── provision  →  Installe Docker + code + SSL
│       ├── init       →  25 migrations SQL + super admin
│       └── update     →  rsync + rebuild Docker
│
├── rsync ──→ ville-lyon.geoclic.fr
├── rsync ──→ ville-marseille.geoclic.fr
└── rsync ──→ ...
          </pre>

          <h3>Comment ça fonctionne</h3>
          <ul>
            <li><strong>Le code source</strong> est sur le serveur maître (<code>/opt/geoclic/</code>)</li>
            <li><strong>rsync</strong> copie le code vers chaque serveur client via SSH</li>
            <li>Chaque client a sa <strong>propre base de données</strong> (isolation totale)</li>
            <li>Chaque client a son <strong>propre certificat SSL</strong></li>
            <li>Les clients ne communiquent jamais entre eux</li>
          </ul>

          <h3>10 conteneurs Docker par serveur</h3>
          <table class="help-table">
            <thead>
              <tr><th>Conteneur</th><th>Rôle</th></tr>
            </thead>
            <tbody>
              <tr><td>geoclic_db</td><td>Base de données PostgreSQL + PostGIS</td></tr>
              <tr><td>geoclic_api</td><td>API FastAPI (backend)</td></tr>
              <tr><td>geoclic_admin</td><td>GéoClic Data (administration)</td></tr>
              <tr><td>geoclic_portail</td><td>Portail citoyen (signalements publics)</td></tr>
              <tr><td>geoclic_demandes</td><td>Back-office gestion des demandes</td></tr>
              <tr><td>geoclic_mobile</td><td>PWA relevé terrain</td></tr>
              <tr><td>geoclic_sig</td><td>Cartographie SIG</td></tr>
              <tr><td>geoclic_services</td><td>Services terrain (desktop)</td></tr>
              <tr><td>geoclic_terrain</td><td>Services terrain (mobile PWA)</td></tr>
              <tr><td>geoclic_nginx</td><td>Reverse proxy SSL</td></tr>
            </tbody>
          </table>

          <h3>Flux d'installation d'un nouveau client</h3>
          <table class="help-table">
            <thead>
              <tr><th>Étape</th><th>Commande</th><th>Ce qui se passe</th></tr>
            </thead>
            <tbody>
              <tr><td>1</td><td><code>provision</code></td><td>Docker installé, code copié, SSL obtenu, conteneurs démarrés</td></tr>
              <tr><td>2</td><td><code>init</code></td><td>25 migrations SQL appliquées, super admin créé, branding configuré</td></tr>
              <tr><td>3</td><td><em>automatique</em></td><td>Le client se connecte → wizard d'onboarding (catégories, services, email)</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ═══ GLOSSAIRE ═══ -->
      <div id="section-glossaire" class="section card" :class="{ open: openSection === 'glossaire' }">
        <h2 @click="toggle('glossaire')">
          <span class="section-icon">📚</span> Glossaire
          <span class="badge-new">Nouveau</span>
          <span class="chevron">{{ openSection === 'glossaire' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'glossaire'" class="section-content">
          <table class="help-table glossaire-table">
            <thead>
              <tr><th style="width:160px">Terme</th><th>Définition</th></tr>
            </thead>
            <tbody>
              <tr><td><strong>VPS</strong></td><td>Virtual Private Server. Un ordinateur distant loué chez un hébergeur, accessible 24h/24 via internet.</td></tr>
              <tr><td><strong>SSH</strong></td><td>Secure Shell. Un moyen sécurisé de se connecter à un ordinateur distant pour y taper des commandes.</td></tr>
              <tr><td><strong>DNS</strong></td><td>Domain Name System. L'annuaire d'internet qui traduit les noms (lyon.geoclic.fr) en adresses IP.</td></tr>
              <tr><td><strong>SSL / HTTPS</strong></td><td>Le cadenas vert dans le navigateur. Chiffre les communications entre le navigateur et le serveur.</td></tr>
              <tr><td><strong>Docker</strong></td><td>Logiciel qui empaquète les applications dans des "conteneurs" isolés. GéoClic en utilise 10 par serveur.</td></tr>
              <tr><td><strong>Conteneur</strong></td><td>Une boîte isolée qui fait tourner une application. Chaque module GéoClic a son conteneur.</td></tr>
              <tr><td><strong>Migration SQL</strong></td><td>Fichier qui modifie la structure de la base de données (tables, colonnes...). GéoClic en a 25.</td></tr>
              <tr><td><strong>rsync</strong></td><td>Outil qui copie des fichiers entre deux serveurs en ne transférant que les changements.</td></tr>
              <tr><td><strong>Let's Encrypt</strong></td><td>Service gratuit qui fournit des certificats SSL (HTTPS), renouvelés automatiquement tous les 3 mois.</td></tr>
              <tr><td><strong>Super admin</strong></td><td>Le compte utilisateur principal qui a tous les droits sur toutes les applications GéoClic.</td></tr>
              <tr><td><strong>Branding</strong></td><td>Personnalisation visuelle (logo, couleurs, nom) pour chaque collectivité cliente.</td></tr>
              <tr><td><strong>Onboarding</strong></td><td>Assistant qui guide le client lors de sa première connexion (catégories, services, email).</td></tr>
              <tr><td><strong>PWA</strong></td><td>Progressive Web App. Application web installable sur mobile comme une app native (sans App Store).</td></tr>
              <tr><td><strong>Provision</strong></td><td>Action de préparer un serveur vierge : installer tout le nécessaire pour que GéoClic fonctionne.</td></tr>
              <tr><td><strong>Clé SSH</strong></td><td>Paire de fichiers (privé + public) qui remplace le mot de passe pour se connecter à un serveur.</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ═══ FAQ ═══ -->
      <div id="section-faq" class="section card" :class="{ open: openSection === 'faq' }">
        <h2 @click="toggle('faq')">
          <span class="section-icon">❓</span> FAQ
          <span class="chevron">{{ openSection === 'faq' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'faq'" class="section-content">
          <div class="faq-item">
            <h3>Est-ce que les clients voient le Fleet Manager ?</h3>
            <p>Non. Le Fleet Manager n'existe que sur le serveur maître (geoclic.fr). Les clients n'y ont pas accès.</p>
          </div>
          <div class="faq-item">
            <h3>Que se passe-t-il si le serveur maître tombe en panne ?</h3>
            <p>Les serveurs clients continuent de fonctionner normalement. Vous ne pourrez simplement pas faire de mises à jour tant que le maître n'est pas rétabli.</p>
          </div>
          <div class="faq-item">
            <h3>Combien de clients peut-on gérer ?</h3>
            <p>Pas de limite technique. La seule contrainte est le temps de mise à jour (~5-10 min par client). Avec 10 clients, une mise à jour globale prend environ 1h.</p>
          </div>
          <div class="faq-item">
            <h3>Les données d'un client sont-elles isolées ?</h3>
            <p>Oui, totalement. Chaque client a son propre serveur, sa propre base de données, ses propres photos. Aucune donnée n'est partagée.</p>
          </div>
          <div class="faq-item">
            <h3>Puis-je mettre à jour seulement certains services ?</h3>
            <p>Oui : <code>geoclic-fleet.sh update --client ville-lyon --services "api portail"</code></p>
          </div>
          <div class="faq-item">
            <h3>Puis-je appliquer une migration SQL seule ?</h3>
            <p>Oui : <code>geoclic-fleet.sh update --client ville-lyon --migration 025_feature.sql</code></p>
          </div>
          <div class="faq-item">
            <h3>Combien de temps prend chaque opération ?</h3>
            <table class="help-table">
              <tr><th>Opération</th><th>Durée</th></tr>
              <tr><td>provision (première installation)</td><td>10-20 minutes</td></tr>
              <tr><td>init (migrations + admin)</td><td>1-3 minutes</td></tr>
              <tr><td>update (mise à jour code)</td><td>5-10 minutes</td></tr>
              <tr><td>backup</td><td>&lt; 1 minute</td></tr>
              <tr><td>status</td><td>&lt; 30 secondes</td></tr>
            </table>
          </div>
          <div class="faq-item">
            <h3>Comment charger les données de démonstration ?</h3>
            <p>Lors de l'init, ajoutez <code>--with-demo</code>. Ou après coup :</p>
            <div class="code-block">
              <code>sudo docker exec -i geoclic_db psql -U geoclic -d geoclic_db &lt; /opt/geoclic/database/demo_data.sql</code>
              <button class="copy-btn" @click="copyCode($event)">Copier</button>
            </div>
          </div>
          <div class="faq-item">
            <h3>Comment supprimer complètement un serveur client ?</h3>
            <ol>
              <li>Backup : <code>geoclic-fleet.sh backup --client NOM</code></li>
              <li>SSH : <code>geoclic-fleet.sh ssh NOM</code></li>
              <li>Arrêter : <code>sudo docker-compose down -v</code></li>
              <li>Supprimer : <code>sudo rm -rf /opt/geoclic</code></li>
              <li>Quitter : <code>exit</code></li>
              <li>Retirer du registre : <code>geoclic-fleet.sh remove --name NOM</code></li>
              <li>Supprimer le VPS chez l'hébergeur + entrée DNS</li>
            </ol>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.help-page {
  max-width: 880px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 4px;
}

/* TOC */
.toc {
  margin-bottom: 20px;
}

.toc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.toc-header h3 {
  font-size: 15px;
}

.search-wrap {
  position: relative;
}

.search-input {
  padding: 6px 12px 6px 30px;
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 13px;
  width: 200px;
  outline: none;
  transition: border-color 0.2s, width 0.2s;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E") no-repeat 10px center;
}

.search-input:focus {
  border-color: var(--primary);
  width: 260px;
}

.toc-groups {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.toc-group {
  flex: 1;
  min-width: 160px;
}

.toc-group-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  font-weight: 600;
  display: block;
  margin-bottom: 4px;
}

.toc-group ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.toc-group a {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  color: var(--text);
  text-decoration: none;
  font-size: 13px;
  transition: all 0.15s;
}

.toc-group a:hover {
  background: var(--primary);
  color: white;
}

.toc-group a.active {
  background: rgba(26, 115, 232, 0.1);
  color: var(--primary);
  font-weight: 500;
}

.toc-icon {
  font-size: 14px;
}

.badge-new-sm {
  background: #2e7d32;
  color: white;
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 8px;
  font-weight: 600;
  margin-left: auto;
}

/* Sections */
.sections {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section h2 {
  font-size: 17px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  user-select: none;
}

.section h2:hover {
  color: var(--primary);
}

.section-icon {
  font-size: 20px;
}

.chevron {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-secondary);
}

.badge-new {
  background: var(--accent, #2e7d32);
  color: white;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.section-content {
  padding-top: 16px;
  border-top: 1px solid var(--border);
  margin-top: 12px;
  font-size: 14px;
  line-height: 1.7;
}

.section-content h3 {
  font-size: 15px;
  margin: 16px 0 8px;
}

.section-content h3:first-child {
  margin-top: 0;
}

.section-content ol,
.section-content ul {
  padding-left: 20px;
  margin-bottom: 12px;
}

.section-content li {
  margin-bottom: 6px;
}

.section-content code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}

.section-content a {
  color: var(--primary);
}

/* Workflow visuel */
.workflow {
  display: flex;
  align-items: center;
  gap: 0;
  margin: 20px 0;
  flex-wrap: wrap;
  justify-content: center;
}

.wf-step {
  background: white;
  border: 2px solid var(--primary, #1a73e8);
  border-radius: 12px;
  padding: 12px 14px;
  text-align: center;
  min-width: 110px;
  font-size: 13px;
}

.wf-step .wf-icon {
  font-size: 24px;
  display: block;
  margin-bottom: 4px;
}

.wf-step strong {
  font-size: 12px;
  display: block;
}

.wf-step p {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.wf-step-new {
  border-color: var(--accent, #2e7d32);
  background: #e8f5e9;
}

.wf-step-done {
  border-color: var(--accent, #2e7d32);
  background: #e8f5e9;
}

.wf-arrow {
  font-size: 20px;
  color: var(--primary, #1a73e8);
  padding: 0 4px;
  flex-shrink: 0;
}

/* Command grid */
.cmd-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  margin: 16px 0;
}

.cmd-grid-ref {
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
}

.cmd-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.cmd-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(26, 35, 126, 0.08);
  transform: translateY(-1px);
}

.cmd-card code {
  font-weight: 700;
  color: var(--primary);
  font-size: 14px;
  background: none;
  padding: 0;
}

.cmd-card p {
  color: var(--text-secondary);
  margin: 4px 0 8px;
  font-size: 12px;
}

.cmd-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.badge-essential {
  background: #e8f0fe;
  color: #1a56db;
}

.badge-gestion {
  background: #fef7e0;
  color: #b45309;
}

.badge-debug {
  background: #f3e8ff;
  color: #7c3aed;
}

/* Steps */
.steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 16px 0;
}

.step-item {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.step-num {
  width: 32px;
  height: 32px;
  background: var(--primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 15px;
  flex-shrink: 0;
}

.step-item p {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 2px;
}

/* Boxes */
.info-box {
  background: #e3f2fd;
  color: #1565c0;
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 14px;
  margin: 12px 0;
}

.warn-box {
  background: #fff3e0;
  color: #e65100;
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 14px;
  margin: 12px 0;
}

.success-box {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 14px;
  margin: 12px 0;
}

/* Code blocks */
.code-block {
  background: #1a1a2e;
  border-radius: 6px;
  padding: 14px 50px 14px 16px;
  margin: 10px 0;
  overflow-x: auto;
  position: relative;
}

.code-block code {
  color: #a4e400;
  background: none;
  padding: 0;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: rgba(255, 255, 255, 0.6);
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.copy-btn.copied {
  background: #2e7d32;
  color: #fff;
}

/* Tables */
.help-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}

.help-table th,
.help-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.help-table th {
  background: var(--bg);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.glossaire-table td:first-child {
  white-space: nowrap;
}

/* FAQ */
.faq-item {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.faq-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.faq-item h3 {
  font-size: 14px !important;
  color: var(--primary);
}

/* Architecture diagram */
.arch-diagram {
  background: #1a1a2e;
  color: #a4e400;
  padding: 16px;
  border-radius: 6px;
  font-family: 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
}
</style>
