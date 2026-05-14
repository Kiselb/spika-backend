from fastapi import APIRouter
from .primary import router as primary_router
from .extended import router as extended_router

router = APIRouter(prefix="/Survey", tags=["Surveys"])
router.include_router(primary_router)
router.include_router(extended_router) 
