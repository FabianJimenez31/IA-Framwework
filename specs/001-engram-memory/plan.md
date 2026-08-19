# Implementation Plan: Engram Persistent Memory Layer

**Branch**: `001-engram-memory` | **Date**: 2026-08-18 | **Spec**: [specs/001-engram-memory/spec.md](spec.md)

## Summary

Se integra Engram como capa de memoria obligatoria del harness. Los hooks de git y de agente escriben las 7 clases de memoria vía la API HTTP local de Engram; los gates existentes se extienden para bloquear cuando falta un estado exigido. Se añaden las superficies de configuración de Claude Code, Codex y Kiro, y se corrige la deuda preexistente que impide implementar el bypass de emergencia.

El principio rector es que **la memoria es subproducto de etapas que el framework ya ejecuta**. Cinco de los siete estados se derivan de artefactos que ya existen: el slug, `plan.md`, `tasks.md`, el mensaje de commit y el resultado del suite de tests. No se pide trabajo nuevo al desarrollador; se persiste lo que hoy se evapora.

## Technical Context

- **Languages/Versions**: Bash 3.2+ (macOS ships 3.2), jq 1.6+, curl
- **Primary Dependencies**: Engram ≥0.1.0 (binario Go), SQLite/FTS5 embebido
- **Storage/Databases**: `~/.engram/engram.db` — fuera del repositorio, por máquina
- **Testing Frameworks**: pytest (suite existente) + bats-style smoke tests en bash
- **Target Platforms**: macOS, Linux

### Contrato con Engram

| Operación | Endpoint | Cuerpo |
|---|---|---|
| Abrir sesión | `POST /sessions` | `{id, project, directory}` |
| Cerrar sesión | `POST /sessions/{id}/end` | `{summary}` |
| Escribir estado | `POST /observations` | `{session_id, type, title, content, topic_key, scope}` |
| Verificar estado | `GET /search` | `?q=&type=&project=&scope=&limit=` |
| Inyectar contexto | `GET /context` | `?project=&scope=` |
| Salud del daemon | `GET /health` | — |

Puerto por defecto `7437`, ligado a `127.0.0.1`. `topic_key` hace upsert sobre `project + scope + topic_key` incrementando `revision_count`, de modo que cada etapa que avanza **actualiza** el estado sin duplicarlo y el timeline conserva la traza.

## Mapa de estados

| Clase | `topic_key` | `type` | Escrito por | Etapa |
|---|---|---|---|---|
| Contextual | *(sesión Engram)* | — | `create-new-feature.sh` | `make spec-new` |
| Episódica | *(derivada)* | — | timeline de Engram | automática |
| Semántica | `spec/<slug>/semantic` | `architecture` | `post-edit.sh` | cierre de `plan.md` |
| Procedimental | `spec/<slug>/procedural` | `pattern` | `post-edit.sh` | cierre de `tasks.md` |
| Decisiones | `spec/<slug>/decision` | `decision` | `post-commit` | cada commit |
| Preferencias | `user/preferences` | `config` | `post-edit.sh` | corrección del usuario |
| Resultados | `spec/<slug>/outcome` | `learning` | `pre-push.sh` | push, CI, hotfix |

Las de tarea son cinco escrituras reales (`contextual` va a `/sessions`, las otras cuatro a `/observations`). La episódica es derivada. Las preferencias son de alcance `personal` y cruzan proyectos, por lo que se verifican como presentes, no como escritas por tarea.

## Cuotas por prefijo de rama

| Prefijo | Clases exigidas |
|---|---|
| `feature/` | Las 7 |
| `fix/`, `hotfix/` | 3 — decisión, resultado, semántica registrada como `bugfix` |
| `chore/` | 1 — decisión |
| `test/`, `claude/`, `codex/` | Solo sesión; sin memoria de tarea |

## Gates acumulativos por etapa

```text
make spec-new     →  contextual
primer commit     →  + semántica, procedimental, decisión
git push          →  + resultado
merge (CI)        →  cuota completa del prefijo
```

## Proposed Changes

### Capa de memoria (nueva)

#### [NEW] scripts/memory/engram_client.sh
Cliente HTTP de bajo nivel. Expone `mem_health`, `mem_ensure_daemon`, `mem_session_open`, `mem_session_close`, `mem_write`, `mem_has_topic`. Toda la comunicación con `curl` + `jq`. Único punto del sistema que conoce el puerto y el formato de payload.

#### [NEW] scripts/memory/memory_gate.sh
Evalúa la cuota exigida según prefijo de rama y etapa, consulta `GET /search` por cada `topic_key` esperado, y devuelve la lista de faltantes. Replica el formato de error de `pre-commit.sh:47-52`. Respeta `HARNESS_EMERGENCY=1`.

#### [NEW] scripts/memory/capture_stage.sh
Compone el contenido estructurado (`**What** / **Why** / **Where** / **Learned**`) a partir de git y de los artefactos de `specs/<slug>/`, y delega la escritura en `engram_client.sh`. Un caso por clase de memoria.

#### [NEW] scripts/memory/session_state.sh
Resuelve el `session_id` vigente. Persiste en `temp/.engram_session` — ya cubierto por el `.gitignore` que genera `install.sh`.

### Enganches en hooks existentes

#### [MODIFY] .claude/hooks/post-edit.sh
Hoy es un stub de 3 líneas (`exit 0`). Pasa a detectar qué archivo se editó y disparar la captura correspondiente: `plan.md` → semántica, `tasks.md` → procedimental. Riesgo de regresión nulo.

#### [NEW] .claude/hooks/git/post-commit
Nuevo hook en el directorio que `install.sh:52` ya enlaza mediante `core.hooksPath`. Escribe el estado de decisión con el mensaje de commit, el resumen de `plan.md` y los archivos tocados. Aditivo: git simplemente empieza a invocarlo.

