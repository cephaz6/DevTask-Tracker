from fastapi import APIRouter
from . import project_router, project_member_router

router = APIRouter()
router.include_router(project_router.router, prefix="/project", tags=["Projects"])
router.include_router(project_member_router.router, prefix="/project-members", tags=["Project Members"])
