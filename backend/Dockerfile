FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    wget \
    curl \
    procps \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 스토리지 디렉토리 생성
RUN mkdir -p /app/storage/assets

# 엔트리포인트 스크립트 권한 설정 및 줄바꿈 처리 (Windows 환경 대응)
# 로컬 볼륨 마운트로 인해 다시 CRLF로 변경되는 것을 방지하기 위해 시스템 경로로 복사하여 사용
COPY entrypoint.sh /usr/local/bin/
RUN dos2unix /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

