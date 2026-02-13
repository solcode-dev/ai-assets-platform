import os
import pytest
from unittest.mock import patch, MagicMock
from app.infrastructure.storage import LocalStorageProvider, S3StorageProvider, get_storage_provider
from app.core.config import settings

pytestmark = pytest.mark.unit

class TestLocalStorageProvider:
    @pytest.fixture
    def provider(self, tmp_path):
        return LocalStorageProvider(base_path=str(tmp_path))

    def test_init_creates_directory(self, tmp_path):
        new_path = tmp_path / "new_storage"
        LocalStorageProvider(base_path=str(new_path))
        assert os.path.exists(new_path)

    @pytest.mark.asyncio
    async def test_save_file(self, provider, tmp_path):
        content = b"test content"
        filename = "test.txt"
        
        # 실제 파일 시스템을 사용하는 통합 테스트 성격의 단위 테스트
        # (LocalStorage가 간단하므로 직접 검증)
        path = await provider.save_file(content, filename)
        
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read() == content

    @pytest.mark.asyncio
    async def test_get_file_url(self, provider):
        url = await provider.get_file_url("test.png")
        assert url == "/storage/assets/test.png"

class TestS3StorageProvider:
    @patch("boto3.client")
    def test_init_s3_client(self, mock_boto):
        S3StorageProvider(bucket_name="test-bucket", region="us-east-1")
        mock_boto.assert_called_once_with(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name="us-east-1"
        )

    @pytest.mark.asyncio
    @patch("boto3.client")
    async def test_save_file_s3(self, mock_boto):
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        provider = S3StorageProvider(bucket_name="test-bucket")
        content = b"s3 content"
        filename = "s3_test.png"
        
        result = await provider.save_file(content, filename)
        
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=filename,
            Body=content
        )
        assert result == "s3://test-bucket/s3_test.png"

    @pytest.mark.asyncio
    @patch("boto3.client")
    async def test_get_file_url_s3(self, mock_boto):
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"
        
        provider = S3StorageProvider(bucket_name="test-bucket")
        url = await provider.get_file_url("test.png")
        
        mock_s3.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': "test-bucket", 'Key': "test.png"},
            ExpiresIn=3600
        )
        assert url == "https://presigned-url.com"

class TestGetStorageProvider:
    def test_get_storage_provider_local(self):
        with patch("app.infrastructure.storage.settings") as mock_settings:
            mock_settings.STORAGE_TYPE = "local"
            provider = get_storage_provider()
            assert isinstance(provider, LocalStorageProvider)

    def test_get_storage_provider_s3(self):
        with patch("app.infrastructure.storage.settings") as mock_settings:
            mock_settings.STORAGE_TYPE = "s3"
            # S3StorageProvider.__init__ 내부의 boto3 임포트 대응
            with patch("boto3.client"):
                provider = get_storage_provider()
                assert isinstance(provider, S3StorageProvider)
