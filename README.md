# ⚠️ DISCLAIMER / ДИСКЛЕЙМЕР

## English

**THIS IS AN EDUCATIONAL PROJECT. FOR EDUCATIONAL PURPOSES ONLY.**

This repository contains an **intentionally vulnerable** web application, created as part of **Laboratory Work No. 2** for an academic course related to information security.

- The application is **intended to run only on `localhost` (127.0.0.1)** and **must not** be deployed to the internet or any public network.
- The vulnerabilities (SQL injection, IDOR) are implemented **on purpose** to demonstrate attack and defense techniques in an educational context.
- The exploit script (`exploit.py`) works **only against a locally running** instance of the application from this same repository.
- The author **assumes no responsibility** for any use of this code for illegal purposes.
- **Do not use** these techniques against systems you do not have explicit permission to test. Doing so is illegal.

If you are not a student performing this laboratory work, **do not run** this application. If you are a student, run it **locally only**, **on your own machine**.

## Русский

**ЭТО УЧЕБНЫЙ ПРОЕКТ. ТОЛЬКО ДЛЯ ОБРАЗОВАТЕЛЬНЫХ ЦЕЛЕЙ.**

Данный репозиторий содержит **намеренно уязвимое** веб-приложение, созданное в рамках **лабораторной работы №2** по дисциплине, связанной с информационной безопасностью.

- Приложение **предназначено только для запуска на `localhost` (127.0.0.1)** и **не должно** развёртываться в интернете или любой публичной сети.
- Уязвимости (SQL-инъекция, IDOR) реализованы **специально** для демонстрации методов атак и защиты в учебных целях.
- Эксплойт (`exploit.py`) работает **только против локально запущенного** экземпляра приложения из этого же репозитория.
- Автор **не несёт ответственности** за любое использование кода в противоправных целях.
- **Не используйте** эти техники против систем, на которые у вас нет явного разрешения. Это незаконно.

Если вы не студент, выполняющий эту лабораторную, — **не запускайте** это приложение. Если вы студент — запускайте **только локально** и **только на своей машине**.

---

# Лабораторная работа №2

Учебное веб-приложение на Flask, демонстрирующее две уязвимости из **OWASP Top 10**:

1. **SQL-инъекция (SQLi)** — категория **A03:2021 (Injection)**
2. **IDOR / Broken Access Control** — категория **A01:2021 (Broken Access Control)**

## Теория

### 1. SQL-инъекция (SQLi)

**Что это.** SQL-инъекция — это внедрение произвольного SQL-кода через пользовательский ввод. Возникает, когда приложение **склеивает** SQL-запрос из строки и пользовательских данных, вместо того чтобы передавать данные отдельно.

**Как работает в этом приложении.** Эндпоинт `/user?name=...` формирует запрос так:

```python
query = f"SELECT username, secret FROM users WHERE username = '{username}'"
cursor.execute(query)
```

Если передать `name = admin' OR '1'='1`, запрос превращается в:

```sql
SELECT username, secret FROM users WHERE username = 'admin' OR '1'='1'
```

Условие `'1'='1'` всегда истинно, поэтому возвращаются **все** пользователи со всеми секретами, а не только `admin`.

**Последствия.** Утечка данных, обход аутентификации, изменение/удаление данных, в некоторых СУБД — выполнение команд ОС.

**Защита.** Параметризованные запросы (prepared statements): запрос и данные передаются **раздельно**. В коде это `?` (плейсхолдер) и кортеж значений:

```python
query = "SELECT username, secret FROM users WHERE username = ?"
cursor.execute(query, (username,))
```

База получает запрос и значение **отдельно**. Ввод трактуется как **строка-значение**, а не как SQL-код. Инъекция невозможна.

### 2. IDOR / Broken Access Control

**Что это.** IDOR (Insecure Direct Object Reference) — разновидность Broken Access Control. Приложение отдаёт объект по его идентификатору, **не проверяя**, что объект принадлежит текущему пользователю.

**Как работает в этом приложении.** Эндпоинт `/message?id=...`:

```python
cursor.execute(f"SELECT owner, text FROM messages WHERE id = {message_id}")
result = cursor.fetchone()
if result:
    owner, text = result
    return f"Сообщение #{message_id} (Владелец: {owner}): {text}"
```

Пользователь `user1` запрашивает `?id=1` — сообщение, принадлежащее `admin`. Приложение отдаёт его **без проверки прав**.

**Последствия.** Пользователь читает/меняет/удаляет чужие данные: сообщения, заказы, документы, профили.

**Защита.** Проверка прав на **каждый** объект:

```python
cursor.execute("SELECT owner, text FROM messages WHERE id = ?", (message_id,))
result = cursor.fetchone()
if result:
    owner, text = result
    if owner != current_user:
        return "Ошибка доступа: У вас нет прав на просмотр этого сообщения!", 403
    return f"Сообщение #{message_id} (Владелец: {owner}): {text}"
```

Плюс — параметризация `id`, чтобы заодно закрыть потенциальную SQLi по этому параметру.

## Структура репозитория

```
app.py          — уязвимое приложение (Flask, SQLite в памяти)
exploit.py      — скрипт эксплуатации обеих уязвимостей
patch.diff      — патч, закрывающий SQLi и IDOR
README.md       — этот файл
```

## Запуск

```bash
pip install flask requests
python app.py
```

Приложение поднимется на `http://127.0.0.1:5000`.

## Эксплуатация

Во втором терминале:

```bash
python exploit.py
```

Ожидаемый вывод (уязвимая версия):

```
[SUCCESS] SQL-инъекция успешно эксплуатирована! Данные утекли.
[SUCCESS] IDOR успешно эксплуатирована! Прочитано приватное сообщение администратора.
```

## Патч

```bash
git apply patch.diff
```

После применения патча:

| Проверка | Уязвимая версия | Пропатченная |
|---|---|---|
| `/user?name=admin' OR '1'='1'` | два секрета (утечка) | `[]` (пусто) |
| `/user?name=admin` | секрет админа | секрет админа (работает) |
| `/message?id=1` (чужое) | секретное сообщение | `403 Ошибка доступа` |
| `/message?id=2` (своё) | работает | работает |

Функционал приложения **не ломается** — закрываются только уязвимости.
