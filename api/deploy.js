/* 生图中转「一键部署」按钮的跳转端点：302 到 Cloudflare Deploy 页。 */
const TARGET = 'https://deploy.workers.cloudflare.com/?url=https://github.com/Ekibenya/nai-proxy';
module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store, max-age=0');
  res.statusCode = 302;
  res.setHeader('Location', TARGET);
  res.end();
};
