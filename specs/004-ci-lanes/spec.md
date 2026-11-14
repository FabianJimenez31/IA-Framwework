# Feature Specification: CI por carriles, cobertura al 80 % y guía web para agentes

**Feature Branch**: `004-ci-lanes`

**Created**: 2026-11-14

**Status**: Implemented

**Input**: User description: "Que el CI sea más rápido: si tocamos back, solo back; si tocamos front, solo front. Bajar la cobertura exigida a 80 %. Y traer el skill de guía web moderna para los agentes."

## Context

El workflow `ci-quality-gate.yml` es un solo job que corre todo en cada cambio. En un proyecto real que adoptó el framework, ese diseño produjo tres problemas medidos:

- Un pull request que solo cambiaba documentación tardó 23,7 minutos en validarse, porque corría la suite de backend y la de frontend en serie.
- Cada merge desplegaba todos los servicios, aunque el cambio fuera una línea de estilos. Reiniciar un worker con trabajos en cola es riesgo sin beneficio.
- El umbral de 100 % de cobertura en código nuevo convertía cambios mecánicos en tareas de escribir tests, y la salida habitual era desactivar el gate.

Además, los agentes escriben interfaz web con los patrones que recuerdan de su entrenamiento, que suelen estar desactualizados.

### Principio rector

> **Cada verificación corre una sola vez, en el lugar más barato donde sirve.**

Un pipeline lento se evade. La confianza no viene de repetir todo en cada paso, sino de que cada control sea real y corra donde corresponde.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Un cambio valida solo lo que toca (Priority: P1)

Quien abre un pull request que solo toca el frontend no espera la suite de backend, y viceversa. Un cambio solo de documentación corre únicamente las convenciones.

**Why this priority**: Es el origen de la demora. Sin esto, todo lo demás optimiza algo que igual corre de más.

**Independent Test**: Ejecutar `ci_lanes.py` con listas de archivos y comprobar qué carriles activa.

**Acceptance Scenarios**:

1. **Given** un cambio solo bajo `frontend/`, **When** se calculan los carriles, **Then** solo `frontend` queda activo.
2. **Given** un cambio solo bajo `docs/` o `specs/`, **When** se calculan los carriles, **Then** ninguno queda activo.
3. **Given** un archivo en una ruta que nadie clasificó, **When** se calculan los carriles, **Then** cae en el carril por defecto.
4. **Given** un cambio al propio workflow, **When** se calculan los carriles de CI, **Then** todos quedan activos.

---

### User Story 2 - El deploy toca solo los servicios afectados (Priority: P1)

Un job de deploy obtiene del mismo clasificador los flags que debe pasar a su script, en lugar de desplegar todo.

**Why this priority**: Es donde está el riesgo en producción: reinicios innecesarios.

**Independent Test**: Ejecutar `ci_lanes.py --mode deploy` y comprobar los flags.

**Acceptance Scenarios**:

1. **Given** un cambio de backend y frontend, **When** se piden los flags, **Then** salen los de ambos carriles en el orden declarado.
2. **Given** un cambio solo bajo `tests/`, **When** se piden los flags, **Then** no sale ninguno.
3. **Given** un diff que no se puede calcular, **When** se piden los flags, **Then** sale `--all`.

---

### User Story 3 - Los carriles se adaptan sin tocar código (Priority: P2)

Cada proyecto declara sus carriles, rutas y flags en `scripts/harness/lanes.json`.

**Why this priority**: El framework es una plantilla; cada proyecto tiene otra estructura.

**Independent Test**: Cargar una configuración alternativa y clasificar rutas con ella.

**Acceptance Scenarios**:

1. **Given** una configuración sin carril por defecto, **When** se clasifica una ruta desconocida, **Then** no activa nada.
2. **Given** una configuración con dos carriles por defecto, **When** se carga, **Then** falla con un error claro.

---

### User Story 4 - Los agentes consultan la práctica web vigente (Priority: P3)

En proyectos con interfaz web, `make web-guidance` instala el skill Modern Web Guidance, y la constitución obliga a consultarlo antes de escribir HTML, CSS o JS de cliente.

**Why this priority**: Mejora la calidad de la interfaz, pero no bloquea nada de lo anterior.

**Independent Test**: Ejecutar `scripts/dev/mwg.sh search "<consulta>"` con un Node por defecto anterior al 22.

**Acceptance Scenarios**:

1. **Given** un Node activo anterior al 22 y uno más nuevo instalado con nvm, **When** se ejecuta el wrapper, **Then** usa el más nuevo sin cambiar el del proyecto.
2. **Given** ningún Node 22 o superior, **When** se ejecuta el wrapper, **Then** termina con código 1 y dice cómo instalarlo.

### Edge Cases

- Rutas con barras invertidas o espacios alrededor: se normalizan antes de clasificar.
- Markdown fuera de la raíz (por ejemplo un prompt bajo `src/`): no es neutro, cuenta como código.
- El carril de frontend activo en un proyecto sin frontend: el job detecta que falta `package.json` y no ejecuta nada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El clasificador lee carriles, rutas neutras, rutas solo de test y rutas del pipeline desde `scripts/harness/lanes.json`.
- **FR-002**: Una ruta sin clasificar cae en el carril marcado como `default`.
- **FR-003**: Un cambio a una ruta del pipeline activa todos los carriles de CI y ninguno de deploy.
- **FR-004**: Las rutas solo de test activan CI pero no deploy.
- **FR-005**: Sin un diff calculable, se activan todos los carriles y el deploy usa `--all`.
- **FR-006**: El workflow ejecuta cada job solo si su carril está activo, y Sonar con la cobertura que exista.
- **FR-007**: El gate de referencia exige 80 % de cobertura en código nuevo.
- **FR-008**: `scripts/dev/mwg.sh` ejecuta el CLI del skill con un Node 22 o superior y con la telemetría apagada.

### Non-Functional Requirements

- **NFR-001**: El clasificador no tiene dependencias fuera de la biblioteca estándar.
- **NFR-002**: El cálculo de carriles tarda segundos y corre antes que cualquier job pesado.

## Open Questions

- Selección de tests por impacto dentro de un carril (correr en el PR solo los tests afectados y la suite completa tras el merge). Queda fuera de esta feature.
