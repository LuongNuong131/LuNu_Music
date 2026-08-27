<template>
  <section class="artists-page">
    <header class="artists-hero">
      <div>
        <p class="eyebrow">LU NU MUSIC / ARTISTS</p>
        <h1>Những giọng ca<br /><em>ở lại lâu hơn.</em></h1>
        <p>Khám phá thư viện theo nghệ sĩ. Khi mở một nghệ sĩ, nút phát và Next chỉ đi qua những bài hát thuộc đúng nghệ sĩ đó.</p>
      </div>
      <div class="hero-stat"><strong>{{ artistGroups.length }}</strong><span>nghệ sĩ<br />trong thư viện</span></div>
    </header>

    <div class="artists-toolbar">
      <div><p class="eyebrow">YOUR VOICES</p><h2>Danh sách ca sĩ</h2></div>
      <label class="artist-search"><span>⌕</span><input v-model.trim="query" type="search" placeholder="Tìm nghệ sĩ..." aria-label="Tìm nghệ sĩ" /></label>
    </div>

    <div v-if="!artistGroups.length" class="artist-empty glass-panel"><span>◌</span><h3>Chưa có dữ liệu nghệ sĩ</h3><p>Hãy thêm bài hát vào thư viện để bắt đầu khám phá.</p></div>
    <div v-else class="artist-layout">
      <aside class="artist-directory glass-panel">
        <button v-for="artist in filteredArtists" :key="artist.key" type="button" class="artist-card" :class="{ active: selectedKey === artist.key }" @click="selectedKey = artist.key">
          <img :src="artist.cover || fallbackCover" :alt="artist.name" loading="lazy" />
          <span><strong>{{ artist.name }}</strong><small>{{ artist.songs.length }} bài hát</small></span>
          <b>›</b>
        </button>
        <div v-if="!filteredArtists.length" class="directory-empty">Không tìm thấy nghệ sĩ phù hợp.</div>
      </aside>

      <main v-if="selectedArtist" class="artist-detail glass-panel">
        <div class="detail-heading">
          <div class="artist-identity"><img :src="selectedArtist.cover || fallbackCover" :alt="selectedArtist.name" /><div><p class="eyebrow">ARTIST COLLECTION</p><h2>{{ selectedArtist.name }}</h2><span>{{ selectedArtist.songs.length }} bài trong LuNu library</span></div></div>
          <button type="button" class="play-all" :disabled="!selectedArtist.songs.length" @click="playAll">▶ Phát nghệ sĩ</button>
        </div>
        <div class="scope-note"><i></i><span>Đang phát trong phạm vi <strong>{{ selectedArtist.name }}</strong> · Next/Back không đi ra ngoài danh sách này.</span></div>
        <div class="artist-track-list">
          <article v-for="(song, index) in selectedArtist.songs" :key="song.id" class="artist-track">
            <span class="track-index">{{ String(index + 1).padStart(2, '0') }}</span>
            <button type="button" class="track-art" @click="playSongInArtist(song)"><img :src="song.cover || fallbackCover" :alt="song.title" /><span>▶</span></button>
            <button type="button" class="track-copy" @click="playSongInArtist(song)"><strong>{{ song.title }}</strong><small>{{ song.album || 'SINGLE' }}</small></button>
            <span class="track-year">{{ song.year || '—' }}</span>
            <button type="button" class="track-play" @click="playSongInArtist(song)" aria-label="Phát bài hát">▶</button>
          </article>
        </div>
      </main>
      <main v-else class="artist-detail artist-detail-empty glass-panel"><span>✦</span><h3>Chọn một nghệ sĩ</h3><p>Mỗi nghệ sĩ mở ra một queue nghe riêng.</p></main>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue';

const fallbackCover = '/images/ChoCiu.jpg';
const props = defineProps({ songs: { type: Array, default: () => [] } });
const emit = defineEmits(['play-song']);
const query = ref('');
const selectedKey = ref('');

