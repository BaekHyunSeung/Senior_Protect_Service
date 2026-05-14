from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from DB.DB import SessionDep
from Data_Receiving.base import DataPipeline 

router = APIRouter(prefix="/data-receiving", tags=["Data Receiving"])
service = DataPipeline()

@router.post("/receive")
async def receive_data(
    session: SessionDep,
    file: UploadFile = File(...),
    payload: str = Form(...),
):
    try:
        await service.run(session=session, file=file, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Data received successfully"}