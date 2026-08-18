# Feature Specification: Engram Persistent Memory Layer

**Feature Branch**: `001-engram-memory`

**Created**: 2026-08-18

**Status**: Draft

**Input**: User description: "Integrar Engram al IA-Framework como capa de memoria obligatoria. Persistir siempre las 7 clases de memoria en cada tarea y dejar registro en cada etapa donde avanza el flujo. Soportar Claude Code, Codex y Kiro."

## Context

IA-Framework gobierna *cómo* se desarrolla (specs, quality gates, CI, rollback) pero no conserva *qué se aprendió*. Cada sesión de agente arranca en cero: se reinvestigan las mismas decisiones, se reproponen arquitecturas ya descartadas, y el conocimiento del proyecto vive solo en la cabeza del desarrollador y en mensajes de commit.

Engram (Go + SQLite/FTS5) resuelve la persistencia. Esta feature lo integra **como backend de memoria del harness**, no como herramienta opcional del agente.

### Decisión de arquitectura central

Engram expone dos canales de escritura:

| Canal | Mecanismo | Quién escribe | Determinista |
|---|---|---|---|
| A — MCP | stdio, `mem_save` | El agente, si se acuerda | **No** |
| B — HTTP | `POST 127.0.0.1:7437/observations` | Los hooks del harness | **Sí** |

Esta feature usa **el canal B como fuente de verdad**. Los hooks de git y de agente escriben memoria con `curl`; el agente la *lee* pero no es responsable de escribirla. El canal A queda habilitado para lectura y para enriquecimiento oportunista, nunca como garantía.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - La memoria se escribe sola (Priority: P1)

Un desarrollador ejecuta `make spec-new`, llena `plan.md`, programa, commitea y hace push. Sin ejecutar ningún comando de memoria, al terminar existen en Engram los registros de las 7 clases asociados a `spec/001-mi-feature/*`.

**Why this priority**: Es el corazón de la feature. Si la memoria depende de disciplina humana o de que el agente se acuerde, el sistema no funciona — es exactamente el modo de falla que el framework ya evita en calidad de código mediante hooks bloqueantes.

**Independent Test**: Correr el flujo completo en un repo limpio y consultar `GET /search?q=<slug>`; deben aparecer las 5 observaciones de tarea más la sesión, sin intervención manual.

**Acceptance Scenarios**:

1. **Given** un repo con el framework instalado y `engram serve` activo, **When** el desarrollador ejecuta `make spec-new` con slug `001-login`, **Then** se abre una sesión de Engram vinculada al slug y se escribe el estado contextual.
2. **Given** una rama `feature/001-login` con `plan.md` completo, **When** se ejecuta el primer commit, **Then** existen los estados semántico, procedimental y de decisión con `topic_key` derivado del slug.
3. **Given** una rama `feature/001-login` lista para push, **When** se ejecuta `git push`, **Then** el resultado del suite de tests queda persistido como estado de resultados.

---

### User Story 2 - La memoria bloquea cuando falta (Priority: P1)

El gate de memoria se comporta igual que el Spec-Kit Gate existente: si falta un estado obligatorio para la etapa, la operación se aborta con un mensaje que dice exactamente qué falta y cómo generarlo.

**Why this priority**: "Obligatorio" sin gate es documentación, no garantía. El framework ya demostró que el gate bloqueante es lo que produce cumplimiento real.

**Independent Test**: Borrar una observación con `DELETE /observations/{id}` e intentar `git push`; debe fallar identificando el estado ausente.

**Acceptance Scenarios**:

1. **Given** una rama `feature/` sin estado de resultados, **When** se ejecuta `git push`, **Then** el push se aborta listando el estado faltante.
2. **Given** el daemon de Engram caído, **When** se ejecuta cualquier hook de escritura, **Then** el hook intenta auto-arrancarlo y, si no lo logra, aborta con instrucciones — nunca continúa en silencio.
3. **Given** `HARNESS_EMERGENCY=1` exportado en el entorno del desarrollador, **When** se ejecuta un hook de memoria, **Then** el gate se omite, se registra la omisión como observación de tipo `bugfix`, y se advierte en consola.

---

### User Story 3 - Exigencia proporcional al tipo de rama (Priority: P2)

No toda tarea merece las 7 clases. Un `chore/` de una línea que exija siete registros produce relleno por trámite, y memoria rellenada por trámite contamina las búsquedas futuras con ruido que parece señal.

**Why this priority**: Protege la señal de la memoria. Sin esto, el gate obligatorio se vuelve contraproducente en el 60% de las ramas.

**Independent Test**: Correr el flujo en ramas `feature/`, `fix/` y `chore/` y verificar que cada una exige exactamente su cuota.

