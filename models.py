from sqlalchemy import Column, Integer, String, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from database import Base

task_user_permissions = Table(
    'task_user_permissions',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id')),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('can_read', Boolean, default=False),
    Column('can_update', Boolean, default=False)
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    tasks_created = relationship('Task', back_populates='owner')
    tasks_shared = relationship('Task', secondary=task_user_permissions, back_populates='shared_users')

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship('User', back_populates='tasks_created')
    shared_users = relationship('User', secondary=task_user_permissions, back_populates='tasks_shared')
