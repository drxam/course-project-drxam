# Примеры содержательных комментариев ревью

## Комментарий 1: Архитектура и дизайн
**Строка 44-47 в app/main.py**
```python
if not name:
    raise ApiError(
        code="validation_error", message="name is required", status=422
    )
```
**Комментарий ревьюера:**
Хорошее улучшение! Разделение валидации на отдельные проверки делает код более читаемым. Предлагаю рассмотреть вынос валидации в отдельную функцию для переиспользования:

```python
def validate_item_name(name: str) -> str:
    if not name:
        raise ApiError(code="validation_error", message="name is required", status=422)
    if len(name) > 100:
        raise ApiError(code="validation_error", message="name must be 1..100 chars", status=422)
    if len(name.strip()) == 0:
        raise ApiError(code="validation_error", message="name cannot be empty or whitespace only", status=422)
    return name.strip()
```

## Комментарий 2: Тестирование
**Строка 22-28 в tests/test_errors.py**
```python
def test_validation_error_whitespace():
    """Тест для новой валидации - только пробелы"""
    r = client.post("/items", params={"name": "   "})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"
    assert "whitespace" in body["error"]["message"]
```
**Комментарий ревьюера:**
Отличные тесты! Покрываете edge cases. Предлагаю добавить еще один тест для проверки успешного случая с пробелами в начале/конце:

```python
def test_validation_success_with_trim():
    """Тест успешного создания с trim пробелов"""
    r = client.post("/items", params={"name": "  valid name  "})
    assert r.status_code == 200
    assert r.json()["name"] == "valid name"  # проверяем что пробелы обрезаны
```

## Комментарий 3: Производительность и безопасность
**Строка 57 в app/main.py**
```python
item = {"id": len(_DB["items"]) + 1, "name": name.strip()}
```
**Комментарий ревьюера:**
Хорошо, что добавили `strip()`! Обратите внимание на потенциальную проблему с ID - если элементы удаляются, могут быть коллизии. Для production стоит рассмотреть UUID или автоинкремент с БД.

## Итерация после комментариев
После получения комментариев разработчик:
1. Добавил функцию `validate_item_name()`
2. Добавил тест `test_validation_success_with_trim()`
3. Обновил код для использования новой функции валидации
4. Все тесты проходят
5. Код стал более модульным и переиспользуемым
