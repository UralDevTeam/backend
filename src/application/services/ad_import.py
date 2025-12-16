from __future__ import annotations

import asyncio
from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any
from uuid import UUID

from ldap3 import (
    ALL_ATTRIBUTES,
    ALL_OPERATIONAL_ATTRIBUTES,
    Connection,
    SIMPLE,
    SUBTREE,
    Server,
)

from src.config import settings
from src.infrastructure.repositories import EmployeeRepository, PositionRepository, TeamRepository


class AdImportService:
    def __init__(
            self,
            employee_repo: EmployeeRepository,
            position_repo: PositionRepository,
            team_repo: TeamRepository,
    ) -> None:
        self.employee_repo = employee_repo
        self.position_repo = position_repo
        self.team_repo = team_repo

    async def update_from_ad(self) -> dict[str, int]:
        ad_users = await self._fetch_all_users()
        if not ad_users:
            return {"imported": 0}

        existing_object_ids = await self.employee_repo.get_object_ids()
        teams = await self.team_repo.get_all()
        if not teams:
            raise ValueError("No teams available to attach imported employees")

        team_lookup = {(team.name, team.parent_id): team for team in teams}
        default_team = teams[0]
        default_leader_id = default_team.leader_employee_id

        imported = 0
        manager_lookup = self._build_manager_lookup(ad_users)
        created_employees: dict[str, dict[str, Any]] = {}

        for entry in ad_users:
            mapped = self._map_entry(entry, manager_lookup)
            if not mapped:
                continue

            if mapped["object_id"] in existing_object_ids:
                continue

            legal_entity_name = mapped["legal_entity"] or default_team.name

            company_team = await self._get_or_create_team(
                name=legal_entity_name,
                leader_employee_id=default_leader_id,
                parent_id=default_team.id,
                lookup=team_lookup,
            )

            department_name = mapped["department"]

            if department_name:
                team = await self._get_or_create_team(
                    name=department_name,
                    leader_employee_id=default_leader_id,
                    parent_id=company_team.id,
                    lookup=team_lookup,
                )
            else:
                team = company_team

            position = await self.position_repo.get_or_create(title=mapped["position"])

            employee = await self.employee_repo.create(
                {
                    "first_name": mapped["first_name"],
                    "middle_name": mapped["middle_name"],
                    "last_name": mapped["last_name"],
                    "birth_date": mapped["birth_date"],
                    "hire_date": mapped["hire_date"],
                    "city": mapped["city"],
                    "email": mapped["email"],
                    "phone": mapped["phone"],
                    "mattermost": None,
                    "tg": None,
                    "about_me": None,
                    "legal_entity": mapped["legal_entity"],
                    "department": mapped["department"],
                    "team_id": team.id,
                    "position_id": position.id,
                    "object_id": mapped["object_id"],
                }
            )

            created_employees[mapped["object_id"]] = {
                "id": employee.id,
                "team_id": team.id,
                "manager_object_id": mapped.get("manager_object_id"),
            }

            existing_object_ids.add(mapped["object_id"])
            imported += 1

        await self._assign_team_leaders(team_lookup, created_employees)

        return {"imported": imported}

    async def _get_or_create_team(
            self,
            *,
            name: str,
            leader_employee_id: UUID,
            parent_id: UUID | None,
            lookup: dict[tuple[str, UUID | None], Any],
    ):
        cache_key = (name, parent_id)
        cached = lookup.get(cache_key)
        if cached:
            return cached

        existing = await self.team_repo.find_by_name(name, parent_id=parent_id)

        if existing and existing.parent_id != parent_id:
            existing = await self.team_repo.update_parent(existing.id, parent_id)
        elif not existing:
            existing = await self.team_repo.create(
                name=name, leader_employee_id=leader_employee_id, parent_id=parent_id
            )

        lookup[cache_key] = existing
        return existing

    async def _fetch_all_users(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._fetch_all_users_sync)

    def _fetch_all_users_sync(self) -> list[dict[str, Any]]:
        ad_settings = settings.ad

        if not ad_settings.user or not ad_settings.password:
            raise ValueError("Active Directory credentials are not configured")

        server = Server(ad_settings.host, use_ssl=ad_settings.use_ssl)
        conn = Connection(
            server,
            user=ad_settings.user,
            password=ad_settings.password.get_secret_value(),
            authentication=SIMPLE,
            auto_bind=True,
        )

        try:
            return self._dump_all_users(
                conn,
                base_dn=ad_settings.base_dn,
                page_size=ad_settings.page_size,
            )
        finally:
            if conn.bound:
                conn.unbind()

    def _dump_all_users(self, conn: Connection, *, base_dn: str, page_size: int) -> list[dict[str, Any]]:
        users: list[dict[str, Any]] = []

        search_filter = "(&(objectCategory=person)(objectClass=user))"
        cookie = None

        while True:
            conn.search(
                search_base=base_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES],
                paged_size=page_size,
                paged_cookie=cookie,
            )

            for entry in conn.entries:
                users.append(
                    {"dn": entry.entry_dn, "attributes": entry.entry_attributes_as_dict}
                )

            controls = conn.result.get("controls", {})
            page_control = controls.get("1.2.840.113556.1.4.319", {})
            cookie = page_control.get("value", {}).get("cookie", None)

            if not cookie:
                break

        return users

    def _map_entry(
            self,
            entry: dict[str, Any],
            manager_lookup: dict[str, str],
    ) -> dict[str, Any] | None:
        attributes: dict[str, Any] = entry.get("attributes", {})

        if self._is_service_account(entry):
            return None

        object_id = self._first_attr(attributes, "objectGUID")
        email = self._first_attr(attributes, "mail") or self._first_attr(
            attributes, "userPrincipalName"
        )

        if not object_id or not email:
            return None

        display_name = self._first_attr(attributes, "displayName") or self._first_attr(
            attributes, "name"
        )
        name_parts = display_name.split() if display_name else []

        first_name = self._first_attr(attributes, "givenName") or (
            name_parts[0] if name_parts else None
        )
        middle_name = self._first_attr(attributes, "middleName")
        last_name = self._first_attr(attributes, "sn") or (
            name_parts[-1] if len(name_parts) > 1 else None
        )

        if not middle_name and len(name_parts) > 2:
            middle_name = " ".join(name_parts[1:-1])

        birth_date = self._parse_date(self._first_attr(attributes, "birthDate"))
        hire_date = self._parse_date(self._first_attr(attributes, "whenCreated"))

        city = self._normalize_city(self._first_attr(attributes, "l"))

        manager_dn = self._first_attr(attributes, "manager")
        manager_dn_lower = str(manager_dn).lower() if manager_dn else None
        manager_object_id = manager_lookup.get(manager_dn_lower) if manager_dn_lower else None

        return {
            "object_id": object_id,
            "email": email,
            "first_name": first_name or "Employee",
            "middle_name": middle_name or "",
            "last_name": last_name,
            "birth_date": birth_date or date.today(),
            "hire_date": hire_date or date.today(),
            "city": city,
            "phone": self._first_attr(attributes, "telephoneNumber"),
            "legal_entity": self._first_attr(attributes, "company"),
            "department": self._first_attr(attributes, "department"),
            "position": self._first_attr(attributes, "title") or "Сотрудник",
            "manager_object_id": manager_object_id,
        }

    def _build_manager_lookup(self, entries: list[dict[str, Any]]) -> dict[str, str]:
        lookup: dict[str, str] = {}
        for entry in entries:
            dn = str(entry.get("dn", "")).lower()
            attributes: dict[str, Any] = entry.get("attributes", {})
            object_id = self._first_attr(attributes, "objectGUID")
            if dn and object_id:
                lookup[dn] = object_id
        return lookup

    def _parse_date(self, value: Any) -> date | None:
        if not value:
            return None

        if isinstance(value, date) and not isinstance(value, datetime):
            return value

        if isinstance(value, datetime):
            return value.date()

        try:
            dt = datetime.fromisoformat(str(value))
            return dt.date()
        except (TypeError, ValueError):
            return None

    def _first_attr(self, attributes: dict[str, Any], key: str) -> Any:
        value = attributes.get(key)
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def _normalize_city(self, value: Any) -> str | None:
        if value is None:
            return None

        city = str(value).strip()
        return city or None

    def _is_service_account(self, entry: dict[str, Any]) -> bool:
        dn = entry.get("dn", "")
        attributes: dict[str, Any] = entry.get("attributes", {})
        distinguished_name = self._first_attr(attributes, "distinguishedName") or ""

        dn_lower = str(dn).lower()
        distinguished_lower = str(distinguished_name).lower()

        return "ou=service" in dn_lower or "ou=service" in distinguished_lower

    async def _assign_team_leaders(
            self,
            team_lookup: dict[tuple[str, UUID | None], Any],
            created_employees: dict[str, dict[str, Any]],
    ) -> None:
        members_by_team: dict[UUID, list[str]] = defaultdict(list)

        for object_id, info in created_employees.items():
            members_by_team[info["team_id"]].append(object_id)

        for team_id, members in members_by_team.items():
            in_team = set(members)
            manager_counts: Counter[str] = Counter()
            fallback_candidate: str | None = None

            for object_id in members:
                manager_object_id = created_employees[object_id].get("manager_object_id")
                if manager_object_id in in_team:
                    manager_counts[manager_object_id] += 1
                elif fallback_candidate is None:
                    fallback_candidate = object_id

            candidate_object_id: str | None = None

            if manager_counts:
                candidate_object_id = manager_counts.most_common(1)[0][0]
            else:
                candidate_object_id = fallback_candidate

            if not candidate_object_id:
                continue

            leader_id = created_employees[candidate_object_id]["id"]
            updated_team = await self.team_repo.update_leader(team_id, leader_id)
            lookup_key = (updated_team.name, updated_team.parent_id)
            team_lookup[lookup_key] = updated_team
