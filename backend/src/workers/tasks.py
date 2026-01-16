"""
Celery Tasks
Background task workers for various operations.
"""

import logging
import socket
from datetime import datetime, timezone
from typing import Dict, Any
from uuid import UUID

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

logger = logging.getLogger(__name__)

# Get worker hostname
WORKER_HOST = socket.gethostname()


def get_sync_session():
    """Get a synchronous database session."""
    from src.core.database import SyncSessionLocal
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_task_status_sync(db, task_id, status, worker_id=None, result=None, error_message=None, error_traceback=None):
    """Update task status synchronously."""
    from src.workers.models import TaskQueue, TaskStatus
    
    task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
    if not task:
        return None
    
    task.status = status
    if worker_id:
        task.worker_id = worker_id
    if result:
        task.result = result
    if error_message:
        task.error_message = error_message
    if error_traceback:
        task.error_traceback = error_traceback
    
    if status == TaskStatus.RUNNING.value and not task.started_at:
        task.started_at = datetime.now(timezone.utc)
    
    if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
        task.completed_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(task)
    return task


def create_task_history_sync(db, task_id, status, attempt_number=1, worker_id=None, 
                              input_payload=None, output_result=None, error_message=None, 
                              error_traceback=None, started_at=None, completed_at=None):
    """Create task history record synchronously."""
    from src.workers.models import TaskHistory
    
    history = TaskHistory(
        task_id=task_id,
        attempt_number=attempt_number,
        status=status,
        worker_id=worker_id,
        input_payload=input_payload,
        output_result=output_result,
        error_message=error_message,
        error_traceback=error_traceback,
        started_at=started_at or datetime.now(timezone.utc),
        completed_at=completed_at,
    )
    
    if completed_at and started_at:
        history.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
    
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def update_task_history_sync(db, history_id, status=None, completed_at=None, 
                             duration_ms=None, output_result=None, error_message=None, 
                             error_traceback=None):
    """Update task history record synchronously."""
    from src.workers.models import TaskHistory
    
    history = db.query(TaskHistory).filter(TaskHistory.id == history_id).first()
    if not history:
        return None
    
    if status:
        history.status = status
    if completed_at:
        history.completed_at = completed_at
    if duration_ms:
        history.duration_ms = duration_ms
    if output_result:
        history.output_result = output_result
    if error_message:
        history.error_message = error_message
    if error_traceback:
        history.error_traceback = error_traceback
    
    db.commit()
    db.refresh(history)
    return history


