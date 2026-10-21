// Self-destroying Service Worker to immediately bust any stale caches
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.map((key) => caches.delete(key)));
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Always fetch directly from network, never from cache
self.addEventListener('fetch', (event) => {
  event.respondWith(fetch(event.request));
});
