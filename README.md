# Terra

Lenguaje de dominio específico (DSL) para el análisis de datos ambientales y de sostenibilidad.

Terra permite describir, con una sintaxis corta y declarativa en español, un flujo completo de ciencia de datos: cargar un CSV, limpiarlo, transformarlo, agruparlo, calcular estadísticas y guardar los resultados.

```
fijo datos = cargar "datos/emisiones_ejemplo.csv"

fijo resumen = datos
    |> eliminar nulos
    |> crear co2_per_capita = co2 * 1000000 / poblacion
    |> agrupar por [pais]
    |> resumir promedio = redondear(media(co2_per_capita), 2),
               registros = contar()
    |> ordenar por promedio desc

mostrar(resumen)
guardar resumen como "salidas/resumen.csv"
```

Proyecto del curso **Lenguajes de Programación y Transducción**, Universidad Sergio Arboleda, semestre 2026-2.

---

## Características

- Gramática escrita en **ANTLR 4** y ejecución con el **patrón Visitor** en Python.
- **Sin librerías externas de datos:** la estructura de tabla, el lector y el escritor de CSV y todas las estadísticas están implementados desde cero (sin pandas, NumPy ni el módulo `csv`).
- **Tuberías (`|>`)**: cada operación recibe una tabla y devuelve una tabla nueva; la original nunca se modifica.
- **Tipado estricto:** `numero`, `decimal`, `texto`, `booleano`, `nulo`, `lista` y `tabla`, con errores claros cuando se mezclan tipos incompatibles.
- **Errores en español con número de línea**, en las etapas léxica, sintáctica y semántica.
- Variables, control de flujo, funciones definidas por el usuario y funciones incorporadas.

---

## Estructura del proyecto

```
terra/
  gramaticas/
    Terra.g4                # Gramatica del lenguaje (se edita a mano)
    TerraLexer.py           # Generado por ANTLR - no editar
    TerraParser.py          # Generado por ANTLR - no editar
    TerraVisitor.py         # Generado por ANTLR - no editar
  src/
    terra.py                # Punto de entrada: CLI y modo interactivo
    visitante_evaluador.py  # Semantica: Visitor y tabla de simbolos
    tabla.py                # Estructura Tabla, lector y escritor CSV
    operaciones.py          # Operaciones de datos y estadistica descriptiva
    manejador_errores.py    # Errores lexicos y sintacticos en espanol
    validador.py            # Validador interactivo de sintaxis
  ejemplos/                 # Programas de ejemplo (.terra)
  datos/                    # Conjuntos de datos
  salidas/                  # Archivos generados por los ejemplos
  tests/
    test_terra.py           # Pruebas del primer corte
    test_corte2.py          # Pruebas del segundo corte
  docs/                     # Informes y gramatica BNF
  generar.sh                # Regenera lexer, parser y visitor
  arbol.sh                  # Muestra el arbol de analisis
  requisitos.txt            # Dependencias
```

La arquitectura separa las responsabilidades:

| Módulo | Responsabilidad |
|---|---|
| `Terra.g4` | Sintaxis: qué programas son válidos |
| `visitante_evaluador.py` | Semántica: recorre el árbol, mantiene la tabla de símbolos y valida tipos |
| `operaciones.py` | Manipulación de tablas; no conoce el árbol de ANTLR |
| `tabla.py` | Representación de los datos y lectura/escritura de archivos |

---

## Requisitos

- Python 3.11 o superior
- Java (solo para generar el parser con ANTLR)
- `antlr4-python3-runtime` y `pytest` (en `requisitos.txt`)

---

## Instalación

**1. Clonar el repositorio**

```bash
git clone <url-del-repositorio>
cd terra
```

**2. Crear y activar el entorno virtual**

```bash
python3 -m venv venv
source venv/bin/activate
```

Hay que repetir el `source` en cada terminal nueva. Si aparece `Orden «python» no encontrada`, es porque el entorno no está activado.

**3. Instalar dependencias**

```bash
pip install -r requisitos.txt
```

**4. Generar el parser** (solo si se modifica la gramática)

```bash
chmod +x generar.sh arbol.sh
./generar.sh
```

`generar.sh` descarga el JAR de ANTLR 4.13.2 si no lo encuentra y genera `TerraLexer.py`, `TerraParser.py` y `TerraVisitor.py` dentro de `gramaticas/`.

---

## Uso

