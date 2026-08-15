---
name: lang-csharp
description: C#/.NET idioms (defers to Vault/Context/Conventions.md)
globs: **/*.cs
always_apply: false
---
# C# / .NET

Follow `Vault/Context/Conventions.md` first. Language idioms:

- Enable nullable reference types and treat warnings seriously.
- `PascalCase` for types/methods/properties, `camelCase` for locals/params.
- Prefer `async`/`await` with `Task`; suffix async methods with `Async`.
- Use dependency injection; program to interfaces, not concretions.
- Throw specific exceptions; use `Result`/typed errors for expected failures.
- Use the framework from `project.yml` (e.g. ASP.NET Core, minimal APIs).
- Tests with the configured runner (`xunit`/`nunit`); `dotnet test`.
- Format with `dotnet format`.
