# 生图中转 · NovelAI 官方

NovelAI 官网生图端点 `image.novelai.net` **不允许网页跨域**调用，所以纯前端网页无法直接连它。
本目录提供一个 **Cloudflare Worker** 中转脚本，替浏览器转发请求并补上 CORS 头。

选它而不用 Vercel 的原因：**Cloudflare Worker 流量不计费**（免费额度按请求数，每天 10 万次），
图片过它多少都不花钱，也**不消耗游戏所在 Vercel 的带宽**。

## 部署（约 2 分钟）
1. 登录 <https://dash.cloudflare.com> → 左侧 **Workers & Pages** → **Create** → **Create Worker**。
2. 起名（如 `nai-proxy`）→ **Deploy** → **Edit code**。
3. 把 [`novelai-cors-worker.js`](./novelai-cors-worker.js) 全部内容粘贴进去，覆盖默认代码 → **Deploy**。
4. 复制它的网址，形如 `https://nai-proxy.你的名字.workers.dev`。

## 在游戏里填写
设置 → **图 · 生图**：
- 接口风格：**NovelAI 官方**
- 接口地址：你的 Worker 网址（上一步复制的）
- 密钥：NovelAI **持久 token**（NAI 官网账户设置 → *Get Persistent API Token*）
- 模型：`nai-diffusion-3`（或你要用的）
- 采样器/噪点表/步数/引导(CFG)/引导重缩放/尺寸/种子按需填

保存 → **测试生图**。之后每幕自动出图（或点正文下「✦ 绘此幕」）。返回的 zip 由游戏**内置解压**成 PNG，存进你本机浏览器图库，存档只记编号。

## 隐私
Worker 只做**无状态转发**，不存储、不记录 token 与图片；token 仅在转发那一刻经过一次。
若你不放心共享 Worker，按上面步骤部署**自己的** Worker 即可（推荐）。
