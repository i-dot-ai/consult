import json
import os
import redis
from rq import Queue

def lambda_handler(event, context):
    """
    Lambda function triggered by EventBridge when AWS Batch job completes
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Extract batch job details
    detail = event.get('detail', {})
    
    # Use real event data or test data
    if detail:
        job_name = detail.get('jobName', 'unknown')
        job_status = detail.get('jobStatus', 'unknown')
        parameters = detail.get('parameters', {})
        consultation_name = parameters.get('CONSULTATION_NAME')
        consultation_code = parameters.get('CONSULTATION_CODE') 
        timestamp = parameters.get('TIMESTAMP')
    else:
        # Test data when no real event
        job_name = "test-job"
        job_status = "SUCCEEDED"
        consultation_name = "Test Defra Consultation"
        consultation_code = "defra" 
        timestamp = "2025-08-21"
    
    print(f"Batch job '{job_name}' completed with status: {job_status}")
    
    # Only process successful jobs
    if job_status != 'SUCCEEDED':
        print(f"Skipping job with status: {job_status}")
        return {'statusCode': 200, 'body': 'Job not successful, skipping'}
    
    # Validate required parameters
    if not all([consultation_name, consultation_code, timestamp]):
        error_msg = f"Missing consultation parameters: name={consultation_name}, code={consultation_code}, timestamp={timestamp}"
        print(error_msg)
        return {'statusCode': 400, 'body': error_msg}
    
    try:
        print("=== RQ JOB SETUP ===")
        
        # Connect to Redis
        redis_host = os.environ.get('REDIS_HOST')
        redis_port = int(os.environ.get('REDIS_PORT', '6379'))
        
        print(f"Connecting to Redis: {redis_host}:{redis_port}")
        
        redis_conn = redis.Redis(
            host=redis_host, 
            port=redis_port,
            socket_timeout=30,
            socket_connect_timeout=30
        )
        
        # Test Redis connection
        print("Testing Redis connection...")
        ping_result = redis_conn.ping()
        print(f"✅ Redis PING result: {ping_result}")
        
        # Create RQ queue (use 'default' or your specific queue name)
        queue_name = 'default'  # Change this if your Django-RQ uses a different queue
        queue = Queue(queue_name, connection=redis_conn)
        
        print(f"Created RQ queue: {queue_name}")
        
        # Prepare job arguments to match your function signature:
        # def import_consultation_job(consultation_name: str, consultation_code: str, timestamp: str, current_user_id: int)
        
        print(f"Job function: consult.tasks.import_consultation_job")
        print(f"Parameters:")
        print(f"  consultation_name: {consultation_name}")
        print(f"  consultation_code: {consultation_code}")
        print(f"  timestamp: {timestamp}")
        print(f"  current_user_id: None")
        
        # Enqueue the RQ job with all parameters as positional arguments
        print("Enqueueing RQ job...")
        job = queue.enqueue(
            'consultation_analyser.support_console.views.consultations.import_consultation_job',  # Function import path
            consultation_name,      # First parameter
            consultation_code,      # Second parameter  
            timestamp,              # Third parameter
            133,                   # Fourth parameter (current_user_id)
        )
        
        print(f"✅ RQ job enqueued successfully!")
        print(f"Job ID: {job.id}")
        print(f"Job status: {job.get_status()}")
        
        # Check queue length
        queue_length = len(queue)
        print(f"Queue '{queue_name}' now has {queue_length} jobs")
        
        success_msg = f"Successfully queued RQ job {job.id} for consultation: {consultation_name}"
        print(success_msg)
        
        return {
            'statusCode': 200, 
            'body': {
                'message': success_msg,
                'job_id': job.id,
                'queue': queue_name,
                'queue_length': queue_length
            }
        }
        
    except Exception as e:
        import traceback
        
        print("=== ERROR DEBUG ===")
        error_msg = f"Failed to trigger consultation import: {str(e)}"
        error_type = type(e).__name__
        stack_trace = traceback.format_exc()
        
        print(f"Error message: {error_msg}")
        print(f"Error type: {error_type}")
        
        # Additional error context
        if hasattr(e, 'errno'):
            print(f"Error number: {e.errno}")
        if hasattr(e, 'strerror'):
            print(f"Error string: {e.strerror}")
        if hasattr(e, 'args'):
            print(f"Error args: {e.args}")
        
        print("Full stack trace:")
        print(stack_trace)
        
        # Debug the exact failure point
        tb = e.__traceback__
        while tb.tb_next:
            tb = tb.tb_next
        
        print(f"Error occurred at:")
        print(f"  File: {tb.tb_frame.f_code.co_filename}")
        print(f"  Function: {tb.tb_frame.f_code.co_name}")
        print(f"  Line: {tb.tb_lineno}")
        
        return {'statusCode': 500, 'body': error_msg}