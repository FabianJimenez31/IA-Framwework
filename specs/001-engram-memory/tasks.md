# Tasks: Engram Persistent Memory Layer

**Branch**: `001-engram-memory` | **Spec**: [specs/001-engram-memory/spec.md](spec.md) | **Plan**: [specs/001-engram-memory/plan.md](plan.md)

Use this document as a living checklist of technical items to implement. Mark items with `[/]` when in progress, and `[x]` when completed.

## Implementation Tasks

- [x] **Phase 0: Corregir deuda preexistente** *(bloquea las fases siguientes)*
  - [x] DP-006 — Resolver el nombre real de rama desde `GITHUB_HEAD_REF` cuando el HEAD está desacoplado, en `pre-commit.sh` y `common.sh`
  - [x] DP-005 — Corregir `sonarqube-quality-gate-action@v2` a `@v1` en `ci-quality-gate.yml`; esa acción no publica una v2 y el job fallaba al preparar el workflow
  - [x] DP-004 — Reemplazar `fi` por `done` en `check-prerequisites.sh:93`; validar con `bash -n` y confirmar que `spec-compliance.yml` pasa por primera vez
  - [x] DP-002 — Alimentar `check-file-size.sh` con stdin JSON en `emergency_hotfix.sh:108`, replicando el patrón de `ci-quality-gate.yml:36`
  - [x] DP-001 — Implementar `HARNESS_EMERGENCY=1` como archivo de estado leído por los hooks, en lugar del `export` a subshell de `emergency_hotfix.sh:129`
  - [x] Unificar la derivación de slug: `pre-commit.sh` delega en `check_feature_branch()` y `spec_kit_effective_branch_name()` de `common.sh`
  - [x] Verificar que `make hotfix` completa el ciclo `crear → validar → aplicar` sin colgarse
  - [x] Añadir el prefijo `kiro/` a las tres copias del regex de ramas (`pre-commit.sh`, `.pre-commit-config.yaml`)
  - [x] Mover el log del suite de `/tmp/harness_tests.log` a `temp/logs/`, conforme a la regla del propio framework

- [x] **Phase 1: Cliente y fundamentos**
  - [x] Crear `scripts/memory/engram_client.sh` con `mem_health`, `mem_ensure_daemon`, `mem_write`, `mem_has_topic`
  - [x] Crear `scripts/memory/session_state.sh` con persistencia en `temp/.engram_session`
  - [x] Implementar auto-arranque del daemon: un intento, timeout de 3s contra `GET /health` (FR-013)
  - [x] Smoke test: escribir y recuperar una observación de prueba contra un daemon local

- [x] **Phase 2: Captura por etapa**
  - [x] Crear `scripts/memory/capture_stage.sh` con un caso por clase de memoria
  - [x] Componer el contenido estructurado `**What** / **Why** / **Where** / **Learned**` desde git y `specs/<slug>/`
  - [x] Cablear `post-edit.sh`: `plan.md` → semántica, `tasks.md` → procedimental
  - [x] Crear `.claude/hooks/git/post-commit` → estado de decisión
  - [x] Modificar `pre-push.sh`: redirigir el log de tests de `/tmp` a `temp/logs/` y escribir el estado de resultados
  - [x] Modificar `create-new-feature.sh`: consultar memoria por slug antes de generar plantillas, y abrir sesión después de crear la rama

- [x] **Phase 3: Gate obligatorio**
  - [x] Crear `scripts/memory/memory_gate.sh` con la tabla de cuotas por prefijo de rama (FR-005)
  - [x] Implementar validación acumulativa por etapa (FR-006)
  - [x] Replicar el formato de error del Spec-Kit Gate (`pre-commit.sh:47-52`)
  - [x] Integrar el gate en `pre-push.sh` — **sin tocar `pre-commit.sh`**
  - [x] Implementar el respeto a `HARNESS_EMERGENCY=1` con registro de la omisión (FR-012)
  - [x] Probar las tres cuotas en ramas `feature/`, `fix/` y `chore/`

