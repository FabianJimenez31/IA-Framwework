# Implementation Plan: Agent Runtime Tier

**Branch**: `002-agent-runtime` | **Date**: 2026-08-18 | **Spec**: [specs/002-agent-runtime/spec.md](spec.md)

## Summary

Se añade la capa de run-time al framework como tipo de artefacto gobernado, no como motor. `agents/<slug>/` pasa a ser un artefacto de primera clase con el mismo ritual que `specs/<slug>/`, y se le aplican tres gates nuevos: captura obligatoria de skills, evaluaciones verdes antes de desplegar, y punto de restauración previo.

El aporte diferencial es el gate de skills. Hermes genera y modifica su propio procedimiento mientras opera; el framework lo intercepta en el área de pendientes que el propio Hermes ofrece, lo trae al control de versiones y lo obliga a pasar por Pull Request. Deja de ser deriva y pasa a ser un cambio revisado.

## Technical Context

- **Languages/Versions**: Bash 3.2+, jq, curl
- **Primary Dependencies**: `001-engram-memory` (cliente de memoria y contexto de tarea); Hermes Agent ≥0.2 como runtime de referencia
- **Storage/Databases**: El runtime posee su propio estado (`~/.hermes/`); el repositorio posee la definición
- **Testing Frameworks**: pytest para el framework; contrato de ejecutables para las evaluaciones de agente
- **Target Platforms**: macOS, Linux

### Contrato con el runtime

Todo lo específico de Hermes queda confinado a `scripts/runtime/hermes_adapter.sh`. El resto del sistema habla contra un contrato de cinco verbos:

| Verbo | Qué hace | Hermes |
|---|---|---|
| `runtime_available` | ¿Hay runtime? | `command -v hermes` |
| `runtime_pending_skills` | Skills generadas sin revisar | `~/.hermes/pending/skills/` |
| `runtime_pull_skills` | Traerlas al repositorio | copia con preservación de estructura |
| `runtime_push_definition` | Publicar la definición vigente | *tap* + `hermes skills tap add` |
| `runtime_status` | Estado del perfil | `hermes -p <perfil>` |

Sustituir Hermes por otro runtime significa escribir otro adaptador, no tocar los gates.

## Anatomía de un empleado digital

```
agents/001-lead-analyst/
├── spec.md        misión, límites, métricas, a quién escala   ← agnóstico de runtime
├── plan.md        herramientas, canales, modelo, permisos     ← aquí vive Hermes
├── tasks.md       checklist de implementación
├── SOUL.md        personalidad (concepto nativo de Hermes)
├── agent.yaml     perfil, approval_mode, límites de recursos
├── skills/        SKILL.md + frontmatter YAML (agentskills.io)
└── evals/         un ejecutable por evaluación; 0 = pasa
```

`spec.md` no puede mencionar Hermes. Es la frontera que mantiene el runtime sustituible.

## Los tres gates

### 1. Gate de skills — el que importa

```text
Hermes opera
   └─> skill_manage crea o modifica una skill
        └─> skills.write_approval: true la deja en ~/.hermes/pending/skills/
             └─> make agent-sync la trae a agents/<slug>/skills/
                  └─> aparece como cambio del árbol de trabajo
                       └─> PR, revisión, merge
                            └─> make agent-deploy la publica al runtime
```

Sin `agent-sync`, `agent-deploy` se aborta. El framework nunca despliega un empleado cuyo procedimiento real difiere del revisado.

El framework debe **exigir** `skills.write_approval: true` en la configuración del runtime; sin esa opción, Hermes escribe directamente y el gate no tiene dónde interceptar.

### 2. Gate de evaluaciones

Contrato mínimo, deliberadamente pobre para no atarse a Hermes: cada archivo ejecutable de `evals/` se ejecuta; código 0 pasa, cualquier otro falla. El framework no define cómo se escribe una evaluación, solo cómo se sabe si pasó.

`evals/` vacío es un fallo, no un caso trivial. Un empleado sin evaluaciones no es desplegable.

### 3. Gate de restauración

Antes de aplicar, se crea un tag `agent-rollback-<slug>-<timestamp>` y un snapshot de la definición, reutilizando el patrón de `emergency_hotfix.sh`.

## Proposed Changes

### Adaptador de runtime (nuevo)

#### [NEW] scripts/runtime/hermes_adapter.sh
Implementa los cinco verbos del contrato. Único archivo con conocimiento de rutas y comandos de Hermes.

#### [NEW] scripts/runtime/agent_context.sh
Resuelve identidad de empleado desde la rama `agent/<slug>` y lee `agent.yaml`. Espeja `scripts/memory/task_context.sh`.

#### [NEW] scripts/runtime/skill_sync.sh
Captura desde pendientes hacia el repositorio. Idempotente (NFR-005). Reporta skills desalineadas de su origen (FR-013) y skills sin evaluación que las cubra (FR-014).

#### [NEW] scripts/runtime/eval_runner.sh
Ejecuta `agents/<slug>/evals/*`, acumula fallos y reporta con el formato del Spec-Kit Gate.

