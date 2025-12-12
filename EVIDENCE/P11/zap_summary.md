# DAST (OWASP ZAP Baseline) Scan Summary

Generated: 2025-12-12T20:36:00+00:00
Workflow: Security - DAST (OWASP ZAP Baseline)
Target: http://localhost:8000/

## Scan Results

**Total alerts**: 2

### Risk Distribution

- **High**: 0
- **Medium**: 0
- **Low**: 0
- **Informational**: 2

### Alert Details

1. **Storable and Cacheable Content [10049]** - WARN
   - Count: 5
   - URLs: http://localhost:8000/ and common paths (robots.txt, sitemap.xml, favicon.ico)
   - Note: These are 404 responses, which is expected for a minimal API

2. **Sec-Fetch-Dest Header is Missing [90005]** - WARN
   - Count: 8-10
   - Description: Missing Sec-Fetch-Dest header in responses
   - Note: Low priority, modern browsers handle this automatically

### Passed Checks

68 security checks passed, including:
- Cookie security flags
- Content-Type headers
- X-Content-Type-Options headers
- Anti-clickjacking headers
- Information disclosure checks
- And many more...

## Reports

- HTML Report: `EVIDENCE/P11/zap_baseline.html`
- JSON Report: `EVIDENCE/P11/zap_baseline.json`

## Notes

- ZAP baseline scan performed against running application
- Application started via docker-compose (production-like configuration)
- All findings should be reviewed and triaged
- False positives should be documented with justification

## Analysis

**Вывод**: Найдено 2 предупреждения низкого приоритета. Критических или высокоприоритетных уязвимостей не обнаружено. Предупреждения связаны с:
1. Отсутствием стандартных файлов (robots.txt, sitemap.xml) - это нормально для API
2. Отсутствием заголовка Sec-Fetch-Dest - низкоприоритетное предупреждение

**Рекомендации**: 
- Рассмотреть добавление robots.txt для SEO (если применимо)
- Добавление Sec-Fetch-Dest заголовка не критично, но может быть улучшением

## Next Steps

1. Review ZAP findings in `zap_baseline.html`
2. Investigate High and Medium severity alerts (none found)
3. Fix critical issues or document accepted risks
4. Update security documentation if needed

