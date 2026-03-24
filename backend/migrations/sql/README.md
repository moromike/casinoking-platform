# SQL Migrations

SQL-first migration scaffold aligned with Documento 12 v3 and Documento 13 v3.

Current intent:
- keep migrations explicit and reviewable
- preserve a conservative path for financial tables
- avoid inventing schema details before the target model is implemented

Planned categories:
- base platform tables
- financial core tables
- game/session tables
- indexes, constraints, and reconciliation helpers

Status:
- bootstrap stage only
- no definitive schema DDL implemented yet
