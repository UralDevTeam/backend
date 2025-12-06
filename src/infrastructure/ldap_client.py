from __future__ import annotations
import os
from typing import Dict, List, Optional, Any
from ldap3 import Server, Connection, Tls, ALL, SUBTREE, ALL_ATTRIBUTES, MODIFY_REPLACE, SIMPLE
import ssl


class LdapClient:
    """
    Простой LDAP-клиент на ldap3.
    Подходит для OpenLDAP/389-DS/AD (с корректировками DN и атрибутов).
    """

    def __init__(
        self,
        host: str,
        port: int = 389,
        use_ssl: bool = False,
        start_tls: bool = False,
        bind_dn: Optional[str] = None,
        bind_password: Optional[str] = None,
        base_dn: str = "",
        timeout: int = 5,
    ):
        self.base_dn = base_dn
        tls = None
        if use_ssl or start_tls:
            tls = Tls(
                validate=ssl.CERT_NONE,
                version=ssl.PROTOCOL_TLS_CLIENT,
            )
        self.server = Server(
            host, port=port, use_ssl=use_ssl, get_info=ALL, tls=tls
        )
        self.conn = Connection(
            self.server,
            user=bind_dn,
            password=bind_password,
            receive_timeout=timeout,
            authentication=SIMPLE,
            auto_bind=True,
        )
        if start_tls and not use_ssl:
            if not self.conn.start_tls():
                raise RuntimeError(f"STARTTLS failed: {self.conn.result}")

        if bind_dn and bind_password:
            if not self.conn.bind():
                raise RuntimeError(f"Bind failed: {self.conn.result}")

    # --- Поиск ---
    def search(
        self,
        search_base: Optional[str],
        ldap_filter: str,
        attributes: Optional[List[str]] = None,
        scope=SUBTREE,
        size_limit: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Возвращает список записей в виде словарей {dn, attributes}.
        size_limit=0 означает без лимита (на стороне клиента).
        """
        base = search_base or self.base_dn
        attrs = attributes or ALL_ATTRIBUTES

        ok = self.conn.search(
            search_base=base,
            search_filter=ldap_filter,
            search_scope=scope,
            attributes=attrs,
            size_limit=size_limit,
        )
        if not ok:
            raise RuntimeError(f"Search error: {self.conn.result}")

        results: List[Dict[str, Any]] = []
        for entry in self.conn.response:
            if entry.get("type") != "searchResEntry":
                continue
            results.append(
                {"dn": entry["dn"], "attributes": entry["attributes"]}
            )
        return results

    # --- Проверка логина пользователя (bind-as-user) ---
    def verify_password(self, user_dn: str, password: str) -> bool:
        """
        Пытается забиндиться от имени пользователя. Пароль не хранится.
        """
        tmp = Connection(self.server, user=user_dn, password=password, auto_bind=False)
        try:
            return tmp.bind()
        finally:
            tmp.unbind()

    # --- Создание записи ---
    def add_entry(self, dn: str, attributes: Dict[str, Any]) -> None:
        ok = self.conn.add(dn, attributes=attributes)
        if not ok:
            raise RuntimeError(f"Add failed: {self.conn.result}")

    # --- Обновление атрибутов (полная замена значений) ---
    def replace_attributes(self, dn: str, attributes: Dict[str, Any]) -> None:
        changes = {k: [(MODIFY_REPLACE, v if isinstance(v, list) else [v])] for k, v in attributes.items()}
        ok = self.conn.modify(dn, changes)
        if not ok:
            raise RuntimeError(f"Modify failed: {self.conn.result}")

    # --- Удаление записи ---
    def delete_entry(self, dn: str) -> None:
        ok = self.conn.delete(dn)
        if not ok:
            raise RuntimeError(f"Delete failed: {self.conn.result}")

    # --- Закрытие соединения ---
    def close(self) -> None:
        try:
            self.conn.unbind()
        except Exception:
            pass


def from_env() -> LdapClient:
    """
    Быстрый конструктор из переменных окружения.
    """
    host = os.getenv("LDAP_HOST", "localhost")
    port = int(os.getenv("LDAP_PORT", "389"))
    use_ssl = os.getenv("LDAP_SSL", "false").lower() == "true"
    start_tls = os.getenv("LDAP_STARTTLS", "false").lower() == "true"
    bind_dn = os.getenv("LDAP_BIND_DN")  # напр. "cn=admin,dc=example,dc=org"
    bind_password = os.getenv("LDAP_BIND_PASSWORD")
    base_dn = os.getenv("LDAP_BASE_DN", "dc=example,dc=org")
    timeout = int(os.getenv("LDAP_TIMEOUT", "5"))

    return LdapClient(
        host=host,
        port=port,
        use_ssl=use_ssl,
        start_tls=start_tls,
        bind_dn=bind_dn,
        bind_password=bind_password,
        base_dn=base_dn,
        timeout=timeout,
    )
