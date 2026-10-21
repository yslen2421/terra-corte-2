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
- **Librería matemática y de matrices desde cero:** seno, coseno, exponencial y logaritmos por series de Taylor; determinante e inversa por eliminación de Gauss.
- **Funciones como valores:** funciones anónimas (`funcion(x) => x * 2`) y de orden superior (`mapear`, `filtro`, `reducir`...).
- **Gestor de memoria** con límite de recursión configurable, consulta de memoria y liberación de variables.
- **Entrada por teclado**, archivos de texto y combinación de tablas (`unir`, `concatenar`).
- **Ayuda integrada:** `ayuda()` muestra cómo se escribe cada instrucción, con ejemplos.

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
    biblioteca.py           # Catalogo de funciones incorporadas y ayuda()
    matematicas.py          # Series de Taylor, vectores y matrices
    memoria.py              # Gestor de memoria y limite de recursion
    manejador_errores.py    # Errores lexicos y sintacticos en espanol
    validador.py            # Validador interactivo de sintaxis
  ejemplos/                 # Programas de ejemplo (.terra)
  datos/                    # Conjuntos de datos
  salidas/                  # Archivos generados por los ejemplos
  tests/
    test_terra.py           # Pruebas del primer corte
    test_corte2.py          # Pruebas del segundo corte (datos)
    test_biblioteca.py      # Pruebas de matematicas, memoria, orden superior...
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
| `biblioteca.py` | Registro de las funciones incorporadas; agregar una función no requiere tocar la gramática |
| `matematicas.py` / `memoria.py` | Cálculo numérico y control de recursos |

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

Dentro de Terra, `ayuda()` lista todas las categorías, `ayuda("matrices")` muestra las funciones de una categoría y `ayuda("mapear")` explica una función con un ejemplo.

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

### Textos

Los textos van entre comillas dobles y admiten las secuencias de escape `\n` (salto de línea), `\t` (tabulador), `\"` (comilla) y `\\` (barra invertida).

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

## Matemáticas y matrices

Todas las funciones están implementadas sin `import math`.

| Función | Resultado |
|---|---|
| `pi()`, `e()` | Constantes |
| `seno(x)`, `coseno(x)`, `tangente(x)` | Trigonométricas (radianes), por series de Taylor con reducción del ángulo |
| `exp(x)`, `ln(x)`, `log(x)`, `log(x, base)` | Exponencial y logaritmos |
| `piso(x)`, `techo(x)`, `factorial(n)` | Redondeos y factorial |
| `aleatorio()`, `semilla(n)` | Generador congruencial lineal reproducible |
| `matriz(f, c, v)`, `ceros(f, c)`, `unos(f, c)`, `identidad(n)`, `aleatoria(f, c)` | Crear matrices |
| `dimension(M)`, `transpuesta(M)`, `traza(M)` | Consultas |
| `mult_matriz(A, B)`, `sumar_matrices(A, B)`, `restar_matrices(A, B)`, `escalar(k, M)` | Operaciones |
| `determinante(M)`, `inversa(M)` | Eliminación de Gauss y Gauss-Jordan |
| `producto_punto(a, b)`, `norma(v)` | Vectores |

```
fijo A = [[4, 7], [2, 6]]
mostrar(determinante(A))               # 10.0
mostrar(mult_matriz(A, inversa(A)))    # [[1.0, 0.0], [0.0, 1.0]]
```

## Funciones anónimas y de orden superior

```
fijo doble = funcion(x) => x * 2
mapear([1, 2, 3], doble)                          # [2, 4, 6]
filtro(rango(1, 11), funcion(n) => n % 2 == 0)    # [2, 4, 6, 8, 10]
reducir([1, 2, 3, 4], funcion(a, b) => a + b)     # 10
mapear([1, 4, 9], raiz)                           # una funcion con nombre tambien es un valor
```

| Función | Resultado |
|---|---|
| `mapear(lista, f)` | Aplica `f` a cada elemento |
| `filtro(lista, f)` | Elementos donde `f` es verdadero |
| `reducir(lista, f [, inicial])` | Combina la lista en un valor |
| `ordenar_por(lista, f [, "desc"])` | Ordena según `f` |
| `todos(lista, f)`, `alguno(lista, f)` | Cuantificadores |
| `componer(f, g)`, `aplicar(f, ...)` | `f(g(x))` y llamada indirecta |
| `aplicar_matriz(M, f)` | Aplica `f` a cada celda |
| `rango(fin)`, `rango(inicio, fin [, paso])` | Lista de enteros |

Una función anónima puede usar las variables del programa (`funcion(x) => x * factor`). La función se llama `filtro` y no `filtrar` porque `filtrar` es parte de las tuberías.

## Memoria y recursión

