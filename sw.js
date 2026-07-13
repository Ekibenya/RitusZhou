/* 周纪·千年天下 — Service Worker
   策略：网络优先（拿到最新版就用最新版，用户更新代码无需重新添加桌面图标），
   离线时回退到缓存。只处理【同源 GET】——AI 接口、NovelAI 中转、生图等跨域请求
   一律不拦截、原样直连，绝不影响生成管线。 */
const CACHE = 'zhouji-v2';
const SHELL = ['/', '/zhouji.html'];

self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(function (c) {
    return c.addAll(SHELL).catch(function () {});
  }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil((async function () {
    const keys = await caches.keys();
    await Promise.all(keys.map(function (k) { return k === CACHE ? null : caches.delete(k); }));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', function (e) {
  const req = e.request;
  if (req.method !== 'GET') return;                       // 只管 GET
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;        // 跨域（AI/中转/生图）放行，不碰

  e.respondWith((async function () {
    try {
      const fresh = await fetch(req);                     // 网络优先
      if (fresh && fresh.status === 200 && fresh.type === 'basic') {
        const c = await caches.open(CACHE);
        c.put(req, fresh.clone());                        // 顺手更新缓存
      }
      return fresh;
    } catch (err) {                                       // 离线：回退缓存
      const cached = await caches.match(req);
      if (cached) return cached;
      if (req.mode === 'navigate') {
        const shell = (await caches.match('/zhouji.html')) || (await caches.match('/'));
        if (shell) return shell;
      }
      throw err;
    }
  })());
});
