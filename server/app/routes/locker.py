from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..utils import db
from ..utils.record_to_dict import record_to_dict


router = APIRouter(prefix="/lockers", tags=["inventories"])


class LockerTransferPayload(BaseModel):
    source_locker_id: int
    destination_locker_id: int
    drug_id: int
    quantity: int


@router.get("")
async def get_lockers(keyword: str | None = Query(default=None)):
    try:
        async with db.pool.acquire() as connection:
            base_query = """
                SELECT
                    lockers_drugs.locker_id,
                    lockers_drugs.drug_id,
                    lockers.locker_name,
                    lockers_drugs.slot_code,
                    drugs.trade_name,
                    lockers_drugs.quantity,
                    lockers_drugs.last_updated
                FROM lockers_drugs
                INNER JOIN drugs
                    ON lockers_drugs.drug_id = drugs.id
                INNER JOIN lockers
                    ON lockers_drugs.locker_id = lockers.id
            """

            if keyword and keyword.strip():
                normalized_keyword = f"%{keyword.strip()}%"
                response = await connection.fetch(
                    base_query
                    + """
                    WHERE lockers.locker_name ILIKE $1
                        OR drugs.trade_name ILIKE $1
                        OR lockers_drugs.slot_code ILIKE $1
                    ORDER BY lockers.id
                    """,
                    normalized_keyword,
                )
            else:
                response = await connection.fetch(base_query + " ORDER BY lockers.id")
    except:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not read drug locker because of database connection"
            },
        )

    return JSONResponse(
        status_code=200, content=[record_to_dict(record) for record in response]
    )


@router.get("/drug/{drug_id}")
async def get_lockers_by_drug_id(drug_id: int):
    try:
        async with db.pool.acquire() as connection:
            response = await connection.fetch(
                """
                SELECT
                    lockers.locker_name,
                    lockers_drugs.slot_code,
                    drugs.trade_name,
                    lockers_drugs.quantity,
                    lockers_drugs.last_updated
                FROM lockers_drugs 
                INNER JOIN drugs
                    ON lockers_drugs.drug_id = drugs.id
                INNER JOIN lockers
                    ON lockers_drugs.locker_id = lockers.id
                WHERE lockers_drugs.drug_id = $1 
                ORDER BY lockers.id
                """,
                drug_id,
            )

        if not response:
            return JSONResponse(
                status_code=404,
                content={"message": "Server could not find a requested locker to read"},
            )
    except:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not read locker because of database connection"
            },
        )

    return JSONResponse(
        status_code=200, content=[record_to_dict(record) for record in response]
    )


@router.get("/{locker_id}")
async def get_lockers_by_drug_id(locker_id: int):
    try:
        async with db.pool.acquire() as connection:
            response = await connection.fetch(
                """
                SELECT 
                    lockers.locker_name,
                    lockers_drugs.slot_code,
                    drugs.trade_name,
                    lockers_drugs.quantity,
                    lockers_drugs.last_updated
                FROM lockers_drugs 
                INNER JOIN drugs
                    ON lockers_drugs.drug_id = drugs.id
                INNER JOIN lockers
                    ON lockers_drugs.locker_id = lockers.id
                WHERE lockers_drugs.locker_id = $1
                ORDER BY lockers.id
                """,
                locker_id,
            )

        if not response:
            return JSONResponse(
                status_code=404,
                content={"message": "Server could not find a requested locker to read"},
            )
    except:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not read locker because of database connection"
            },
        )

    return JSONResponse(
        status_code=200, content=[record_to_dict(record) for record in response]
    )


@router.put("/{locker_id}/drug/{drug_id}/add/{quantity}")
async def add_quantity(locker_id: int, drug_id: int, quantity: int):
    try:
        async with db.pool.acquire() as connection:
            response = await connection.fetchrow(
                """
                UPDATE lockers_drugs
                SET quantity = quantity + $1, last_updated = NOW()
                WHERE locker_id = $2 AND drug_id = $3 
                RETURNING *
                """,
                quantity,
                locker_id,
                drug_id,
            )

            if not response:
                return JSONResponse(
                    status_code=404,
                    content={
                        "message": "Server could not find a requested drug to update"
                    },
                )
    except:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not update locker because of database connection"
            },
        )

    return JSONResponse(status_code=200, content=record_to_dict(response))


@router.put("/{locker_id}/drug/{drug_id}/subtract/{quantity}")
async def subtract_quantity(locker_id: int, drug_id: int, quantity: int):
    try:
        async with db.pool.acquire() as connection:
            response = await connection.fetchrow(
                """
                UPDATE lockers_drugs 
                SET quantity = quantity - $1, last_updated = NOW()
                WHERE locker_id = $2 AND drug_id = $3
                RETURNING *
                """,
                quantity,
                locker_id,
                drug_id,
            )

            if not response:
                return JSONResponse(
                    status_code=404,
                    content={
                        "message": "Server could not find a requested drug to update"
                    },
                )
    except:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not update locker because of database connection"
            },
        )

    return JSONResponse(status_code=200, content=record_to_dict(response))


@router.put("/transfer")
async def transfer_quantity(payload: LockerTransferPayload):
    if payload.source_locker_id == payload.destination_locker_id:
        return JSONResponse(
            status_code=400,
            content={"message": "Source and destination lockers must be different"},
        )

    if payload.quantity <= 0:
        return JSONResponse(
            status_code=400,
            content={"message": "Transfer quantity must be a positive integer"},
        )

    try:
        async with db.pool.acquire() as connection:
            async with connection.transaction():
                source_record = await connection.fetchrow(
                    """
                    SELECT *
                    FROM lockers_drugs
                    WHERE locker_id = $1 AND drug_id = $2
                    FOR UPDATE
                    """,
                    payload.source_locker_id,
                    payload.drug_id,
                )
                destination_record = await connection.fetchrow(
                    """
                    SELECT *
                    FROM lockers_drugs
                    WHERE locker_id = $1 AND drug_id = $2
                    FOR UPDATE
                    """,
                    payload.destination_locker_id,
                    payload.drug_id,
                )

                if not source_record or not destination_record:
                    return JSONResponse(
                        status_code=404,
                        content={
                            "message": "Server could not find source or destination locker record"
                        },
                    )

                if source_record["quantity"] < payload.quantity:
                    return JSONResponse(
                        status_code=400,
                        content={"message": "Insufficient stock in source locker"},
                    )

                updated_source = await connection.fetchrow(
                    """
                    UPDATE lockers_drugs
                    SET quantity = quantity - $1, last_updated = NOW()
                    WHERE locker_id = $2 AND drug_id = $3
                    RETURNING *
                    """,
                    payload.quantity,
                    payload.source_locker_id,
                    payload.drug_id,
                )
                updated_destination = await connection.fetchrow(
                    """
                    UPDATE lockers_drugs
                    SET quantity = quantity + $1, last_updated = NOW()
                    WHERE locker_id = $2 AND drug_id = $3
                    RETURNING *
                    """,
                    payload.quantity,
                    payload.destination_locker_id,
                    payload.drug_id,
                )
    except:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Server could not transfer stock because of database connection"
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "message": "Stock transferred successfully",
            "source": record_to_dict(updated_source),
            "destination": record_to_dict(updated_destination),
        },
    )
