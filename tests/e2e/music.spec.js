import { test, expect } from '@playwright/test';
const songs = Array.from({ length: 35 }, (_, i) => ({
  id: String(i + 1),
  title: i === 0 ? 'Đừng làm trái tim anh đau' : `Giai điệu ${String(i + 1).padStart(2, '0')}`,
  artist: i % 2 ? 'Vũ.' : 'Sơn Tùng M-TP',
  cover: '/images/ChoCiu.jpg',
  url: '/test-track.wav',
  duration: 20,
}));
const user = { id: 'listener', username: 'luong', display_name: 'Lương', role: 'admin' };
const wav = () => {
  const pcm = Buffer.alloc(20 * 8000 * 2);
  const header = Buffer.alloc(44);
  header.write('RIFF');
  header.writeUInt32LE(pcm.length + 36, 4);
  header.write('WAVEfmt ', 8);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22);
  header.writeUInt32LE(8000, 24);
  header.writeUInt32LE(16000, 28);
  header.writeUInt16LE(2, 32);
  header.writeUInt16LE(16, 34);
  header.write('data', 36);
  header.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([header, pcm]);
};
async function mockApi(page, { authenticated = true, failSongs = false, emptySongs = false } = {}) {
  await page.route('**/test-track.wav', (route) =>
    route.fulfill({ contentType: 'audio/wav', body: wav() }),
  );
  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === '/api/login')
      return route.fulfill({ json: { success: true, user, access_token: 'fixture-token' } });
    if (url.pathname === '/api/songs')
      return route.fulfill(
        failSongs
          ? { status: 503, json: { detail: 'Thư viện đang bảo trì.' } }
          : { json: emptySongs ? [] : songs },
      );
    if (url.pathname === '/api/health')
      return route.fulfill({
        json: {
          ok: true,
          media_worker: { configured: false, configuration_valid: true },
          youtube_cooldown_seconds: 120,
          direct_audio_providers: {},
        },
      });
    if (url.pathname.endsWith('/search_youtube'))
      return route.fulfill({
        json: {
          success: true,
          results: [
            {
              id: 'BaW_jenozKc',
              title: 'Bản nhạc thử',
              uploader: 'LuNu',
              thumbnail: '/images/listening-room.svg',
            },
          ],
        },
      });
    if (url.pathname === '/api/songs/add')
      return route.fulfill({ json: { success: true, job_id: 'job-1' } });
    if (url.pathname.includes('/import-jobs/'))
      return route.fulfill({
        json: { success: true, status: 'completed', song: songs[0], message: 'Đã thêm nhạc.' },
      });
    if (url.pathname === '/api/notifications')
      return route.fulfill({ json: { success: true, notifications: [], unread_count: 0 } });
    if (
      url.pathname === '/api/playlists' ||
      url.pathname === '/api/users' ||
      url.pathname === '/api/admin/chat-reports'
    )
      return route.fulfill({ json: [] });
    return route.fulfill({
      json: { success: true, playlists: [], reports: [], notifications: [] },
    });
  });
  if (authenticated)
    await page.addInitScript((u) => {
      localStorage.setItem('lunu_user', JSON.stringify(u));
      localStorage.setItem('lunu_access_token', 'fixture-token');
    }, user);
}

test('logging in loads songs without a reload and password visibility works', async ({ page }) => {
  await mockApi(page, { authenticated: false });
  await page.goto('/');
  await page.getByLabel('Tài khoản', { exact: true }).fill('luong');
  await page.getByLabel('Mật khẩu', { exact: true }).fill('password');
  await page.getByRole('button', { name: 'Hiện mật khẩu' }).click();
  await expect(page.getByLabel('Mật khẩu', { exact: true })).toHaveAttribute('type', 'text');
  await page.getByRole('button', { name: 'Vào không gian của bạn' }).click();
  await expect(page.getByRole('heading', { name: 'Hôm nay, nghe gì?' })).toBeVisible();
  await expect(page.locator('.library-track')).toHaveCount(24);
});

test('accent-insensitive search, favorites and layout controls', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  await expect(page.locator('.library-track')).toHaveCount(24);
  await page.getByLabel('Tìm bài hát hoặc nghệ sĩ').fill('dung lam trai tim');
  await expect(page.locator('.library-track')).toHaveCount(1);
  await page
    .locator('.library-track')
    .getByRole('button', { name: 'Yêu thích Đừng làm trái tim anh đau', exact: true })
    .click();
  await page.getByLabel('Tìm bài hát hoặc nghệ sĩ').clear();
  await page.getByRole('button', { name: 'Hiển thị dạng lưới', exact: true }).click();
  await expect(page.locator('.track-collection')).toHaveClass(/grid-mode/);
  await page.getByRole('button', { name: 'Xem thêm 11 bài hát' }).click();
  await expect(page.locator('.library-track')).toHaveCount(35);
  await page
    .getByRole('navigation', { name: 'Điều hướng chính' })
    .getByRole('button', { name: 'Yêu thích' })
    .click();
  await expect(page.locator('.library-track')).toHaveCount(1);
  await page.reload();
  await page
    .getByRole('navigation', { name: 'Điều hướng chính' })
    .getByRole('button', { name: 'Yêu thích' })
    .click();
  await expect(page.locator('.library-track')).toHaveCount(1);
});

