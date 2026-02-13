import os
import aiofiles
from typing import Optional
from app.domain.interfaces import StorageProvider
from app.core.config import settings

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_path: str = settings.STORAGE_PATH):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

    async def save_file(self, content: bytes, filename: str) -> str:
        file_path = os.path.join(self.base_path, filename)
        async with aiofiles.open(file_path, mode='wb') as f:
            await f.write(content)
        return file_path
    
    async def get_file_url(self, filename: str) -> str:
        """로컬 파일의 상대 경로를 반환합니다."""
        return f"/storage/assets/{filename}"

class S3StorageProvider(StorageProvider):
    def __init__(
        self, 
        bucket_name: str = settings.AWS_S3_BUCKET_NAME,
        region: str = settings.AWS_REGION
    ):
        import boto3
        from botocore.exceptions import NoCredentialsError
        
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=region
        )

    async def save_file(self, content: bytes, filename: str) -> str:
        # 비동기 처리를 위해 run_in_executor 등을 사용할 수 있으나, 
        # 여기서는 단순화를 위해 직접 boto3를 호출하는 예시로 작성합니다.
        # 실제 운영 환경에서는 aioboto3 등을 권장합니다.
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=filename,
            Body=content
        )
        return f"s3://{self.bucket_name}/{filename}"
    
    async def get_file_url(self, filename: str) -> str:
        """S3 파일의 pre-signed URL을 반환합니다."""
        url = self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': filename},
            ExpiresIn=3600  # 1시간 유효
        )
        return url

def get_storage_provider() -> StorageProvider:
    if settings.STORAGE_TYPE == "s3":
        return S3StorageProvider()
    return LocalStorageProvider()
