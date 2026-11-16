import { getImportJob } from '../services/api';

export async function waitForImport(
  jobId,
  { signal, onProgress = () => {}, interval = 1800, timeout = 15 * 60 * 1000 } = {},
) {
  const deadline = Date.now() + timeout;
  while (!signal?.aborted && Date.now() < deadline) {
    const job = await getImportJob(jobId, { signal });
    onProgress(job);
    if (job.status === 'completed') return job;
    if (job.status === 'failed') {
      const error = new Error(
        job.message || 'Chưa thể thêm nhạc. Hãy thử nguồn khác hoặc thêm file audio.',
      );
      error.code = job.error_code;
      throw error;
    }
    await new Promise((resolve, reject) => {
      const abort = () => {
        clearTimeout(timer);
        reject(new DOMException('Aborted', 'AbortError'));
      };
      const timer = setTimeout(() => {
        signal?.removeEventListener('abort', abort);
        resolve();
      }, interval);
      signal?.addEventListener('abort', abort, { once: true });
      if (signal?.aborted) abort();
    });
  }
  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
  throw new Error('Tác vụ chưa hoàn tất sau 15 phút. Kiểm tra trạng thái nguồn trước khi thử lại.');
}
