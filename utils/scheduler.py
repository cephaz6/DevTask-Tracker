from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlmodel import Session, select
from models.task import Task
from models.notification import NotificationType
from utils.core import create_notification
from db.database import engine

# Background job to check task due dates and notify assignees
def check_due_dates():
    try:
        with Session(engine) as session:
            now = datetime.utcnow()
            tomorrow = now + timedelta(days=1)

            tasks = session.exec(
                select(Task).where(Task.due_date != None)
            ).all()

            for task in tasks:
                if not task.due_date:
                    continue

                # Load task.assignments relationship manually if needed
                if not hasattr(task, "assignments") or not task.assignments:
                    task.assignments = session.exec(
                        select(task.assignment_model).where(task.assignment_model.task_id == task.id)
                    ).all()

                for assignment in task.assignments:
                    user_id = assignment.user_id

                    if task.due_date.date() == tomorrow.date():
                        message = f"Reminder: Task '{task.title}' is due tomorrow."
                    elif task.due_date.date() == now.date():
                        message = f"Task '{task.title}' is due today!"
                    elif task.due_date < now:
                        message = f"Task '{task.title}' is overdue!"
                    else:
                        continue

                    # TODO: Optional check - prevent duplicate notifications (e.g., via a unique constraint or last sent time)

                    create_notification(
                        session=session,
                        recipient_user_id=user_id,
                        message=message,
                        task_id=task.id,
                        notif_type=NotificationType.GENERAL
                    )
    except Exception as e:
        print(f"[DueDateChecker Error] {e}")

# Initialize and start the background scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(check_due_dates, "interval", hours=24)
scheduler.start()
