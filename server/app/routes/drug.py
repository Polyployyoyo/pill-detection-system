from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..utils import db
from ..utils.record_to_dict import record_to_dict


router = APIRouter(prefix="/drugs", tags=["drugs"])


@router.get("")
async def get_drugs():
    try:
        async with db.pool.acquire() as connection:
            response = await connection.fetch("SELECT * FROM drugs")
            print(response)
    except:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not read drugs because of database connection"
            },
        )

    return JSONResponse(
        status_code=200, content=[record_to_dict(record) for record in response]
    )


@router.get("/{drug_id}")
async def get_drug_by_id(drug_id: int):
    try:
        async with db.pool.acquire() as connection:
            response = await connection.fetch(
                "SELECT * FROM drugs WHERE id = $1", drug_id
            )

        if not response:
            return JSONResponse(
                status_code=404,
                content={"message": "Server could not find a requested drug to read"},
            )
    except:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not read drugs because of database connection"
            },
        )

    return JSONResponse(status_code=200, content=record_to_dict(response[0]))
