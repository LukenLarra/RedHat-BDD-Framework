# 🔧 Guía de Pre-commit y Formateo de Código

## 📋 Índice

- [¿Qué es Pre-commit?](#qué-es-pre-commit)
- [Instalación](#instalación)
- [Uso](#uso)
- [Herramientas Configuradas](#herramientas-configuradas)
- [Configuración Personalizada](#configuración-personalizada)
- [Troubleshooting](#troubleshooting)

---

## ¿Qué es Pre-commit?

**Pre-commit** es un framework que gestiona y mantiene hooks de git multi-lenguaje. Los hooks se ejecutan automáticamente antes de cada commit para:

- ✅ **Formatear código** automáticamente (Python con Black, JS con Prettier)
- ✅ **Ordenar imports** (Python con isort)
- ✅ **Detectar errores** (linting con Flake8)
- ✅ **Validar sintaxis** (YAML, JSON)
- ✅ **Limpiar whitespace** y finales de archivo
- ✅ **Prevenir commits problemáticos**

**Beneficio**: Todo el equipo usa el mismo formato de código, evitando discusiones de estilo en code reviews.

---

## 📦 Instalación

### Opción 1: Instalación Automática (Recomendado)

```bash
# Instala todas las dependencias de desarrollo y configura pre-commit
npm run install:dev
```

### Opción 2: Instalación Manual

```bash
# 1. Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# 2. Instalar los hooks de pre-commit
pre-commit install

# 3. (Opcional) Ejecutar en todos los archivos por primera vez
pre-commit run --all-files
```

### Verificar Instalación

```bash
pre-commit --version
# Debe mostrar: pre-commit 3.6.0 o superior
```

---

## 🚀 Uso

### Automático (en cada commit)

Una vez instalado, los hooks se ejecutan **automáticamente** cada vez que haces commit:

```bash
git add .
git commit -m "feat: añadir nueva funcionalidad"
```

Si algún hook falla o modifica archivos:

1. Los archivos modificados no se commitean automáticamente
2. Debes revisar los cambios
3. Hacer `git add` nuevamente
4. Volver a hacer commit

### Manual (sin hacer commit)

Puedes ejecutar los hooks manualmente:

```bash
# Ejecutar en todos los archivos
pre-commit run --all-files

# Ejecutar en archivos staged
pre-commit run

# Ejecutar un hook específico
pre-commit run black
pre-commit run prettier
pre-commit run flake8
```

### Scripts NPM

El proyecto incluye scripts convenientes:

```bash
# Formatear todo el código (Python + JavaScript)
npm run format

# Solo Python
npm run format:python

# Solo JavaScript
npm run format:js

# Linting (verificar sin modificar)
npm run lint
npm run lint:python
npm run lint:js

# Ejecutar pre-commit manualmente
npm run precommit
```

---

## 🛠 Herramientas Configuradas

### Para Python

| Herramienta | Propósito                       | Configuración                              |
| ----------- | ------------------------------- | ------------------------------------------ |
| **Black**   | Formateo automático de código   | Longitud de línea: 100 chars               |
| **isort**   | Ordenar imports automáticamente | Compatible con Black                       |
| **Flake8**  | Linting y detección de errores  | Max line: 100, ignora conflictos con Black |

### Para JavaScript

| Herramienta  | Propósito                    | Configuración                     |
| ------------ | ---------------------------- | --------------------------------- |
| **Prettier** | Formateo de JS/HTML/CSS/JSON | Print width: 100, comillas dobles |

### Hooks Generales

- ✂️ **trailing-whitespace**: Elimina espacios al final de líneas
- 📄 **end-of-file-fixer**: Asegura línea vacía al final de archivos
- ✅ **check-yaml**: Valida sintaxis YAML
- ✅ **check-json**: Valida sintaxis JSON
- 🚫 **check-added-large-files**: Previene commits de archivos >500KB
- 🚫 **no-commit-to-branch**: Previene commits directos a main/master
- 📝 **markdownlint**: Linting de archivos Markdown

---

## ⚙️ Configuración Personalizada

### Archivos de Configuración

El proyecto incluye los siguientes archivos de configuración:

```
.pre-commit-config.yaml   # Configuración principal de pre-commit
pyproject.toml            # Configuración de Black, isort, Flake8
.prettierrc               # Configuración de Prettier (JavaScript)
.prettierignore           # Archivos a ignorar por Prettier
.markdownlint.json        # Configuración de Markdown linting
```

### Modificar Configuración de Python

Edita [pyproject.toml](pyproject.toml):

```toml
[tool.black]
line-length = 120  # Cambiar longitud de línea

[tool.isort]
line_length = 120
# Añadir más opciones...
```

### Modificar Configuración de JavaScript

Edita [.prettierrc](.prettierrc):

```json
{
  "printWidth": 120,
  "singleQuote": true, // Usar comillas simples
  "semi": false // Sin punto y coma
}
```

### Deshabilitar un Hook Específico

Edita [.pre-commit-config.yaml](.pre-commit-config.yaml) y comenta el hook:

```yaml
# - repo: https://github.com/pycqa/flake8
#   rev: 7.0.0
#   hooks:
#     - id: flake8
```

Luego actualiza:

```bash
pre-commit install
```

### Saltar Pre-commit en un Commit Específico

**⚠️ No recomendado**, pero si es urgente:

```bash
git commit --no-verify -m "mensaje"
```

---

## 🔍 Ejemplos de Uso

### Ejemplo 1: Formatear Código Python

**Antes de pre-commit:**

```python
import os
import sys
from typing import Dict,List
def mi_funcion(  param1,param2 ):
    resultado=param1+param2
    return resultado
```

**Después de pre-commit (Black + isort):**

```python
import os
import sys
from typing import Dict, List


def mi_funcion(param1, param2):
    resultado = param1 + param2
    return resultado
```

### Ejemplo 2: Formatear JavaScript

**Antes:**

```javascript
const myFunction = (param1, param2) => {
  const result = { value: param1 + param2 };
  return result;
};
```

**Después (Prettier):**

```javascript
const myFunction = (param1, param2) => {
  const result = { value: param1 + param2 };
  return result;
};
```

---

## 🐛 Troubleshooting

### Error: "command not found: pre-commit"

**Solución:**

```bash
pip install pre-commit
pre-commit install
```

### Error: Los hooks no se ejecutan automáticamente

**Solución:**

```bash
# Reinstalar los hooks
pre-commit uninstall
pre-commit install
```

### Error: "No module named 'black'"

**Solución:**

```bash
pip install -r requirements-dev.txt
```

### Actualizar Versiones de los Hooks

```bash
pre-commit autoupdate
```

### Pre-commit es Muy Lento

Opciones:

1. Ejecutar solo en archivos modificados (comportamiento por defecto)
2. Reducir el número de hooks en `.pre-commit-config.yaml`
3. Usar `--no-verify` ocasionalmente (no recomendado)

### Conflictos de Formateo entre Herramientas

La configuración actual está diseñada para que Black, isort y Flake8 sean compatibles:

- isort usa `--profile=black`
- Flake8 ignora E203, W503, E501 (conflictos con Black)

---

## 📚 Recursos Adicionales

- [Documentación oficial de Pre-commit](https://pre-commit.com/)
- [Documentación de Black](https://black.readthedocs.io/)
- [Documentación de Prettier](https://prettier.io/docs/)
- [Documentación de Flake8](https://flake8.pycqa.org/)

---

## 🤝 Contribuir

Si encuentras problemas con la configuración de pre-commit o quieres sugerir mejoras:

1. Abre un Issue en el repositorio
2. Propón cambios en la configuración
3. Documenta el problema y la solución

---

## ✅ Checklist para Nuevos Desarrolladores

- [ ] Instalar pre-commit: `npm run install:dev`
- [ ] Ejecutar en todos los archivos: `pre-commit run --all-files`
- [ ] Hacer un commit de prueba para verificar que funciona
- [ ] Familiarizarse con los comandos de formateo manual
- [ ] Leer las configuraciones en `pyproject.toml` y `.prettierrc`

**¡Listo!** Ahora todos tus commits tendrán código formateado consistentemente. 🎉
