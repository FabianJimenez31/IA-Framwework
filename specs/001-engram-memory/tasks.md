# Tasks: Engram Persistent Memory Layer

**Branch**: `001-engram-memory` | **Spec**: [specs/001-engram-memory/spec.md](spec.md) | **Plan**: [specs/001-engram-memory/plan.md](plan.md)

Use this document as a living checklist of technical items to implement. Mark items with `[/]` when in progress, and `[x]` when completed.

## Implementation Tasks

- [ ] **Phase 0: Corregir deuda preexistente** *(bloquea las fases siguientes)*
  - [ ] DP-004 — Reemplazar `fi` por `done` en `check-prerequisites.sh:93`; validar con `bash -n` y confirmar que `spec-compliance.yml` pasa por primera vez
  - [ ] DP-002 — Alimentar `check-file-size.sh` con stdin JSON en `emergency_hotfix.sh:108`, replicando el patrón de `ci-quality-gate.yml:36`
  - [ ] DP-001 — Implementar `HARNESS_EMERGENCY=1` como archivo de estado leído por los hooks, en lugar del `export` a subshell de `emergency_hotfix.sh:129`
  - [ ] Unificar la derivación de slug: reemplazar el regex de `pre-commit.sh:26` por `spec_kit_effective_branch_name()` de `common.sh:53`, o alinear ambos regex
  - [ ] Verificar que `make hotfix` completa el ciclo `crear → validar → aplicar` sin colgarse

- [ ] **Phase 1: Cliente y fundamentos**
  - [ ] Crear `scripts/memory/engram_client.sh` con `mem_health`, `mem_ensure_daemon`, `mem_write`, `mem_has_topic`
  - [ ] Crear `scripts/memory/session_state.sh` con persistencia en `temp/.engram_session`
  - [ ] Implementar auto-arranque del daemon: un intento, timeout de 3s contra `GET /health` (FR-013)
  - [ ] Smoke test: escribir y recuperar una observación de prueba contra un daemon local

- [ ] **Phase 2: Captura por etapa**
  - [ ] Crear `scripts/memory/capture_stage.sh` con un caso por clase de memoria
  - [ ] Componer el contenido estructurado `**What** / **Why** / **Where** / **Learned**` desde git y `specs/<slug>/`
  - [ ] Cablear `post-edit.sh`: `plan.md` → semántica, `tasks.md` → procedimental
  - [ ] Crear `.claude/hooks/git/post-commit` → estado de decisión
  - [ ] Modificar `pre-push.sh`: redirigir el log de tests de `/tmp` a `temp/logs/` y escribir el estado de resultados
  - [ ] Modificar `create-new-feature.sh`: consultar memoria por slug antes de generar plantillas, y abrir sesión después de crear la rama

- [ ] **Phase 3: Gate obligatorio**
  - [ ] Crear `scripts/memory/memory_gate.sh` con la tabla de cuotas por prefijo de rama (FR-005)
  - [ ] Implementar validación acumulativa por etapa (FR-006)
  - [ ] Replicar el formato de error del Spec-Kit Gate (`pre-commit.sh:47-52`)
  - [ ] Integrar el gate en `pre-push.sh` — **sin tocar `pre-commit.sh`**
  - [ ] Implementar el respeto a `HARNESS_EMERGENCY=1` con registro de la omisión (FR-012)
  - [ ] Probar las tres cuotas en ramas `feature/`, `fix/` y `chore/`

- [ ] **Phase 4: Superficies de agente**
  - [ ] Crear `.claude/settings.json` con `SessionStart`, `PreToolUse` y `PostToolUse` — cierra DP-003
  - [ ] Verificar que `check-file-size.sh` por fin se ejecuta en vivo dentro de Claude Code
  - [ ] Añadir la sección "Memory Protocol" a `AGENTS.md` (superficie nativa de Codex)
  - [ ] Espejar la sección en `CLAUDE.md` y en `.specify/templates/constitution-template.md`
  - [ ] Crear `.kiro/steering/ia-framework.md` con la constitución y el protocolo
  - [ ] Instruir en el steering que Kiro use `specs/<slug>/` y no genere su propio árbol — el nombre `tasks.md` colisiona
  - [ ] Crear `.kiro/settings/mcp.json` con el registro del MCP de Engram a nivel de workspace

- [ ] **Phase 5: Instalación y CLI**
  - [ ] `install.sh`: detectar e instalar Engram; abortar si no lo consigue (FR-008)
  - [ ] `install.sh`: generar `.engram/config.json` desde el basename del repo (FR-009)
  - [ ] `install.sh`: selector interactivo de agentes y ejecución de `engram setup <agente>` (FR-010)
  - [ ] `install.sh`: arrancar el daemon y verificar `GET /health`
  - [ ] `install.sh`: añadir `.engram/`, `temp/logs/` y `temp/.engram_session` a los patrones de `.gitignore` (líneas 76-83)
  - [ ] `Makefile`: añadir `mem-context`, `mem-check`, `mem-doctor`, `mem-ingest` a los targets, a `help` y a `.PHONY`

- [ ] **Phase 6: Safeguards & Quality**
  - [ ] Confirmar que ningún archivo nuevo supera 1000 líneas (NFR-003)
  - [ ] Confirmar que todos los wrappers son bash — un `.py` con nombre genérico en `scripts/` haría que `validate_structure.py` se auto-bloqueara (NFR-002)
  - [ ] Medir la latencia añadida al camino de commit; debe quedar bajo 500ms (NFR-001)
  - [ ] `shellcheck` sobre todos los scripts nuevos
  - [ ] Confirmar que `make dev-check` pasa limpio

- [ ] **Phase 7: Verification & Tests**
  - [ ] Prueba de instalación limpia en un repo vacío sin Engram presente
  - [ ] Prueba de flujo completo en `feature/002-smoke` con verificación de las 5 escrituras
  - [ ] Prueba de bloqueo: borrar un estado exigido y confirmar que el push aborta
  - [ ] Prueba de daemon caído: auto-arranque exitoso, y aborto limpio cuando el puerto está bloqueado
  - [ ] Prueba de `HARNESS_EMERGENCY=1`
  - [ ] Prueba de los tres agentes contra sus rutas nativas
  - [ ] Actualizar `README.md` con la sección de memoria persistente

- [ ] **Phase 8: CI**
  - [ ] `ci-quality-gate.yml`: emitir el estado de resultados como artifact JSON
  - [ ] Implementar `make mem-ingest` para consumir el artifact localmente
  - [ ] Resolver OQ-002: decidir si la ingestión es automática en `post-merge` o manual

## Progress Tracking

Keep this document up to date to communicate current completion status to the user and agents.

**Estado actual**: Especificación completa. Ninguna fase iniciada.

**Preguntas abiertas que bloquean fases**: OQ-002 bloquea la Fase 8. OQ-001 y OQ-003 no bloquean nada — se resuelven en una iteración posterior.
