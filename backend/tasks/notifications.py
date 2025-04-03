from celery import shared_task
from time import sleep

# Using shared_task decorator integrates with the global Celery instance
@shared_task(ignore_result=False)
def send_order_notification(order_id) -> str:
    # Simulate a long-running task, e.g., sending an email or SMS
    print(f"Starting order notification for order: {order_id}")
    sleep(5)  # Simulate delay
    print(f"Notification sent for order: {order_id}")
    return f"Notification sent for order {order_id}"