| Función | Resultado |
|---|---|
| `memoria_info()` | Tabla con cada variable, su tipo, elementos y memoria estimada |
| `memoria_estado()` | Variables, funciones, llamadas anidadas y límites |
| `liberar("x")` | Elimina una variable |
| `fijar_limite_recursion(n)` | Cambia el límite de llamadas anidadas (por defecto 200, máximo 2000) |

Una recursión infinita se detiene con un mensaje en español en lugar de un error de Python, y las matrices de más de 5 millones de celdas se rechazan antes de crearse.

## Entrada, tablas y archivos

| Función | Resultado |
|---|---|
| `leer("mensaje")`, `leer_numero("mensaje")` | Lectura por teclado; `leer_numero` repite la pregunta si no recibe un número |
| `columna(t, "co2")` | Una columna como lista (para usar con `media`, `mapear`, etc.) |
| `nombres(t)`, `num_filas(t)`, `fila(t, i)`, `valores_unicos(t, "col")` | Estructura de una tabla |
| `tabla_desde(columnas, filas)` | Crea una tabla |
| `a_matriz(t [, columnas])` | Tabla numérica a matriz |
| `unir(t1, t2, "clave" [, "izquierda"])` | Une tablas por una columna |
| `concatenar(t1, t2)` | Filas de `t2` debajo de las de `t1` |
| `leer_archivo`, `leer_lineas`, `escribir_archivo`, `agregar_archivo`, `existe_archivo`, `borrar_archivo` | Archivos de texto |

`guardar` también acepta separador: `guardar d como "x.csv" con separador ";"`.

Una tubería dentro de los argumentos de una función va entre paréntesis: `unir((d |> filtrar donde anio == 2021), metas, "pais")`.

---

## Decisiones de diseño

- **Las tuberías no modifican la tabla original.** Cada operación devuelve una tabla nueva, así un paso nunca altera en silencio un resultado anterior.
- **Nulos estrictos en operaciones, ignorados en agregaciones.** `co2 + 1` con un `co2` nulo es un error de tipos, para que los datos faltantes no pasen desapercibidos; en cambio `media(co2)` ignora los nulos, como en estadística descriptiva.
- **El tipo se infiere por columna, no por celda.** Así una columna nunca queda con números en unas filas y textos en otras.
- **`con encabezado falso` en lugar de `sin encabezado`.** Evita reservar la palabra `sin`, que en un lenguaje matemático puede ser una función.
- **Operadores lógicos simbólicos (`&&`, `||`, `!`).** Si `y` y `o` fueran palabras reservadas, no se podrían usar como nombres de variables.
- **Catálogo de funciones separado del evaluador.** Las funciones nuevas se registran en `biblioteca.py` con su nombre y número de argumentos; no hace falta tocar la gramática.
- **Funciones como valores.** El nombre de una función sin paréntesis es un valor, y `funcion(x) => ...` reutiliza la palabra reservada `funcion` sin agregar otra.
- **Límite de recursión de Terra antes que el de Python.** El gestor de memoria ajusta la pila de Python para que el usuario siempre vea el mensaje de Terra.
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
| `14_matematicas.terra` | Trigonometría, logaritmos y álgebra lineal |
| `15_memoria_recursion.terra` | Recursión, consulta y liberación de memoria |
| `16_orden_superior.terra` | Funciones anónimas y de orden superior |
| `17_entrada.terra` | Calculadora de huella de carbono por teclado |
| `18_tablas_archivos.terra` | Unir y concatenar tablas, matrices desde tablas y archivos de texto |

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
pytest tests/ -q                      # todas (207)
pytest tests/test_corte2.py -v        # datos del segundo corte (53)
pytest tests/test_biblioteca.py -v    # matematicas, memoria, orden superior... (54)
```

Las pruebas cubren casos positivos y negativos: análisis léxico y sintáctico, tipos, variables, control de flujo, funciones, lectura de CSV con comillas y filas malformadas, cada operación de tubería, agregaciones, `describir` y los errores semánticos de cada instrucción.

---

## Estado por corte

| Corte | Contenido | Estado |
|---|---|---|
| Primero | Gramática, lexer y parser, variables, expresiones, control de flujo, funciones, errores léxicos y sintácticos | Completo |
| Segundo | Tabla y CSV desde cero, tuberías, agrupamiento, agregaciones, `describir`, errores semánticos, caso con datos reales, matemáticas y matrices, gestor de memoria, orden superior, entrada por teclado, archivos y `ayuda()` | Completo |
| Tercero | Visualizaciones exportadas a PNG, CLI definitiva, caso de estudio final | Pendiente |

`graficar` ya se reconoce sintácticamente; su ejecución corresponde al tercer corte.
