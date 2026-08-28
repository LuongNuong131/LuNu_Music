<template>
  <Teleport to="body">
    <Transition name="concierge-fade">
      <div v-if="visible" class="concierge-overlay" @click.self="close">
        <section class="concierge-panel" role="dialog" aria-modal="true" aria-labelledby="concierge-title">
          <header class="concierge-header">
            <div class="concierge-brand">
              <span class="concierge-orb">✦</span>
              <div>
                <p class="concierge-kicker">LUNU AI / MUSIC CONCIERGE</p>
                <h2 id="concierge-title">Chọn nhạc theo mood.</h2>
              </div>
            </div>
            <button type="button" class="concierge-close" aria-label="Đóng AI Concierge" @click="close">×</button>
          </header>

          <div ref="messageList" class="concierge-messages">
            <div v-if="!messages.length" class="concierge-welcome">
              <p class="concierge-eyebrow">A LITTLE HELP FOR YOUR HEADPHONES</p>
              <h3>Nay bạn đang<br /><em>cảm thấy thế nào?</em></h3>
              <p class="concierge-welcome-copy">Kể cho t nghe một câu. T sẽ tìm những giai điệu hợp với khoảnh khắc này.</p>
              <div class="quick-prompts">
                <button v-for="prompt in quickPrompts" :key="prompt" type="button" @click="sendPrompt(prompt)">{{ prompt }}</button>
              </div>
            </div>

            <article v-for="(item, index) in messages" :key="`${item.role}-${index}`" class="concierge-message" :class="item.role">
              <div v-if="item.role === 'assistant'" class="assistant-avatar">✦</div>
              <div class="message-content">
                <p class="message-copy">{{ item.content }}</p>
                <span v-if="item.mood" class="mood-pill">{{ item.mood }}</span>
                <div v-if="item.recommendations?.length" class="ai-recommendations">
                  <div class="recommendation-heading"><span>GỢI Ý CHO BẠN</span><small>{{ item.recommendations.length }} bài</small></div>
                  <div class="ai-song-list">
                    <div v-for="song in item.recommendations" :key="song.id" class="ai-song-card">
                      <img :src="song.cover || '/images/ChoCiu.jpg'" :alt="song.title" />
                      <div class="ai-song-info"><strong>{{ song.title }}</strong><span>{{ song.artist }}</span><small>{{ song.reason }}</small></div>
                      <div class="ai-song-actions">
                        <button type="button" class="ai-play" :aria-label="`Phát ${song.title}`" @click="emit('play-song', song)">▶</button>
                        <button type="button" class="ai-queue" :aria-label="`Thêm ${song.title} vào hàng đợi`" @click="emit('queue-song', song)">+</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </article>
            <div v-if="loading" class="concierge-thinking"><span class="thinking-orb">✦</span><span>Đang tìm đúng giai điệu...</span><i></i><i></i><i></i></div>
          </div>

          <footer class="concierge-composer">
            <div class="composer-hint"><span>AI</span><small>Gemini đang tìm trong thư viện LuNu</small></div>
            <form class="composer-form" @submit.prevent="sendPrompt(draft)">
              <input ref="inputRef" v-model="draft" type="text" maxlength="1200" placeholder="Ví dụ: nay t buồn, cho t nhạc thất tình..." :disabled="loading" />
              <button type="submit" :disabled="loading || draft.trim().length < 2" aria-label="Gửi tin nhắn">↗</button>
            </form>
            <p v-if="error" class="concierge-error">{{ error }}</p>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue';
import { getAIConcierge } from '../services/api';

const props = defineProps({ visible: Boolean });
const emit = defineEmits(['close', 'play-song', 'queue-song']);
const draft = ref('');
const loading = ref(false);
const error = ref('');
const messages = ref([]);
const messageList = ref(null);
const inputRef = ref(null);
const quickPrompts = ['Nay t buồn, cho t nhạc thất tình', 'Cho t nhạc chill để làm việc', 'T muốn nghe gì đó thật tích cực'];

