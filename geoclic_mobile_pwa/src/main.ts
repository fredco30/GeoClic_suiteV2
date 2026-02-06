import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

// Le Service Worker est enregistré automatiquement par VitePWA (registerType: 'autoUpdate')
// Ne pas enregistrer manuellement pour éviter les conflits de chemin