| Comando | Efecto |
|---|---|
| `python src/terra.py archivo.terra` | Ejecuta el programa |
| `python src/terra.py` | Modo interactivo (REPL) |
| `python src/terra.py archivo.terra --validar` | Solo verifica la sintaxis |
| `python src/terra.py archivo.terra --arbol` | Imprime el árbol de análisis |
| `python src/terra.py archivo.terra --tokens` | Lista los tokens reconocidos |
| `python src/validador.py` | Validador interactivo de construcciones |
| `./arbol.sh archivo.terra -gui` | Árbol en una ventana, exportable a PNG |
| `pytest tests/ -q` | Ejecuta todas las pruebas |

Terra solo ejecuta archivos con extensión `.terra`.

---

## El lenguaje

### Variables y tipos

```
fijo PI = 3.14159          # constante: no se puede reasignar
var contador = 0           # variable: se puede reasignar
contador = contador + 1

fijo nombre = "Colombia"
fijo activo = verdadero
fijo valores = [86.2, 92.5, 79.8]
fijo vacio = nulo
```

### Operadores

| Tipo | Operadores |
|---|---|
| Aritméticos | `+  -  *  /  %  ^` |
| Relacionales | `>  <  >=  <=  ==  !=` |
| Lógicos | `&&  \|\|  !` |
| Pertenencia | `en` (por ejemplo `x en [1, 2, 3]`) |

### Control de flujo y funciones

```
si co2 > 80:
    mostrar("alto")
sino si co2 > 50:
    mostrar("medio")
sino:
    mostrar("bajo")
fin

para valor en [1, 2, 3]:
    mostrar(valor)
fin

funcion per_capita(emisiones, habitantes):
    retornar emisiones * 1000000 / habitantes
fin
```

Los bloques se cierran con `fin`.

---

## Trabajo con datos

### Cargar

```
fijo datos = cargar "datos/emisiones_ejemplo.csv"
fijo otros = cargar "datos/archivo.csv" con separador ";" con encabezado falso
```

- El separador por defecto es la coma y el encabezado está activado.
- Sin encabezado, las columnas se llaman `col1`, `col2`, ...
- El tipo de cada columna se infiere automáticamente: booleano, número, decimal o texto.
- Las celdas vacías, `NA`, `null` o `nulo` se leen como `nulo`.
- Si el separador no corresponde al archivo, Terra lo detecta y lo indica.

### Tuberías

Cada operación recibe la tabla anterior y produce una nueva:

| Operación | Ejemplo |
|---|---|
| Seleccionar columnas | `\|> seleccionar [pais, anio, co2]` |
| Filtrar filas | `\|> filtrar donde anio >= 2018 && co2 > 50` |
| Crear columna calculada | `\|> crear total = co2 * 2` |
| Renombrar | `\|> renombrar energia_renovable como renovable` |
| Ordenar | `\|> ordenar por co2 desc` |
| Eliminar duplicados | `\|> eliminar duplicados` |
| Eliminar nulos | `\|> eliminar nulos` o `\|> eliminar nulos en [co2]` |
| Rellenar nulos | `\|> rellenar nulos en energia_renovable con 0.0` |
| Convertir tipo | `\|> convertir anio como texto` |
| Limitar filas | `\|> limitar 10` |
| Agrupar y resumir | `\|> agrupar por [pais] \|> resumir total = suma(co2)` |

Dentro de `filtrar` y `crear`, los nombres de las columnas se usan como variables de la fila actual.

### Agrupar y resumir

```
fijo por_pais = datos
    |> agrupar por [pais]
    |> resumir total = suma(co2),
               promedio = media(co2),
               mediana = mediana(co2),
               minimo = minimo(co2),
               maximo = maximo(co2),
               desviacion = desviacion(co2),
               registros = contar()
```

- Dentro de `resumir`, cada columna es la **lista de valores de su grupo**, así que se usan las mismas funciones que con cualquier lista.
- `contar()` sin argumentos devuelve el número de filas del grupo; `contar(columna)` cuenta los valores no nulos.
- Las agregaciones ignoran los nulos.
- `resumir` sin `agrupar` resume toda la tabla en una sola fila.
- Después de `agrupar` solo puede venir `resumir`.

### Describir

```
mostrar(describir(datos))
```

Devuelve una tabla con una fila por columna: conteo, nulos, media, desviación, mínimo, mediana y máximo para las columnas numéricas; valores distintos y el más frecuente para las de texto.

### Guardar

```
guardar resumen como "salidas/resumen.csv"
```

La carpeta de destino debe existir.

### Funciones incorporadas de estadística

| Función | Resultado |
|---|---|
| `suma(lista)` | Suma de los valores |
| `media(lista)` | Promedio |
| `mediana(lista)` | Valor central |
| `minimo(lista)` / `maximo(lista)` | Extremos |
| `desviacion(lista)` | Desviación estándar muestral |
| `contar()` / `contar(lista)` | Filas del grupo / cantidad de elementos |
| `redondear(valor, decimales)` | Redondeo |
| `describir(tabla)` | Resumen de cada columna |

