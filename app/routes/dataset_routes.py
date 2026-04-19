from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.controllers.dataset_controller import DatasetController
from app.dependencies import get_current_user, get_dataset_service
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.dataset import DatasetResponse
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


def get_dataset_controller(dataset_service: DatasetService = Depends(get_dataset_service)):
    return DatasetController(dataset_service)


@router.post("/upload", response_model=SuccessResponse[DatasetResponse])
async def upload_dataset(
    name: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    controller: DatasetController = Depends(get_dataset_controller),
):
    result = await controller.upload_dataset(current_user.id, name, description, file)
    return SuccessResponse(data=result)


@router.get("", response_model=SuccessResponse[list[DatasetResponse]])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    controller: DatasetController = Depends(get_dataset_controller),
):
    return SuccessResponse(data=await controller.list_datasets(current_user.id))
