from sqlalchemy import Integer, String, Text, Column, ForeignKey
from ..database import Base

class SystemPromptType(Base):
    __tablename__ = "SystemPromptsTypes"
    prompt_type_id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_name = Column(String(255), unique=True, nullable=False)

class SystemPrompt(Base):
    __tablename__ = "SystemPrompts"
    prompt_id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_type_id = Column(Integer, ForeignKey("SystemPromptsTypes.prompt_type_id"), nullable=False)
    prompt_text = Column(Text, nullable=False)