const normalizeArtist = (value) => String(value || 'Unknown artist').trim().toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
const displayArtist = (value) => String(value || 'Unknown artist').trim() || 'Unknown artist';
const artistGroups = computed(() => {
  const groups = new Map();
  props.songs.forEach((song) => {
    const name = displayArtist(song.artist);
    const key = normalizeArtist(name);
    if (!groups.has(key)) groups.set(key, { key, name, cover: song.cover, songs: [] });
    const group = groups.get(key);
    if (!group.cover && song.cover) group.cover = song.cover;
    group.songs.push(song);
  });
  return [...groups.values()].sort((a, b) => a.name.localeCompare(b.name, 'vi'));
});
const filteredArtists = computed(() => {
  const needle = normalizeArtist(query.value);
  return artistGroups.value.filter((artist) => !query.value || artist.key.includes(needle));
});
const selectedArtist = computed(() => artistGroups.value.find((artist) => artist.key === selectedKey.value) || filteredArtists.value[0] || null);
const playSongInArtist = (song) => { if (selectedArtist.value) emit('play-song', song, selectedArtist.value.songs); };
const playAll = () => { if (selectedArtist.value?.songs[0]) playSongInArtist(selectedArtist.value.songs[0]); };
watch(artistGroups, (groups) => { if (!groups.some((artist) => artist.key === selectedKey.value)) selectedKey.value = groups[0]?.key || ''; }, { immediate: true });
watch(filteredArtists, (artists) => { if (!artists.some((artist) => artist.key === selectedKey.value)) selectedKey.value = artists[0]?.key || ''; });
</script>

