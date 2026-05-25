import { spawn } from 'node:child_process';
import { writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';

const root = fileURLToPath(new URL('..', import.meta.url));
const host = 'http://127.0.0.1:4175';
const isWindows = process.platform === 'win32';
const devCommand = isWindows ? process.env.ComSpec || 'cmd.exe' : 'npm';
const devArgs = isWindows
  ? ['/d', '/s', '/c', 'npm.cmd run dev -- --host 127.0.0.1 --port 4175']
  : ['run', 'dev', '--', '--host', '127.0.0.1', '--port', '4175'];

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

async function uploadCsv(page, scope, fileName, contents) {
  await page.getByRole('button', { name: '导入周报/净值数据' }).click();
  await page.getByRole('button', { name: new RegExp(scope) }).click();
  const csvPath = join(tmpdir(), `${fileName}-${Date.now()}.csv`);
  await writeFile(csvPath, contents, 'utf-8');
  await page.locator('input[type="file"]').setInputFiles(csvPath);
  await page.getByText('自动字段映射').waitFor({ timeout: 15000 });
  await page.getByRole('button', { name: '确认导入并刷新工作台' }).click();
}

async function run() {
  const server = spawn(devCommand, devArgs, { cwd: root, stdio: 'pipe', shell: false });
  server.stdout.on('data', (chunk) => process.stdout.write(chunk));
  server.stderr.on('data', (chunk) => process.stderr.write(chunk));

  let browser;
  try {
    await waitForServer(host);
    browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(host, { waitUntil: 'domcontentloaded', timeout: 20000 });

    await page.getByText('生成产品情况周报').waitFor({ timeout: 15000 });
    await page.waitForFunction(() => {
      const node = document.querySelector('[data-testid="product-count-kpi"] strong');
      return node && Number(node.textContent.trim()) >= 80;
    }, null, { timeout: 20000 });

    await page.waitForFunction(() => {
      const node = document.querySelector('[data-testid="weekly-date-select"]');
      return node && node.querySelectorAll('option').length >= 4;
    }, null, { timeout: 20000 });
    const dateOptions = await page.getByTestId('weekly-date-select').locator('option').count();
    if (dateOptions < 4) fail(`日期下拉选项不足 4 个，当前 ${dateOptions}`);
    await page.locator('.data-mode-panel').waitFor({ timeout: 15000 });
    const dataModeText = await page.locator('.data-mode-panel').innerText();
    if (!dataModeText.includes('own_company') || !dataModeText.includes('synthetic_weekly_snapshot')) {
      fail('数据模式卡片未展示 source_type record_count');
    }

    const firstAttentionName = page.locator('.attention-product-name').first();
    await firstAttentionName.waitFor({ timeout: 15000 });
    const attentionStyle = await firstAttentionName.evaluate((node) => {
      const style = window.getComputedStyle(node);
      return { whiteSpace: style.whiteSpace, overflow: style.overflow, textOverflow: style.textOverflow };
    });
    if (attentionStyle.whiteSpace !== 'normal' || attentionStyle.textOverflow === 'ellipsis') {
      fail(`产品名称仍被省略: ${JSON.stringify(attentionStyle)}`);
    }

    await uploadCsv(
      page,
      'own_company',
      'wealth-agent-own-upload',
      'report_date,product_code,product_name,product_type,channel,risk_level,product_scale_bn,latest_nav,return_3m,max_drawdown,volatility,sharpe,benchmark_status\n2025-04-04,UP001,上传测试稳健添利90天持有期A,纯固收,直销,R2,1.2,1.01,1.2%,-0.4%,2.1%,0.8,in_range\n'
    );
    await page.getByText('用户上传 + 演示样本').waitFor({ timeout: 15000 });
    await page.getByText('产品系列归类与手工修正').waitFor({ timeout: 15000 });
    await page.getByText('上传测试稳健添利90天持有期A').waitFor({ timeout: 15000 });

    await uploadCsv(
      page,
      'reference_rates',
      'wealth-agent-rates-upload',
      'rate_id,as_of_date,currency,rate_type,tenor_days,tenor_label,annual_yield\nRMB_UPLOAD_3M,2025-04-04,CNY,deposit,90,3M,1.50%\n'
    );
    await page.getByText('基准利率对比').waitFor({ timeout: 15000 });
    await page.getByText('manual_upload + synthetic_reference_rates').waitFor({ timeout: 15000 });

    await page.getByRole('button', { name: '产品对标' }).click();
    await page.getByText('竞品对标').first().waitFor({ timeout: 15000 });
    await page.waitForFunction(() => {
      const select = document.querySelector('.filter-panel select');
      return select && select.querySelectorAll('option').length >= 80;
    }, null, { timeout: 20000 });
    const initialSelectCount = await page.locator('.filter-panel select').first().locator('option').count();
    await page.locator('.filter-panel select').nth(3).selectOption('R5');
    await page.waitForTimeout(500);
    const filteredSelectCount = await page.locator('.filter-panel select').first().locator('option').count();
    if (filteredSelectCount >= initialSelectCount) fail(`筛选后产品 select 数量未下降: ${initialSelectCount} -> ${filteredSelectCount}`);

    const benchmarkText = await visibleText(page);
    if (benchmarkText.includes('"return_percentile"') || benchmarkText.includes('peer_universe_explainer')) {
      fail('产品对标页直接暴露了 raw JSON 文本');
    }

    await page.getByRole('button', { name: '同类绩优产品' }).click();
    await page.getByText('入选原因').waitFor({ timeout: 15000 });
    const ranks = await page.locator('table tbody tr td:first-child').evaluateAll((nodes) =>
      nodes.map((node) => Number(node.textContent.trim())).filter(Number.isFinite).slice(0, 12)
    );
    if (Math.max(...ranks) <= 8) fail(`同类绩优产品排名仍疑似循环: ${ranks.join(',')}`);

    await page.getByRole('button', { name: '净值对比' }).click();
    await page.getByText('5只产品净值对比').waitFor({ timeout: 15000 });
    const lineCount = await page.locator('.multi-line-chart polyline').count();
    if (lineCount < 2) fail(`净值对比曲线不足，当前 ${lineCount}`);

    await page.getByRole('button', { name: '审计追踪' }).click();
    await page.getByText('数字一致性').waitFor({ timeout: 15000 });
    await page.getByRole('button', { name: 'Skill / Harness' }).click();
    await page.getByText('Skill / Harness Runtime').waitFor({ timeout: 15000 });
    const skillText = await visibleText(page);
    for (const keyword of ['selected_skills', 'harness pass/fail', 'source boundary check']) {
      if (!skillText.includes(keyword)) fail(`Skill/Harness tab 缺少 ${keyword}`);
    }
    await page.getByRole('button', { name: 'External Verification' }).click();
    await page.getByText('外部验证覆盖率').waitFor({ timeout: 15000 });
    await page.getByRole('button', { name: 'Source Coverage' }).click();
    await page.getByText('official_public_nav').waitFor({ timeout: 15000 });
    await page.getByRole('button', { name: 'AI 报告校准' }).click();
    await page.getByText('AI 报告校准结果').waitFor({ timeout: 15000 });
    const dpoText = await visibleText(page);
    if (dpoText.includes('template_baseline')) fail('AI 报告校准页默认暴露了 template_baseline 技术字段');

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