---

## Decisiones de diseño

- **Las tuberías no modifican la tabla original.** Cada operación devuelve una tabla nueva, así un paso nunca altera en silencio un resultado anterior.
- **Nulos estrictos en operaciones, ignorados en agregaciones.** `co2 + 1` con un `co2` nulo es un error de tipos, para que los datos faltantes no pasen desapercibidos; en cambio `media(co2)` ignora los nulos, como en estadística descriptiva.
- **El tipo se infiere por columna, no por celda.** Así una columna nunca queda con números en unas filas y textos en otras.
- **`con encabezado falso` en lugar de `sin encabezado`.** Evita reservar la palabra `sin`, que en un lenguaje matemático puede ser una función.
- **Operadores lógicos simbólicos (`&&`, `||`, `!`).** Si `y` y `o` fueran palabras reservadas, no se podrían usar como nombres de variables.
- **Lector CSV con dos caminos.** Un autómata que maneja comillas, separadores dentro de campos y comillas escapadas; y un atajo para archivos sin comillas que da el mismo resultado y es mucho más rápido.

---

## Errores

Terra informa cada error con su línea y un mensaje en español:

```
Error en evaluacion: [linea 2] la columna 'temperatura' no existe. Columnas disponibles: pais, anio, co2, poblacion, energia_renovable
Error en evaluacion: [linea 2] la condicion de 'filtrar' debe ser booleana, se obtuvo decimal
Error en evaluacion: [linea 2] despues de 'agrupar' debe venir 'resumir'
Error en evaluacion: [linea 1] el archivo parece usar ',' como separador, no ';'. Revisa la opcion 'con separador'
```

---

## Ejemplos

| Archivo | Contenido |
|---|---|
| `01_variables.terra` | Variables y tipos |
| `02_operadores.terra` | Operadores y precedencia |
| `03_control.terra` | Condicionales y ciclos |
| `04_carga_seleccion.terra` | Carga y selección |
| `05_indicadores_ambientales.terra` | Indicadores con listas |
| `06_errores.terra` | Programa con errores intencionales |
| `07_carga_guardado.terra` | Cargar y guardar CSV |
| `08_tuberias.terra` | Preparación de datos con tuberías |
| `09_funciones.terra` | Funciones definidas por el usuario |
| `10_agrupacion.terra` | Agrupamiento y estadísticas por grupo |
| `11_describir.terra` | Resumen descriptivo |
| `12_opciones_carga.terra` | Separador y encabezado configurables |
| `13_caso_owid.terra` | Caso de estudio con datos reales |

```bash
python src/terra.py ejemplos/10_agrupacion.terra
```

---

## Caso de estudio: emisiones de CO₂

`13_caso_owid.terra` procesa el conjunto público de emisiones de CO₂ de **Our World in Data** (50 411 filas, 79 columnas, 254 países y regiones). El programa:

1. Deja solo países (los agregados regionales no tienen código ISO).
2. Analiza Sudamérica desde el año 2000 con `describir`.
3. Calcula indicadores por país con `agrupar` y `resumir`.
4. Muestra la evolución de Colombia desde 2010.
5. Lista los 10 países con más CO₂ por habitante en 2023.

Los resultados se guardan en `salidas/`. Todo el programa se ejecuta en unos 5 segundos.

El archivo está incluido en `datos/owid-co2-data.csv`. Para descargar una versión actualizada:

```bash
curl -L -o datos/owid-co2-data.csv https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv
```

Fuente: Our World in Data, *CO₂ and Greenhouse Gas Emissions* (https://github.com/owid/co2-data).

---

## Pruebas

```bash
pytest tests/ -q                    # todas (153)
pytest tests/test_corte2.py -v      # solo las del segundo corte (53)
```

Las pruebas cubren casos positivos y negativos: análisis léxico y sintáctico, tipos, variables, control de flujo, funciones, lectura de CSV con comillas y filas malformadas, cada operación de tubería, agregaciones, `describir` y los errores semánticos de cada instrucción.

---

## Estado por corte

| Corte | Contenido | Estado |
|---|---|---|
| Primero | Gramática, lexer y parser, variables, expresiones, control de flujo, funciones, errores léxicos y sintácticos | Completo |
| Segundo | Tabla y CSV desde cero, tuberías, agrupamiento, agregaciones, `describir`, errores semánticos, caso con datos reales | Completo |
| Tercero | Visualizaciones exportadas a PNG, CLI definitiva, caso de estudio final | Pendiente |

`graficar` ya se reconoce sintácticamente; su ejecución corresponde al tercer corte.
