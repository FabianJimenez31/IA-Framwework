# Feature Specification: Agent Runtime Tier

**Feature Branch**: `002-agent-runtime`

**Created**: 2026-08-18

**Status**: Draft

**Input**: User description: "El framework tiene dos capas y solo existe una. Añadir el runtime como concepto de primera clase, con Hermes como runtime de referencia. Newton es solo un consumidor."

## Context

IA-Framework gobierna cómo se **construye** software: especificaciones obligatorias, quality gates, CI, rollback y —desde `001-engram-memory`— memoria persistente. Todo eso es build-time.

No tiene nada para lo que ocurre después: trabajadores persistentes que reciben eventos, ejecutan acciones sobre sistemas reales, deciden dentro de límites y responden por métricas. Esa es la capa de run-time, y es donde el framework puntúa 1 o 2 sobre 10 en orquestación multiagente, agentes especializados, ejecución autónoma continua e integraciones.

Hoy el repositorio tiene `src/`, `tests/` y `specs/`. No tiene dónde poner un empleado digital.

### Principio rector

> **El framework gobierna el runtime. El framework no es el runtime.**

No se implementa un motor de agentes. Se define un tipo de artefacto nuevo —el empleado digital— y se le aplica la misma disciplina que hoy protege al código: especificación previa, revisión por PR, gates automáticos, evaluaciones y rollback.

### Por qué Hermes como runtime de referencia

