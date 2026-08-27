import { reactive } from 'vue';

export const chatSession = reactive({ selectedId: '', selectedKind: '' });

export const selectChatConversation = (conversation) => {
  chatSession.selectedId = String(conversation?.id || '');
  chatSession.selectedKind = conversation?.kind || '';
};

export const clearChatConversation = () => {
  chatSession.selectedId = '';
  chatSession.selectedKind = '';
};