#### [NEW] scripts/runtime/agent_gate.sh
Compone los tres gates. Respeta `HARNESS_EMERGENCY=1` con el mismo criterio de `001`: suspende proceso, nunca seguridad.

#### [NEW] scripts/deployment/agent_deploy.sh
Verifica el gate, crea el punto de restauración, publica la definición y registra el resultado en memoria.

#### [NEW] scripts/deployment/agent_rollback.sh
Lista y aplica puntos de restauración. Espeja `rollback.sh`.

### Plantillas y creación

#### [NEW] .specify/templates/agent-spec-template.md, agent-plan-template.md, agent-soul-template.md
Plantillas del artefacto de empleado.

#### [NEW] .specify/scripts/bash/create-new-agent.sh
Espeja `create-new-feature.sh`: crea rama `agent/<slug>`, genera artefactos, consulta memoria previa y abre la sesión.

### Gates existentes

#### [MODIFY] .claude/hooks/pre-commit.sh
Añade `agent` a la convención de ramas y extiende el Spec-Kit Gate a `agents/<slug>/`. La lógica de artefactos faltantes se factoriza para servir a ambos tipos.

#### [MODIFY] .specify/scripts/bash/common.sh
`check_feature_branch` pasa a validar también el slug de `agent/`.

#### [MODIFY] .pre-commit-config.yaml
Tercera copia de la convención de ramas.

#### [MODIFY] .claude/hooks/pre-push.sh
Cuando la rama es `agent/`, corre `agent_gate.sh` además del gate de memoria.

### Memoria

#### [MODIFY] scripts/memory/task_context.sh
Reconoce el prefijo `agent/` y emite `topic_key` bajo `agent/<slug>/<clase>`. Cuota de `agent/`: las siete clases, igual que `feature/` — un empleado digital no es un cambio menor.

#### [MODIFY] scripts/memory/capture_stage.sh
Casos nuevos: `semantic` desde `agents/<slug>/plan.md`, `procedural` desde `skills/`, `outcome` desde el resultado de las evaluaciones y del despliegue.

### Superficie

#### [MODIFY] Makefile
`agent-new`, `agent-sync`, `agent-check`, `agent-eval`, `agent-deploy`, `agent-rollback`, `agent-status`.

#### [MODIFY] CLAUDE.md, AGENTS.md, .kiro/steering/ia-framework.md, constitution-template.md
Sección "Agent Runtime" con las dos reglas que no son negociables:

> **Aislamiento por consumidor.** La memoria del empleado guarda procedimiento agnóstico. Los datos del consumidor viajan en la tarea y su registro vive en el sistema del consumidor. El runtime aísla por perfil, no por consumidor.

> **Modo de aprobación.** Todo empleado que opere sobre sistemas de terceros declara `approval_mode: manual` en `agent.yaml`. Es configuración versionada, no un interruptor de runtime.

#### [MODIFY] install.sh
Detecta Hermes. **Si no está, continúa** (NFR-003): un proyecto que solo construye software no necesita runtime. Si está, verifica `skills.write_approval: true` y advierte si falta.

---

## Verification & Rollback Plan

### Automated Verification

- **Testing Command**: `pytest tests/`
- **Quality Verification**: `make dev-check`
- **Agent Verification**: `make agent-check` — los tres gates contra la rama actual
- **Evaluaciones**: `make agent-eval`

### Manual Verification

1. `make agent-new` en un repo limpio; confirmar artefactos y que el gate bloquea si quedan vacíos.
2. Provocar que Hermes genere una skill; confirmar que `make agent-sync` la trae y que `agent-deploy` se aborta antes de capturarla.
3. Ejecutar `agent-sync` dos veces sin cambios; confirmar que no produce diferencias (NFR-005).
4. Desplegar con `evals/` vacío y con una evaluación que falle; confirmar el aborte en ambos casos.
5. Desplegar con evaluaciones verdes; confirmar el punto de restauración y revertir con `agent-rollback`.
6. Instalar el framework **sin** Hermes; confirmar que todo lo de build-time sigue funcionando (NFR-003).
7. Detener el runtime; confirmar que `agent-sync` y `agent-deploy` fallan con instrucciones, no en silencio.

### Rollback Plan

Toda la superficie nueva está aislada en `scripts/runtime/`, `scripts/deployment/agent_*.sh`, `agents/` y las plantillas de agente. Revertir es:

```bash
rm -rf scripts/runtime agents .specify/templates/agent-*.md \
       .specify/scripts/bash/create-new-agent.sh scripts/deployment/agent_*.sh
git checkout main -- .claude/hooks/pre-commit.sh .claude/hooks/pre-push.sh \
  .specify/scripts/bash/common.sh .pre-commit-config.yaml scripts/memory/ \
  install.sh Makefile CLAUDE.md AGENTS.md
```

Los gates de build-time no cambian de comportamiento para ramas que no sean `agent/`. Un proyecto sin empleados digitales no percibe esta feature.
