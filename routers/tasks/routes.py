from fastapi import APIRouter
from . import crud, core

router = APIRouter()
router.include_router(crud.router, prefix="/tasks", tags=["Tasks"])
router.include_router(core.router, prefix="/tasks", tags=["Task Core"])
