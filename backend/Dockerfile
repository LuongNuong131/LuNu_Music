# Đã nâng cấp lên Python 3.11 để Render hết báo lỗi Deprecated
FROM python:3.11-slim

# Cập nhật và cài đặt FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements.txt và cài thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code BE vào container
COPY . .

# Mở cổng
EXPOSE 8000

# Lệnh khởi chạy server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]