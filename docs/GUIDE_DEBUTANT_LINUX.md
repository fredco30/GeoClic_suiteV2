# Guide Linux pour Grands Débutants

> Ce guide est fait pour quelqu'un qui n'a JAMAIS utilisé Linux.
> Suivez les étapes dans l'ordre, sans sauter aucune ligne.

---

## Tu as une interface graphique Ubuntu (VNC) !

Bonne nouvelle ! Tu as accès à une interface graphique Ubuntu via VNC.
C'est **comme Windows** : tu as un bureau, des fenêtres, une souris, etc.

---

## Différences Windows vs Ubuntu (avec interface graphique)

| Windows | Ubuntu |
|---------|--------|
| Menu Démarrer | Bouton "Activités" en haut à gauche |
| Explorateur de fichiers | "Fichiers" (icône dossier) |
| Invite de commandes | "Terminal" |
| .exe pour installer | "Logithèque Ubuntu" ou commandes |
| `C:\Users\...` | `/home/ubuntu/...` |

**Ubuntu avec interface graphique ressemble beaucoup à Windows !**

---

## Comment accéder à ton serveur

### OPTION 1 : Via VNC (Interface graphique - RECOMMANDÉ)

Tu as VNC configuré sur le port 5901. Voici comment te connecter :

**Sur Windows :**
1. Télécharge un client VNC gratuit : [RealVNC Viewer](https://www.realvnc.com/fr/connect/download/viewer/)
2. Installe-le et ouvre-le
3. Dans la barre d'adresse, tape : `51.210.8.158:5901`
4. Entre ton mot de passe VNC
5. **Tu vois le bureau Ubuntu !**

**Avantages du VNC :**
- Interface graphique comme Windows
- Tu peux copier-coller facilement
- Tu vois ce qui se passe visuellement

### OPTION 2 : Via SSH (Ligne de commande)

Si tu préfères la ligne de commande depuis ton PC :

**Sur Windows 10/11 :**
1. Appuie sur la touche Windows
2. Tape `cmd` ou `powershell`
3. Clique sur "Invite de commandes" ou "PowerShell"

**Sur Mac :**
1. Appuie sur Cmd + Espace
2. Tape `Terminal`
3. Appuie sur Entrée

**Puis tape :**
```
ssh ubuntu@51.210.8.158
```

**La première fois**, il va te demander :
```
Are you sure you want to continue connecting (yes/no)?
```
Tape `yes` et appuie sur Entrée.

Ensuite il demande le mot de passe. **ATTENTION** : quand tu tapes le mot de passe, RIEN ne s'affiche (pas d'étoiles, rien). C'est normal !

---

## Ouvrir le Terminal sur Ubuntu (via VNC)

Une fois connecté en VNC et que tu vois le bureau Ubuntu :

### Méthode 1 : Raccourci clavier
Appuie sur **Ctrl + Alt + T** → Le terminal s'ouvre !

### Méthode 2 : Par le menu
1. Clique sur **"Activités"** (en haut à gauche)
2. Tape **"Terminal"** dans la barre de recherche
3. Clique sur l'icône **Terminal**

### À quoi ressemble le Terminal ?
C'est une fenêtre noire avec du texte blanc, qui ressemble à ça :
```
ubuntu@vps-xxxxx:~$
```
C'est ici que tu vas taper les commandes.

---

## Tu es prêt ! Passe à l'installation

---

## Les commandes de base

| Commande | Ce qu'elle fait | Équivalent Windows |
|----------|-----------------|-------------------|
| `ls` | Liste les fichiers | `dir` |
| `cd dossier` | Entre dans un dossier | `cd dossier` |
| `cd ..` | Remonte d'un dossier | `cd ..` |
| `pwd` | Affiche où tu es | - |
| `sudo` | Exécute en administrateur | "Exécuter en tant qu'admin" |
| `nano fichier` | Ouvre un fichier pour l'éditer | Bloc-notes |

---

## Comment copier-coller dans le terminal

**ATTENTION** : Ctrl+C et Ctrl+V ne fonctionnent PAS dans le terminal !

| Action | Windows Terminal/PowerShell | Mac Terminal |
|--------|---------------------------|--------------|
| Copier | Sélectionne + clic droit | Cmd + C |
| Coller | Clic droit | Cmd + V |

Dans certains terminaux : `Ctrl+Shift+C` pour copier, `Ctrl+Shift+V` pour coller.

---

## Installation de GéoClic (LA MÉTHODE SIMPLE)

### Une seule commande à copier-coller !

Connecte-toi à ton serveur (voir Étape 2 ci-dessus), puis copie-colle TOUTE cette ligne :

```bash
curl -sSL https://raw.githubusercontent.com/fredco30/GeoClic_Suite/main/deploy/install-geoclic.sh | sudo bash -s -- --domain geoclic.fr --email ton@email.fr
```

**Remplace `ton@email.fr`** par ton vrai email (pour les certificats SSL).

Cette commande va :
1. Télécharger le script d'installation
2. Installer Docker automatiquement
3. Télécharger GéoClic
4. Tout configurer
5. Tout démarrer

**Durée** : environ 5-10 minutes. Ne ferme pas la fenêtre !

---

## Après l'installation

Tu pourras accéder à :

| Application | URL |
|-------------|-----|
| Portail Citoyen | https://geoclic.fr |
| Admin Patrimoine | https://geoclic.fr/admin |
| Gestion Demandes | https://geoclic.fr/demandes |
| API | https://geoclic.fr/api/docs |

---

## Commandes utiles au quotidien

### Voir si tout fonctionne
```bash
cd /opt/geoclic/GeoClic_Suite/deploy
docker compose ps
```

Tu dois voir tous les services avec "Up" ou "running".

### Voir les erreurs (logs)
```bash
cd /opt/geoclic/GeoClic_Suite/deploy
docker compose logs -f
```
Appuie sur `Ctrl+C` pour arrêter de voir les logs.

### Redémarrer GéoClic
```bash
cd /opt/geoclic/GeoClic_Suite/deploy
docker compose restart
```

### Arrêter GéoClic
```bash
cd /opt/geoclic/GeoClic_Suite/deploy
docker compose down
```

### Relancer GéoClic
```bash
cd /opt/geoclic/GeoClic_Suite/deploy
docker compose up -d
```

---

## En cas de problème

### "Permission denied"
Ajoute `sudo` devant la commande :
```bash
sudo docker compose ps
```

### "Command not found"
La commande n'existe pas ou n'est pas installée.

### Le site ne répond pas
```bash
cd /opt/geoclic/GeoClic_Suite/deploy
docker compose ps
docker compose logs
```

### Je veux tout recommencer
```bash
cd /opt/geoclic/GeoClic_Suite/deploy
docker compose down -v
docker compose up -d --build
```

---

## Glossaire

| Terme | Signification |
|-------|---------------|
| Terminal | L'écran noir où on tape des commandes |
| SSH | Connexion sécurisée à distance |
| Docker | Logiciel qui fait tourner les applications dans des "boîtes" isolées |
| Container | Une "boîte" Docker qui contient une application |
| sudo | "Super User DO" - exécuter en administrateur |
| curl | Télécharger un fichier depuis internet |

---

## Besoin d'aide ?

1. Relis ce guide depuis le début
2. Vérifie que tu as bien copié-collé la commande ENTIÈRE
3. Regarde les logs pour voir l'erreur exacte

---

*Guide créé pour GéoClic Suite V14.3*
