import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';

const root = fileURLToPath(new URL('..', import.meta.url));
const host = 'http://127.0.0.1:4174';
const isWindows = process.platform === 'win32';
const devCommand = isWindows ? process.env.ComSpec || 'cmd.exe' : 'npm';
const devArgs = isWindows
  ? ['/d', '/s', '/c', 'npm.cmd run dev -- --host 127.0.0.1 --port 4174']
  : ['run', 'dev', '--', '--host', '127.0.0.1', '--port', '4174'];

function fail(message) {
  throw new Error(message);
}

async function waitForServer(url, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Server is still starting.
    }
    await delay(400);
  }
  fail(`Timed out waiting for ${url}`);
}

async function visibleText(page) {
  return page.locator('body').innerText();
}

async function run() {
  const server = spawn(devCommand, devArgs, {
    cwd: root,
    stdio: 'pipe',
    shell: false
  });
  server.stdout.on('data', (chunk) => process.stdout.write(chunk));
  server.stderr.on('data', (chunk) => process.stderr.write(chunk));

  let browser;
  try {
    await waitForServer(host);
    console.log('server ready');
    browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(host, { waitUntil: 'domcontentloaded', timeout: 20000 });

    await page.getByText('生成产品情况周报').waitFor({ timeout: 15000 });
    await page.waitForFunction(() => {
      const node = document.querySelector('[data-testid="product-count-kpi"] strong');
      return node && Number(node.textContent.trim()) >= 80;
    }, null, { timeout: 20000 });

    await page.getByRole('button', { name: '产品对标' }).click();
    await page.getByText('竞品对标').first().waitFor({ timeout: 15000 });
    const benchmarkText = await visibleText(page);
    if (benchmarkText.includes('"return_percentile"') || benchmarkText.includes('peer_universe_explainer')) {
      fail('产品对标页直接暴露了 raw JSON 文本');
    }

    await page.getByRole('button', { name: '审计追踪' }).click();
    await page.getByText('数字一致性').waitFor({ timeout: 15000 });
    const traceText = await visibleText(page);
    for (const keyword of ['数字一致性', '证据覆盖', '禁用措辞']) {
      if (!traceText.includes(keyword)) fail(`审计追踪页缺少 ${keyword}`);
    }

    await page.getByRole('button', { name: 'AI 报告校准' }).click();
    await page.getByText('AI 报告校准结果').waitFor({ timeout: 15000 });
    const dpoText = await visibleText(page);
    if (dpoText.includes('template_baseline')) {
      fail('AI 报告校准页默认直接展示了 template_baseline 技术字段');
    }

    console.log('smoke ok');
  } finally {
    if (browser) await browser.close();
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(server.pid), '/t', '/f'], { stdio: 'ignore' });
    } else {
      server.kill();
    }
  }
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
