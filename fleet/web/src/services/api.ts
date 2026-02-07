const API_BASE = '/api'

function getHeaders(): Record<string, string> {
  const token = localStorage.getItem('fleet_auth_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: { ...getHeaders(), ...(options.headers as Record<string, string> || {}) },
  })

  if (res.status === 401) {
    localStorage.removeItem('fleet_auth_token')
    window.location.href = '/fleet/login'
    throw new Error('Non authentifié')
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(data.detail || `Erreur ${res.status}`)
  }

  return res.json()
}

export const api = {
  // Auth (utilise l'API principale de GéoClic)
  async login(email: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    })

    if (!res.ok) {
      const data = await res.json().catch(() => ({ detail: 'Erreur de connexion' }))
      throw new Error(data.detail || 'Identifiants incorrects')
    }

    const data = await res.json()
    if (!data.user?.is_super_admin) {
      throw new Error('Accès réservé au super administrateur')
    }

    localStorage.setItem('fleet_auth_token', data.access_token)
    return data
  },

  logout() {
    localStorage.removeItem('fleet_auth_token')
  },

  // Fleet API
  listServers() {
    return request<{ servers: any[] }>('/fleet/servers')
  },

  serversStatus() {
    return request<{ servers: any[] }>('/fleet/servers/status')
  },

  serverStatus(name: string) {
    return request<any>(`/fleet/servers/${name}/status`)
  },

  addServer(data: { name: string; domain: string; ip: string; ssh_user?: string; ssh_port?: number }) {
    return request<any>('/fleet/servers', { method: 'POST', body: JSON.stringify(data) })
  },

  removeServer(name: string) {
    return request<any>(`/fleet/servers/${name}`, { method: 'DELETE' })
  },

  provisionServer(data: {
    name: string; domain: string; ip: string; email: string;
    ssh_user?: string; ssh_port?: number
  }) {
    return request<{ task_id: string }>(`/fleet/servers/${data.name}/provision`, {
      method: 'POST', body: JSON.stringify(data),
    })
  },

  initServer(name: string, data: {
    email: string; password: string; collectivite: string; with_demo?: boolean
  }) {
    return request<{ task_id: string }>(`/fleet/servers/${name}/init`, {
      method: 'POST', body: JSON.stringify(data),
    })
  },

  updateServer(name: string, data?: { services?: string; migration?: string }) {
    return request<{ task_id: string }>(`/fleet/servers/${name}/update`, {
      method: 'POST', body: JSON.stringify(data || {}),
    })
  },

  updateAllServers(data?: { services?: string; migration?: string }) {
    return request<{ task_id: string }>('/fleet/servers/update-all', {
      method: 'POST', body: JSON.stringify(data || {}),
    })
  },

  backupServer(name: string) {
    return request<{ task_id: string }>(`/fleet/servers/${name}/backup`, { method: 'POST' })
  },

  serverLogs(name: string, service = 'api', lines = 100) {
    return request<{ logs: string }>(`/fleet/servers/${name}/logs?service=${service}&lines=${lines}`)
  },

  testSsh(ip: string, user = 'ubuntu', port = 22) {
    return request<{ status: string }>(`/fleet/test-ssh?ip=${ip}&user=${user}&port=${port}`, { method: 'POST' })
  },

  getSshKey() {
    return request<{ public_key: string }>('/fleet/ssh-key')
  },

  generateSshKey() {
    return request<{ public_key: string }>('/fleet/ssh-key/generate', { method: 'POST' })
  },

  getTask(taskId: string) {
    return request<any>(`/fleet/tasks/${taskId}`)
  },

  getTaskLog(taskId: string, lines = 100) {
    return request<{ log: string }>(`/fleet/tasks/${taskId}/log?lines=${lines}`)
  },
}
