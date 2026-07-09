/* 生图中转「一键部署」按钮的跳转端点：302 到 Cloudflare Deploy 页。
   经过这里的每次点击都会计入本函数的调用次数——在 Vercel 控制台
   （项目 → Observability → Functions，或 Usage → Function Invocations）即可查看点击数。
   no-store 确保每次点击都真实打到函数（不被边缘缓存吞掉计数）。 */
const TARGET = 'https://deploy.workers.cloudflare.com/?url=https://github.com/Ekibenya/nai-proxy';
module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store, max-age=0');
  res.statusCode = 302;
  res.setHeader('Location', TARGET);
  res.end();
};
