# 生图中转 · NovelAI 官方 · Image proxy for NovelAI

NovelAI 官网生图端点 `image.novelai.net` **不允许网页跨域**（no CORS for browsers），
纯前端网页无法直接连它。本目录的 **Cloudflare Worker** 替浏览器转发请求、补上 CORS 头。

选 Cloudflare 而非 Vercel 的原因：**Worker 流量不计费**（unmetered bandwidth，免费额度按请求数，
100,000 次/天），图片过它多少都不花钱，也**不消耗游戏所在 Vercel 的带宽**。

中转建在**你自己的 Cloudflare 账号**里 → token 与图片只走你自己的通道，**保护隐私**。

---

## 方法一 · 最省事，不需要 GitHub（推荐给小白）
> The Cloudflare dashboard is in English. Button names are shown below in **bold**.

1. 打开 <https://dash.cloudflare.com>，注册 / 登录（免费，只需邮箱）。
2. 左侧点 **Compute (Workers)**（旧版叫 **Workers & Pages**）。
3. 点 **Create** → **Start with Hello World** / **Create Worker** → 起个名 → 点 **Deploy**。
4. 点 **Edit code**（或 **`</>` Edit code**）→ 把编辑器里原有代码**全选删掉**，
   粘贴 [`novelai-cors-worker.js`](./novelai-cors-worker.js) 的全部内容 → 右上再点 **Deploy**。
5. 复制它给你的网址（形如 `你起的名.你的用户名.workers.dev`）。

游戏里也有「**复制中转代码**」按钮，一键复制第 4 步要粘贴的代码。

## 方法二 · 一键部署（需要 GitHub 账号，有的话更快）
点 **Deploy to Cloudflare** 按钮（游戏「图·生图」里那个「⚡ 一键部署」）：
→ 登录 Cloudflare 并 **authorize / 授权连接 GitHub**（会在你的 GitHub 建一个副本仓库）
→ 点 **Deploy** → 复制生成的网址。
没有 GitHub 就用方法一。

---

## 在游戏里填写 · Configure in the game
设置 → **图 · 生图**：
- 接口风格 Style：**NovelAI 官方**
- 接口地址 URL：你的 Worker 网址（上面复制的）
- 密钥 Key：NovelAI **持久 token**（NAI 官网 *User Settings → Account → Get Persistent API Token*）
- 模型 Model：`nai-diffusion-3`（或你要用的）
- 采样器 / 噪点表 / 步数 / 引导(CFG) / 引导重缩放 / 尺寸 / 种子 按需填

保存 → **测试生图**。之后每幕自动出图（或点正文下「✦ 绘此幕」）。
返回的 zip 由游戏**内置解压**成 PNG，存进你本机浏览器图库，存档只记编号。

## 隐私 · Privacy
Worker 只做**无状态转发**，不存储、不记录 token 与图片；token 仅在转发那一刻经过一次。
中转与 NAI 账号都在**你自己名下**，与游戏站点所有者无关。