# =============================================================================
# SMS Notification Task
# =============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send SMS notifications.
    """
    from src.core.database import SyncSessionLocal
    from src.workers.models import TaskStatus
    
    db = SyncSessionLocal()
    task_uuid = UUID(task_id)
    
    try:
        # Update task status to running
        update_task_status_sync(db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST)
        
        # Create history record
        history = create_task_history_sync(
            db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST, input_payload=payload
        )
        
        # Get SMS configuration
        from src.core.config import settings
        
        recipients = payload.get("recipients", [])
        message = payload.get("message", "")
        template_id = payload.get("template_id")
        
        results = []
        success_count = 0
        fail_count = 0
        
        for recipient in recipients:
            try:
                # TODO: Implement actual SMS sending based on provider
                logger.info(f"Sending SMS to {recipient}: {message[:50]}...")
                result = {
                    "recipient": recipient,
                    "status": "sent",
                    "message_id": f"sms_{recipient}_{datetime.now().timestamp()}"
                }
                results.append(result)
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send SMS to {recipient}: {e}")
                results.append({
                    "recipient": recipient,
                    "status": "failed",
                    "error": str(e)
                })
                fail_count += 1
        
        # Update task as completed
        update_task_status_sync(
            db, task_uuid, TaskStatus.COMPLETED.value,
            result={"results": results, "success_count": success_count, "fail_count": fail_count}
        )
        
        # Update history
        update_task_history_sync(
            db, history.id,
            status=TaskStatus.COMPLETED.value,
            completed_at=datetime.now(timezone.utc),
            output_result={"results": results}
        )
        
        db.close()
        
        return {
            "success": True,
            "task_id": task_id,
            "success_count": success_count,
            "fail_count": fail_count
        }
        
    except Exception as e:
        logger.error(f"SMS task failed: {e}")
        
        update_task_status_sync(
            db, task_uuid, TaskStatus.FAILED.value,
            error_message=str(e), error_traceback=str(e)
        )
        
        db.close()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e)
        }


# =============================================================================
# Email Notification Task
# =============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send email notifications.
    """
    from src.core.database import SyncSessionLocal
    from src.workers.models import TaskStatus
    
    db = SyncSessionLocal()
    task_uuid = UUID(task_id)
    
    try:
        update_task_status_sync(db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST)
        
        history = create_task_history_sync(
            db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST, input_payload=payload
        )
        
        recipients = payload.get("recipients", [])
        subject = payload.get("subject", "")
        body = payload.get("body", "")
        html_body = payload.get("html_body")
        
        results = []
        success_count = 0
        fail_count = 0
        
        for recipient in recipients:
            try:
                logger.info(f"Sending email to {recipient}: {subject}")
                result = {
                    "recipient": recipient,
                    "status": "sent",
                    "message_id": f"email_{recipient}_{datetime.now().timestamp()}"
                }
                results.append(result)
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send email to {recipient}: {e}")
                results.append({
                    "recipient": recipient,
                    "status": "failed",
                    "error": str(e)
                })
                fail_count += 1
        
        update_task_status_sync(
            db, task_uuid, TaskStatus.COMPLETED.value,
            result={"results": results, "success_count": success_count, "fail_count": fail_count}
        )
        
        update_task_history_sync(
            db, history.id,
            status=TaskStatus.COMPLETED.value,
            completed_at=datetime.now(timezone.utc),
            output_result={"results": results}
        )
        
        db.close()
        
        return {
            "success": True,
            "task_id": task_id,
            "success_count": success_count,
            "fail_count": fail_count
        }
        
    except Exception as e:
        logger.error(f"Email task failed: {e}")
        
        update_task_status_sync(
            db, task_uuid, TaskStatus.FAILED.value,
            error_message=str(e), error_traceback=str(e)
        )
        
        db.close()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e)
        }


# =============================================================================
# Push Notification Task
# =============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_push_notification(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send push notifications.
    """
    from src.core.database import SyncSessionLocal
    from src.workers.models import TaskStatus
    
    db = SyncSessionLocal()
    task_uuid = UUID(task_id)
    
    try:
        update_task_status_sync(db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST)
        
        history = create_task_history_sync(
            db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST, input_payload=payload
        )
        
        tokens = payload.get("device_tokens", [])
        title = payload.get("title", "")
        body = payload.get("body", "")
        data = payload.get("data", {})
        
        results = []
        success_count = 0
        fail_count = 0
        
        for token in tokens:
            try:
                logger.info(f"Sending push notification to token: {token[:20]}...")
                result = {
                    "token": token[:20] + "...",
                    "status": "sent",
                    "message_id": f"push_{token[:10]}_{datetime.now().timestamp()}"
                }
                results.append(result)
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send push to {token[:20]}...: {e}")
                results.append({
                    "token": token[:20] + "...",
                    "status": "failed",
                    "error": str(e)
                })
                fail_count += 1
        
        update_task_status_sync(
            db, task_uuid, TaskStatus.COMPLETED.value,
            result={"results": results, "success_count": success_count, "fail_count": fail_count}
        )
        
        update_task_history_sync(
            db, history.id,
            status=TaskStatus.COMPLETED.value,
            completed_at=datetime.now(timezone.utc),
            output_result={"results": results}
        )
        
        db.close()
        
        return {
            "success": True,
            "task_id": task_id,
            "success_count": success_count,
            "fail_count": fail_count
        }
        
    except Exception as e:
        logger.error(f"Push notification task failed: {e}")
        
        update_task_status_sync(
            db, task_uuid, TaskStatus.FAILED.value,
            error_message=str(e), error_traceback=str(e)
        )
        
        db.close()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e)
        }


# =============================================================================
# Bulk Operation Task
# =============================================================================

@shared_task(bind=True, max_retries=1, default_retry_delay=120)
def bulk_operation(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform bulk operations on data.
    """
    from src.core.database import SyncSessionLocal
    from src.workers.models import TaskStatus
    
    db = SyncSessionLocal()
    task_uuid = UUID(task_id)
    
    try:
        update_task_status_sync(db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST)
        
        history = create_task_history_sync(
            db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST, input_payload=payload
        )
        
        operation_type = payload.get("operation_type", "")
        data = payload.get("data", [])
        batch_size = payload.get("batch_size", 100)
        
        results = {
            "total_items": len(data),
            "processed_items": 0,
            "success_items": 0,
            "failed_items": 0,
            "batches_processed": 0,
            "errors": []
        }
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            
            try:
                for item in batch:
                    try:
                        if operation_type == "update":
                            pass  # TODO: Perform update operation
                        elif operation_type == "delete":
                            pass  # TODO: Perform delete operation
                        elif operation_type == "export":
                            pass  # TODO: Export item
                        else:
                            results["errors"].append({
                                "item": item,
                                "error": f"Unknown operation type: {operation_type}"
                            })
                            results["failed_items"] += 1
                            continue
                        
                        results["success_items"] += 1
                        
                    except Exception as e:
                        results["errors"].append({
                            "item": item,
                            "error": str(e)
                        })
                        results["failed_items"] += 1
                
                results["processed_items"] += len(batch)
                results["batches_processed"] += 1
                
            except Exception as e:
                logger.error(f"Batch {results['batches_processed']} failed: {e}")
                results["errors"].append({
                    "batch": i // batch_size,
                    "error": str(e)
                })
        
        update_task_status_sync(db, task_uuid, TaskStatus.COMPLETED.value, result=results)
        
        update_task_history_sync(
            db, history.id,
            status=TaskStatus.COMPLETED.value,
            completed_at=datetime.now(timezone.utc),
            output_result=results
        )
        
        db.close()
        
        return {
            "success": True,
            "task_id": task_id,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Bulk operation task failed: {e}")
        
        update_task_status_sync(
            db, task_uuid, TaskStatus.FAILED.value,
            error_message=str(e), error_traceback=str(e)
        )
        
        db.close()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e)
        }


