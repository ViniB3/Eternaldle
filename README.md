# Eternaldle

Jogo Eternaldle
Bem-vindo ao Eternaldle, um jogo de adivinhação de personagens.

https://eternaldle.onrender.com/

## Uso opcional do Redis (Upstash) para contador diário

Se o serviço estiver hospedado em um plano sem disco persistente (ex.: Render Free), você pode usar um Redis gerenciado (por exemplo, Upstash) apenas para o contador diário.

- Configure uma instância Upstash/Redis e copie a `Redis URL`.
- Defina a variável de ambiente `REDIS_URL` (ou `UPSTASH_REDIS_URL`) no painel do Render para essa URL.
- O código usará Redis para incrementar/ler o contador diário de forma atômica; se `REDIS_URL` não estiver definida, o app continuará usando o SQLite local como fallback.

### Migrar dados existentes (opcional)

Se quiser importar os contadores já existentes do SQLite para o Redis, defina uma variável de ambiente `MIGRATE_TOKEN` com um token secreto e faça um POST ao endpoint protegido:

```bash
curl -X POST -H "Authorization: Bearer $MIGRATE_TOKEN" https://seu-servico.onrender.com/admin/migrate_counts
```

> Observação: adicione `redis` ao `requirements.txt` (já incluído neste repositório).
