# Implementation Plan: CI por carriles, cobertura al 80 % y guía web para agentes

**Branch**: `004-ci-lanes` | **Date**: 2026-11-14 | **Spec**: [specs/004-ci-lanes/spec.md](spec.md)

## Summary

Un clasificador en Python decide qué carriles activa un conjunto de archivos, a partir de una configuración JSON. El workflow de CI se divide en jobs condicionados por carril. El mismo clasificador entrega los flags de deploy. Se añade el gate de referencia con 80 % y un wrapper para el skill Modern Web Guidance.

## Technical Context

- **Languages/Versions**: Python 3.10 (biblioteca estándar), Bash, YAML de GitHub Actions
- **Primary Dependencies**: ninguna nueva; el skill se instala con `npx` bajo demanda
- **Storage/Databases**: no aplica
- **Testing Frameworks**: pytest
- **Target Platforms**: GitHub Actions y la máquina del desarrollador

## Proposed Changes

### Clasificador de carriles

#### [NEW] scripts/harness/ci_lanes.py
Carga `lanes.json`, normaliza rutas y expone `lane_for`, `ci_lanes`, `deploy_lanes`, `deploy_flags` y `changed_files`. CLI con `--mode ci|deploy`; imprime `carril=true|false`, `any` y, en deploy, `flags`. Escribe lo mismo en `GITHUB_OUTPUT` si existe.

#### [NEW] scripts/harness/lanes.json
Carriles `frontend` (`frontend/`) y `backend` (`src/`, por defecto), rutas neutras, `tests/` como solo de test y las rutas del pipeline.

#### [NEW] tests/harness/test_ci_lanes.py
Clasificación por ruta, mezcla de carriles, configuraciones alternativas, respaldo sin diff y salidas.

#### [MODIFY] pytest.ini
`pythonpath = .` para que los tests importen `scripts.harness`.

### Pipeline

#### [MODIFY] .github/workflows/ci-quality-gate.yml
De un job a seis: `changes`, `conventions`, `backend-tests`, `frontend-tests`, `sonar` y `outcome`. Cada job de tests sube su artefacto de cobertura y Sonar descarga los que existan. `outcome` conserva el artefacto de memoria, ahora con el resultado agregado.

#### [MODIFY] sonar-project.properties
Ruta del lcov del frontend.

#### [NEW] infra/sonarqube/quality-gate.json
Definición versionada del gate, con `new_coverage` en 80.

### Guía web

#### [NEW] scripts/dev/mwg.sh
Busca un Node 22 o superior (el activo o el más nuevo de nvm), apaga la telemetría y delega en `npx -y modern-web-guidance@latest`.

### Constitución y documentación

#### [MODIFY] CLAUDE.md, AGENTS.md, .specify/templates/constitution-template.md
Reglas «One Check, Once» y «Coverage on New Code (80%)»; secciones «CI Lanes» y «Modern Web Guidance».

#### [MODIFY] README.md, Makefile, install.sh
Secciones nuevas, targets `make lanes` y `make web-guidance`, carpeta `scripts/dev`.

---

## Verification & Rollback Plan

### Automated Verification
- **Testing Command**: `pytest tests/harness`
- El pull request toca el workflow, así que activa todos los carriles y ejerce el pipeline completo.

### Manual Verification
- `make lanes` en una rama con cambios de un solo tipo.
- `scripts/dev/mwg.sh search "dark mode toggle"` con un Node por defecto anterior al 22.

### Rollback
Revertir el commit restaura el workflow de un solo job. El clasificador no tiene estado.
