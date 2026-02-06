const CACHE_NAME = 'geoclic-services-v2';
const OFFLINE_URL = '/terrain/offline.html';

// Assets to cache immediately on install
const PRECACHE_ASSETS = [
  '/terrain/',
  '/terrain/index.html',
  '/terrain/manifest.json',
  '/terrain/offline.html',
];

// API routes to cache with network-first strategy
const API_CACHE_NAME = 'geoclic-api-v1';
const API_ROUTES = [
  '/api/services/demandes',
];

// Install event - precache essential assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching precache assets');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME && name !== API_CACHE_NAME)
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - handle requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // API requests - network first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request, API_CACHE_NAME));
    return;
  }

  // JS/CSS assets with hash - network first (ensures updates are applied)
  if (url.pathname.match(/\/terrain\/assets\/.*\.(js|css)$/)) {
    event.respondWith(networkFirst(request, CACHE_NAME));
    return;
  }

  // Other static assets - cache first
  if (url.pathname.startsWith('/terrain/')) {
    event.respondWith(cacheFirst(request));
    return;
  }
});

// Cache-first strategy
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlineResponse = await caches.match(OFFLINE_URL);
      if (offlineResponse) {
        return offlineResponse;
      }
    }
    throw error;
  }
}

// Network-first strategy for API calls
async function networkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    throw error;
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-demandes') {
    event.waitUntil(syncDemandes());
  }
});

async function syncDemandes() {
  // Get pending actions from IndexedDB and sync
  const clients = await self.clients.matchAll();
  clients.forEach(client => {
    client.postMessage({ type: 'SYNC_COMPLETE' });
  });
}

// Listen for messages from client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
