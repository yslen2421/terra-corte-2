"""
memoria.py
==========
Gestor de memoria de Terra.

Se encarga de cuatro cosas:

    1. Limite de recursion. Terra cuenta cuantas llamadas a funciones
       del usuario estan abiertas al mismo tiempo (evaluador.profundidad)
       y corta con un mensaje claro al pasar del limite. Como cada
       llamada de Terra usa varios niveles de la pila de Python (un nivel
       por cada regla de la gramatica que se recorre), el gestor tambien
       ajusta el limite de Python para que el de Terra se alcance primero.

    2. Limite de tamano. Las matrices y tablas que se crean con funciones
       de la biblioteca no pueden pasar de un numero maximo de celdas.

    3. Consulta. memoria_info() devuelve una tabla con cada variable, su
       tipo, cuantos elementos guarda y un estimado de cuanto ocupa.

    4. Liberacion. liberar("x") elimina una variable de la tabla de
       simbolos para que su contenido se pueda descartar.

El tamano en bytes es un estimado propio, calculado con el tamano
aproximado de cada tipo de valor en Python; no usa ninguna libreria.
"""

import sys

from src.tabla import Tabla, ErrorDatos

# Niveles de la pila de Python que puede usar, como maximo, una llamada
# a una funcion de Terra (recorrido del arbol desde la sentencia hasta
# la llamada, ida y vuelta por accept/visit).
NIVELES_PYTHON_POR_LLAMADA = 120

LIMITE_RECURSION_MAXIMO = 2000
LIMITE_CELDAS = 5_000_000

# Tamanos aproximados de cada valor en Python (64 bits)
_BYTES = {"numero": 28, "decimal": 24, "booleano": 28, "nulo": 16}
_BYTES_TEXTO_BASE = 49
_BYTES_LISTA_BASE = 56
_BYTES_REFERENCIA = 8


def _tipo(valor) -> str:
    if valor is None:
        return "nulo"
    if isinstance(valor, bool):
        return "booleano"
    if isinstance(valor, int):
        return "numero"
    if isinstance(valor, float):
        return "decimal"
    if isinstance(valor, str):
        return "texto"
    if isinstance(valor, list):
        if valor and all(isinstance(f, list) for f in valor):
            return "matriz"
        return "lista"
    if isinstance(valor, Tabla):
        return "tabla"
    return "funcion"


def contar_elementos(valor) -> int:
    """Cuantos valores simples guarda: 1 para un numero, n para una lista."""
    if isinstance(valor, list):
        return sum(contar_elementos(v) for v in valor)
    if isinstance(valor, Tabla):
        return valor.num_filas * valor.num_columnas
    return 1


def estimar_bytes(valor) -> int:
    """Estimado de la memoria que ocupa un valor, recorriendolo completo."""
    tipo = _tipo(valor)
    if tipo in _BYTES:
        return _BYTES[tipo]
    if tipo == "texto":
        return _BYTES_TEXTO_BASE + len(valor)
    if tipo in ("lista", "matriz"):
        return (_BYTES_LISTA_BASE + _BYTES_REFERENCIA * len(valor)
                + sum(estimar_bytes(v) for v in valor))
    if tipo == "tabla":
        total = _BYTES_LISTA_BASE * (1 + valor.num_filas)
        total += sum(estimar_bytes(c) for c in valor.columnas)
        for fila in valor.filas:
            total += _BYTES_REFERENCIA * len(fila)
            total += sum(estimar_bytes(v) for v in fila)
        return total
    return 0


def _formato_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


class GestorMemoria:
    """Limites y consultas de memoria de un evaluador."""

    def __init__(self, evaluador):
        self.evaluador = evaluador
        self.limite_celdas = LIMITE_CELDAS
        self.ajustar_pila(evaluador.LIMITE_RECURSION)

    # ------------------------------------------------------------ recursion

    def ajustar_pila(self, limite_terra: int) -> None:
        """
        Sube el limite de la pila de Python lo suficiente para que el
        limite de recursion de Terra se alcance antes. Asi el usuario ve
        el mensaje de Terra y no un RecursionError de Python.
        """
        necesario = limite_terra * NIVELES_PYTHON_POR_LLAMADA + 1000
        if sys.getrecursionlimit() < necesario:
            sys.setrecursionlimit(necesario)

    def fijar_limite_recursion(self, n) -> None:
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise ErrorDatos(
                "fijar_limite_recursion() necesita un numero entero mayor "
                "que 0")
        if n > LIMITE_RECURSION_MAXIMO:
            raise ErrorDatos(
                f"fijar_limite_recursion(): el maximo permitido es "
                f"{LIMITE_RECURSION_MAXIMO}")
        self.evaluador.LIMITE_RECURSION = n
        self.ajustar_pila(n)

    # ------------------------------------------------------------ tamano

    def validar_celdas(self, celdas: int, que: str) -> None:
        if celdas > self.limite_celdas:
            raise ErrorDatos(
                f"{que} tendria {celdas} celdas y el limite de memoria es "
                f"{self.limite_celdas}")

    # ------------------------------------------------------------ consultas

    def info(self) -> Tabla:
        """
        Tabla con las variables visibles, de la que mas ocupa a la que
        menos, y una ultima fila con el total.
        """
        filas = []
        total_elementos = 0
        total_bytes = 0
        for nombre, entrada in self.evaluador.memoria.items():
            valor = entrada["valor"]
            elementos = contar_elementos(valor)
            tamano = estimar_bytes(valor)
            total_elementos += elementos
            total_bytes += tamano
            filas.append([nombre, _tipo(valor),
                          "var" if entrada["mutable"] else "fijo",
                          elementos, tamano])

        filas.sort(key=lambda f: f[4], reverse=True)
        filas = [f[:4] + [_formato_bytes(f[4])] for f in filas]
        filas.append(["TOTAL", "", "", total_elementos,
                      _formato_bytes(total_bytes)])
        return Tabla(["variable", "tipo", "clase", "elementos", "memoria"],
                     filas)

    def estado(self) -> Tabla:
        """Limites configurados y uso actual."""
        ev = self.evaluador
        return Tabla(["indicador", "valor"], [
            ["variables declaradas", len(ev.memoria)],
            ["funciones definidas", len(ev.funciones)],
            ["llamadas anidadas ahora", ev.profundidad],
            ["limite de recursion", ev.LIMITE_RECURSION],
            ["limite de celdas", self.limite_celdas],
        ])

    def liberar(self, nombre) -> None:
        """Elimina una variable; despues se puede volver a declarar."""
        if not isinstance(nombre, str):
            raise ErrorDatos(
                "liberar() recibe el nombre de la variable como texto, "
                "por ejemplo liberar(\"datos\")")
        if nombre not in self.evaluador.memoria:
            raise ErrorDatos(f"no existe la variable '{nombre}' para liberar")
        del self.evaluador.memoria[nombre]
