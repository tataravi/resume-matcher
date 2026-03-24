import asyncio
import json
from typing import Dict, Optional, Any, List
from datetime import datetime
import aioboto3
from botocore.exceptions import ClientError
import structlog

from src.config import settings


logger = structlog.get_logger()


class SQSService:
    """Service for AWS SQS operations."""
    
    def __init__(
        self,
        queue_url: str = settings.aws_sqs_queue_url,
        region_name: str = settings.aws_region,
        aws_access_key_id: str = settings.aws_access_key_id,
        aws_secret_access_key: str = settings.aws_secret_access_key
    ):
        self.queue_url = queue_url
        self.region_name = region_name
        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
    async def send_message(
        self,
        message_body: Dict[str, Any],
        delay_seconds: int = 0,
        message_attributes: Optional[Dict[str, Any]] = None,
        message_group_id: Optional[str] = None,
        message_deduplication_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to SQS queue."""
        
        try:
            async with self.session.client('sqs') as sqs_client:
                # Convert message body to JSON string
                message_body_str = json.dumps(message_body, default=str)
                
                send_params = {
                    'QueueUrl': self.queue_url,
                    'MessageBody': message_body_str
                }
                
                if delay_seconds > 0:
                    send_params['DelaySeconds'] = delay_seconds
                    
                if message_attributes:
                    send_params['MessageAttributes'] = self._format_message_attributes(
                        message_attributes
                    )
                    
                # For FIFO queues
                if message_group_id:
                    send_params['MessageGroupId'] = message_group_id
                    
                if message_deduplication_id:
                    send_params['MessageDeduplicationId'] = message_deduplication_id
                
                logger.info(
                    "sqs_send_start",
                    queue_url=self.queue_url,
                    message_size=len(message_body_str),
                    delay_seconds=delay_seconds,
                    message_group_id=message_group_id
                )
                
                response = await sqs_client.send_message(**send_params)
                
                result = {
                    "message_id": response['MessageId'],
                    "md5_of_body": response['MD5OfBody'],
                    "md5_of_message_attributes": response.get('MD5OfMessageAttributes'),
                    "sequence_number": response.get('SequenceNumber'),  # FIFO queues only
                    "queue_url": self.queue_url
                }
                
                logger.info(
                    "sqs_send_success",
                    queue_url=self.queue_url,
                    message_id=result['message_id'],
                    sequence_number=result.get('sequence_number')
                )
                
                return result
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "sqs_send_error",
                queue_url=self.queue_url,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "sqs_send_unexpected_error",
                queue_url=self.queue_url,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def receive_messages(
        self,
        max_number_of_messages: int = 1,
        wait_time_seconds: int = 20,
        visibility_timeout_seconds: Optional[int] = None,
        message_attribute_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Receive messages from SQS queue."""
        
        try:
            async with self.session.client('sqs') as sqs_client:
                receive_params = {
                    'QueueUrl': self.queue_url,
                    'MaxNumberOfMessages': max_number_of_messages,
                    'WaitTimeSeconds': wait_time_seconds
                }
                
                if visibility_timeout_seconds:
                    receive_params['VisibilityTimeout'] = visibility_timeout_seconds
                    
                if message_attribute_names:
                    receive_params['MessageAttributeNames'] = message_attribute_names
                else:
                    receive_params['MessageAttributeNames'] = ['All']
                
                logger.info(
                    "sqs_receive_start",
                    queue_url=self.queue_url,
                    max_messages=max_number_of_messages,
                    wait_time=wait_time_seconds
                )
                
                response = await sqs_client.receive_message(**receive_params)
                
                messages = []
                for message in response.get('Messages', []):
                    # Parse message body from JSON
                    try:
                        body = json.loads(message['Body'])
                    except json.JSONDecodeError:
                        body = message['Body']  # Keep as string if not valid JSON
                    
                    processed_message = {
                        "message_id": message['MessageId'],
                        "receipt_handle": message['ReceiptHandle'],
                        "body": body,
                        "md5_of_body": message['MD5OfBody'],
                        "attributes": message.get('Attributes', {}),
                        "message_attributes": self._parse_message_attributes(
                            message.get('MessageAttributes', {})
                        )
                    }
                    messages.append(processed_message)
                
                logger.info(
                    "sqs_receive_success",
                    queue_url=self.queue_url,
                    messages_received=len(messages)
                )
                
                return messages
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "sqs_receive_error",
                queue_url=self.queue_url,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "sqs_receive_unexpected_error",
                queue_url=self.queue_url,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def delete_message(self, receipt_handle: str) -> bool:
        """Delete a message from SQS queue."""
        
        try:
            async with self.session.client('sqs') as sqs_client:
                logger.info(
                    "sqs_delete_start",
                    queue_url=self.queue_url,
                    receipt_handle=receipt_handle[:20] + "..."  # Truncate for logging
                )
                
                await sqs_client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
                
                logger.info(
                    "sqs_delete_success",
                    queue_url=self.queue_url
                )
                
                return True
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "sqs_delete_error",
                queue_url=self.queue_url,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "sqs_delete_unexpected_error",
                queue_url=self.queue_url,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def delete_messages_batch(self, receipt_handles: List[str]) -> Dict[str, Any]:
        """Delete multiple messages from SQS queue in batch."""
        
        try:
            async with self.session.client('sqs') as sqs_client:
                # Prepare batch delete entries
                delete_entries = []
                for i, receipt_handle in enumerate(receipt_handles[:10]):  # Max 10 messages per batch
                    delete_entries.append({
                        'Id': str(i),
                        'ReceiptHandle': receipt_handle
                    })
                
                logger.info(
                    "sqs_batch_delete_start",
                    queue_url=self.queue_url,
                    message_count=len(delete_entries)
                )
                
                response = await sqs_client.delete_message_batch(
                    QueueUrl=self.queue_url,
                    Entries=delete_entries
                )
                
                result = {
                    "successful": response.get('Successful', []),
                    "failed": response.get('Failed', []),
                    "successful_count": len(response.get('Successful', [])),
                    "failed_count": len(response.get('Failed', []))
                }
                
                logger.info(
                    "sqs_batch_delete_success",
                    queue_url=self.queue_url,
                    successful_count=result['successful_count'],
                    failed_count=result['failed_count']
                )
                
                return result
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "sqs_batch_delete_error",
                queue_url=self.queue_url,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "sqs_batch_delete_unexpected_error",
                queue_url=self.queue_url,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def change_message_visibility(
        self,
        receipt_handle: str,
        visibility_timeout_seconds: int
    ) -> bool:
        """Change the visibility timeout of a message."""
        
        try:
            async with self.session.client('sqs') as sqs_client:
                logger.info(
                    "sqs_change_visibility_start",
                    queue_url=self.queue_url,
                    visibility_timeout=visibility_timeout_seconds
                )
                
                await sqs_client.change_message_visibility(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle,
                    VisibilityTimeout=visibility_timeout_seconds
                )
                
                logger.info(
                    "sqs_change_visibility_success",
                    queue_url=self.queue_url,
                    visibility_timeout=visibility_timeout_seconds
                )
                
                return True
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "sqs_change_visibility_error",
                queue_url=self.queue_url,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "sqs_change_visibility_unexpected_error",
                queue_url=self.queue_url,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def get_queue_attributes(self) -> Dict[str, Any]:
        """Get queue attributes."""
        
        try:
            async with self.session.client('sqs') as sqs_client:
                response = await sqs_client.get_queue_attributes(
                    QueueUrl=self.queue_url,
                    AttributeNames=['All']
                )
                
                attributes = response.get('Attributes', {})
                
                # Convert numeric attributes to integers
                numeric_attributes = [
                    'ApproximateNumberOfMessages',
                    'ApproximateNumberOfMessagesNotVisible',
                    'ApproximateNumberOfMessagesDelayed',
                    'DelaySeconds',
                    'MessageRetentionPeriod',
                    'ReceiveMessageWaitTimeSeconds',
                    'VisibilityTimeout'
                ]
                
                for attr in numeric_attributes:
                    if attr in attributes:
                        attributes[attr] = int(attributes[attr])
                
                logger.info(
                    "sqs_get_attributes_success",
                    queue_url=self.queue_url,
                    message_count=attributes.get('ApproximateNumberOfMessages', 0)
                )
                
                return attributes
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "sqs_get_attributes_error",
                queue_url=self.queue_url,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "sqs_get_attributes_unexpected_error",
                queue_url=self.queue_url,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    def _format_message_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Format message attributes for SQS."""
        formatted = {}
        for key, value in attributes.items():
            if isinstance(value, str):
                formatted[key] = {
                    'StringValue': value,
                    'DataType': 'String'
                }
            elif isinstance(value, (int, float)):
                formatted[key] = {
                    'StringValue': str(value),
                    'DataType': 'Number'
                }
            elif isinstance(value, bytes):
                formatted[key] = {
                    'BinaryValue': value,
                    'DataType': 'Binary'
                }
        return formatted
        
    def _parse_message_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Parse message attributes from SQS format."""
        parsed = {}
        for key, value in attributes.items():
            data_type = value.get('DataType', 'String')
            if data_type == 'String':
                parsed[key] = value.get('StringValue')
            elif data_type == 'Number':
                string_value = value.get('StringValue')
                if string_value:
                    try:
                        parsed[key] = float(string_value) if '.' in string_value else int(string_value)
                    except ValueError:
                        parsed[key] = string_value
            elif data_type == 'Binary':
                parsed[key] = value.get('BinaryValue')
        return parsed


# Global SQS service instance
_sqs_service = None


async def get_sqs_service() -> SQSService:
    """Dependency injection for SQS service."""
    global _sqs_service
    if _sqs_service is None:
        _sqs_service = SQSService()
    return _sqs_service