#### [MODIFY] .claude/hooks/pre-push.sh
Redirige el resultado del suite de tests de `/tmp/harness_tests.log` (línea 50, fuera de `temp/` y contra la propia regla del framework) hacia `temp/logs/` y hacia el estado de resultados. Añade la verificación del gate antes de permitir el push.

#### [MODIFY] .specify/scripts/bash/create-new-feature.sh
Antes de generar plantillas (línea 37), consulta `GET /search` por el slug y muestra decisiones previas relacionadas. Después de crear la rama, abre la sesión de Engram. Ambos pasos son informativos salvo el de apertura de sesión.

#### [MODIFY] scripts/deployment/emergency_hotfix.sh
Corrige **DP-002**: alimenta `check-file-size.sh` con stdin JSON en la línea 108, igual que hace `ci-quality-gate.yml:36`. Corrige **DP-001**: escribe `HARNESS_EMERGENCY=1` a un archivo de estado que los hooks leen, en lugar de exportarlo a un subshell que muere. Registra el incidente como estado `bugfix`.

### Superficies de agente

#### [NEW] .claude/settings.json
Corrige **DP-003**. Cablea `SessionStart` (abre sesión + inyecta `GET /context`), `PreToolUse` → `check-file-size.sh` (que hoy está huérfano) y `PostToolUse` → `post-edit.sh`.

#### [NEW] .kiro/steering/ia-framework.md
Steering de workspace, versionado. Kiro carga `.kiro/steering/*.md` del raíz del proyecto. Contiene la constitución y el Protocolo de Memoria. **Debe instruir explícitamente a Kiro a usar `specs/<slug>/` del framework y no generar su propio árbol de specs** — Kiro produce `requirements.md`, `design.md` y `tasks.md`, y ese último nombre colisiona exactamente con el del framework.

#### [NEW] .kiro/settings/mcp.json
Registro del servidor MCP de Engram a nivel de workspace, para lectura desde Kiro.

#### [MODIFY] AGENTS.md
Añade la sección "Memory Protocol". Es la superficie nativa de Codex a nivel de proyecto; los servidores MCP de Codex solo se configuran globalmente en `~/.codex/config.toml`, por lo que esa parte la resuelve `install.sh` ejecutando `engram setup codex`.

#### [MODIFY] CLAUDE.md y .specify/templates/constitution-template.md
Espejo de la sección de AGENTS.md, para mantener la equivalencia que el framework ya sostiene.

### Instalación

#### [MODIFY] install.sh
Añade tras el paso 4 (enlace de hooks):
1. Detecta `engram`; si falta, instala por Homebrew o release de GitHub. Aborta si no lo consigue (FR-008).
2. Genera `.engram/config.json` con `project_name` desde el basename del repo.
3. Pregunta qué agentes configurar (Claude Code / Codex / Kiro) y ejecuta `engram setup <agente>` para los elegidos.
4. Arranca `engram serve` y verifica `GET /health`.
5. Añade `.engram/`, `temp/logs/` y `temp/.engram_session` a la lista de patrones de `.gitignore` (líneas 76-83).

#### [MODIFY] Makefile
Nuevos targets siguiendo la convención existente: `mem-context`, `mem-check`, `mem-doctor`, `mem-ingest`. Se registran en `help` y en `.PHONY`.

### CI

#### [MODIFY] .github/workflows/ci-quality-gate.yml
El runner no tiene Engram. Emite el estado de resultados como artifact JSON para ingestión local posterior. Sigue el patrón de degradación que el workflow ya usa para las credenciales de Sonar (líneas 54-62): advierte, no falla.

---

## Verification & Rollback Plan

### Automated Verification

- **Testing Command**: `pytest tests/`
- **Quality Verification**: `make dev-check`
- **Memory Verification**: `make mem-check` — evalúa el gate contra la rama actual
- **Diagnóstico**: `make mem-doctor` — envuelve `GET /doctor` de Engram

### Manual Verification

1. Clonar el repo en un directorio limpio y ejecutar `./install.sh` sin Engram instalado; confirmar que lo instala y aborta con mensaje claro si no puede.
2. Correr el flujo completo en `feature/002-smoke` y verificar las 5 escrituras con `GET /search?q=002-smoke`.
3. Borrar el estado de resultados e intentar `git push`; confirmar que aborta identificando el faltante.
4. Repetir en `fix/` y `chore/` y confirmar las cuotas de 3 y 1.
5. Detener el daemon y confirmar que el hook lo auto-arranca; detenerlo y bloquear el puerto, confirmar que aborta.
6. Verificar `HARNESS_EMERGENCY=1` y confirmar que omite el gate y registra la omisión.
7. Configurar los tres agentes y confirmar que cada uno recibe el protocolo por su ruta nativa.

### Rollback Plan

Toda la superficie nueva está aislada en `scripts/memory/`, `.claude/hooks/git/post-commit`, `.claude/settings.json` y `.kiro/`. Revertir es:

```bash
rm -rf scripts/memory .kiro .claude/settings.json .claude/hooks/git/post-commit
git checkout main -- .claude/hooks/post-edit.sh .claude/hooks/pre-push.sh \
  .specify/scripts/bash/create-new-feature.sh scripts/deployment/emergency_hotfix.sh \
  install.sh Makefile AGENTS.md CLAUDE.md
```

`pre-commit.sh` no se modifica en ninguna fase. Es el gate más crítico del framework y queda intacto, de modo que un fallo en la capa de memoria nunca puede impedir un commit por una vía distinta a la del gate de memoria, que sí es desactivable.
