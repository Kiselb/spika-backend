from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Role(Base):
    __tablename__ = "Roles"
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(255), unique=True, nullable=False)

    users = relationship("User", secondary="UsersRoles", back_populates="roles")

class UserRole(Base):
    __tablename__ = "UsersRoles"
    user_id = Column(Integer, ForeignKey("Users.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("Roles.role_id"), primary_key=True)
