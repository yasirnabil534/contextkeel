---
name: db-migration
description: Create and apply database schema migrations using the project's ORM/migration tool, then update the context store. Use when changing the data model, adding tables/columns, or asked for a migration.
model_invocable: true
---
# Database Migration

## Steps
1. Resolve `database` and `orm` from `project.yml` (or detect).
2. Make the model/schema change in code first where the ORM is code-first.
3. Generate the migration with the right tool:
   - Prisma → `prisma migrate dev --name <change>`
   - Drizzle → `drizzle-kit generate`
   - SQLAlchemy + Alembic → `alembic revision --autogenerate -m "<change>"`
   - EF Core → `dotnet ef migrations add <Change>`
   - sqlx → `sqlx migrate add <change>`
   - Gorm/raw → write the SQL migration file
4. **Review the generated SQL** for correctness and destructive operations
   (drops, type changes). Flag anything that loses data.
5. Apply to the dev database and verify.
6. Update `Vault/Context/API Contracts.md` if the schema change affects it,
   and run `update-context` to regenerate the graph.

## Rules
- Never auto-apply a destructive migration without confirming with the user.
- Migrations are append-only; fix mistakes with a new migration.
