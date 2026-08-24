import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { songs } from '../legacy_songs.js';

const slug = (value) => String(value || '').trim();
const uuidFromUrl = (url) => {
  const hash = crypto.createHash('sha1').update(url).digest('hex').slice(0, 32).split('');
  hash[12] = '5';
  hash[16] = ((parseInt(hash[16], 16) & 0x3) | 0x8).toString(16);
  const text = hash.join('');
  return `${text.slice(0, 8)}-${text.slice(8, 12)}-${text.slice(12, 16)}-${text.slice(16, 20)}-${text.slice(20)}`;
};

const catalog = songs.map((song, index) => {
  const url = slug(song.url);
  if (!url.startsWith('http')) throw new Error(`Record ${index + 1} thiếu URL Cloudinary.`);
  return {
    id: uuidFromUrl(url),
    legacyId: Number(song.id),
    title: slug(song.title) || `Untitled ${index + 1}`,
    artist: slug(song.artist) || 'Unknown artist',
    url,
    cover: slug(song.cover) || '/images/ChoCiu.jpg',
    lyrics: slug(song.lyrics) === 'Đang cập nhật...' ? '' : slug(song.lyrics),
  };
});

const duplicateUrls = catalog.filter((song, index) => catalog.findIndex((item) => item.url === song.url) !== index);
if (duplicateUrls.length) throw new Error(`Phát hiện ${duplicateUrls.length} URL bị trùng.`);
if (catalog.length !== 188) throw new Error(`Cần đúng 188 record, nhận được ${catalog.length}.`);

const json = JSON.stringify(catalog, null, 2);
const js = `// Generated from legacy_songs.js. Do not hand-edit.\nexport const legacyCatalog = ${json};\nexport default legacyCatalog;\n`;
await fs.mkdir('src/data', { recursive: true });
await fs.mkdir('supabase', { recursive: true });
await fs.writeFile('src/data/legacyCatalog.js', js);

const sqlLiteral = (value) => `'${String(value).replaceAll("'", "''")}'`;
const statements = catalog.map((song) => `INSERT INTO songs (id, title, artist, url, cover, lyrics) VALUES (${sqlLiteral(song.id)}, ${sqlLiteral(song.title)}, ${sqlLiteral(song.artist)}, ${sqlLiteral(song.url)}, ${sqlLiteral(song.cover)}, ${sqlLiteral(song.lyrics)}) ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, artist = EXCLUDED.artist, url = EXCLUDED.url, cover = EXCLUDED.cover, lyrics = EXCLUDED.lyrics;`).join('\n');
const sql = `-- LuNu Music legacy catalog import: ${catalog.length} records\n-- Run in Supabase SQL Editor after confirming songs.id is uuid.\nBEGIN;\n${statements}\nCOMMIT;\n`;
await fs.writeFile('supabase/import_legacy_songs.sql', sql);
await fs.writeFile('supabase/legacy_songs.json', `${json}\n`);
await fs.writeFile('supabase/catalog_report.json', JSON.stringify({ count: catalog.length, uniqueUrls: new Set(catalog.map((song) => song.url)).size, recordsWithLyrics: catalog.filter((song) => song.lyrics).length, generatedAt: new Date().toISOString() }, null, 2) + '\n');
console.log(JSON.stringify({ count: catalog.length, uniqueUrls: new Set(catalog.map((song) => song.url)).size, recordsWithLyrics: catalog.filter((song) => song.lyrics).length }));
