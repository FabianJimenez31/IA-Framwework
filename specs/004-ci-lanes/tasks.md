# Tasks: CI por carriles, cobertura al 80 % y guía web para agentes

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Implementation Tasks

### Clasificador
- [x] T001 Definir el formato de `scripts/harness/lanes.json`
- [x] T002 Implementar `scripts/harness/ci_lanes.py` (clasificación, modos ci y deploy, salidas)
- [x] T003 Respaldos: carril por defecto, pipeline activa todo, sin diff activa todo
- [x] T004 Tests en `tests/harness/test_ci_lanes.py` y `pythonpath` en `pytest.ini`

### Pipeline
- [x] T005 Dividir `ci-quality-gate.yml` en jobs por carril
- [x] T006 Artefactos de cobertura por carril y Sonar con los que existan
- [x] T007 Conservar el artefacto de memoria con el resultado agregado
- [x] T008 Gate de referencia en `infra/sonarqube/quality-gate.json` con 80 %

### Guía web
- [x] T009 Wrapper `scripts/dev/mwg.sh`
- [x] T010 Targets `make lanes` y `make web-guidance`

### Documentación
- [x] T011 Reglas y secciones en `CLAUDE.md`, `AGENTS.md` y la plantilla de constitución
- [x] T012 Secciones en `README.md`

## Progress Tracking

| Fase | Estado |
|---|---|
| Clasificador | Hecho |
| Pipeline | Hecho; se ejerce por primera vez en el pull request de esta feature |
| Guía web | Hecho |
| Documentación | Hecho |

## Pendiente fuera de esta feature

- Selección de tests por impacto dentro de un carril.
- Hooks locales que usen el clasificador para correr solo lo tocado.