**Acceptance Scenarios**:

1. **Given** una rama `feature/`, **When** se evalúa el gate en merge, **Then** exige las 7 clases.
2. **Given** una rama `fix/` u `hotfix/`, **When** se evalúa el gate, **Then** exige 3: decisión, resultado y semántica registrada como `bugfix`.
3. **Given** una rama `chore/`, **When** se evalúa el gate, **Then** exige 1: decisión.

---

### User Story 4 - Tres agentes, un contrato (Priority: P2)

El framework debe funcionar igual con Claude Code, Codex y Kiro. Cada uno lee su propio archivo de configuración, pero el Protocolo de Memoria y la constitución del proyecto son uno solo.

**Why this priority**: El framework es un boilerplate público. Atarlo a un solo agente contradice su diseño — ya mantiene `AGENTS.md` como espejo de `CLAUDE.md` por esta razón.

**Independent Test**: Clonar el repo, correr `install.sh` eligiendo cada agente, y verificar que los tres reciben el mismo protocolo por su ruta nativa.

**Acceptance Scenarios**:

1. **Given** un repo recién instalado, **When** el agente es Claude Code, **Then** existe `.claude/settings.json` con los hooks de sesión y edición cableados.
2. **Given** un repo recién instalado, **When** el agente es Codex, **Then** `AGENTS.md` contiene el Protocolo de Memoria y `engram setup codex` registró el MCP en `~/.codex/config.toml`.
3. **Given** un repo recién instalado, **When** el agente es Kiro, **Then** existe `.kiro/steering/ia-framework.md` versionado en el repo con el protocolo.

---

### Edge Cases

- **El daemon no está corriendo.** El hook intenta `engram serve` en background una vez, espera hasta 3s por `GET /health`, y si falla aborta. Nunca escribe a un vacío ni continúa asumiendo éxito.
- **Deriva del nombre de proyecto.** Engram resuelve el proyecto por cwd/git-remote con seis niveles de fallback; dos desarrolladores pueden escribir a buckets distintos del mismo repo. Se fija con `.engram/config.json` versionado, que tiene la precedencia más alta en su algoritmo de detección.
- **CI no puede escribir memoria.** El runner de GitHub Actions no tiene `~/.engram` ni el daemon. El estado de resultados que produce el CI se emite como artifact JSON y se ingiere localmente en el siguiente `post-merge`.
- **Colisión de nombres con Kiro.** Kiro genera sus propios `requirements.md`, `design.md` y `tasks.md`. El nombre `tasks.md` colisiona exactamente con el del framework. El steering debe instruir a Kiro a usar `specs/<slug>/` del framework y no crear su propio árbol de specs.
- **Slug fuera de convención.** `pre-commit.sh:26` acepta `feature/[a-z0-9._/-]+` pero `common.sh:75` exige `^[0-9]{3,}-[a-z0-9-]+$`. Una rama `feature/login` pasa local y falla en CI. El `topic_key` debe derivarse de una única fuente: `spec_kit_effective_branch_name()`.
- **Rama sin slug de spec** (`test/`, `claude/`, `codex/`). No se exige memoria de tarea; solo se registra la sesión.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST escribir memoria mediante la API HTTP local de Engram (`POST /observations`, `POST /sessions`), no mediante MCP.
- **FR-002**: El sistema MUST persistir 5 estados por tarea bajo `topic_key` derivado del slug: `spec/<slug>/{contextual,semantic,procedural,decision,outcome}`.
- **FR-003**: El sistema MUST tratar la memoria episódica como derivada — se obtiene del timeline de Engram y no requiere escritura propia.
- **FR-004**: El sistema MUST mantener el estado de preferencias en `topic_key: user/preferences` con `scope: personal`, compartido entre proyectos y no por tarea.
- **FR-005**: El sistema MUST exigir cuotas por prefijo de rama: `feature/` las 7 clases; `fix/` y `hotfix/` 3 (decisión, resultado, semántica como `bugfix`); `chore/` 1 (decisión).
- **FR-006**: El sistema MUST validar los estados de forma acumulativa por etapa: `spec-new` exige contextual; el primer commit exige además semántica y procedimental; el push exige además decisión y resultado; el merge exige la cuota completa.
- **FR-007**: El sistema MUST abortar la operación de git cuando falte un estado exigido, con el mismo formato de error que el Spec-Kit Gate (`pre-commit.sh:47-52`).
- **FR-008**: `install.sh` MUST instalar el binario de Engram cuando no esté presente, y MUST abortar la instalación si no lo consigue.
- **FR-009**: `install.sh` MUST generar `.engram/config.json` con `project_name` derivado del basename del repositorio.
- **FR-010**: `install.sh` MUST ofrecer configuración para Claude Code, Codex y Kiro, y ejecutar `engram setup <agente>` para los seleccionados.
- **FR-011**: El sistema MUST versionar en el repositorio las superficies de agente que lo admiten: `.claude/settings.json`, `AGENTS.md`, `.kiro/steering/ia-framework.md` y `.kiro/settings/mcp.json`.
- **FR-012**: El sistema MUST implementar el bypass `HARNESS_EMERGENCY=1` de forma funcional en todos los gates de memoria, registrando cada uso como observación.
- **FR-013**: Los hooks MUST auto-arrancar `engram serve` si no responde, con un solo intento y timeout de 3 segundos.
- **FR-014**: El sistema MUST derivar el slug exclusivamente mediante `spec_kit_effective_branch_name()` de `.specify/scripts/bash/common.sh`.
- **FR-015**: El sistema MUST inyectar el contexto de memoria relevante al inicio de cada sesión de agente, vía `GET /context`.
- **FR-016**: `make spec-new` MUST consultar la memoria por el slug antes de generar plantillas y mostrar las decisiones previas relacionadas.

