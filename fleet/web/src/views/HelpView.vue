<script setup lang="ts">
import { ref } from 'vue'

const openSection = ref('quick-start')

function toggle(id: string) {
  openSection.value = openSection.value === id ? '' : id
}
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

    <!-- Table des matières -->
    <div class="toc card">
      <h3>Sommaire</h3>
      <ul>
        <li><a href="#" @click.prevent="toggle('quick-start')">Démarrage rapide</a></li>
        <li><a href="#" @click.prevent="toggle('new-vps')">Préparer un nouveau VPS (OVH)</a></li>
        <li><a href="#" @click.prevent="toggle('dns')">Configurer le nom de domaine (DNS)</a></li>
        <li><a href="#" @click.prevent="toggle('provisioning')">Installer GéoClic sur un nouveau serveur</a></li>
        <li><a href="#" @click.prevent="toggle('update')">Mettre à jour les serveurs</a></li>
        <li><a href="#" @click.prevent="toggle('backup')">Sauvegardes</a></li>
        <li><a href="#" @click.prevent="toggle('troubleshoot')">Dépannage</a></li>
        <li><a href="#" @click.prevent="toggle('architecture')">Architecture technique</a></li>
        <li><a href="#" @click.prevent="toggle('faq')">FAQ</a></li>
      </ul>
    </div>

    <!-- Sections -->
    <div class="sections">

      <!-- DÉMARRAGE RAPIDE -->
      <div class="section card" :class="{ open: openSection === 'quick-start' }">
        <h2 @click="toggle('quick-start')">
          <span class="section-icon">🚀</span> Démarrage rapide
          <span class="chevron">{{ openSection === 'quick-start' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'quick-start'" class="section-content">
          <p>Le Fleet Manager vous permet de gérer tous vos serveurs GéoClic depuis cette interface. Voici le flux pour ajouter un nouveau client :</p>
          <div class="steps">
            <div class="step-item">
              <span class="step-num">1</span>
              <div>
                <strong>Commander un VPS chez OVH</strong>
                <p>~5€/mois pour un VPS Starter (suffisant pour une petite commune)</p>
              </div>
            </div>
            <div class="step-item">
              <span class="step-num">2</span>
              <div>
                <strong>Pointer le domaine vers le VPS</strong>
                <p>Créer un enregistrement DNS A : ville.geoclic.fr → IP du VPS</p>
              </div>
            </div>
            <div class="step-item">
              <span class="step-num">3</span>
              <div>
                <strong>Copier la clé SSH sur le VPS</strong>
                <p>La clé est affichée dans l'écran "Ajouter un serveur"</p>
              </div>
            </div>
            <div class="step-item">
              <span class="step-num">4</span>
              <div>
                <strong>Cliquer "Ajouter un serveur" dans le dashboard</strong>
                <p>Remplir les infos, tester SSH, lancer l'installation. C'est automatique !</p>
              </div>
            </div>
          </div>
          <div class="info-box">
            <strong>Temps total estimé :</strong> ~20 minutes (dont ~15 min d'installation automatique)
          </div>
        </div>
      </div>

      <!-- NOUVEAU VPS -->
      <div class="section card" :class="{ open: openSection === 'new-vps' }">
        <h2 @click="toggle('new-vps')">
          <span class="section-icon">🖥️</span> Préparer un nouveau VPS (OVH)
          <span class="chevron">{{ openSection === 'new-vps' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'new-vps'" class="section-content">
          <h3>Étape 1 : Commander le VPS</h3>
          <ol>
            <li>Allez sur <a href="https://www.ovhcloud.com/fr/vps/" target="_blank">OVH VPS</a></li>
            <li>Choisissez <strong>VPS Starter</strong> (2 Go RAM, 20 Go SSD) minimum</li>
            <li>Système : <strong>Ubuntu 24.04</strong> (ou 22.04)</li>
            <li>Localisaction : <strong>France</strong> (Gravelines ou Strasbourg)</li>
            <li>Options : aucune nécessaire</li>
          </ol>

          <h3>Étape 2 : Pré-installer la clé SSH chez OVH (recommandé)</h3>
          <p>Pour ne plus avoir à copier manuellement la clé SSH sur chaque nouveau VPS, enregistrez-la une fois pour toutes dans votre espace OVH :</p>
          <ol>
            <li>Connectez-vous à l'<a href="https://www.ovh.com/manager/" target="_blank">espace client OVH</a></li>
            <li>Allez dans <strong>Public Cloud</strong> ou <strong>Bare Metal Cloud &gt; Clés SSH</strong></li>
            <li>Cliquez <strong>Ajouter une clé SSH</strong></li>
            <li>Nom : <strong>geoclic-fleet</strong></li>
            <li>Clé : collez la clé SSH affichée dans le <router-link to="/">Dashboard</router-link> (section "Clé SSH Fleet")</li>
            <li>Validez</li>
          </ol>
          <div class="info-box">
            <strong>Résultat :</strong> Lors de la commande d'un nouveau VPS, sélectionnez la clé "geoclic-fleet" dans les options SSH. Le VPS sera livré avec la clé déjà installée — aucune manipulation manuelle nécessaire !
          </div>

          <h3>Alternative : Ajouter la clé après la commande</h3>
          <p>Si vous n'avez pas pré-installé la clé, vous pouvez le faire après la livraison du VPS via l'espace client OVH ou en vous connectant en SSH avec le mot de passe.</p>

          <h3>Étape 3 : Récupérer l'IP</h3>
          <p>Une fois le VPS livré (quelques minutes), notez l'adresse IP dans votre espace client OVH.</p>

          <h3>Recommandation VPS par taille de commune</h3>
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

      <!-- DNS -->
      <div class="section card" :class="{ open: openSection === 'dns' }">
        <h2 @click="toggle('dns')">
          <span class="section-icon">🌐</span> Configurer le nom de domaine (DNS)
          <span class="chevron">{{ openSection === 'dns' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'dns'" class="section-content">
          <p>Pour que <code>ville-lyon.geoclic.fr</code> pointe vers le bon VPS, vous devez créer un enregistrement DNS.</p>

          <h3>Option A : Sous-domaine de geoclic.fr (recommandé)</h3>
          <ol>
            <li>Connectez-vous à l'espace client OVH</li>
            <li>Allez dans <strong>Noms de domaine &gt; geoclic.fr &gt; Zone DNS</strong></li>
            <li>Cliquez <strong>Ajouter une entrée</strong></li>
            <li>Type : <strong>A</strong></li>
            <li>Sous-domaine : <strong>ville-lyon</strong> (le nom du client)</li>
            <li>Cible : <strong>51.210.42.100</strong> (l'IP du VPS)</li>
            <li>Validez et attendez ~5 minutes la propagation</li>
          </ol>

          <h3>Option B : Domaine du client</h3>
          <p>Si le client a son propre domaine (ex: signalements.ville-lyon.fr), demandez-lui de créer un enregistrement A pointant vers l'IP du VPS.</p>

          <div class="info-box">
            <strong>Vérification :</strong> Après avoir ajouté l'enregistrement, vous pouvez vérifier avec :
            <code>nslookup ville-lyon.geoclic.fr</code> ou <a href="https://dnschecker.org/" target="_blank">dnschecker.org</a>
          </div>
        </div>
      </div>

      <!-- PROVISIONING -->
      <div class="section card" :class="{ open: openSection === 'provisioning' }">
        <h2 @click="toggle('provisioning')">
          <span class="section-icon">⚡</span> Installer GéoClic sur un nouveau serveur
          <span class="chevron">{{ openSection === 'provisioning' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'provisioning'" class="section-content">
          <p>Une fois le VPS commandé, le domaine configuré et la clé SSH ajoutée, l'installation est entièrement automatique :</p>
          <ol>
            <li>Cliquez <router-link to="/add"><strong>+ Ajouter un serveur</strong></router-link></li>
            <li>Remplissez : domaine, IP, email</li>
            <li>Testez la connexion SSH (bouton vert = OK)</li>
            <li>Confirmez et lancez l'installation</li>
          </ol>

          <h3>Ce que l'installation fait automatiquement :</h3>
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
            <strong>Important :</strong> Le domaine DOIT pointer vers l'IP du VPS AVANT l'installation (nécessaire pour le certificat SSL).
          </div>
        </div>
      </div>

      <!-- MISE À JOUR -->
      <div class="section card" :class="{ open: openSection === 'update' }">
        <h2 @click="toggle('update')">
          <span class="section-icon">🔄</span> Mettre à jour les serveurs
          <span class="chevron">{{ openSection === 'update' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'update'" class="section-content">
          <p>Quand vous modifiez le code de GéoClic (nouvelle fonctionnalité, correction de bug), vous devez pousser la mise à jour vers vos serveurs clients.</p>

          <h3>Mettre à jour un seul serveur</h3>
          <ol>
            <li>Cliquez sur le serveur dans le dashboard</li>
            <li>Cliquez <strong>Mettre à jour</strong></li>
            <li>Attendez la fin de l'opération (~5-10 min)</li>
          </ol>

          <h3>Mettre à jour TOUS les serveurs</h3>
          <ol>
            <li>Depuis le dashboard, cliquez <strong>Tout mettre à jour</strong></li>
            <li>Les serveurs sont mis à jour les uns après les autres</li>
          </ol>

          <h3>Ce que la mise à jour fait :</h3>
          <ol>
            <li>Sauvegarde de la base de données (sécurité)</li>
            <li>Copie du nouveau code via rsync</li>
            <li>Application des migrations SQL (si spécifiée)</li>
            <li>Reconstruction des conteneurs Docker</li>
            <li>Vérification que le site répond (HTTP 200)</li>
          </ol>

          <div class="info-box">
            <strong>Pas de coupure :</strong> Le site reste accessible pendant la copie du code. La coupure est d'environ 1-2 minutes pendant le rebuild Docker.
          </div>
        </div>
      </div>

      <!-- BACKUP -->
      <div class="section card" :class="{ open: openSection === 'backup' }">
        <h2 @click="toggle('backup')">
          <span class="section-icon">💾</span> Sauvegardes
          <span class="chevron">{{ openSection === 'backup' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'backup'" class="section-content">
          <p>Chaque serveur a une sauvegarde automatique quotidienne à 2h du matin. Vous pouvez aussi déclencher une sauvegarde manuelle depuis le dashboard.</p>

          <h3>Sauvegarde automatique (incluse)</h3>
          <ul>
            <li>Base de données : dump SQL + format custom (pour restauration rapide)</li>
            <li>Photos : archive tar.gz</li>
            <li>Rétention : 7 jours quotidien + 4 semaines hebdomadaire</li>
          </ul>

          <h3>Sauvegarde manuelle</h3>
          <ol>
            <li>Ouvrez le détail du serveur</li>
            <li>Cliquez <strong>Sauvegarder</strong></li>
          </ol>
        </div>
      </div>

      <!-- DÉPANNAGE -->
      <div class="section card" :class="{ open: openSection === 'troubleshoot' }">
        <h2 @click="toggle('troubleshoot')">
          <span class="section-icon">🔧</span> Dépannage
          <span class="chevron">{{ openSection === 'troubleshoot' ? '▼' : '▶' }}</span>
        </h2>
        <div v-show="openSection === 'troubleshoot'" class="section-content">
          <div class="faq-item">
            <h3>Le serveur est marqué 🔴 (hors ligne)</h3>
            <p><strong>Causes possibles :</strong></p>
            <ul>
              <li>Le VPS est éteint → Vérifier dans l'espace client OVH</li>
              <li>Docker est arrêté → Vérifier les logs depuis le dashboard</li>
              <li>Le domaine ne pointe plus vers la bonne IP → Vérifier le DNS</li>
              <li>Le certificat SSL a expiré → Le renouvellement est normalement automatique</li>
            </ul>
          </div>

          <div class="faq-item">
            <h3>La connexion SSH échoue</h3>
            <ul>
              <li>Vérifiez que la clé SSH fleet est bien dans <code>~/.ssh/authorized_keys</code> sur le VPS</li>
              <li>Vérifiez que le port SSH est le bon (par défaut 22)</li>
              <li>Vérifiez que le pare-feu OVH ne bloque pas le port SSH</li>
            </ul>
          </div>

          <div class="faq-item">
            <h3>Le certificat SSL ne s'installe pas</h3>
            <ul>
              <li>Le domaine doit pointer vers l'IP du VPS (vérifiez avec nslookup)</li>
              <li>Le port 80 doit être accessible (pas de pare-feu qui bloque)</li>
              <li>Let's Encrypt a une limite de 5 certificats par domaine par semaine</li>
            </ul>
          </div>

          <div class="faq-item">
            <h3>La mise à jour échoue</h3>
            <ul>
              <li>Vérifiez les logs dans le détail du serveur</li>
              <li>Problème fréquent : espace disque plein → faire le ménage Docker avec <code>docker system prune</code></li>
              <li>La base de données est toujours sauvegardée avant la mise à jour (pas de risque de perte)</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- ARCHITECTURE -->
      <div class="section card" :class="{ open: openSection === 'architecture' }">
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
            <li>Les clients ne se parlent jamais entre eux</li>
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
        </div>
      </div>

      <!-- FAQ -->
      <div class="section card" :class="{ open: openSection === 'faq' }">
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
            <p>Il n'y a pas de limite technique. La seule contrainte est le temps de mise à jour (chaque client prend ~5-10 min). Avec 10 clients, une mise à jour globale prend environ 1h.</p>
          </div>
          <div class="faq-item">
            <h3>Les données d'un client sont-elles isolées ?</h3>
            <p>Oui, totalement. Chaque client a son propre serveur, sa propre base de données, ses propres photos. Aucune donnée n'est partagée.</p>
          </div>
          <div class="faq-item">
            <h3>Puis-je mettre à jour seulement certains services ?</h3>
            <p>Oui, via le terminal. Exemple : <code>geoclic-fleet.sh update --client ville-lyon --services "api portail"</code></p>
          </div>
          <div class="faq-item">
            <h3>Puis-je appliquer une migration SQL ?</h3>
            <p>Oui, via le terminal : <code>geoclic-fleet.sh update --client ville-lyon --migration 023_new_feature.sql</code></p>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.help-page {
  max-width: 800px;
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

.toc {
  margin-bottom: 20px;
}

.toc h3 {
  font-size: 15px;
  margin-bottom: 8px;
}

.toc ul {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.toc a {
  display: inline-block;
  padding: 4px 12px;
  background: var(--bg);
  border-radius: 16px;
  color: var(--primary);
  text-decoration: none;
  font-size: 13px;
  transition: all 0.2s;
}

.toc a:hover {
  background: var(--primary);
  color: white;
}

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
