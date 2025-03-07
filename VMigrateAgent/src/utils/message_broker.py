"""
Message broker for asynchronous task execution using RabbitMQ.
"""
import asyncio
import json
import logging
import pika
from typing import Dict, Any, Callable, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MessageBroker:
    """
    Message broker for asynchronous task execution using RabbitMQ.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 5672, 
                username: str = 'guest', password: str = 'guest'):
        """
        Initialize the message broker.
        
        Args:
            host: RabbitMQ host
            port: RabbitMQ port
            username: RabbitMQ username
            password: RabbitMQ password
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.logger = logging.getLogger("MessageBroker")
        
    async def connect(self) -> None:
        """
        Connect to RabbitMQ.
        """
        try:
            # Create connection parameters
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            
            # Connect to RabbitMQ
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare default exchange
            self.channel.exchange_declare(
                exchange='vmigrateagent',
                exchange_type='topic',
                durable=True
            )
            
            self.logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """
        Disconnect from RabbitMQ.
        """
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.logger.info("Disconnected from RabbitMQ")
    
    async def declare_queue(self, queue_name: str) -> None:
        """
        Declare a queue.
        
        Args:
            queue_name: Queue name
        """
        if not self.channel:
            await self.connect()
            
        self.channel.queue_declare(
            queue=queue_name,
            durable=True
        )
        
        # Bind queue to exchange
        self.channel.queue_bind(
            exchange='vmigrateagent',
            queue=queue_name,
            routing_key=queue_name
        )
        
        self.logger.info(f"Declared queue: {queue_name}")
    
    async def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        """
        Publish a message to a queue.
        
        Args:
            queue_name: Queue name
            message: Message to publish
        """
        if not self.channel:
            await self.connect()
            
        # Ensure queue exists
        await self.declare_queue(queue_name)
        
        # Publish message
        self.channel.basic_publish(
            exchange='vmigrateagent',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )
        
        self.logger.info(f"Published message to queue: {queue_name}")
    
    async def consume(self, queue_name: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Consume messages from a queue.
        
        Args:
            queue_name: Queue name
            callback: Callback function to process messages
        """
        if not self.channel:
            await self.connect()
            
        # Ensure queue exists
        await self.declare_queue(queue_name)
        
        # Define callback wrapper
        def callback_wrapper(ch, method, properties, body):
            try:
                # Parse message
                message = json.loads(body)
                
                # Call callback
                callback(message)
                
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                # Reject message and requeue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        # Set up consumer
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback_wrapper
        )
        
        self.logger.info(f"Started consuming from queue: {queue_name}")
        
        # Start consuming
        self.channel.start_consuming()
    
    async def consume_async(self, queue_name: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Consume messages from a queue asynchronously.
        
        Args:
            queue_name: Queue name
            callback: Callback function to process messages
        """
        # Run consume in a separate thread
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.consume(queue_name, callback))


class TaskQueue:
    """
    Task queue for asynchronous task execution.
    """
    
    def __init__(self, broker: MessageBroker):
        """
        Initialize the task queue.
        
        Args:
            broker: Message broker
        """
        self.broker = broker
        self.logger = logging.getLogger("TaskQueue")
        
    async def enqueue_task(self, task_type: str, task_data: Dict[str, Any]) -> None:
        """
        Enqueue a task.
        
        Args:
            task_type: Task type
            task_data: Task data
        """
        # Create task message
        message = {
            "task_type": task_type,
            "task_data": task_data
        }
        
        # Publish to queue
        await self.broker.publish(task_type, message)
        
        self.logger.info(f"Enqueued task: {task_type}")
    
    async def register_handler(self, task_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a task handler.
        
        Args:
            task_type: Task type
            handler: Handler function
        """
        # Define callback
        def callback(message: Dict[str, Any]) -> None:
            try:
                # Extract task data
                task_data = message.get("task_data", {})
                
                # Call handler
                handler(task_data)
                
                self.logger.info(f"Processed task: {task_type}")
                
            except Exception as e:
                self.logger.error(f"Error handling task: {str(e)}")
        
        # Start consuming
        await self.broker.consume_async(task_type, callback)
        
        self.logger.info(f"Registered handler for task type: {task_type}")
