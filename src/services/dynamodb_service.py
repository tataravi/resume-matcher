import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime
import aioboto3
from botocore.exceptions import ClientError
from decimal import Decimal
import json
import structlog

from src.config import settings


logger = structlog.get_logger()


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class DynamoDBService:
    """Service for AWS DynamoDB operations."""
    
    def __init__(
        self,
        table_name: str = settings.aws_dynamodb_table,
        region_name: str = settings.aws_region,
        aws_access_key_id: str = settings.aws_access_key_id,
        aws_secret_access_key: str = settings.aws_secret_access_key
    ):
        self.table_name = table_name
        self.region_name = region_name
        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
    def _python_to_dynamodb(self, value: Any) -> Any:
        """Convert Python values to DynamoDB compatible format."""
        if isinstance(value, float):
            return Decimal(str(value))
        elif isinstance(value, dict):
            return {k: self._python_to_dynamodb(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._python_to_dynamodb(item) for item in value]
        elif isinstance(value, datetime):
            return value.isoformat()
        return value
        
    def _dynamodb_to_python(self, value: Any) -> Any:
        """Convert DynamoDB values to Python format."""
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, dict):
            return {k: self._dynamodb_to_python(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._dynamodb_to_python(item) for item in value]
        return value
        
    async def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Put an item into DynamoDB table."""
        
        try:
            async with self.session.client('dynamodb') as dynamodb_client:
                # Convert to DynamoDB format
                dynamodb_item = self._python_to_dynamodb(item)
                
                logger.info(
                    "dynamodb_put_start",
                    table=self.table_name,
                    item_keys=list(item.keys())
                )
                
                response = await dynamodb_client.put_item(
                    TableName=self.table_name,
                    Item=dynamodb_item,
                    ReturnValues='ALL_OLD'
                )
                
                result = {
                    "operation": "put_item",
                    "table": self.table_name,
                    "consumed_capacity": response.get('ConsumedCapacity'),
                    "item_collection_metrics": response.get('ItemCollectionMetrics')
                }
                
                if 'Attributes' in response:
                    result['previous_item'] = self._dynamodb_to_python(response['Attributes'])
                
                logger.info(
                    "dynamodb_put_success",
                    table=self.table_name,
                    consumed_capacity=result.get('consumed_capacity')
                )
                
                return result
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "dynamodb_put_error",
                table=self.table_name,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "dynamodb_put_unexpected_error",
                table=self.table_name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get an item from DynamoDB table."""
        
        try:
            async with self.session.client('dynamodb') as dynamodb_client:
                # Convert key to DynamoDB format
                dynamodb_key = self._python_to_dynamodb(key)
                
                logger.info(
                    "dynamodb_get_start",
                    table=self.table_name,
                    key=key
                )
                
                response = await dynamodb_client.get_item(
                    TableName=self.table_name,
                    Key=dynamodb_key,
                    ConsistentRead=True
                )
                
                if 'Item' in response:
                    item = self._dynamodb_to_python(response['Item'])
                    logger.info(
                        "dynamodb_get_success",
                        table=self.table_name,
                        key=key,
                        item_found=True
                    )
                    return item
                else:
                    logger.info(
                        "dynamodb_get_success",
                        table=self.table_name,
                        key=key,
                        item_found=False
                    )
                    return None
                    
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "dynamodb_get_error",
                table=self.table_name,
                key=key,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "dynamodb_get_unexpected_error",
                table=self.table_name,
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def update_item(
        self,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        return_values: str = "UPDATED_NEW"
    ) -> Dict[str, Any]:
        """Update an item in DynamoDB table."""
        
        try:
            async with self.session.client('dynamodb') as dynamodb_client:
                # Convert to DynamoDB format
                dynamodb_key = self._python_to_dynamodb(key)
                
                update_params = {
                    'TableName': self.table_name,
                    'Key': dynamodb_key,
                    'UpdateExpression': update_expression,
                    'ReturnValues': return_values
                }
                
                if expression_attribute_names:
                    update_params['ExpressionAttributeNames'] = expression_attribute_names
                    
                if expression_attribute_values:
                    update_params['ExpressionAttributeValues'] = self._python_to_dynamodb(
                        expression_attribute_values
                    )
                
                logger.info(
                    "dynamodb_update_start",
                    table=self.table_name,
                    key=key,
                    update_expression=update_expression
                )
                
                response = await dynamodb_client.update_item(**update_params)
                
                result = {
                    "operation": "update_item",
                    "table": self.table_name,
                    "consumed_capacity": response.get('ConsumedCapacity'),
                    "item_collection_metrics": response.get('ItemCollectionMetrics')
                }
                
                if 'Attributes' in response:
                    result['updated_attributes'] = self._dynamodb_to_python(response['Attributes'])
                
                logger.info(
                    "dynamodb_update_success",
                    table=self.table_name,
                    key=key,
                    consumed_capacity=result.get('consumed_capacity')
                )
                
                return result
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "dynamodb_update_error",
                table=self.table_name,
                key=key,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "dynamodb_update_unexpected_error",
                table=self.table_name,
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def delete_item(self, key: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an item from DynamoDB table."""
        
        try:
            async with self.session.client('dynamodb') as dynamodb_client:
                # Convert key to DynamoDB format
                dynamodb_key = self._python_to_dynamodb(key)
                
                logger.info(
                    "dynamodb_delete_start",
                    table=self.table_name,
                    key=key
                )
                
                response = await dynamodb_client.delete_item(
                    TableName=self.table_name,
                    Key=dynamodb_key,
                    ReturnValues='ALL_OLD'
                )
                
                result = {
                    "operation": "delete_item",
                    "table": self.table_name,
                    "consumed_capacity": response.get('ConsumedCapacity'),
                    "item_collection_metrics": response.get('ItemCollectionMetrics')
                }
                
                if 'Attributes' in response:
                    result['deleted_item'] = self._dynamodb_to_python(response['Attributes'])
                
                logger.info(
                    "dynamodb_delete_success",
                    table=self.table_name,
                    key=key,
                    consumed_capacity=result.get('consumed_capacity')
                )
                
                return result
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "dynamodb_delete_error",
                table=self.table_name,
                key=key,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "dynamodb_delete_unexpected_error",
                table=self.table_name,
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def query_items(
        self,
        key_condition_expression: str,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        filter_expression: Optional[str] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        scan_index_forward: bool = True
    ) -> Dict[str, Any]:
        """Query items from DynamoDB table."""
        
        try:
            async with self.session.client('dynamodb') as dynamodb_client:
                query_params = {
                    'TableName': self.table_name,
                    'KeyConditionExpression': key_condition_expression,
                    'ScanIndexForward': scan_index_forward
                }
                
                if expression_attribute_names:
                    query_params['ExpressionAttributeNames'] = expression_attribute_names
                    
                if expression_attribute_values:
                    query_params['ExpressionAttributeValues'] = self._python_to_dynamodb(
                        expression_attribute_values
                    )
                    
                if filter_expression:
                    query_params['FilterExpression'] = filter_expression
                    
                if index_name:
                    query_params['IndexName'] = index_name
                    
                if limit:
                    query_params['Limit'] = limit
                
                logger.info(
                    "dynamodb_query_start",
                    table=self.table_name,
                    index_name=index_name,
                    limit=limit
                )
                
                response = await dynamodb_client.query(**query_params)
                
                items = [self._dynamodb_to_python(item) for item in response.get('Items', [])]
                
                result = {
                    "items": items,
                    "count": response.get('Count', 0),
                    "scanned_count": response.get('ScannedCount', 0),
                    "last_evaluated_key": response.get('LastEvaluatedKey'),
                    "consumed_capacity": response.get('ConsumedCapacity')
                }
                
                logger.info(
                    "dynamodb_query_success",
                    table=self.table_name,
                    index_name=index_name,
                    count=result['count'],
                    scanned_count=result['scanned_count'],
                    consumed_capacity=result.get('consumed_capacity')
                )
                
                return result
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "dynamodb_query_error",
                table=self.table_name,
                index_name=index_name,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "dynamodb_query_unexpected_error",
                table=self.table_name,
                index_name=index_name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
            
    async def scan_items(
        self,
        filter_expression: Optional[str] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Scan items from DynamoDB table."""
        
        try:
            async with self.session.client('dynamodb') as dynamodb_client:
                scan_params = {
                    'TableName': self.table_name
                }
                
                if filter_expression:
                    scan_params['FilterExpression'] = filter_expression
                    
                if expression_attribute_names:
                    scan_params['ExpressionAttributeNames'] = expression_attribute_names
                    
                if expression_attribute_values:
                    scan_params['ExpressionAttributeValues'] = self._python_to_dynamodb(
                        expression_attribute_values
                    )
                    
                if index_name:
                    scan_params['IndexName'] = index_name
                    
                if limit:
                    scan_params['Limit'] = limit
                
                logger.info(
                    "dynamodb_scan_start",
                    table=self.table_name,
                    index_name=index_name,
                    limit=limit
                )
                
                response = await dynamodb_client.scan(**scan_params)
                
                items = [self._dynamodb_to_python(item) for item in response.get('Items', [])]
                
                result = {
                    "items": items,
                    "count": response.get('Count', 0),
                    "scanned_count": response.get('ScannedCount', 0),
                    "last_evaluated_key": response.get('LastEvaluatedKey'),
                    "consumed_capacity": response.get('ConsumedCapacity')
                }
                
                logger.info(
                    "dynamodb_scan_success",
                    table=self.table_name,
                    index_name=index_name,
                    count=result['count'],
                    scanned_count=result['scanned_count'],
                    consumed_capacity=result.get('consumed_capacity')
                )
                
                return result
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                "dynamodb_scan_error",
                table=self.table_name,
                index_name=index_name,
                error_code=error_code,
                error_message=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "dynamodb_scan_unexpected_error",
                table=self.table_name,
                index_name=index_name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise


# Global DynamoDB service instance
_dynamodb_service = None


async def get_dynamodb_service() -> DynamoDBService:
    """Dependency injection for DynamoDB service."""
    global _dynamodb_service
    if _dynamodb_service is None:
        _dynamodb_service = DynamoDBService()
    return _dynamodb_service