### Non-Functional Requirements

- **NFR-001**: Ningún hook de memoria MUST añadir más de 500ms al camino de commit en condiciones normales.
- **NFR-002**: Los wrappers MUST escribirse en bash, no en Python. `validate_structure.py:12-21` prohíbe los nombres `common.py`, `utils.py` y `helpers.py`, y `scripts/` no está en su lista de exclusiones — un wrapper en Python haría que el framework se auto-bloqueara.
- **NFR-003**: Ningún archivo nuevo MUST exceder 1000 líneas, conforme a la regla crítica del framework.
- **NFR-004**: La base de datos de Engram MUST permanecer fuera del control de versiones. `install.sh` debe añadir los patrones correspondientes al `.gitignore` que ya genera.
- **NFR-005**: El sistema MUST funcionar en macOS y Linux. Windows queda fuera de alcance en esta iteración.

## Deuda preexistente que esta feature corrige

Detectados durante la auditoría del repositorio; los tres bloquean o degradan el diseño de memoria.

- **DP-001**: `HARNESS_EMERGENCY=1` no existe funcionalmente. `emergency_hotfix.sh:129` lo exporta dentro de su propio subshell y ningún hook lo lee, pese a estar documentado en `CLAUDE.md:36`, `AGENTS.md:36`, `constitution-template.md:36` y `README.md:147`.
- **DP-002**: `emergency_hotfix.sh:108` invoca `check-file-size.sh` sin stdin, pero ese hook abre con `json_input=$(cat)`. En terminal queda colgado indefinidamente.
- **DP-005**: `.github/workflows/ci-quality-gate.yml:75` fija `SonarSource/sonarqube-quality-gate-action@v2`, una versión que no existe: esa acción solo publica hasta `v1`. GitHub resuelve todas las acciones de un job antes de evaluar cualquier `if:`, de modo que el workflow fallaba en la fase de preparación sin ejecutar un solo paso, incluso sin credenciales de Sonar configuradas. Junto con DP-004 significa que ninguno de los dos workflows del repositorio había podido ejecutarse nunca.
- **DP-004**: `.specify/scripts/bash/check-prerequisites.sh:93` cierra un bucle `for ... do` con `fi` en lugar de `done`. Es un error de sintaxis: el script no parsea en ninguna versión de bash y siempre sale con código 2. Es el único comando que ejecuta el workflow `spec-compliance.yml:23`, por lo que ese job de CI nunca ha podido pasar. Bloquea el gate de memoria en merge (FR-006), que se apoya en esa misma ruta.
- **DP-003**: No existe `.claude/settings.json`. `check-file-size.sh` y `post-edit.sh` están escritos como hooks de agente (PreToolUse/PostToolUse) pero nada los conecta; hoy solo corren en CI.

## Open Questions

- **OQ-001**: ¿Compartir memoria entre desarrolladores en esta iteración? `engram sync` exporta y importa chunks; Engram Cloud requiere infraestructura. Propuesta: local en esta iteración, sync en la siguiente.
- **OQ-002**: ¿El estado de resultados del CI se ingiere automáticamente en `post-merge`, o se deja como paso manual `make mem-ingest`?
- **OQ-003**: ¿Qué ocurre cuando un `feature/` se abandona sin merge? ¿La memoria se marca como descartada o se conserva como decisión negativa? Propuesta: conservar — saber qué se descartó y por qué es de las memorias más valiosas.
