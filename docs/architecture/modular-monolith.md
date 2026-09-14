# Modular monolith: target and migration plan

## Rules

`apps.platform` is stable infrastructure. It contains application discovery,
tenant context and domain events. It must not import `applications.*`.
`domain` contains shared business contracts and is allowed to use a temporary
storage adapter while legacy tables are moved. `applications` may depend on
Platform and Domain. They communicate through domain services or events, never
through scattered model imports.

The package is named `apps.platform`, rather than a top-level `platform`, to
avoid shadowing Python's standard library module.

## Current dependency map

| Producer | Direct dependency before this change | Transition boundary |
| --- | --- | --- |
| `accounts` | `atendimento.Prestador` and `RascunhoEditorDocumento` | `domain.profissionais` port; lazy compatibility lookup for draft cleanup |
| project URLConf | PEP, classification, panel and totem attendance views | application-owned URL adapters discovered by registry |
| `atendimento` | no cross-application contract for a new attendance | `atendimento.criado` platform domain event |
| `core` | navigation/data configuration and attendance-specific imports in management/tests | application registry is outside Core; remaining legacy configuration is a later extraction |

The largest hotspot remains `apps/atendimento`: `views.py` is about 550 KB and
owns appointment/reception, shared clinical models, PEP, classification, panel,
totem and document-editor controllers. Its migrations and model app label stay
in place for this phase, preserving all existing database tables and foreign
keys.

## Application registry

Every package under `applications/` has an `AppConfig` with an
`ApplicationManifest`. The manifest declares code, name, version,
dependencies, URL contribution, permissions, menus, events, reports and
settings. `apps.platform.registry` discovers them from Django's app registry.
`sync_applications` is the explicit idempotent catalog synchronization command;
the same synchronization hook runs after migrations.

Initially manifests describe existing navigation access keys but do not rewrite
legacy `Module` or `ScreenDefinition` rows. This preserves `PapelTela`, URLs
and navigation without a bulk permission migration. A new application can own
its Module/ScreenDefinition rows by setting `navigation_module` in its manifest.

## Incremental slices

1. Extract `domain.pessoas`, `domain.pacientes`, `domain.profissionais`,
   `domain.organizacao` and `domain.atendimentos` ports. Keep their models'
   `db_table`, primary keys and Django app labels in compatibility adapters.
2. Move attendance controllers into application packages by vertical slice:
   scheduling/reception, PEP, classification, panel/totem and editor. Keep
   legacy URL names as thin adapters until consumers migrate.
3. Move document/audit/configuration implementations to Platform contracts;
   replace `apps.core` imports in feature apps with those contracts.
4. Give each manifest its own navigation module and migrate `PapelTela` only
   in an audited data migration that maps old access keys to unchanged keys.
5. Add an outbox implementation behind `apps.platform.events` before extracting
   any service. The in-process signal is intentionally the current monolith
   implementation, not a microservice transport.

## Tenant rule

Use `apps.platform.tenancy.current_tenant(request)` for new code. It is the
single boundary around the existing `request.session['cd_empresa']` contract.
Existing filters retain their database behavior; each slice should replace
inline session reads with this service while it is touched.
