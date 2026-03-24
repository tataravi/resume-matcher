import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError
import structlog

from src.config import settings


logger = structlog.get_logger()


class S3Service:
    """Service for AWS S3 operations."""
    
    def __init__(
        self,
        bucket_name: str = settings.aws_s3_bucket,
        region_name: str = settings.aws_region,
        aws_access_key_id: str = settings.aws_access_key_id,
        aws_secret_access_key: str = settings.aws_secret_access_key
    ):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
    async def upload_file(
        self,
        content: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
        server_side_encryption: str = "AES256"
    ) -> Dict[str, Any]:
        """Upload a file to S3."""
        
        try:
            async with self.session.client('s3') as s3_client:
                extra_args = {
                    'ContentType': content_type,
                    'ServerSideEncryption': server_side_encryption
                }
                
                if metadata:
                    extra_args['Metadata'] = metadata
                
                logger.info(
                    "s3_upload_start",
                    bucket=self.bucket_name,
                    key=key,
                    content_length=len(content),
                    content_type=content_type
                )
                
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content,
                    **extra_args
                )
                
                # Get object info
                response = await s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                
                result = {
                    "bucket": self.bucket_name,
                    "key": key,
                    "etag": response.get("ETag", "").strip('"'),
                    "size": response.get("ContentLength", len(content)),
                    "last_modified": response.get("LastModified"),
                    "content_type": response.get("ContentType", content_type),
                    "server_side_encryption": response.get("ServerSideEncryption"),
                    "metadata": response.get("Metadata", {})
                }
                
                logger.info(
                    "s3_upload_success",
                    bucket=self.bucket_name,
                    key=key,
                    etag=result["etag"],
                    size=result["size"]
                )
                
                return result
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "s3_upload_error",
                bucket=self.bucket_name,
                key=key,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "s3_upload_unexpected_error",
                bucket=self.bucket_name,
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def download_file(self, key: str) -> bytes:
        """Download a file from S3."""
        
        try:
            async with self.session.client('s3') as s3_client:
                logger.info(
                    "s3_download_start",
                    bucket=self.bucket_name,
                    key=key
                )
                
                response = await s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                
                content = await response['Body'].read()
                
                logger.info(
                    "s3_download_success",
                    bucket=self.bucket_name,
                    key=key,
                    content_length=len(content)
                )
                
                return content
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "s3_download_error",
                bucket=self.bucket_name,
                key=key,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "s3_download_unexpected_error",
                bucket=self.bucket_name,
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def delete_file(self, key: str) -> bool:
        """Delete a file from S3."""
        
        try:
            async with self.session.client('s3') as s3_client:
                logger.info(
                    "s3_delete_start",
                    bucket=self.bucket_name,
                    key=key
                )
                
                await s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                
                logger.info(
                    "s3_delete_success",
                    bucket=self.bucket_name,
                    key=key
                )
                
                return True
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "s3_delete_error",
                bucket=self.bucket_name,
                key=key,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "s3_delete_unexpected_error",
                bucket=self.bucket_name,
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        
        try:
            async with self.session.client('s3') as s3_client:
                await s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                return True
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404':
                return False
            else:
                logger.error(
                    "s3_file_exists_error",
                    bucket=self.bucket_name,
                    key=key,
                    error_code=error_code,
                    error_message=str(e)
                )
                raise
        except Exception as e:
            logger.error(
                "s3_file_exists_unexpected_error",
                bucket=self.bucket_name,
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def list_files(
        self,
        prefix: str = "",
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """List files in S3 bucket with optional prefix filter."""
        
        try:
            async with self.session.client('s3') as s3_client:
                logger.info(
                    "s3_list_start",
                    bucket=self.bucket_name,
                    prefix=prefix,
                    max_keys=max_keys
                )
                
                kwargs = {
                    'Bucket': self.bucket_name,
                    'MaxKeys': max_keys
                }
                
                if prefix:
                    kwargs['Prefix'] = prefix
                
                response = await s3_client.list_objects_v2(**kwargs)
                
                files = []
                for obj in response.get('Contents', []):
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag'].strip('"'),
                        'storage_class': obj.get('StorageClass', 'STANDARD')
                    })
                
                logger.info(
                    "s3_list_success",
                    bucket=self.bucket_name,
                    prefix=prefix,
                    file_count=len(files),
                    is_truncated=response.get('IsTruncated', False)
                )
                
                return files
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "s3_list_error",
                bucket=self.bucket_name,
                prefix=prefix,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "s3_list_unexpected_error",
                bucket=self.bucket_name,
                prefix=prefix,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        http_method: str = 'GET'
    ) -> str:
        """Generate a presigned URL for file access."""
        
        try:
            async with self.session.client('s3') as s3_client:
                operation_name = 'get_object' if http_method == 'GET' else 'put_object'
                
                url = await s3_client.generate_presigned_url(
                    operation_name,
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
                
                logger.info(
                    "s3_presigned_url_generated",
                    bucket=self.bucket_name,
                    key=key,
                    expiration=expiration,
                    http_method=http_method
                )
                
                return url
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "s3_presigned_url_error",
                bucket=self.bucket_name,
                key=key,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "s3_presigned_url_unexpected_error",
                bucket=self.bucket_name,
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def copy_file(
        self,
        source_key: str,
        destination_key: str,
        source_bucket: Optional[str] = None
    ) -> Dict[str, Any]:
        """Copy a file within S3."""
        
        source_bucket = source_bucket or self.bucket_name
        
        try:
            async with self.session.client('s3') as s3_client:
                copy_source = {
                    'Bucket': source_bucket,
                    'Key': source_key
                }
                
                logger.info(
                    "s3_copy_start",
                    source_bucket=source_bucket,
                    source_key=source_key,
                    destination_bucket=self.bucket_name,
                    destination_key=destination_key
                )
                
                await s3_client.copy_object(
                    CopySource=copy_source,
                    Bucket=self.bucket_name,
                    Key=destination_key
                )
                
                # Get copied object info
                response = await s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=destination_key
                )
                
                result = {
                    "source_bucket": source_bucket,
                    "source_key": source_key,
                    "destination_bucket": self.bucket_name,
                    "destination_key": destination_key,
                    "etag": response.get("ETag", "").strip('"'),
                    "size": response.get("ContentLength"),
                    "last_modified": response.get("LastModified")
                }
                
                logger.info(
                    "s3_copy_success",
                    source_bucket=source_bucket,
                    source_key=source_key,
                    destination_bucket=self.bucket_name,
                    destination_key=destination_key
                )
                
                return result
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "s3_copy_error",
                source_bucket=source_bucket,
                source_key=source_key,
                destination_bucket=self.bucket_name,
                destination_key=destination_key,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "s3_copy_unexpected_error",
                source_bucket=source_bucket,
                source_key=source_key,
                destination_bucket=self.bucket_name,
                destination_key=destination_key,
                error=str(e),
                error_type=type(e).__name__
            )
            raise


# Global S3 service instance
_s3_service = None


async def get_s3_service() -> S3Service:
    """Dependency injection for S3 service."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service