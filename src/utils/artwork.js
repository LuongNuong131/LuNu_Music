const palettes = [
  ['#254e62', '#8fcdc5', '#d5efe7'],
  ['#675997', '#e0b5d1', '#f6e2d9'],
  ['#aa684f', '#e7c097', '#fff0d3'],
  ['#375384', '#aac2ee', '#e5dcfa'],
  ['#59735a', '#c4d6a3', '#f3ebc8'],
  ['#8a485d', '#f2acb2', '#ffe1c5'],
];
const cache = new Map();
const escapeXml = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (character) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' })[character],
  );
export const songArtwork = (song) => {
  if (song?.cover && song.cover !== '/images/ChoCiu.jpg') return song.cover;
  const key = `${song?.id || ''}:${song?.title || 'LuNu'}:${song?.artist || ''}`;
  if (cache.has(key)) return cache.get(key);
  const seed = [...key].reduce((value, char) => (value * 31 + char.codePointAt(0)) >>> 0, 0);
  const [base, accent, ink] = palettes[seed % palettes.length];
  const title = escapeXml(String(song?.title || 'LuNu Music').slice(0, 30));
  const artist = escapeXml(String(song?.artist || 'Giai điệu của riêng bạn').slice(0, 38));
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><rect width="400" height="400" fill="${base}"/><circle cx="${240 + (seed % 55)}" cy="105" r="165" fill="${accent}"/><circle cx="${240 + (seed % 55)}" cy="105" r="115" fill="none" stroke="${base}" stroke-width="2"/><circle cx="${240 + (seed % 55)}" cy="105" r="65" fill="none" stroke="${base}" stroke-width="2"/><path d="M-30 220Q100 110 220 220t220 0" fill="none" stroke="${ink}" stroke-opacity=".65" stroke-width="28"/><path d="M-30 266Q100 156 220 266t220 0" fill="none" stroke="${accent}" stroke-width="13"/><text x="27" y="337" font-family="sans-serif" font-size="24" font-weight="600" fill="${ink}">${title}</text><text x="28" y="366" font-family="sans-serif" font-size="14" fill="${ink}" opacity=".8">${artist}</text></svg>`;
  const url = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  if (cache.size > 500) cache.clear();
  cache.set(key, url);
  return url;
};
