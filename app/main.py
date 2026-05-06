from fastapi import FastAPI
from .database import engine, Base
from .routers import users, surveys, education, questions, roles, auth, profile, prompts

app = FastAPI(title="Spika API")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(surveys.router)
app.include_router(education.router)
app.include_router(questions.router)
app.include_router(roles.router)
app.include_router(profile.router)
app.include_router(prompts.router)

@app.get("/")
def root():
    return {"message": "Spika API is running"}