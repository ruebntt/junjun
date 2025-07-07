from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import Base, User, Task
from database import engine, get_db
from schemas import UserCreate, UserRead, TaskCreate, TaskRead, PermissionUpdate
import crud
from jose import JWTError, jwt
from datetime import datetime, timedelta

app = FastAPI()

SECRET_KEY = "cwrL9Z7hRKYJYI82Ayk4rW0JGmMAks0iuuWIQ9oAMV0wV71eB8PPyEOCQ2xBaCrB"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

acess_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjliYTBmNGI2MDg0YTk3ZjNjMzMwM2I1MTVjMTg2NDE1NDcxY2NjY2MzYmEwOGNlY2VmYmNlNDA3NzNlZjUyNjg4YzExM2JmMDIzMDA0NGIyIn0.eyJhdWQiOiJkOTc2ZjY0Yy1jZTRhLTRiZDktYTMzMy03NDVkYjFhZTNiNTciLCJqdGkiOiI5YmEwZjRiNjA4NGE5N2YzYzMzMDNiNTE1YzE4NjQxNTQ3MWNjY2NjM2JhMDhjZWNlZmJjZTQwNzczZWY1MjY4OGMxMTNiZjAyMzAwNDRiMiIsImlhdCI6MTc1MTgwMzgxMSwibmJmIjoxNzUxODAzODExLCJleHAiOjE3NjA3NDU2MDAsInN1YiI6IjExOTIwMjE4IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyNTMwNTMwLCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiZjkwMzc5MTMtYjdjMi00YTZkLTgzMmUtM2QyYmQxNmEyNzkyIiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.dOjF4HdBbE_pUfY3EliLNc6d7xkJwgTXmuOrv_w2pHQpOMZFwXqaGEhMJPcE31woY0heBUAZAItv6gsjqJA9tYljVrsNO7QimPK_h3HFb8Ex_ifmETGwXx-Qt2LM04kb-kUyvWuVvwiTfZfcvOwa1QRNypJQgyCwULBcNNsZDFg9ROEsGY28cB5BI1plPiAo_zmTW1Bi3U6mfvHY02VmtUsC7Lw6XSOl-ioo3oFim6UjL6t4KfekWNC6Yp2RKS8UwLPFeY1nniHhe5x1m-wMluhVaQSZR64XX5kBrNh06Qm8aKyiDFLIot3LOpeEoeXUR9FkdtekUzMdygRsxAcPNg"

Base.metadata.create_all(bind=engine)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    from fastapi.security import OAuth2PasswordBearer
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    token = Depends(oauth2_scheme)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

@app.post("/register", response_model=UserRead)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = crud.create_user(db, user)
    return user

@app.post("/token")
def login_for_access_token(form_data: UserCreate, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/tasks/", response_model=TaskRead)
def create_task_endpoint(task: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task_obj = crud.create_task(db, task, owner_id=current_user.id)
    return task_obj

@app.get("/tasks/", response_model=List[TaskRead])
def read_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = crud.get_tasks(db, owner_id=current_user.id)
    return tasks

@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_task = crud.get_task(db, task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    if existing_task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updated_task = crud.update_task(db, task_id, task.dict())
    return updated_task

@app.delete("/tasks/{task_id}")
def delete_task_endpoint(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_task = crud.get_task(db, task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    if existing_task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud.delete_task(db, task_id)
    return {"detail": "Task deleted"}

@app.post("/tasks/{task_id}/permissions")
def set_task_permissions(task_id: int, permission: PermissionUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to change permissions")
    crud.set_task_permission(db, task_id, permission.user_id, permission.can_read, permission.can_update)
    return {"detail": "Permissions updated"}
