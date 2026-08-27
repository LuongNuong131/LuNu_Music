<template><span class="room-sync-bridge" aria-hidden="true"></span></template>

<script setup>
import { onBeforeUnmount, onMounted } from 'vue';
import { getListeningRoom, updateListeningRoomState } from '../services/api';
import { pause, play, playSong, playerState, seek } from '../store/playerState';
import { roomSession, updateRoomSessionVersion } from '../store/roomSession';

let timer = null;
let publishInFlight = false;
let lastSignature = '';
let latestRoom = null;

const toRoomSong = (song) => song ? ({ id: song.id, title: song.title, artist: song.artist, cover: song.cover, url: song.url, audio_url: song.audio_url, audioUrl: song.audioUrl, media_key: song.media_key }) : null;
const fromRoomSong = (song) => song ? ({ ...song, url: song.url || song.audio_url || song.audioUrl || '' }) : null;
const positionAtNow = (room) => { const base = Math.max(0, Number(room?.position_seconds) || 0); if (!room?.is_playing || !room?.updated_at) return base; const updated = Date.parse(room.updated_at); return Number.isFinite(updated) ? base + Math.max(0, (Date.now() - updated) / 1000) : base; };

const publishHostState = async () => { if (!roomSession.roomId || !roomSession.isHost || !playerState.currentSong || publishInFlight) return; const signature = [playerState.currentSong.id, playerState.isPlaying, Math.floor((Number(playerState.currentTime) || 0) / 2), playerState.queue.length].join('|'); if (signature === lastSignature) return; lastSignature = signature; publishInFlight = true; try { const response = await updateListeningRoomState(roomSession.roomId, { current_song: toRoomSong(playerState.currentSong), queue: playerState.queue.map(toRoomSong), is_playing: playerState.isPlaying, position_seconds: Number(playerState.currentTime) || 0, expected_version: null }); latestRoom = response.room; updateRoomSessionVersion(response.room?.state_version); } catch (error) { console.warn('[LuNu room sync] host publish failed', error); } finally { publishInFlight = false; } };

const applyRoomState = (room) => { if (!room?.current_song) return; const song = fromRoomSong(room.current_song); if (!song?.url) return; const queue = (room.queue || []).map(fromRoomSong).filter((item) => item?.url); const sameSong = String(playerState.currentSong?.id || '') === String(song.id || ''); const position = positionAtNow(room); if (!sameSong) playSong(song, queue, { replaceQueue: true, autoplay: Boolean(room.is_playing) }); else if (room.is_playing && !playerState.isPlaying) play(); else if (!room.is_playing && playerState.isPlaying) pause(); window.setTimeout(() => { seek(position); if (!room.is_playing) pause(); }, sameSong ? 0 : 180); updateRoomSessionVersion(room.state_version); };

const pullMemberState = async () => { if (!roomSession.roomId || roomSession.isHost || !roomSession.syncEnabled) return; try { const room = await getListeningRoom(roomSession.roomId); const version = Number(room?.state_version || 0); latestRoom = room; if (version > Number(roomSession.stateVersion || 0)) applyRoomState(room); } catch (error) { if (error.status !== 403 && error.status !== 410) console.warn('[LuNu room sync] member pull failed', error); } };
const tick = () => { if (!roomSession.roomId) return; if (roomSession.isHost) publishHostState(); else pullMemberState(); };

onMounted(() => { timer = window.setInterval(tick, 1000); });
onBeforeUnmount(() => { if (timer) window.clearInterval(timer); timer = null; latestRoom = null; });
</script>

<style scoped>.room-sync-bridge { display: none; }</style>