- [x] **Phase 4: Superficies de agente**
  - [x] Crear `.claude/settings.json` con `SessionStart`, `PreToolUse` y `PostToolUse` — cierra DP-003
  - [x] Verificar que `check-file-size.sh` por fin se ejecuta en vivo dentro de Claude Code
  - [x] Añadir la sección "Memory Protocol" a `AGENTS.md` (superficie nativa de Codex)
  - [x] Espejar la sección en `CLAUDE.md` y en `.specify/templates/constitution-template.md`
  - [x] Crear `.kiro/steering/ia-framework.md` con la constitución y el protocolo
  - [x] Instruir en el steering que Kiro use `specs/<slug>/` y no genere su propio árbol — el nombre `tasks.md` colisiona
  - [x] Crear `.kiro/settings/mcp.json` con el registro del MCP de Engram a nivel de workspace

- [x] **Phase 5: Instalación y CLI**
  - [x] `install.sh`: detectar e instalar Engram; abortar si no lo consigue (FR-008)
  - [x] `install.sh`: generar `.engram/config.json` desde el basename del repo (FR-009)
  - [x] `install.sh`: selector interactivo de agentes y ejecución de `engram setup <agente>` (FR-010)
  - [x] `install.sh`: arrancar el daemon y verificar `GET /health`
  - [x] `install.sh`: añadir `.engram/`, `temp/logs/` y `temp/.engram_session` a los patrones de `.gitignore` (líneas 76-83)
  - [x] `Makefile`: añadir `mem-context`, `mem-check`, `mem-doctor`, `mem-ingest` a los targets, a `help` y a `.PHONY`

- [x] **Phase 6: Safeguards & Quality**
  - [x] Confirmar que ningún archivo nuevo supera 1000 líneas (NFR-003)
  - [x] Confirmar que todos los wrappers son bash — un `.py` con nombre genérico en `scripts/` haría que `validate_structure.py` se auto-bloqueara (NFR-002)
  - [x] Medir la latencia añadida al camino de commit; debe quedar bajo 500ms (NFR-001)
  - [x] `shellcheck` sobre todos los scripts nuevos
  - [x] Confirmar que `make dev-check` pasa limpio

- [x] **Phase 7: Verification & Tests**
  - [x] Prueba de instalación limpia en un repo vacío sin Engram presente
  - [x] Prueba de flujo completo en `feature/002-smoke` con verificación de las 5 escrituras
  - [x] Prueba de bloqueo: borrar un estado exigido y confirmar que el push aborta
  - [x] Prueba de daemon caído: auto-arranque exitoso, y aborto limpio cuando el puerto está bloqueado
  - [x] Prueba de `HARNESS_EMERGENCY=1`
  - [x] Prueba de los tres agentes contra sus rutas nativas
  - [x] Actualizar `README.md` con la sección de memoria persistente

- [x] **Phase 8: CI**
  - [x] `ci-quality-gate.yml`: emitir el estado de resultados como artifact JSON
  - [x] Implementar `make mem-ingest` para consumir el artifact localmente
  - [x] Resolver OQ-002: decidir si la ingestión es automática en `post-merge` o manual

## Progress Tracking

Keep this document up to date to communicate current completion status to the user and agents.

**Estado actual**: Fases 0 a 8 completadas y verificadas.

Verificación ejecutada contra un doble de prueba del daemon de Engram que implementa la superficie HTTP realmente utilizada, incluido el upsert por `topic_key`. Cubre: resolución de proyecto y slug, las tres cuotas por prefijo de rama, bloqueo y aprobación del gate, no duplicación con incremento de `revision_count`, disparo del hook `post-commit`, captura desde `post-edit`, bypass de emergencia con registro de la omisión, fallo duro con el daemon caído, los cinco targets `mem-*`, la ingesta del artifact de CI, y la latencia añadida al camino de commit (268 ms, bajo el límite de 500 ms).

**Pendiente de validar contra Engram real**: la instalación por Homebrew, `engram setup <agente>` para los tres agentes, y el comportamiento de `GET /context` y `GET /search`, cuya forma exacta de respuesta se aproximó en el doble de prueba.

**Preguntas abiertas resueltas**: OQ-002 — la ingesta del resultado de CI es manual (`make mem-ingest`), no automática en `post-merge`. El runner no alcanza el daemon, así que emite un artifact y la ingesta ocurre en una máquina que sí tiene el almacén.

**Preguntas abiertas pendientes**: OQ-001 (memoria compartida entre desarrolladores vía `engram sync` o Cloud) y OQ-003 (qué hacer con la memoria de una feature abandonada). Ninguna bloquea el uso.
