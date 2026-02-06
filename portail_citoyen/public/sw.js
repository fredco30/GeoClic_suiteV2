const CACHE_NAME = 'portail-citoyen-v2';
const OFFLINE_URL = '/portail/offline.html';

// Only cache truly static assets - NOT index.html (which references hashed JS files)
const PRECACHE_ASSETS = [
  '/portail/manifest.json',
  '/portail/offline.html',
];

// Install event - precache essential assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Portail Citoyen: Caching assets');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean ALL old caches and take control immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME)
            .map((name) => {
              console.log('Portail Citoyen: Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('Portail Citoyen: New SW v2 activated, taking control');
        return self.clients.claim();
      })
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

  // API requests - network only (no caching)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkOnly(request));
    return;
  }

  // Navigation requests (HTML pages) - network first to always get fresh HTML
  if (request.mode === 'navigate' || url.pathname.endsWith('.html') || url.pathname === '/portail/' || url.pathname === '/portail') {
    event.respondWith(networkFirst(request));
    return;
  }

  // JS/CSS assets - network first (ensures updates are applied)
  if (url.pathname.match(/\/portail\/assets\/.*\.(js|css)$/)) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Other static assets (images, fonts) - cache first
  if (url.pathname.startsWith('/portail/')) {
    event.respondWith(cacheFirst(request));
    return;
  }
});

// Network-only strategy for API calls
async function networkOnly(request) {
  try {
    return await fetch(request);
  } catch (error) {
    // Return error response for API failures
    return new Response(JSON.stringify({ error: 'Offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

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

// Network-first strategy
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
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

// Listen for messages from client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
