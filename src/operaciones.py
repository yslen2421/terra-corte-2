"""
operaciones.py
==============
Operaciones de preparacion de datos de Terra sobre la clase Tabla.

Cada funcion recibe una Tabla y devuelve una Tabla NUEVA; la original
no se modifica.

Este modulo no conoce el arbol de ANTLR. Las operaciones que dependen
de una expresion del lenguaje (filtrar y crear) reciben una funcion
que el evaluador construye: dado el numero de fila, devuelve el
resultado de evaluar la expresion en esa fila. Asi la semantica del
lenguaje queda separada de la manipulacion de datos.
"""

from src.tabla import (Tabla, ErrorDatos, formatear_valor,
                       nombre_tipo_valor, _es_entero, _es_decimal,
                       VALORES_VERDADERO, VALORES_FALSO)

TIPOS_CELDA = (bool, int, float, str)


def seleccionar(tabla: Tabla, nombres: list) -> Tabla:
    """Deja solo las columnas indicadas, en el orden indicado."""
    indices = [tabla.indice(n) for n in nombres]
    filas = [[fila[j] for j in indices] for fila in tabla.filas]
    return Tabla(nombres, filas)


def filtrar(tabla: Tabla, condicion) -> Tabla:
    """Conserva las filas i para las que condicion(i) es verdadero."""
    filas = [fila for i, fila in enumerate(tabla.filas) if condicion(i)]
    return Tabla(tabla.columnas, filas)


def crear(tabla: Tabla, nombre: str, calcular) -> Tabla:
    """
    Agrega una columna calculada con calcular(i) para cada fila i.
    Si la columna ya existe, se reemplaza su contenido.
    """
    valores = [calcular(i) for i in range(tabla.num_filas)]
    for v in valores:
        if v is not None and not isinstance(v, TIPOS_CELDA):
            raise ErrorDatos(
                f"la columna '{nombre}' solo puede guardar numeros, "
                f"decimales, textos, booleanos o nulos")

    if tabla.tiene_columna(nombre):
        j = tabla.indice(nombre)
        filas = [fila[:j] + [v] + fila[j + 1:]
                 for fila, v in zip(tabla.filas, valores)]
        return Tabla(tabla.columnas, filas)

    filas = [fila + [v] for fila, v in zip(tabla.filas, valores)]
    return Tabla(tabla.columnas + [nombre], filas)


def renombrar(tabla: Tabla, viejo: str, nuevo: str) -> Tabla:
    """Cambia el nombre de una columna."""
    tabla.indice(viejo)
    if nuevo != viejo and tabla.tiene_columna(nuevo):
        raise ErrorDatos(
            f"no se puede renombrar '{viejo}' como '{nuevo}': "
            f"ya existe una columna con ese nombre")
    columnas = [nuevo if c == viejo else c for c in tabla.columnas]
    return Tabla(columnas, tabla.filas)


def ordenar(tabla: Tabla, nombre: str, descendente: bool = False) -> Tabla:
    """
    Ordena las filas por una columna. Los nulos siempre van al final.
    El orden es estable: filas con el mismo valor conservan su orden.
    """
    j = tabla.indice(nombre)
    con_valor = [f for f in tabla.filas if f[j] is not None]
    nulas = [f for f in tabla.filas if f[j] is None]
    try:
        con_valor = sorted(con_valor, key=lambda f: f[j],
                           reverse=descendente)
    except TypeError:
        raise ErrorDatos(
            f"no se puede ordenar por '{nombre}': la columna mezcla "
            f"tipos que no se pueden comparar")
    return Tabla(tabla.columnas, con_valor + nulas)


def eliminar_duplicados(tabla: Tabla) -> Tabla:
    """Quita las filas repetidas, conservando la primera aparicion."""
    vistas = set()
    filas = []
    for fila in tabla.filas:
        clave = tuple(fila)
        if clave not in vistas:
            vistas.add(clave)
            filas.append(fila)
    return Tabla(tabla.columnas, filas)


def eliminar_nulos(tabla: Tabla, nombres: list = None) -> Tabla:
    """
    Quita las filas que tengan nulos en las columnas indicadas.
    Sin columnas, revisa todas.
    """
    nombres = nombres if nombres else tabla.columnas
    indices = [tabla.indice(n) for n in nombres]
    filas = [f for f in tabla.filas
             if all(f[j] is not None for j in indices)]
    return Tabla(tabla.columnas, filas)


def rellenar_nulos(tabla: Tabla, nombre: str, valor) -> Tabla:
    """Reemplaza los nulos de una columna por un valor del mismo tipo."""
    j = tabla.indice(nombre)

    if valor is None:
        raise ErrorDatos("no se puede rellenar nulos con nulo")
    if not isinstance(valor, TIPOS_CELDA):
        raise ErrorDatos(
            "solo se puede rellenar con un numero, decimal, texto "
            "o booleano")

    tipo_col = tabla.tipo_columna(nombre)
    tipo_val = nombre_tipo_valor(valor)
    numericos = ("numero", "decimal")

    if tipo_col == "decimal" and tipo_val == "numero":
        valor = float(valor)
    elif tipo_col in ("nulo", "mixto"):
        pass
    elif tipo_col in numericos and tipo_val in numericos:
        pass
    elif tipo_col != tipo_val:
        raise ErrorDatos(
            f"no se puede rellenar la columna '{nombre}' (de tipo "
            f"{tipo_col}) con un valor de tipo {tipo_val}")

    filas = [f[:j] + [valor if f[j] is None else f[j]] + f[j + 1:]
             for f in tabla.filas]
    return Tabla(tabla.columnas, filas)


