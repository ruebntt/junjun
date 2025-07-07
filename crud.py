from sqlalchemy.orm import Session
from models import User, Task, task_user_permissions
from sqlalchemy import select, update

import bcrypt

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode()
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
        return user
    return False

def create_task(db: Session, task: TaskCreate, owner_id: int):
    db_task = Task(title=task.title, description=task.description, owner_id=owner_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_tasks(db: Session, owner_id: int):
    return db.query(Task).filter(Task.owner_id == owner_id).all()

def get_task(db: Session, task_id: int):
    return db.query(Task).filter(Task.id == task_id).first()

def delete_task(db: Session, task_id: int):
    task = get_task(db, task_id)
    if task:
        db.delete(task)
        db.commit()
        return True
    return False

def update_task(db: Session, task_id: int, task_data: dict):
    task = get_task(db, task_id)
    if not task:
        return None
    for key, value in task_data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task

def set_task_permission(db: Session, task_id: int, user_id: int, can_read: bool, can_update: bool):
    task = get_task(db, task_id)
    if not task:
        return None
      
    stmt = select(task_user_permissions).where(
        task_user_permissions.c.task_id == task_id,
        task_user_permissions.c.user_id == user_id
    )
    result = db.execute(stmt).first()

    if result:
        update_stmt = update(task_user_permissions).where(
            task_user_permissions.c.task_id == task_id,
            task_user_permissions.c.user_id == user_id
        ).values(can_read=can_read, can_update=can_update)
        db.execute(update_stmt)
    else:
        ins = task_user_permissions.insert().values(
            task_id=task_id,
            user_id=user_id,
            can_read=can_read,
            can_update=can_update
        )
        db.execute(ins)
    db.commit()
    return True
