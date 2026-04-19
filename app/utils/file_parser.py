import io
import json
import csv
from typing import Any

from fastapi import HTTPException, UploadFile, status


async def parse_upload(file: UploadFile) -> tuple[list[dict[str, Any]], str]:
    raw_bytes = await file.read()
    filename = file.filename or "dataset"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension == "csv":
        decoded = raw_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        rows: list[dict[str, Any]] = []
        for row in reader:
            rows.append({key: value if value is not None else "" for key, value in row.items()})
        return rows, "csv"

    if extension == "json":
        content = json.loads(raw_bytes.decode("utf-8"))
        if isinstance(content, list):
            return content, "json"
        if isinstance(content, dict):
            return [content], "json"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported file type. Only CSV and JSON are allowed.",
    )
