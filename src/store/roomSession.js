import { reactive } from 'vue';

export const roomSession = reactive({
  roomId: '',
  isHost: false,
  syncEnabled: false,
  stateVersion: 0,
});

export const openRoomSession = (room, userId) => {
  const id = String(userId || '');
  roomSession.roomId = String(room?.id || '');
  roomSession.isHost = Boolean(id && (String(room?.host_id || '') === id || room?.members?.some((member) => member.role === 'host' && String(member.user_id) === id)));
  roomSession.syncEnabled = false;
  roomSession.stateVersion = Number(room?.state_version || 0);
};

export const setRoomSyncEnabled = (enabled, stateVersion = roomSession.stateVersion) => {
  roomSession.syncEnabled = Boolean(enabled);
  roomSession.stateVersion = Number(stateVersion || roomSession.stateVersion || 0);
};

export const updateRoomSessionVersion = (version) => {
  roomSession.stateVersion = Number(version || roomSession.stateVersion || 0);
};

export const closeRoomSession = () => {
  roomSession.roomId = '';
  roomSession.isHost = false;
  roomSession.syncEnabled = false;
  roomSession.stateVersion = 0;
};
