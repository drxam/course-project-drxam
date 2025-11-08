# Настройка защиты ветки main

## Текущее состояние
✅ CI workflow настроен в `.github/workflows/ci.yml`
✅ Workflow запускается на PR и push в main
✅ Проверки: ruff, black, isort, pytest, pre-commit

## Настройки защиты ветки (для GitHub репозитория)

### 1. Перейти в Settings → Branches
- Repository → Settings → Branches
- Нажать "Add rule" для ветки `main`

### 2. Настроить правила защиты
```
Branch name pattern: main
☑️ Require a pull request before merging
  ☑️ Require approvals (1)
  ☑️ Dismiss stale PR approvals when new commits are pushed
☑️ Require status checks to pass before merging
  ☑️ Require branches to be up to date before merging
  ☑️ CI / build (required check)
☑️ Require conversation resolution before merging
☑️ Restrict pushes that create files larger than 100 MB
```

### 3. Проверка через GitHub CLI
```bash
# Проверить настройки защиты
gh api repos/:owner/:repo/branches/main/protection

# Проверить required checks
gh api repos/:owner/:repo/branches/main/protection/required_status_checks
```

## Доказательства настройки
- Скриншот настроек защиты ветки
- Вывод `gh api` команд (без секретов)
- Зеленый статус CI в PR

## Дополнительные настройки (опционально)
- CODEOWNERS файл для автоматического назначения ревьюеров
- Автоматическое подписание коммитов
- Правила для force push
