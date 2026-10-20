from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date, datetime

from pydantic import ValidationError

from app.categories import age_category
from app.errors import ConflictError
from app.repositories.common import fetch_or_404
from app.schemas import AthleteCreate, AthleteImportError, AthleteImportResult, AthleteOut

IMPORT_COLUMNS = {
    "nom",
    "prenom",
    "date_naissance",
    "sexe",
    "club",
    "licence",
    "certificat_valide_jusqu",
}


def _to_athlete(row: sqlite3.Row) -> AthleteOut:
    birth_date = date.fromisoformat(row["birth_date"])
    certificate = row["medical_certificate_valid_until"]
    return AthleteOut(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        birth_date=birth_date,
        sex=row["sex"],
        club=row["club"],
        license_number=row["license_number"],
        medical_certificate_valid_until=date.fromisoformat(certificate) if certificate else None,
        category=age_category(birth_date),
    )


def list_athletes(conn: sqlite3.Connection, club: str | None = None) -> list[AthleteOut]:
    sql = "SELECT * FROM athletes"
    params: tuple[str, ...] = ()
    if club is not None:
        sql += " WHERE club = ?"
        params = (club,)
    sql += " ORDER BY last_name, first_name, id"
    return [_to_athlete(row) for row in conn.execute(sql, params)]


def get_athlete(conn: sqlite3.Connection, athlete_id: int) -> AthleteOut:
    row = fetch_or_404(
        conn,
        "SELECT * FROM athletes WHERE id = ?",
        (athlete_id,),
        f"Athlète {athlete_id} introuvable",
    )
    return _to_athlete(row)


def create_athlete(conn: sqlite3.Connection, data: AthleteCreate) -> AthleteOut:
    existing = conn.execute(
        "SELECT id FROM athletes WHERE license_number = ?", (data.license_number,)
    ).fetchone()
    if existing is not None:
        raise ConflictError(f"Licence {data.license_number} déjà enregistrée")

    certificate = data.medical_certificate_valid_until
    cursor = conn.execute(
        "INSERT INTO athletes (first_name, last_name, birth_date, sex, club, license_number,"
        " medical_certificate_valid_until) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data.first_name,
            data.last_name,
            data.birth_date.isoformat(),
            data.sex.value,
            data.club,
            data.license_number,
            certificate.isoformat() if certificate else None,
        ),
    )
    row = conn.execute("SELECT * FROM athletes WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _to_athlete(row)


def _parse_french_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        raise ValueError(f"date invalide « {value} » (format jj/mm/aaaa attendu)") from None


def _row_to_athlete_create(row: dict[str, str | None]) -> AthleteCreate:
    values = {key: (value or "").strip() for key, value in row.items() if key is not None}
    birth_date = _parse_french_date(values["date_naissance"])
    if birth_date is None:
        raise ValueError("date de naissance manquante")
    try:
        return AthleteCreate(
            last_name=values["nom"],
            first_name=values["prenom"],
            birth_date=birth_date,
            sex=values["sexe"],
            club=values["club"] or None,
            license_number=values["licence"],
            medical_certificate_valid_until=_parse_french_date(values["certificat_valide_jusqu"]),
        )
    except ValidationError as exc:
        first = exc.errors()[0]
        raise ValueError(f"{first['loc'][0]} : {first['msg']}") from None


def missing_import_columns(content: str) -> set[str]:
    """Colonnes obligatoires absentes de l'en-tête du CSV."""
    header = next(csv.reader(io.StringIO(content), delimiter=";"), [])
    return IMPORT_COLUMNS - {name.strip() for name in header}


def import_athletes(conn: sqlite3.Connection, content: str) -> AthleteImportResult:
    """Importe un CSV de la fédération : une ligne invalide n'arrête pas les suivantes."""
    created = 0
    skipped = 0
    errors: list[AthleteImportError] = []
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    reader.fieldnames = [name.strip() for name in reader.fieldnames or []]
    for row in reader:
        line = reader.line_num
        try:
            data = _row_to_athlete_create(row)
            create_athlete(conn, data)
        except ConflictError:
            skipped += 1
        except ValueError as exc:
            errors.append(AthleteImportError(line=line, message=str(exc)))
        else:
            created += 1
    return AthleteImportResult(created=created, skipped=skipped, errors=errors)
