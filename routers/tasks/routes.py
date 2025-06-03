from fastapi import APIRouter
from . import crud, core, task_assignment_router

router = APIRouter()
router.include_router(crud.router, prefix="/tasks", tags=["Tasks"])
router.include_router(core.router, prefix="/tasks", tags=["Task Core"])
router.include_router(
    task_assignment_router.router,
    prefix="/tasks/assignments",
    tags=["Task Assignments"],
)
