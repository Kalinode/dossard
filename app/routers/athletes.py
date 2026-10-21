from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request, status
from fastapi.exceptions import RequestValidationError

from app.db import Conn
from app.repositories import athletes
from app.schemas import AthleteCreate, AthleteImportResult, AthleteOut

router = APIRouter(prefix="/athletes", tags=["athletes"])


@router.get("", response_model=list[AthleteOut], summary="Lister les athlètes")
def list_athletes(
    conn: Conn,
    club: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AthleteOut]:
    return athletes.list_athletes(conn, club=club, limit=limit, offset=offset)


@router.get("/{athlete_id}", response_model=AthleteOut, summary="Consulter un athlète")
def get_athlete(athlete_id: int, conn: Conn) -> AthleteOut:
    return athletes.get_athlete(conn, athlete_id)


@router.post(
    "",
    response_model=AthleteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un athlète",
)
def create_athlete(data: AthleteCreate, conn: Conn) -> AthleteOut:
    return athletes.create_athlete(conn, data)


@router.post(
    "/import",
    response_model=AthleteImportResult,
    summary="Importer les athlètes depuis le CSV de la fédération",
)
async def import_athletes(request: Request, conn: Conn) -> AthleteImportResult:
    """Importe le CSV brut de la fédération (text/csv, séparateur `;`, dates jj/mm/aaaa)."""
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "text/csv":
        raise _invalid_body("Content-Type text/csv attendu")
    try:
        content = (await request.body()).decode("utf-8-sig")
    except UnicodeDecodeError:
        raise _invalid_body("CSV en UTF-8 attendu") from None
    missing = athletes.missing_import_columns(content)
    if missing:
        raise _invalid_body("Colonnes manquantes : " + ", ".join(sorted(missing)))
    return athletes.import_athletes(conn, content)


def _invalid_body(message: str) -> RequestValidationError:
    return RequestValidationError([{"loc": ("body",), "msg": message, "type": "value_error"}])
