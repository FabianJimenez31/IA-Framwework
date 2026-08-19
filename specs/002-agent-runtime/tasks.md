# Tasks: Agent Runtime Tier

**Branch**: `002-agent-runtime` | **Spec**: [specs/002-agent-runtime/spec.md](spec.md) | **Plan**: [specs/002-agent-runtime/plan.md](plan.md)

Use this document as a living checklist of technical items to implement. Mark items with `[/]` when in progress, and `[x]` when completed.

> **Depende de `001-engram-memory`.** Esta rama está apilada sobre aquella. No iniciar hasta que el PR #1 esté mergeado o se confirme que se mergeará.

## Implementation Tasks

- [ ] **Phase 0: Decisiones que bloquean el diseño**
  - [ ] Resolver OQ-002: contrato de evaluaciones. Propuesta en `plan.md`: un ejecutable por evaluación, código 0 pasa
  - [ ] Resolver OQ-004: mapeo de `agents/<slug>/` a perfiles del runtime
  - [ ] Validar contra un Hermes real que `~/.hermes/pending/skills/` se comporta como documenta — **todo el gate de skills depende de esto**
  - [ ] Confirmar que `skills.write_approval: true` es exigible por configuración y no puede desactivarse en caliente

- [ ] **Phase 1: Contrato de runtime**
  - [ ] Crear `scripts/runtime/hermes_adapter.sh` con los cinco verbos
  - [ ] Crear `scripts/runtime/agent_context.sh`: identidad desde la rama `agent/<slug>` y lectura de `agent.yaml`
  - [ ] Degradación limpia cuando no hay runtime instalado (NFR-003)
  - [ ] Fallo duro con instrucciones cuando el runtime está instalado pero no responde (FR-012)

- [ ] **Phase 2: Artefacto de empleado digital**
  - [ ] Crear las tres plantillas en `.specify/templates/agent-*.md`
  - [ ] Crear `.specify/scripts/bash/create-new-agent.sh` espejando `create-new-feature.sh`
  - [ ] Definir el esquema de `agent.yaml`: perfil, `approval_mode`, límites de recursos, canales
  - [ ] Añadir el target `agent-new` al Makefile

- [ ] **Phase 3: Gate de skills**
  - [ ] Crear `scripts/runtime/skill_sync.sh` con captura idempotente (NFR-005)
  - [ ] Preservar el formato `SKILL.md` con frontmatter YAML del estándar agentskills.io (FR-004)
  - [ ] Preservar la estructura de soporte: `references/`, `templates/`, `scripts/`, `examples/`, `assets/`
  - [ ] Reportar skills desalineadas de su origen aguas arriba (FR-013)
  - [ ] Advertir sobre skills sin evaluación que las cubra (FR-014, OQ-001)
  - [ ] Abortar el despliegue si quedan pendientes sin capturar (FR-005)

- [ ] **Phase 4: Gate de evaluaciones**
  - [ ] Crear `scripts/runtime/eval_runner.sh` con el contrato de ejecutables
  - [ ] Tratar `evals/` vacío como fallo, no como caso trivial (FR-006)
  - [ ] Reportar con el formato del Spec-Kit Gate
  - [ ] Añadir el target `agent-eval`

- [ ] **Phase 5: Despliegue y reversión**
  - [ ] Crear `scripts/deployment/agent_deploy.sh` con punto de restauración previo (FR-007)
  - [ ] Publicar la definición como *tap* instalable por el runtime (FR-010)
  - [ ] Crear `scripts/deployment/agent_rollback.sh` espejando `rollback.sh`
  - [ ] Exigir `approval_mode: manual` para empleados que operan sobre sistemas de terceros (FR-008)
  - [ ] Añadir los targets `agent-deploy`, `agent-rollback`, `agent-status`

- [ ] **Phase 6: Integración con los gates existentes**
  - [ ] Añadir `agent` a la convención de ramas en las tres copias (FR-002)
  - [ ] Extender `check_feature_branch` en `common.sh` al slug de `agent/`
  - [ ] Factorizar la verificación de artefactos de `pre-commit.sh` para servir a `specs/` y `agents/` (FR-003)
  - [ ] Enganchar `agent_gate.sh` en `pre-push.sh` cuando la rama es `agent/`
  - [ ] Respetar `HARNESS_EMERGENCY=1` con el criterio de `001`: suspende proceso, nunca seguridad
  - [ ] Verificar que ninguna rama que no sea `agent/` cambia de comportamiento

- [ ] **Phase 7: Memoria del runtime**
  - [ ] Extender `task_context.sh` al prefijo `agent/` con `topic_key` bajo `agent/<slug>/<clase>` (FR-009)
  - [ ] Cuota de `agent/`: las siete clases
  - [ ] Casos nuevos en `capture_stage.sh`: semántica desde `plan.md`, procedimental desde `skills/`, resultado desde evaluaciones y despliegue
  - [ ] Verificar que la clase de resultados liga la decisión de diseño con el desempeño en operación

- [ ] **Phase 8: Constitución y documentación**
  - [ ] Añadir la sección "Agent Runtime" a `CLAUDE.md`, `AGENTS.md`, `.kiro/steering/ia-framework.md` y la plantilla de constitución
  - [ ] Redactar la regla de aislamiento por consumidor
  - [ ] Redactar la regla del modo de aprobación
  - [ ] `install.sh`: detectar Hermes, continuar sin él, y advertir si `skills.write_approval` no está activo
  - [ ] Actualizar `README.md` con la capa de run-time

- [ ] **Phase 9: Verificación**
  - [ ] Flujo completo con un empleado de prueba en `agent/002-smoke-agent`
  - [ ] Prueba de captura: provocar una skill generada y confirmar la interceptación
  - [ ] Prueba de idempotencia: dos capturas seguidas sin cambios
  - [ ] Prueba de bloqueo: pendientes sin capturar, `evals/` vacío, evaluación que falla
  - [ ] Prueba de reversión completa
  - [ ] Prueba de instalación **sin** Hermes: todo build-time intacto (NFR-003)
  - [ ] Prueba de runtime caído: fallo duro con instrucciones
  - [ ] Confirmar límite de 1000 líneas y que todo sea bash (NFR-001, NFR-002)

## Progress Tracking

**Estado actual**: Especificación completa. Ninguna fase iniciada.

**Bloqueo real**: la Fase 0 exige validar contra un Hermes instalado que el área de pendientes se comporta como documenta. El gate de skills —el aporte central de esta feature— depende por entero de ese mecanismo. Toda la especificación se escribió desde documentación oficial, no desde una instalación en funcionamiento.

**Riesgo principal**: si `skills.write_approval` resulta desactivable en caliente por el propio agente, el gate se puede evadir desde dentro y hay que rediseñarlo — probablemente comparando hashes del directorio de skills en vez de confiar en el área de pendientes.