test('playback follows the selected position, and native volume arrows remain usable', async ({
  page,
}) => {
  await mockApi(page);
  await page.goto('/');
  await expect(page.locator('.library-track')).toHaveCount(24);
  await page.locator('.library-track').nth(4).locator('.track-name').click();
  await expect(page.locator('.now-track strong')).toHaveText('Giai điệu 05');
  await expect(page.getByRole('button', { name: 'Tạm dừng', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Bài tiếp', exact: true }).click();
  await expect(page.locator('.now-track strong')).toHaveText('Giai điệu 06');
  await page.getByRole('button', { name: 'Bài trước', exact: true }).click();
  await expect(page.locator('.now-track strong')).toHaveText('Giai điệu 05');
  await page.getByLabel('Âm lượng', { exact: true }).focus();
  const before = Number(await page.getByLabel('Âm lượng', { exact: true }).inputValue());
  await page.keyboard.press('ArrowRight');
  const after = Number(await page.getByLabel('Âm lượng', { exact: true }).inputValue());
  expect(after).toBeGreaterThan(before);
  await page.getByRole('button', { name: 'Tạm dừng', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Phát nhạc', exact: true })).toBeVisible();
});

test('API failure is visible with fallback while an empty library stays empty', async ({
  page,
}) => {
  await mockApi(page, { failSongs: true });
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('Thư viện đang bảo trì');
  await expect(page.locator('.library-track')).toHaveCount(24);
});

test('an empty successful API response does not resurrect legacy songs', async ({ page }) => {
  await mockApi(page, { emptySongs: true });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Chưa có bài hát phù hợp' })).toBeVisible();
  await expect(page.locator('.library-track')).toHaveCount(0);
});

for (const width of [375, 768, 1024, 1440])
  test(`layout at ${width}px, theme and navigation`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await mockApi(page);
    await page.goto('/');
    await expect(page.locator('.library-track')).toHaveCount(24);
    await page.waitForTimeout(250);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    expect(
      await page.locator('.main-content').evaluate((el) => el.scrollWidth <= el.clientWidth + 1),
    ).toBe(true);
    if (width < 761) {
      await page.getByRole('button', { name: 'Mở menu điều hướng' }).click();
      await expect(page.locator('#lunu-navigation')).toHaveClass(/mobile-open/);
      await page.getByRole('button', { name: 'Đóng menu' }).click();
      await expect(page.locator('#lunu-navigation')).not.toHaveClass(/mobile-open/);
    }
    await page.getByRole('button', { name: 'Chuyển giao diện sáng', exact: true }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    const background = await page
      .locator('.listening-feature')
      .evaluate((el) => getComputedStyle(el).backgroundColor);
    expect(background).toBe('rgb(217, 208, 255)');
  });

test('YouTube source import uses the explicit provider and displays real completion', async ({
  page,
}) => {
  await mockApi(page);
  await page.goto('/');
  await page
    .getByRole('navigation', { name: 'Điều hướng chính' })
    .getByRole('button', { name: 'Quản trị', exact: true })
    .click();
  await expect(page.getByText('YouTube tạm nghỉ 2 phút', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'YouTube', exact: true }).click();
  await page.getByLabel('Tìm nguồn nhạc').fill('Bản nhạc thử');
  await page.getByRole('button', { name: 'Tìm kiếm', exact: true }).click();
  await page.locator('.result-item').getByRole('button', { name: 'Chọn', exact: true }).click();
  const requestPromise = page.waitForRequest((request) => request.url().endsWith('/api/songs/add'));
  await page.getByRole('button', { name: 'Thêm vào thư viện', exact: true }).click();
  const request = await requestPromise;
  expect(request.postDataJSON()).toMatchObject({ provider: 'youtube', source_id: 'BaW_jenozKc' });
  await expect(page.locator('.status-message')).toContainText('Đã thêm');
});

test('fullscreen player and queue support keyboard dismissal and restore focus', async ({
  page,
}) => {
  await mockApi(page);
  await page.goto('/');
  await expect(page.locator('.library-track')).toHaveCount(24);
  await page.locator('.library-track').first().locator('.track-name').click();
  await page.getByRole('button', { name: 'Mở trình phát toàn màn hình', exact: true }).click();
  await expect(page.getByRole('dialog', { name: songs[0].title, exact: true })).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Thu nhỏ trình phát' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.locator('.np-overlay')).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Mở trình phát toàn màn hình', exact: true }),
  ).toBeFocused();
  await page
    .getByRole('contentinfo', { name: 'Trình phát nhạc' })
    .getByRole('button', { name: 'Mở hàng đợi', exact: true })
    .click();
  await expect(page.getByRole('dialog', { name: 'Hàng đợi', exact: true })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('.queue-panel')).toHaveCount(0);
});
