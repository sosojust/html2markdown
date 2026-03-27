const fs = require('fs');
const path = require('path');

// 1. 读取简单的 .env 文件 (如果存在)
const envPath = path.join(__dirname, '.env');
const envVars = {
  API_URL: 'http://localhost:8000', // 默认开发环境
  DASHBOARD_URL: 'http://localhost:5173' // 默认开发环境
};

if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
    if (match) {
      envVars[match[1]] = match[2].replace(/^['"](.*)['"]$/, '$1'); // 去除引号
    }
  });
}

// 也可以通过命令行环境变量覆盖 (例如: API_URL=https://api.domain.com node build.js)
if (process.env.API_URL) envVars.API_URL = process.env.API_URL;
if (process.env.DASHBOARD_URL) envVars.DASHBOARD_URL = process.env.DASHBOARD_URL;

console.log('--- 开始打包 Chrome 插件 ---');
console.log('目标 API_URL:', envVars.API_URL);
console.log('目标 DASHBOARD_URL:', envVars.DASHBOARD_URL);

// 2. 准备 dist 目录
const srcDir = __dirname;
const distDir = path.join(__dirname, '..', 'dist_chrome');

if (fs.existsSync(distDir)) {
  fs.rmSync(distDir, { recursive: true, force: true });
}
fs.mkdirSync(distDir, { recursive: true });

// 3. 复制并替换文件
function copyAndReplace(src, dest) {
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    // 忽略 node_modules 和 dist 自身等无关文件夹
    if (src.includes('node_modules') || src.includes('.git')) return;
    
    if (!fs.existsSync(dest)) fs.mkdirSync(dest);
    const files = fs.readdirSync(src);
    for (const file of files) {
      copyAndReplace(path.join(src, file), path.join(dest, file));
    }
  } else {
    // 只处理 JS 和 HTML 文件的替换
    if (src.endsWith('.js') || src.endsWith('.html')) {
      let content = fs.readFileSync(src, 'utf8');
      
      // 替换 API 地址
      content = content.replace(/http:\/\/localhost:8000/g, envVars.API_URL);
      // 替换 Dashboard 地址 (同时兼容 localhost 和 127.0.0.1)
      content = content.replace(/http:\/\/(localhost|127\.0\.0\.1):5173/g, envVars.DASHBOARD_URL);
      
      fs.writeFileSync(dest, content, 'utf8');
    } else {
      // 图片、CSS 等直接复制
      // 忽略配置文件本身
      if (!src.endsWith('build.js') && !src.endsWith('.env') && !src.endsWith('package.json') && !src.endsWith('package-lock.json')) {
         fs.copyFileSync(src, dest);
      }
    }
  }
}

copyAndReplace(srcDir, distDir);

console.log(`\n打包完成! 插件已输出到: ${distDir}`);
console.log(`在 Chrome 中加载已解压的扩展程序，选择此 dist_chrome 文件夹即可。`);
