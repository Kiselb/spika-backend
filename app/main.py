from fastapi import FastAPI
from .database import engine, Base
from .routers import users, surveys, education, questions, thinking
from .routers import roles

# Создать таблицы (для разработки, в продакшене использовать миграции)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spika API")

app.include_router(users.router)
app.include_router(surveys.router)
app.include_router(education.router)
app.include_router(questions.router)
app.include_router(thinking.router)
app.include_router(roles.router)

@app.get("/")
def root():
    return {"message": "Spika API is running"}
