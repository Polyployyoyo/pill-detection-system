from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..utils import db
from ..utils.record_to_dict import record_to_dict

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def get_logs():
    try:
        async with db.pool.acquire() as connection:
            response = await connection.fetch(
                """
                SELECT
                    detection_logs.id,
                    detection_logs.drug_id,
                    drugs.trade_name,
                    detection_logs.detected_quantity,
                    detection_logs.confidence,
                    detection_logs.detected_at
                FROM detection_logs
                INNER JOIN drugs
                    ON detection_logs.drug_id = drugs.id
                ORDER BY detection_logs.detected_at DESC
                """
            )
    except:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not read logs because of database connection"
            },
        )

    return JSONResponse(
        status_code=200, content=[record_to_dict(record) for record in response]
    )


class DetectionLogCreate(BaseModel):
    drug_id: int
    detected_quantity: int
    confidence: float


@router.post("")
async def create_logs(payload: DetectionLogCreate):
    try:
        async with db.pool.acquire() as connection:
            query = """
                INSERT INTO detection_logs (drug_id, detected_quantity, confidence)
                VALUES ($1, $2, $3)
                RETURNING *
            """
            record = await connection.fetchrow(
                query, payload.drug_id, payload.detected_quantity, payload.confidence
            )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not create log because of database connection"
            },
        )

    return JSONResponse(status_code=201, content=record_to_dict(record))


@router.delete("/{log_id}")
async def delete_log(log_id: int):
    try:
        async with db.pool.acquire() as connection:
            record = await connection.fetchrow(
                """
                DELETE FROM detection_logs
                WHERE id = $1
                RETURNING *
                """,
                log_id,
            )

            if not record:
                return JSONResponse(
                    status_code=404,
                    content={
                        "message": "Server could not find a requested log to delete"
                    },
                )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not delete log because of database connection"
            },
        )

    return JSONResponse(status_code=200, content=record_to_dict(record))
