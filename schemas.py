from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    password: str

class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    owner_id: int

    class Config:
        orm_mode = True

class PermissionUpdate(BaseModel):
    user_id: int
    can_read: bool
    can_update: bool
