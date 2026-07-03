// src/data/songs.js
// Nơi chứa dữ liệu bài hát, liên kết trực tiếp với repo luongnuong131/db_lunumusic

// Đường dẫn gốc trỏ vào đúng thư mục chứa nhạc trên GitHub của ông
const baseUrl = 'https://raw.githubusercontent.com/luongnuong131/db_lunumusic/main/DB_LuNuMusic-66d75bbf04dc13b143139b727fe94d48741dd8cc/';

// Hàm encode tên file để trình duyệt không bị lỗi khi đọc dấu cách và ký tự đặc biệt
const getAudioUrl = (fileName) => baseUrl + encodeURIComponent(fileName);

export const songs = [
  // ==========================================
  // LIST NHẠC CỦA DONALD GOLD
  // ==========================================
  {
    id: 1,
    title: 'Quan Hệ Rộng',
    artist: 'Donald Gold',
    cover: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300&q=80',
    url: getAudioUrl('Quan Hệ Rộng - Donald Gold.mp3')
  },
  {
    id: 2,
    title: 'Ngáo Ngơ Hết Ngày',
    artist: 'Donald Gold',
    cover: 'https://images.unsplash.com/photo-1493225457124-a1a2a29ce73?w=300&q=80',
    url: getAudioUrl('Ngáo Ngơ Hết Ngày - Donald Gold.mp3')
  },
  {
    id: 3,
    title: 'Đỉnh (Sao Hạng A Dissing)',
    artist: 'Donald Gold',
    cover: 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&q=80',
    url: getAudioUrl('Donald Gold - Đỉnh [ Sao Hạng A Dissing ] - Donald Gold.mp3')
  },
  {
    id: 4,
    title: 'Trăng Hoa Mây Mưa',
    artist: 'Donald Gold',
    cover: 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&q=80',
    url: getAudioUrl('Donald Gold - Trăng Hoa Mây Mưa - Donald Gold.mp3')
  },
  {
    id: 5,
    title: 'OBGTLH',
    artist: 'Donald Gold x Lil Shady',
    cover: 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=300&q=80',
    url: getAudioUrl('Donald Gold - OBGTLH x Lil Shady  Official MV - Donald Gold.mp3')
  },
  {
    id: 6,
    title: 'Lái Máy Bay',
    artist: 'Donald Gold',
    cover: 'https://images.unsplash.com/photo-1571330804093-g219a16f21c2?w=300&q=80',
    url: getAudioUrl('Donald Gold - Lái Máy Bay   Official Lyrics Video - Donald Gold.mp3')
  },
  {
    id: 7,
    title: 'Đổi Tư Thế',
    artist: 'Donald Gold x Andree Right Hand',
    cover: 'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=300&q=80',
    url: getAudioUrl('DONALD GOLD - ĐỔI TƯ THẾ x ANDREE RIGHT HAND  OFFICIAL MUSIC VIDEO - Donald Gold.mp3')
  },
  {
    id: 8,
    title: 'ADAMN',
    artist: 'Donald Gold',
    cover: 'https://images.unsplash.com/photo-1598387993441-a364f854c3e1?w=300&q=80',
    url: getAudioUrl('DONALD GOLD - ADAMN  [OFFICIAL MV] - Donald Gold.mp3')
  },
  {
    id: 9,
    title: 'BCDBL',
    artist: 'Donald Gold',
    cover: 'https://images.unsplash.com/photo-1483058712412-4245e9b90334?w=300&q=80',
    url: getAudioUrl('BCDBL - Donald Gold.mp3')
  },

  // ==========================================
  // LIST NHẠC CỦA ANDREE RIGHT HAND
  // ==========================================
  {
    id: 10,
    title: 'Chơi Như Tụi Mỹ',
    artist: 'Andree Right Hand',
    cover: 'https://images.unsplash.com/photo-1506157786151-b8491531f063?w=300&q=80',
    url: getAudioUrl('Andree Right Hand - Ch i Nh   Official MV - Andree Right Hand.mp3')
  },
  {
    id: 11,
    title: 'Công Ty 4',
    artist: 'Andree Right Hand ft. Dangrangto, TeuYungBoy, WOKEUP',
    cover: 'https://images.unsplash.com/photo-1520008358485-802521fde5d0?w=300&q=80',
    url: getAudioUrl('Andree Right Hand - C ng Ty 4 ft. Dangrangto, TeuYungBoy, WOKEUP  Official MV - Andree Right Hand.mp3')
  },
  {
    id: 12,
    title: 'Em Iu (Cleaned Version)',
    artist: 'Andree Right Hand ft. Wxrdie, Bình Gold, 2pillz',
    cover: 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=300&q=80',
    url: getAudioUrl('Andree Right Hand - Em iu feat. Wxrdie, Bình Gold, 2pillz  Official MV (CLEANED VERSION) - Andree Right Hand.mp3')
  }
];