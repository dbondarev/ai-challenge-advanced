# День 3. Testing Bookreader

## Уровень 1

Промпт: `prompt-level-1.txt`. С первого раза: три файла, 10 тестов, `scripts/check.sh` зелёный. Лог: `level-1-check.log`.

- `apps/api/test/epub.test.ts`
- `apps/api/test/progress.test.ts`
- `apps/api/test/http.test.ts` (главы, 404, DELETE)

В продукте добавлено удаление книги (API + кнопка Delete), без этого smoke «создать → удалить» не закрывался.

## Уровень 2

Сценарии: `smoke.md`. Playwright MCP, скриншоты в `screenshots/`. Отчёт: `smoke-report.md`. Все четыре сценария прошли.

Логина нет: создать = загрузка EPUB.

## Flow

`bookreader/.cursor/agents/qa-runner.md` — после изменения/PR: check.sh + smoke MCP + один отчёт.
Скилл `update-smoke` — «задеплоил фичу, обнови smoke и прогони всё». Delete уже внесен в `qa/smoke.md` как новая фича этого дня.