[Hermes Agent](https://hermes-agent.nousresearch.com/docs/) de Nous Research: MIT, autoalojable, 60+ herramientas, MCP bidireccional, 25+ canales de mensajería, cron interno, servidor A2A JSON-RPC, y aislamiento por contenedor con aprobación humana de comandos peligrosos.

Y una razón de fondo: **Hermes crea y modifica sus propias skills en caliente** (`skill_manage`, "the agent's procedural memory"). Eso es exactamente la deriva de agente que el README de este framework declara combatir, trasladada del código al comportamiento del negocio. Hermes no tiene gobierno para ello; este framework es precisamente eso.

Hermes ya ofrece el punto de enganche: con `skills.write_approval: true`, las skills que el agente genera quedan en `~/.hermes/pending/skills/` esperando revisión humana. El framework convierte esa revisión en un flujo de control de versiones.

### Alcance del runtime

El framework define el contrato del artefacto; Hermes es la primera implementación. Cualquier otro runtime que acepte definiciones equivalentes debe poder sustituirlo sin cambiar `agents/<slug>/spec.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Un empleado digital se define con el mismo ritual (Priority: P1)

`make agent-new` crea `agents/<slug>/` con la misma trilogía que ya conoce el equipo, más los artefactos propios del runtime. Nadie aprende un flujo nuevo.

**Why this priority**: Si definir un empleado digital requiere un proceso distinto, el gobierno se evade. El valor del framework es que hay un solo camino.

**Independent Test**: Ejecutar `make agent-new`, verificar que se crean los artefactos y que el gate bloquea el commit si quedan sin llenar.

**Acceptance Scenarios**:

1. **Given** un repo con el framework instalado, **When** se ejecuta `make agent-new` con slug `001-lead-analyst`, **Then** se crea la rama `agent/001-lead-analyst` y `agents/001-lead-analyst/` con `spec.md`, `plan.md`, `tasks.md`, `SOUL.md`, `skills/` y `evals/`.
2. **Given** una rama `agent/` con artefactos sin editar, **When** se intenta commitear, **Then** el gate bloquea igual que el Spec-Kit Gate hace hoy con `feature/`.
3. **Given** un `agents/<slug>/spec.md` completo, **When** se consulta memoria por el slug, **Then** aparecen las decisiones previas relacionadas.

---

### User Story 2 - Las skills autogeneradas no derivan (Priority: P1)

Hermes escribe skills mientras opera. El framework las captura desde el área de pendientes, las trae al repositorio y **bloquea el despliegue hasta que pasen por Pull Request**.

**Why this priority**: Es el aporte central. Un agente que reescribe su propio procedimiento en producción, sin especificación ni revisión, es deriva de agente en su forma más pura. Ninguna otra herramienta del ecosistema resuelve esto, y es exactamente lo que este framework existe para hacer.

**Independent Test**: Provocar que el runtime genere una skill, ejecutar la captura, y verificar que aparece como cambio sin commitear que el gate exige revisar.

**Acceptance Scenarios**:

1. **Given** un runtime con `skills.write_approval: true` y una skill pendiente, **When** se ejecuta `make agent-sync`, **Then** la skill aparece bajo `agents/<slug>/skills/` como cambio del árbol de trabajo.
2. **Given** skills pendientes sin capturar, **When** se intenta desplegar, **Then** el despliegue se aborta indicando cuántas hay y cómo capturarlas.
3. **Given** una skill capturada y commiteada, **When** el runtime vuelve a modificarla, **Then** la siguiente captura muestra el diff, no un archivo nuevo.

---

### User Story 3 - Ningún empleado se despliega sin evaluaciones verdes (Priority: P1)

Un empleado digital tiene un suite de evaluaciones en `agents/<slug>/evals/`. Sin evaluaciones que pasen, no hay despliegue. Es el `make test` de los agentes.

**Why this priority**: Un empleado digital toma decisiones sobre sistemas reales. Desplegarlo sin medir su comportamiento es peor que desplegar código sin pruebas, porque el fallo es probabilístico y no lanza excepción.

**Independent Test**: Definir un empleado con una evaluación que falle y confirmar que el despliegue se aborta.

**Acceptance Scenarios**:

1. **Given** un empleado sin ningún archivo en `evals/`, **When** se intenta desplegar, **Then** se aborta: un empleado sin evaluaciones no es desplegable.
2. **Given** evaluaciones que fallan, **When** se ejecuta `make agent-deploy`, **Then** se aborta mostrando cuáles fallaron.
3. **Given** evaluaciones verdes, **When** se despliega, **Then** se crea un punto de rollback antes de aplicar los cambios.

---

### User Story 4 - Las siete clases de memoria se extienden al runtime (Priority: P2)

El modelo de memoria de `001-engram-memory` cubre cómo se construyó el software. Se extiende para cubrir cómo trabaja el empleado, con la clase de **resultados** uniendo ambas capas.

**Why this priority**: Es lo que convierte el registro de decisiones en registro de consecuencias. Sin esto, el framework sabe qué se decidió al diseñar un empleado, pero nunca si funcionó.

**Independent Test**: Desplegar un empleado, registrar un resultado de operación, y verificar que queda ligado al `topic_key` de la decisión de diseño.

**Acceptance Scenarios**:

1. **Given** un empleado desplegado, **When** se registra su desempeño, **Then** se escribe bajo `agent/<slug>/outcome` y es recuperable junto a la decisión de diseño.
2. **Given** un empleado con skills capturadas, **When** se consulta memoria, **Then** la clase procedimental refleja las skills vigentes.

---

### User Story 5 - Un empleado digital se revierte como se revierte el código (Priority: P2)

`make agent-rollback` devuelve un empleado a su definición anterior usando la misma maquinaria de tags y snapshots que ya existe en `scripts/deployment/`.

**Why this priority**: Un empleado que empieza a comportarse mal en producción necesita el mismo camino de salida que un despliegue roto. Sin esto, la única opción es apagarlo.

**Acceptance Scenarios**:

1. **Given** un empleado desplegado, **When** se ejecuta `make agent-rollback`, **Then** se listan los puntos de restauración disponibles.
2. **Given** un punto seleccionado, **When** se aplica, **Then** el runtime queda con la definición y las skills de ese punto.

---

### Edge Cases

- **Aislamiento por perfil, no por consumidor.** Hermes aísla por perfil de sistema operativo: cada perfil tiene su propio `HERMES_HOME`, memoria, sesiones y proceso gateway, y la documentación advierte que compartir el directorio corrompe la memoria. Un perfil que atiende a varios consumidores acumula datos de todos en su memoria. **Regla del framework: la memoria del empleado guarda procedimiento agnóstico del consumidor; los datos del consumidor viajan en la tarea y su registro vive en el sistema del consumidor.** Va en la constitución, no en el código de cada proyecto.
- **Autorización invertida.** El gateway de Hermes autoriza por allowlist y emparejamiento por DM, y su documentación prohíbe `GATEWAY_ALLOW_ALL_USERS=true` en producción. Un empleado digital expuesto a público desconocido debe recibir el tráfico a través del sistema del consumidor vía A2A, nunca conectando el canal directo.
- **Skills editadas a mano.** `hermes skills update` salta deliberadamente las skills modificadas localmente. Tras la captura, todas las skills del repositorio quedan en ese estado, así que las actualizaciones aguas arriba dejan de llegar solas. El framework debe reportarlo, no ocultarlo.
- **Runtime no disponible.** Si el runtime no responde, la captura y el despliegue fallan de forma dura con instrucciones, nunca en silencio. Mismo criterio que el gate de memoria.
- **Skills que cambian sin evaluaciones que las cubran.** Una skill capturada sin evaluación asociada es un cambio de comportamiento sin medición. El gate lo advierte; bloquear o no queda como pregunta abierta.
- **Modo de aprobación.** `smart` delega en un LLM auxiliar decidir qué es peligroso. Para empleados que operan sobre sistemas de terceros, el framework exige `manual`, versionado en la definición del empleado y no ajustable en caliente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST definir `agents/<slug>/` como tipo de artefacto de primera clase, con `spec.md`, `plan.md`, `tasks.md`, `SOUL.md`, `skills/` y `evals/`.
- **FR-002**: El sistema MUST aceptar el prefijo de rama `agent/` en las tres copias de la convención de nombres, con la misma regla de slug `NNN-kebab-case`.
- **FR-003**: El gate de artefactos MUST exigir `spec.md`, `plan.md` y `tasks.md` completos en ramas `agent/`, reutilizando la lógica que hoy aplica a `feature/`.
- **FR-004**: El sistema MUST capturar las skills que el runtime genere, desde su área de pendientes hacia `agents/<slug>/skills/`, preservando el formato `SKILL.md` con frontmatter YAML del estándar agentskills.io.
- **FR-005**: El sistema MUST abortar el despliegue cuando existan skills pendientes sin capturar.
- **FR-006**: El sistema MUST abortar el despliegue cuando `evals/` esté vacío o alguna evaluación falle.
- **FR-007**: El sistema MUST crear un punto de restauración antes de cada despliegue, usando la maquinaria de `scripts/deployment/`.
- **FR-008**: El sistema MUST exigir `approval_mode: manual` en la definición de todo empleado que opere sobre sistemas de terceros.
- **FR-009**: El sistema MUST extender las clases de memoria al runtime bajo `agent/<slug>/{semantic,procedural,decision,outcome}`.
- **FR-010**: El sistema MUST publicar `agents/<slug>/skills/` en un formato instalable por el runtime; para Hermes, la estructura de *tap* (repositorio con `skills/` conteniendo `SKILL.md`).
- **FR-011**: El sistema MUST tratar el runtime como sustituible: `agents/<slug>/spec.md` no puede contener detalles específicos de Hermes, que van en `plan.md`.
- **FR-012**: El sistema MUST fallar de forma explícita y con instrucciones cuando el runtime no esté disponible.
- **FR-013**: El sistema MUST reportar cuando una skill capturada quede desalineada de su origen aguas arriba.
- **FR-014**: El sistema MUST advertir cuando una skill cambie sin que ninguna evaluación la cubra.

### Non-Functional Requirements

- **NFR-001**: Los scripts nuevos MUST escribirse en bash, por la misma razón que en `001`: `validate_structure.py` prohíbe nombres genéricos de módulo y no excluye `scripts/`.
- **NFR-002**: Ningún archivo nuevo MUST exceder 1000 líneas.
- **NFR-003**: El framework MUST seguir instalándose y funcionando sin runtime configurado. Un proyecto que solo construye software no debe verse obligado a instalar Hermes.
- **NFR-004**: Ninguna credencial del runtime MUST quedar versionada. La configuración va por variables de entorno, como el resto del framework.
- **NFR-005**: La captura de skills MUST ser idempotente: ejecutarla dos veces sin cambios en el runtime no produce diferencias en el árbol de trabajo.

## Deuda y dependencias

- Depende de `001-engram-memory` para el cliente de memoria, la resolución de identidad de tarea y el gate de cuota. Esta rama está apilada sobre aquella.
- La regla de aislamiento por consumidor y la de modo de aprobación deben incorporarse a `CLAUDE.md`, `AGENTS.md`, `.kiro/steering/` y la plantilla de constitución.

## Open Questions

- **OQ-001**: ¿Una skill capturada sin evaluación que la cubra bloquea el despliegue o solo advierte? Propuesta: advertir en la primera iteración; bloquear cuando el equipo tenga costumbre de escribir evaluaciones.
- **OQ-002**: ¿Cómo se ejecutan las evaluaciones? Un runner propio del framework, o delegar en el runtime. Propuesta: contrato mínimo —un ejecutable por evaluación que sale 0 o distinto de 0— para no atarse a Hermes.
- **OQ-003**: ¿El despliegue lo hace el framework o CI? El runner de GitHub no alcanza un runtime autoalojado, igual que no alcanza al daemon de memoria. Propuesta: despliegue local en la primera iteración.
- **OQ-004**: ¿Un empleado digital por repositorio, o varios? Hermes aísla por perfil y varios perfiles corren en paralelo, así que varios es viable. Falta definir cómo se mapea `agents/<slug>/` a perfiles.
- **OQ-005**: ¿Se versiona `SOUL.md` por empleado o se comparte una personalidad base del proyecto? Propuesta: por empleado, con posibilidad de heredar.
