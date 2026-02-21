const CACHE_NAME = 'lifeos-v1';

// Core pages to cache for offline
const STATIC_CACHE = [
  '/',
  '/fitness/',
  '/meals/',
  '/bible/',
  '/checklist/',
  '/hydration/',
  '/finance/',
  '/static/manifest.json',
];

// ── Install: cache core pages ─────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_CACHE).catch(() => {
        // Don't fail install if some pages aren't accessible yet
      });
    })
  );
  self.skipWaiting();
});

// ── Activate: clear old caches ────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: network-first with cache fallback ──────────────
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Only intercept same-origin GET requests
  if (event.request.method !== 'GET') return;
  if (url.origin !== location.origin) return;

  // Skip admin and API calls (always live)
  if (url.pathname.startsWith('/admin/')) return;
  if (url.pathname.startsWith('/accounts/')) return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Cache successful page responses
        if (response.ok && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, clone);
          });
        }
        return response;
      })
      .catch(() => {
        // Offline fallback — serve from cache
        return caches.match(event.request).then(cached => {
          if (cached) return cached;
          // Return offline page if nothing in cache
          return caches.match('/fitness/');
        });
      })
  );
});

// ── Push notifications (future use) ──────────────────────
self.addEventListener('push', event => {
  if (!event.data) return;
  const data = event.data.json();
  self.registration.showNotification(data.title || 'LifeOS', {
    body: data.body || '',
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-72.png',
  });
});