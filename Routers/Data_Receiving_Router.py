from fastapi import APIRouter, File, Form, UploadFile

from Data_Receiving.base import DataPipeline 

router = APIRouter(prefix="/data-receiving", tags=["Data Receiving"])
service = DataPipeline()

@router.post("/receive")
async def receive_data(
    file: UploadFile = File(...),
    payload: str = Form(...),
):
    await service.run(file=file, payload=payload)
    return {"message": "Data received successfully"}