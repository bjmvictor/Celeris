# Modular monolith: target and migration plan

## Rules

`apps.platform` is stable infrastructure. It contains application discovery,
tenant context and domain events. It must not import `apps.applications.*`.
`apps.domain` contains shared business contracts and is allowed to use a temporary
storage adapter while legacy tables are moved. `apps.applications` may depend on
Platform and Domain. They communicate through domain services or events, never
through scattered model imports.

The package is named `apps.platform`, rather than a top-level `platform`, to
avoid shadowing Python's standard library module.

## Current dependency map

| Producer | Direct dependency before this change | Transition boundary |
| --- | --- | --- |
| `accounts` | `atendimento.Prestador` and `RascunhoEditorDocumento` | `apps.domain.profissionais` port; lazy compatibility lookup for draft cleanup |
| project URLConf | PEP, classification, panel and totem attendance views | application-owned URL adapters discovered by registry |
| `core.form_registry` | attendance form names, classes and field labels | neutral Platform registry; Atendimento registers its own form definitions on startup |
| `atendimento` | no cross-application contract for a new attendance | `atendimento.criado` platform domain event |
| `core` | navigation/data configuration and attendance-specific imports in management/tests | application registry is outside Core; remaining legacy configuration is a later extraction |

The largest hotspot remains `apps/atendimento`: `views.py` is about 550 KB and
owns appointment/reception, shared clinical models, PEP, classification, panel,
totem and document-editor controllers. Its migrations and model app label stay
in place for this phase, preserving all existing database tables and foreign
keys.

## Application registry

Every package under `apps/applications/` has an `AppConfig` with an
`ApplicationManifest`. The manifest declares code, name, version,
dependencies, URL contribution, permissions, menus, events, reports and
settings. `apps.platform.registry` discovers them from Django's app registry.
`sync_applications` is the explicit idempotent catalog synchronization command;
the same synchronization hook runs after migrations.

Initially manifests describe existing navigation access keys but do not rewrite
legacy `Module` or `ScreenDefinition` rows. This preserves `PapelTela`, URLs
and navigation without a bulk permission migration. A new application can own
its Module/ScreenDefinition rows by setting `navigation_module` in its manifest.

## Current boundaries and remaining work

The Core keeps the generic persistence model for company-level form-field
configuration and its configuration screen.  It no longer lists any clinical
form, imports a clinical form class, or owns clinical labels.  Atendimento
registers those definitions through `apps.platform.form_registry` in its
`AppConfig.ready()` hook; another application can now contribute a configurable
form without editing Core.

The public `populate` command is now a neutral orchestrator.  The Platform
discovers registered demo-seed providers, resolves their declared dependencies
and supplies a small context containing only command inputs, an output writer
and explicitly registered scalar identifiers. It cannot transport models,
querysets or service objects between providers. The existing complete scenario
is registered by Atendimento as the
single `atendimento.demo_legacy` compatibility provider, so its public command
name, arguments, transaction and fixture data remain unchanged.

That provider still creates the established cross-module demo scenario
(accounts, attendance and research).  Splitting it into Accounts, Atendimento
and Pesquisas providers is deliberately deferred: their current creation order
links users to legacy `atendimento.Prestador` rows, and a partial split could
change an idempotent fixture.  Existing Django models and migrations keep their
current app labels and physical tables. They are compatibility boundaries, not
evidence that a domain model has been moved.

Recommended next slices are: extract the demo-data providers from `populate`,
then move the remaining PEP controller logic behind its now application-owned
entry points before moving classification, panel and totem controllers. No
model relocation should occur until a data-migration plan
preserves every existing `db_table`, foreign key and permission mapping.

## Documents boundary audit

`DocumentoClinico`, `ModeloDocumento`, draft cleanup, rendering and PDF output
remain physically owned by legacy Atendimento. Tickets now consumes the public
`apps.atendimento.documents` API for template selection, rendering and PDF
responses; Accounts consumes `apps.atendimento.public` for draft cleanup.
Editor now exposes the public rendering service and PEP exposes the public
route entry points; both delegate to legacy Atendimento controllers while the
models, signing infrastructure and templates remain in place. Moving those
implementations is deferred because it would change model ownership or
existing clinical workflows.

## Functional ownership extraction

The Totem ticket-generation view was the first controller moved out of
`apps.atendimento.views`. `apps.applications.totem.views.gerar_senha_totem`
now owns the request handling, ticket-number allocation transaction, rule and
class selection, and history query. The legacy Atendimento URL retains its
name and decorators, but delegates to that implementation. The template and
the legacy shared models (`SenhaAtendimento`, classes and rules) remain
unchanged.

PEP, Editor, Classification and Panel still have controller implementations in
Atendimento or direct imports from it. They remain deferred because their
current views share large private helper sets and clinical action routes; a
partial copy would increase duplication rather than invert a dependency. The
next recommended slice is to extract PEP list selectors and then its main
controller, replacing the current PEP-to-Atendimento view import.

PEP now owns the read-only selectors for patient search, tenant-scoped patient
and encounter resolution, and the basic record context (selected encounter and
vital-sign history). The legacy PEP controller consumes those selectors, so
these queries no longer have competing implementations. Documents, menu
composition, prescriptions and clinical write actions remain in Atendimento;
they are intentionally outside this read-only extraction.

## Incremental slices

1. Extract `apps.domain.pessoas`, `apps.domain.pacientes`, `apps.domain.profissionais`,
   `apps.domain.organizacao` and `apps.domain.atendimentos` ports. Keep their models'
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