const scrollToBottom = async () => {
  await nextTick();
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight;
};
const close = () => emit('close');
const sendPrompt = async (value) => {
  const content = String(value || '').trim();
  if (!content || loading.value) return;
  draft.value = '';
  error.value = '';
  const history = messages.value.slice(-8).map((item) => ({ role: item.role, content: item.content }));
  messages.value.push({ role: 'user', content });
  loading.value = true;
  await scrollToBottom();
  try {
    const response = await getAIConcierge(content, history);
    messages.value.push({ role: 'assistant', content: response.message, mood: response.mood, recommendations: response.recommendations || [] });
  } catch (cause) {
    error.value = cause.message || 'AI đang bận một chút. Thử lại sau nhé.';
  } finally {
    loading.value = false;
    await scrollToBottom();
    await nextTick();
    inputRef.value?.focus();
  }
};
watch(() => props.visible, async (visible) => {
  if (visible) {
    error.value = '';
    await nextTick();
    inputRef.value?.focus();
  }
});
onBeforeUnmount(() => { messages.value = []; });
</script>

<style scoped>
.concierge-overlay { position: fixed; inset: 0; z-index: 410; display: flex; justify-content: flex-end; padding: 18px; background: rgba(4, 6, 11, .58); backdrop-filter: blur(12px); }
.concierge-panel { display: flex; flex-direction: column; width: min(470px, 100%); height: min(760px, calc(100vh - 36px)); overflow: hidden; border: 1px solid rgba(245,185,122,.23); border-radius: 24px; background: linear-gradient(145deg, rgba(23,27,39,.98), rgba(10,13,21,.99)); box-shadow: 0 30px 90px rgba(0,0,0,.5), 0 0 0 1px rgba(255,255,255,.025); }
.concierge-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; padding: 25px 24px 19px; border-bottom: 1px solid rgba(255,255,255,.07); }
.concierge-brand { display: flex; align-items: center; gap: 12px; }.concierge-orb { display: grid; place-items: center; width: 37px; height: 37px; border-radius: 12px; background: linear-gradient(135deg, var(--gold-bright), var(--coral)); color: #161017; box-shadow: 0 10px 26px rgba(245,185,122,.2); }.concierge-kicker,.concierge-eyebrow,.recommendation-heading span { margin: 0; color: var(--gold); font: 8px var(--font-mono); letter-spacing: 1.7px; }.concierge-header h2 { margin-top: 6px; color: var(--text-main); font: 500 25px var(--font-display); letter-spacing: -.6px; }.concierge-close { display: grid; place-items: center; width: 32px; height: 32px; border: 1px solid var(--hairline); border-radius: 10px; background: var(--glass); color: var(--text-main); cursor: pointer; font-size: 22px; }.concierge-close:hover { color: var(--gold); background: var(--glass-strong); }
.concierge-messages { flex: 1; min-height: 0; overflow: auto; padding: 23px 20px 15px; }.concierge-welcome { padding: 13px 6px 12px; }.concierge-welcome h3 { margin-top: 16px; color: var(--text-main); font: 500 36px/1 var(--font-display); letter-spacing: -1.8px; }.concierge-welcome h3 em { color: var(--gold-bright); font-style: italic; }.concierge-welcome-copy { max-width: 330px; margin-top: 17px; color: var(--text-sub); font-size: 11px; line-height: 1.55; }.quick-prompts { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }.quick-prompts button { padding: 9px 11px; border: 1px solid var(--hairline); border-radius: 99px; background: rgba(255,255,255,.035); color: var(--text-sub); cursor: pointer; font-size: 10px; text-align: left; }.quick-prompts button:hover { border-color: rgba(245,185,122,.35); background: rgba(245,185,122,.08); color: var(--text-main); }
.concierge-message { display: flex; gap: 9px; margin: 15px 0; }.concierge-message.user { justify-content: flex-end; }.assistant-avatar { display: grid; place-items: center; flex: none; width: 24px; height: 24px; margin-top: 3px; border-radius: 8px; background: rgba(245,185,122,.14); color: var(--gold); font-size: 13px; }.message-content { max-width: 91%; }.message-copy { padding: 11px 13px; border: 1px solid var(--hairline-soft); border-radius: 14px 14px 14px 4px; background: rgba(255,255,255,.045); color: var(--text-main); font-size: 11px; line-height: 1.55; white-space: pre-wrap; }.user .message-copy { border-color: rgba(245,185,122,.18); border-radius: 14px 14px 4px 14px; background: linear-gradient(135deg, rgba(245,185,122,.18), rgba(245,185,122,.07)); }.mood-pill { display: inline-block; margin: 7px 0 0 3px; color: var(--gold); font: 8px var(--font-mono); letter-spacing: 1px; text-transform: uppercase; }
.ai-recommendations { margin-top: 13px; }.recommendation-heading { display: flex; align-items: center; justify-content: space-between; padding: 0 3px 8px; }.recommendation-heading small { color: var(--text-faint); font: 8px var(--font-mono); }.ai-song-list { display: grid; gap: 7px; }.ai-song-card { display: flex; align-items: center; gap: 9px; padding: 8px; border: 1px solid var(--hairline-soft); border-radius: 13px; background: rgba(255,255,255,.035); }.ai-song-card img { width: 43px; height: 43px; flex: none; border-radius: 9px; object-fit: cover; }.ai-song-info { display: flex; flex: 1; flex-direction: column; min-width: 0; }.ai-song-info strong,.ai-song-info span,.ai-song-info small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.ai-song-info strong { color: var(--text-main); font-size: 10px; }.ai-song-info span { margin-top: 3px; color: var(--text-sub); font-size: 9px; }.ai-song-info small { margin-top: 5px; color: var(--text-faint); font-size: 8px; }.ai-song-actions { display: flex; gap: 5px; flex: none; }.ai-play,.ai-queue { display: grid; place-items: center; width: 29px; height: 29px; border: 1px solid var(--hairline); border-radius: 9px; cursor: pointer; }.ai-play { background: var(--gold-bright); color: #171019; }.ai-queue { background: transparent; color: var(--gold); font-size: 18px; }.ai-play:hover,.ai-queue:hover { transform: translateY(-1px); }
.concierge-thinking { display: flex; align-items: center; gap: 6px; padding: 10px 4px; color: var(--text-faint); font-size: 10px; }.thinking-orb { color: var(--gold); }.concierge-thinking i { width: 3px; height: 3px; border-radius: 50%; background: var(--gold); animation: concierge-blink 1s ease-in-out infinite; }.concierge-thinking i:nth-last-child(2) { animation-delay: .16s; }.concierge-thinking i:last-child { animation-delay: .32s; } @keyframes concierge-blink { 0%,100% { opacity: .25; transform: translateY(0); } 50% { opacity: 1; transform: translateY(-2px); } }
.concierge-composer { padding: 14px 18px max(17px, env(safe-area-inset-bottom)); border-top: 1px solid rgba(255,255,255,.07); background: rgba(8,10,16,.38); }.composer-hint { display: flex; align-items: center; gap: 7px; margin: 0 3px 9px; }.composer-hint span { color: var(--gold); font: 8px var(--font-mono); letter-spacing: 1px; }.composer-hint small { color: var(--text-faint); font-size: 9px; }.composer-form { display: flex; align-items: center; gap: 8px; padding: 6px 7px 6px 13px; border: 1px solid var(--hairline); border-radius: 14px; background: rgba(255,255,255,.05); }.composer-form:focus-within { border-color: rgba(245,185,122,.5); box-shadow: 0 0 0 3px rgba(245,185,122,.08); }.composer-form input { flex: 1; min-width: 0; border: 0; outline: 0; background: transparent; color: var(--text-main); font-size: 11px; }.composer-form input::placeholder { color: var(--text-faint); }.composer-form button { display: grid; place-items: center; width: 34px; height: 34px; border: 0; border-radius: 10px; background: var(--gold-bright); color: #171019; cursor: pointer; font-size: 18px; }.composer-form button:disabled { opacity: .35; cursor: not-allowed; }.concierge-error { margin: 8px 3px 0; color: var(--crimson); font-size: 9px; line-height: 1.4; }.concierge-fade-enter-active,.concierge-fade-leave-active { transition: opacity .22s ease; }.concierge-fade-enter-from,.concierge-fade-leave-to { opacity: 0; }.concierge-fade-enter-active .concierge-panel,.concierge-fade-leave-active .concierge-panel { transition: transform .28s var(--ease-out); }.concierge-fade-enter-from .concierge-panel,.concierge-fade-leave-to .concierge-panel { transform: translateX(35px); }
@media (max-width: 640px) { .concierge-overlay { align-items: flex-end; padding: 0; }.concierge-panel { width: 100%; height: min(760px, 92dvh); border-right: 0; border-bottom: 0; border-radius: 23px 23px 0 0; }.concierge-header { padding: 20px 17px 15px; }.concierge-messages { padding: 18px 14px 12px; }.concierge-welcome h3 { font-size: 32px; }.concierge-composer { padding-inline: 13px; } }
</style>