def _convertir_valor(valor, tipo: str, nombre: str):
    """Convierte una celda al tipo de Terra indicado."""
    if valor is None:
        return None

    error = ErrorDatos(
        f"no se puede convertir el valor '{formatear_valor(valor)}' "
        f"de la columna '{nombre}' a {tipo}")

    if tipo == "texto":
        if isinstance(valor, bool):
            return "verdadero" if valor else "falso"
        return str(valor)

    if tipo == "booleano":
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, str):
            t = valor.strip().lower()
            if t in VALORES_VERDADERO:
                return True
            if t in VALORES_FALSO:
                return False
        raise error

    # numero y decimal no aceptan booleanos
    if isinstance(valor, bool):
        raise error

    if tipo == "numero":
        if isinstance(valor, int):
            return valor
        if isinstance(valor, float):
            return int(valor)            # se descarta la parte decimal
        texto = valor.strip()
        if _es_entero(texto):
            return int(texto)
        if _es_decimal(texto):
            return int(float(texto))
        raise error

    if tipo == "decimal":
        if isinstance(valor, (int, float)):
            return float(valor)
        texto = valor.strip()
        if _es_decimal(texto):
            return float(texto)
        raise error

    raise ErrorDatos(f"tipo desconocido '{tipo}'")


def convertir(tabla: Tabla, nombre: str, tipo: str) -> Tabla:
    """Convierte todos los valores de una columna a otro tipo."""
    j = tabla.indice(nombre)
    filas = [f[:j] + [_convertir_valor(f[j], tipo, nombre)] + f[j + 1:]
             for f in tabla.filas]
    return Tabla(tabla.columnas, filas)


def limitar(tabla: Tabla, n: int) -> Tabla:
    """Deja solo las primeras n filas."""
    return Tabla(tabla.columnas, tabla.filas[:n])


# ---------------------------------------------------------------------
# AGRUPAMIENTO
# ---------------------------------------------------------------------

class Agrupada:
    """
    Resultado de 'agrupar por'. Guarda la tabla, las columnas clave y
    los grupos, a la espera de 'resumir'. No es una Tabla: la unica
    operacion que puede venir despues es 'resumir'.

    grupos: lista de (valores_clave, [indices de filas]) en el orden en
    que cada grupo aparece por primera vez.
    """

    def __init__(self, tabla, claves, grupos):
        self.tabla = tabla
        self.claves = claves
        self.grupos = grupos

    def __repr__(self):
        return (f"Agrupada por {', '.join(self.claves)} "
                f"({len(self.grupos)} grupos)")


def agrupar(tabla: Tabla, claves: list) -> Agrupada:
    """Reune las filas que comparten los mismos valores en las claves."""
    if len(set(claves)) != len(claves):
        raise ErrorDatos("una columna aparece repetida en 'agrupar por'")
    indices_clave = [tabla.indice(c) for c in claves]

    grupos = {}
    for i, fila in enumerate(tabla.filas):
        clave = tuple(fila[j] for j in indices_clave)
        grupos.setdefault(clave, []).append(i)

    return Agrupada(tabla, list(claves), list(grupos.items()))


# ---------------------------------------------------------------------
# ESTADISTICA DESCRIPTIVA (desde cero)
# ---------------------------------------------------------------------

def _media(valores: list) -> float:
    return sum(valores) / len(valores)


def _mediana(valores: list):
    ordenados = sorted(valores)
    n = len(ordenados)
    centro = n // 2
    if n % 2 == 1:
        return ordenados[centro]
    return (ordenados[centro - 1] + ordenados[centro]) / 2


def _desviacion(valores: list):
    """Desviacion estandar muestral (divide entre n - 1)."""
    if len(valores) < 2:
        return None
    m = _media(valores)
    return (sum((x - m) ** 2 for x in valores) / (len(valores) - 1)) ** 0.5


def describir(tabla: Tabla) -> Tabla:
    """
    Resumen de cada columna de la tabla.

    Numericas: conteo, nulos, media, desviacion, minimo, mediana, maximo.
    Texto y booleanas: conteo, nulos, valores distintos y el mas
    frecuente (si hay empate, gana el que aparece primero).
    Lo que no aplica a un tipo de columna queda como nulo.
    """
    columnas = ["columna", "tipo", "conteo", "nulos",
                "media", "desviacion", "minimo", "mediana", "maximo",
                "distintos", "mas_frecuente"]
    filas = []

    for nombre in tabla.columnas:
        valores = tabla.columna(nombre)
        presentes = [v for v in valores if v is not None]
        tipo = tabla.tipo_columna(nombre)
        fila = [nombre, tipo, len(presentes), len(valores) - len(presentes)]

        if tipo in ("numero", "decimal") and presentes:
            fila += [_media(presentes), _desviacion(presentes),
                     min(presentes), _mediana(presentes), max(presentes),
                     None, None]
        else:
            frecuencias = {}
            for v in presentes:
                frecuencias[v] = frecuencias.get(v, 0) + 1
            moda = None
            if frecuencias:
                moda = formatear_valor(max(frecuencias, key=frecuencias.get))
            fila += [None, None, None, None, None, len(frecuencias), moda]

        filas.append(fila)

    return Tabla(columnas, filas)
