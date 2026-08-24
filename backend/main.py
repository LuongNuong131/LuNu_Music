import os
import uuid
import yt_dlp
import cloudinary
import cloudinary.uploader
import tempfile
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )
except Exception as e:
    print("⚠️ Cảnh báo: Lỗi cấu hình Cloudinary -", e)

try:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Cảnh báo: Thiếu URL hoặc KEY của Supabase trong file .env!")
        supabase = None
    else:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print("⚠️ Cảnh báo: Lỗi kết nối Supabase -", e)
    supabase = None

class AddSongRequest(BaseModel):
    video_id: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


def get_ydl_opts(is_download=False, temp_dir=None):
    """Hàm tạo cấu hình yt-dlp tích hợp sẵn Cookie nếu có"""
    opts = {
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'}
    }
    
    # Kiểm tra xem có file cookies.txt do Render truyền vào không
    cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
    if os.path.exists(cookie_path):
        opts['cookiefile'] = cookie_path
        print("✅ Đã nạp thành công Giấy thông hành (cookies.txt)!")
    else:
        print("⚠️ Không tìm thấy cookies.txt, quá trình tải có thể bị YouTube chặn.")

    if is_download and temp_dir:
        opts.update({
            'format': 'bestaudio/best',
            'noplaylist': True,
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })
    else:
        opts.update({
            'extract_flat': True,
            'quiet': True
        })
        
    return opts


def process_and_upload_song(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    temp_dir = tempfile.gettempdir()
    ydl_opts = get_ydl_opts(is_download=True, temp_dir=temp_dir)

    try:
        print(f"⏳ Đang tải MP3 từ YouTube (Có Cookie): {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            title = info.get('title', 'Đang cập nhật')
            artist = info.get('uploader', 'Đang cập nhật')
            thumbnail = info.get('thumbnail', f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg")
            
            file_name = os.path.join(temp_dir, f"{video_id}.mp3")

            print(f"⏳ Đang đẩy lên mây Cloudinary: {file_name}...")
            result = cloudinary.uploader.upload(
                file_name,
                resource_type="video",
                folder="lunu_music",
                use_filename=True,
                unique_filename=False,
                overwrite=True
            )
            
            secure_url = result.get("secure_url")
            print(f"✅ Tải lên thành công: {secure_url}")

            if supabase:
                print("⏳ Đang ghi thông tin vào Supabase...")
                song_data = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "artist": artist,
                    "url": secure_url,
                    "cover": thumbnail,
                    "lyrics": "Đang cập nhật..."
                }
                supabase.table("songs").insert(song_data).execute()
                print("🎉 HOÀN TẤT!")
            else:
                print("❌ Lỗi: Chưa kết nối được Supabase!")

            if os.path.exists(file_name):
                os.remove(file_name)

    except Exception as e:
        print(f"❌ Lỗi khi xử lý bài hát ID '{video_id}': {e}")


@app.get("/api/songs")
async def get_songs():
    try:
        if not supabase: return []
        response = supabase.table("songs").select("*").execute()
        return response.data
    except Exception as e:
        print("Lỗi get_songs:", str(e))
        return []

@app.get("/api/songs/search_youtube")
async def search_youtube(query: str):
    ydl_opts = get_ydl_opts(is_download=False)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            results = []
            if 'entries' in info:
                for entry in info['entries']:
                    results.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'uploader': entry.get('uploader', entry.get('channel', 'Kênh Youtube')),
                    })
            return {"success": True, "results": results}
    except Exception as e:
        print("❌ Lỗi tìm kiếm YouTube:", str(e))
        return {"success": False, "message": "Lỗi khi tìm kiếm. Có thể do YouTube chặn."}

@app.post("/api/songs/add")
async def add_song(request: AddSongRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_and_upload_song, request.video_id)
    return {"message": "Đang xử lý tải mp3 từ Video ông chọn. Cưng chờ xíu nha!"}

@app.delete("/api/songs/{song_id}")
async def delete_song(song_id: str):
    try:
        if not supabase: return {"success": False, "message": "Lỗi kết nối Supabase"}
        supabase.table("songs").delete().eq("id", song_id).execute()
        return {"success": True, "message": "Đã xóa bài hát khỏi hệ thống"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi DB: {str(e)}"}

@app.post("/api/login")
async def login(req: LoginRequest):
    try:
        if not supabase:
            return {"success": False, "message": "Server mất kết nối với Supabase."}
            
        res = supabase.table("users").select("*").eq("username", req.username).eq("password", req.password).execute()
        if len(res.data) > 0:
            user_info = {"id": res.data[0]["id"], "username": res.data[0]["username"], "role": res.data[0]["role"]}
            return {"success": True, "user": user_info}
        return {"success": False, "message": "Sai tên tài khoản hoặc mật khẩu!"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi từ máy chủ: {str(e)}"}

@app.get("/api/users")
async def get_users():
    try:
        if not supabase: return []
        res = supabase.table("users").select("id, username, role").execute()
        return res.data
    except Exception as e:
        print("Lỗi get_users:", str(e))
        return []

@app.post("/api/users/add")
async def add_user(req: UserRequest):
    try:
        if not supabase: return {"success": False, "message": "Lỗi kết nối Supabase"}
        new_user = {"username": req.username, "password": req.password, "role": req.role}
        supabase.table("users").insert(new_user).execute()
        return {"success": True, "message": "Đã cấp tài khoản thành công"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi DB: {str(e)}"}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    try:
        if not supabase: return {"success": False, "message": "Lỗi kết nối Supabase"}
        supabase.table("users").delete().eq("id", user_id).execute()
        return {"success": True, "message": "Đã thu hồi tài khoản"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi DB: {str(e)}"}