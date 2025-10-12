from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import Request
import csv
from pathlib import Path

# --- Pydantic-модель (отражает столбцы CSV) ---
class ADUser(BaseModel):
    name: str = Field(..., alias="Name")
    sam: str = Field(..., alias="SamAccountName")
    upn: Optional[str] = Field(None, alias="UserPrincipalName")
    enabled: Optional[bool] = Field(None, alias="Enabled")
    department: Optional[str] = Field(None, alias="Department")
    title: Optional[str] = Field(None, alias="Title")

    @staticmethod
    def _to_bool(v: str | bool | None) -> Optional[bool]:
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        if s in {"true", "1", "yes"}:
            return True
        if s in {"false", "0", "no"}:
            return False
        return None

    @classmethod
    def from_csv_row(cls, row: dict) -> "ADUser":
        # нормализуем ключи (на случай BOM/пробелов)
        norm = {k.strip("\ufeff ").strip(): (v.strip() if isinstance(v, str) else v)
                for k, v in row.items()}
        # кастуем Enabled к bool
        if "Enabled" in norm:
            norm["Enabled"] = cls._to_bool(norm["Enabled"])
        return cls.model_validate(norm)

# --- простое хранилище в памяти ---
class Store:
    def __init__(self, path: str) -> None:
        self.items: list[ADUser] = []
        self.by_sam: dict[str, ADUser] = {}
        self.path: Path = Path(path)

    def load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"CSV не найден: {self.path}")
        with self.path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            self.items = [ADUser.from_csv_row(r) for r in reader]
        self.by_sam = {u.sam.lower(): u for u in self.items}

    def search(
        self,
        q: Optional[str],
        enabled: Optional[bool],
        department: Optional[str],
        title: Optional[str],
        offset: int,
        limit: int,
        sort: str
    ) -> tuple[int, List[ADUser]]:
        data = self.items
        # фильтры
        if q:
            ql = q.lower()
            data = [
                u for u in data
                if ql in (u.name or "").lower()
                or ql in (u.sam or "").lower()
                or ql in (u.upn or "").lower()
                or ql in (u.department or "").lower()
                or ql in (u.title or "").lower()
            ]
        if enabled is not None:
            data = [u for u in data if u.enabled is enabled]
        if department:
            dl = department.lower()
            data = [u for u in data if (u.department or "").lower() == dl]
        if title:
            tl = title.lower()
            data = [u for u in data if (u.title or "").lower() == tl]

        # сортировка
        key_map = {
            "name": lambda u: (u.name or "").lower(),
            "sam": lambda u: (u.sam or "").lower(),
            "department": lambda u: (u.department or "").lower(),
            "title": lambda u: (u.title or "").lower(),
        }
        desc = sort.startswith("-")
        field = sort[1:] if desc else sort
        key = key_map.get(field, key_map["name"])
        data = sorted(data, key=key, reverse=desc)

        total = len(data)
        # пагинация
        page = data[offset: offset + limit]
        return total, page

def get_store(request: Request) -> Store:
    return request.app.state.store