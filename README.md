# backend

Инструкция по запуску
---

# Запуск проекта

### 1. Соберите и запустите контейнеры

```bash
docker compose build --no-cache
docker compose up -d
```

### 2. Проверьте работу сервиса

**Проверка API:**

```bash
curl http://127.0.0.1:8000/api/ping
# → {"ping":"pong"}
```

**Проверка соединения с LDAP:**

```bash
curl http://127.0.0.1:8000/ldap/ping
# → {"ldap":"ok"}
```

**Документация FastAPI:**
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 3. Веб-интерфейс LDAP (phpLDAPadmin)

* URL: [http://127.0.0.1:8080](http://127.0.0.1:8080)
* Login DN: `cn=admin,dc=example,dc=org`
* Password: `admin`

---

### 4. Остановка контейнеров

```bash
docker compose down
```

---