# =============================================================================
# ML Inference Task
# =============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def ml_inference(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run ML model inference.
    """
    from src.core.database import SyncSessionLocal
    from src.workers.models import TaskStatus
    
    db = SyncSessionLocal()
    task_uuid = UUID(task_id)
    
    try:
        update_task_status_sync(db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST)
        
        history = create_task_history_sync(
            db, task_uuid, TaskStatus.RUNNING.value, worker_id=WORKER_HOST, input_payload=payload
        )
        
        model_name = payload.get("model_name", "")
        input_data = payload.get("input_data", {})
        version = payload.get("version", "latest")
        
        logger.info(f"Running ML inference with model {model_name} (version: {version})")
        
        # Simulate inference result
        result = {
            "predictions": {
                "class": "positive",
                "confidence": 0.85,
                "probabilities": {
                    "positive": 0.85,
                    "negative": 0.10,
                    "neutral": 0.05
                }
            },
            "model_info": {
                "name": model_name,
                "version": version,
                "inference_time_ms": 150
            }
        }
        
        update_task_status_sync(db, task_uuid, TaskStatus.COMPLETED.value, result=result)
        
        update_task_history_sync(
            db, history.id,
            status=TaskStatus.COMPLETED.value,
            completed_at=datetime.now(timezone.utc),
            output_result=result
        )
        
        db.close()
        
        return {
            "success": True,
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"ML inference task failed: {e}")
        
        update_task_status_sync(
            db, task_uuid, TaskStatus.FAILED.value,
            error_message=str(e), error_traceback=str(e)
        )
        
        db.close()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e)
        }


# =============================================================================
# Generic Task Handler
# =============================================================================

@shared_task(bind=True)
def execute_task(self, task_id: str, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic task executor for different task types.
    """
    task_handlers = {
        "sms_notification": send_sms,
        "email_notification": send_email,
        "push_notification": send_push_notification,
        "bulk_operation": bulk_operation,
        "ml_inference": ml_inference,
    }
    
    handler = task_handlers.get(task_type)
    
    if handler:
        return handler(task_id, payload)
    else:
        logger.warning(f"Unknown task type: {task_type}")
        return {
            "success": False,
            "task_id": task_id,
            "error": f"Unknown task type: {task_type}"
        }