<style scoped>
.artists-page { max-width: 1440px; margin: 0 auto; padding-bottom: 70px; }.eyebrow { margin: 0 0 11px; color: var(--gold); font: 9px var(--font-mono); letter-spacing: 2px; }.artists-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; min-height: 245px; padding: clamp(28px, 5vw, 62px); border: 1px solid rgba(255,255,255,.08); border-radius: 28px; background: radial-gradient(circle at 78% 28%, rgba(139,224,190,.13), transparent 25%), linear-gradient(118deg, rgba(38,42,55,.96), rgba(16,19,27,.82)); }.artists-hero h1 { margin: 0; color: var(--text-main); font: 500 clamp(39px, 5vw, 65px)/.98 var(--font-display); letter-spacing: -2px; }.artists-hero h1 em { color: var(--gold); font-style: italic; }.artists-hero p:last-child { max-width: 560px; margin-top: 18px; color: var(--text-sub); font-size: 13px; line-height: 1.65; }.hero-stat { display: flex; align-items: baseline; gap: 10px; color: var(--text-sub); }.hero-stat strong { color: var(--gold-bright); font: 500 64px var(--font-display); }.hero-stat span { color: var(--text-faint); font: 8px/1.5 var(--font-mono); letter-spacing: 1px; text-transform: uppercase; }.artists-toolbar { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; padding: 33px 0 20px; }.artists-toolbar h2 { margin-top: 5px; color: var(--text-main); font: 500 28px var(--font-display); }.artist-search { display: flex; align-items: center; gap: 8px; width: min(300px, 100%); padding: 10px 13px; border: 1px solid var(--hairline); border-radius: 11px; background: rgba(255,255,255,.035); color: var(--gold); }.artist-search input { width: 100%; border: 0; outline: 0; background: transparent; color: var(--text-main); font: 11px var(--font-body); }.artist-layout { display: grid; grid-template-columns: 310px minmax(0, 1fr); gap: 18px; }.artist-directory { align-self: start; max-height: 610px; overflow: auto; padding: 11px; border-radius: 18px; }.artist-card { display: flex; align-items: center; width: 100%; gap: 10px; padding: 9px; border: 1px solid transparent; border-radius: 12px; background: transparent; color: var(--text-main); text-align: left; cursor: pointer; }.artist-card:hover, .artist-card.active { border-color: var(--hairline-soft); background: rgba(245,185,122,.08); }.artist-card img { width: 43px; height: 43px; flex: none; border-radius: 12px; object-fit: cover; }.artist-card span { display: flex; flex: 1; flex-direction: column; min-width: 0; }.artist-card strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 11px; }.artist-card small { margin-top: 4px; color: var(--text-faint); font: 8px var(--font-mono); }.artist-card b { color: var(--gold); font-size: 17px; font-weight: 400; }.directory-empty { padding: 24px 8px; color: var(--text-faint); text-align: center; font-size: 10px; }.artist-detail { min-width: 0; padding: clamp(20px, 3vw, 34px); border-radius: 20px; }.detail-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; }.artist-identity { display: flex; align-items: center; gap: 14px; min-width: 0; }.artist-identity img { width: 84px; height: 84px; flex: none; border-radius: 22px; object-fit: cover; box-shadow: 0 14px 34px rgba(0,0,0,.28); }.artist-identity h2 { margin: 6px 0; overflow: hidden; color: var(--text-main); text-overflow: ellipsis; white-space: nowrap; font: 500 clamp(28px, 4vw, 48px) var(--font-display); }.artist-identity span { color: var(--text-sub); font-size: 10px; }.play-all { flex: none; border: 0; border-radius: 10px; padding: 11px 14px; background: var(--gold); color: #171218; cursor: pointer; font-size: 10px; font-weight: 800; }.play-all:disabled { opacity: .5; cursor: not-allowed; }.scope-note { display: flex; align-items: center; gap: 9px; margin: 25px 0 13px; padding: 11px 12px; border: 1px solid rgba(139,224,190,.2); border-radius: 10px; background: rgba(139,224,190,.06); color: var(--text-sub); font-size: 10px; }.scope-note i { width: 7px; height: 7px; border-radius: 50%; background: var(--mint); box-shadow: 0 0 11px var(--mint); }.scope-note strong { color: var(--mint); }.artist-track-list { border-top: 1px solid var(--hairline-soft); }.artist-track { display: grid; grid-template-columns: 28px 46px minmax(0,1fr) 55px 28px; align-items: center; gap: 12px; min-height: 69px; border-bottom: 1px solid var(--hairline-soft); }.track-index, .track-year { color: var(--text-faint); font: 9px var(--font-mono); }.track-art { position: relative; width: 46px; height: 46px; padding: 0; overflow: hidden; border: 0; border-radius: 10px; background: transparent; cursor: pointer; }.track-art img { width: 100%; height: 100%; object-fit: cover; }.track-art span { position: absolute; inset: 0; display: grid; place-items: center; background: rgba(5,7,12,.58); color: var(--gold); opacity: 0; }.track-art:hover span { opacity: 1; }.track-copy { min-width: 0; padding: 0; border: 0; background: transparent; color: var(--text-main); text-align: left; cursor: pointer; }.track-copy strong, .track-copy small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.track-copy strong { font-size: 11px; }.track-copy small { margin-top: 4px; color: var(--text-sub); font-size: 9px; }.track-play { width: 28px; height: 28px; border: 1px solid var(--hairline); border-radius: 8px; background: transparent; color: var(--gold); cursor: pointer; font-size: 10px; }.artist-detail-empty, .artist-empty { display: grid; place-items: center; align-content: center; min-height: 360px; text-align: center; }.artist-detail-empty > span, .artist-empty > span { color: var(--gold); font-size: 28px; }.artist-detail-empty h3, .artist-empty h3 { margin: 12px 0 6px; color: var(--text-main); font: 500 21px var(--font-display); }.artist-detail-empty p, .artist-empty p { color: var(--text-sub); font-size: 11px; }
@media (max-width: 850px) { .artist-layout { grid-template-columns: 1fr; }.artist-directory { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); max-height: none; }.artist-card { min-width: 0; }.artist-detail-empty { min-height: 250px; }}
@media (max-width: 560px) { .artists-hero { align-items: flex-start; flex-direction: column; }.hero-stat strong { font-size: 45px; }.artists-toolbar { align-items: stretch; flex-direction: column; }.artist-search { width: auto; }.artist-directory { display: block; max-height: 280px; }.artist-card { margin-bottom: 4px; }.detail-heading { align-items: flex-start; flex-direction: column; }.play-all { width: 100%; }.artist-identity img { width: 65px; height: 65px; border-radius: 17px; }.artist-track { grid-template-columns: 22px 43px minmax(0,1fr) 28px; gap: 8px; }.track-art { width: 43px; height: 43px; }.track-year { display: none; }}
</style>
