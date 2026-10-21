"""
matematicas.py
==============
Libreria matematica de Terra, escrita desde cero (sin el modulo math).

Contiene dos grupos de funciones:

    1. Funciones de una variable: seno, coseno, tangente, exp, ln, log,
       piso, techo y factorial. Se calculan con series de Taylor y
       reduccion de rango, que es la misma idea que usan las
       calculadoras: llevar el numero a un intervalo pequeno donde la
       serie converge rapido.

    2. Algebra lineal: vectores (listas de numeros) y matrices (listas
       de listas de numeros con filas del mismo tamano).

Las funciones de este modulo trabajan con valores de Python y lanzan
ErrorDatos cuando algo no es valido. El evaluador las registra como
funciones incorporadas y convierte ese error en ErrorSemantico con la
linea del programa.
"""

from src.tabla import ErrorDatos

PI = 3.141592653589793
E = 2.718281828459045
_EPSILON = 1e-17          # cuando un termino de la serie es menor, se para
_MAX_TERMINOS = 200       # seguro contra ciclos infinitos


# ---------------------------------------------------------------------
# VALIDACIONES
# ---------------------------------------------------------------------

def es_numero(x) -> bool:
    """Numero o decimal de Terra (los booleanos no cuentan)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def numero(x, funcion: str):
    if not es_numero(x):
        raise ErrorDatos(f"{funcion}() necesita un numero")
    return x


def entero_no_negativo(x, funcion: str, que: str = "el argumento") -> int:
    if isinstance(x, bool) or not isinstance(x, int) or x < 0:
        raise ErrorDatos(
            f"{funcion}(): {que} debe ser un numero entero mayor o igual a 0")
    return x


def vector(v, funcion: str, nombre: str = "el vector") -> list:
    """Lista no vacia de numeros."""
    if not isinstance(v, list) or not v:
        raise ErrorDatos(f"{funcion}(): {nombre} debe ser una lista no vacia")
    for x in v:
        if not es_numero(x):
            raise ErrorDatos(
                f"{funcion}(): {nombre} solo puede contener numeros")
    return v


def matriz(M, funcion: str, nombre: str = "la matriz"):
    """
    Valida una matriz y devuelve (filas, columnas).
    Una matriz es una lista no vacia de filas no vacias, todas del mismo
    tamano y con solo numeros.
    """
    if not isinstance(M, list) or not M:
        raise ErrorDatos(f"{funcion}(): {nombre} debe ser una lista de filas")
    if not all(isinstance(f, list) and f for f in M):
        raise ErrorDatos(
            f"{funcion}(): {nombre} debe ser una lista de listas no vacias")
    columnas = len(M[0])
    for fila in M:
        if len(fila) != columnas:
            raise ErrorDatos(
                f"{funcion}(): {nombre} tiene filas de distinto tamano")
        for x in fila:
            if not es_numero(x):
                raise ErrorDatos(
                    f"{funcion}(): {nombre} solo puede contener numeros")
    return len(M), columnas


def _limpiar(x: float) -> float:
    """
    Quita el ruido de redondeo de la aritmetica de punto flotante:
    1.2e-16 pasa a 0 y 0.9999999999999996 pasa a 1.0.
    """
    if abs(x) < 1e-12:
        return 0.0
    return round(x, 12)


def _pulir(x):
    """Limpia el ruido de redondeo solo en decimales; los enteros quedan igual."""
    return _limpiar(x) if isinstance(x, float) else x


# ---------------------------------------------------------------------
# FUNCIONES DE UNA VARIABLE
# ---------------------------------------------------------------------

def _reducir_angulo(x: float) -> float:
    """Lleva un angulo al intervalo [-pi, pi], donde la serie converge rapido."""
    dos_pi = 2 * PI
    x = x - dos_pi * int(x / dos_pi)
    if x > PI:
        x -= dos_pi
    elif x < -PI:
        x += dos_pi
    return x


def seno(x) -> float:
    """sen(x) = x - x^3/3! + x^5/5! - ...   (x en radianes)"""
    x = _reducir_angulo(float(numero(x, "seno")))
    termino = x
    total = x
    n = 1
    while abs(termino) > _EPSILON and n < _MAX_TERMINOS:
        termino *= -x * x / ((2 * n) * (2 * n + 1))
        total += termino
        n += 1
    return _limpiar(total)


def coseno(x) -> float:
    """cos(x) = 1 - x^2/2! + x^4/4! - ...   (x en radianes)"""
    x = _reducir_angulo(float(numero(x, "coseno")))
    termino = 1.0
    total = 1.0
    n = 1
    while abs(termino) > _EPSILON and n < _MAX_TERMINOS:
        termino *= -x * x / ((2 * n - 1) * (2 * n))
        total += termino
        n += 1
    return _limpiar(total)


def tangente(x) -> float:
    """tan(x) = sen(x) / cos(x); no existe donde el coseno vale 0."""
    numero(x, "tangente")
    c = coseno(x)
    if c == 0:
        raise ErrorDatos(
            "tangente() no esta definida en ese angulo (el coseno vale 0)")
    return _limpiar(seno(x) / c)


def exp(x) -> float:
    """
    e^x con la serie 1 + x + x^2/2! + ...

    Para que la serie converja rapido se usa e^x = (e^(x/2^k))^(2^k):
    se divide x hasta que sea pequeno y al final se eleva al cuadrado
    k veces.
    """
    x = float(numero(x, "exp"))
    if x > 709:
        raise ErrorDatos("exp(): el resultado es demasiado grande")
    if x < 0:
        return 1.0 / exp(-x) if x > -745 else 0.0
    k = 0
    while x > 0.5:
        x /= 2
        k += 1
    termino = 1.0
    total = 1.0
    n = 1
    while abs(termino) > _EPSILON and n < _MAX_TERMINOS:
        termino *= x / n
        total += termino
        n += 1
    for _ in range(k):
        total *= total
    return total


def _ln_reducido(m: float) -> float:
    """
    ln(m) para m cercano a 1, con ln(m) = 2 * atanh((m - 1) / (m + 1)):
    ln(m) = 2 * (y + y^3/3 + y^5/5 + ...),  con y = (m - 1) / (m + 1)
    """
    y = (m - 1) / (m + 1)
    y2 = y * y
    potencia = y
    total = 0.0
    n = 1
    while abs(potencia / n) > _EPSILON and n < 2 * _MAX_TERMINOS:
        total += potencia / n
        potencia *= y2
        n += 2
    return 2 * total


_LN2 = _ln_reducido(2.0)


def ln(x) -> float:
    """
    Logaritmo natural. Se escribe x = m * 2^k con m en [0.5, 1), asi
    ln(x) = k * ln(2) + ln(m), y ln(m) converge rapido.
    """
    x = float(numero(x, "ln"))
    if x <= 0:
        raise ErrorDatos("ln() solo esta definido para numeros mayores que 0")
    k = 0
    while x >= 1:
        x /= 2
        k += 1
    while x < 0.5:
        x *= 2
        k -= 1
    return _limpiar(k * _LN2 + _ln_reducido(x))


def log(x, base=10) -> float:
    """Logaritmo en cualquier base (10 por defecto)."""
    numero(x, "log")
    numero(base, "log")
    if base <= 0 or base == 1:
        raise ErrorDatos("log(): la base debe ser mayor que 0 y distinta de 1")
    resultado = ln(x) / ln(base)
    redondo = round(resultado)
    # log(1000) debe dar 3 y no 2.9999999999999996
    if abs(resultado - redondo) < 1e-12:
        return float(redondo)
    return resultado


def piso(x) -> int:
    """Mayor entero menor o igual a x."""
    x = numero(x, "piso")
    n = int(x)
    return n - 1 if x < 0 and n != x else n


def techo(x) -> int:
    """Menor entero mayor o igual a x."""
    x = numero(x, "techo")
    n = int(x)
    return n + 1 if x > 0 and n != x else n


def factorial(n) -> int:
    n = entero_no_negativo(n, "factorial")
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado


# ---------------------------------------------------------------------
# NUMEROS ALEATORIOS (generador congruencial lineal)
# ---------------------------------------------------------------------

class GeneradorAleatorio:
    """
    x(n+1) = (a * x(n) + c) mod m, con las constantes de Numerical Recipes.
    Con la misma semilla produce siempre la misma secuencia, lo que hace
    reproducibles los programas y las pruebas.
    """
    A = 1664525
    C = 1013904223
    M = 2 ** 32

    def __init__(self, semilla: int = 12345):
        self.estado = semilla % self.M

    def semilla(self, n):
        self.estado = entero_no_negativo(n, "semilla") % self.M

    def siguiente(self) -> float:
        """Decimal en [0, 1)."""
        self.estado = (self.A * self.estado + self.C) % self.M
        return self.estado / self.M


GENERADOR = GeneradorAleatorio()


def aleatorio() -> float:
    return GENERADOR.siguiente()


# ---------------------------------------------------------------------
# VECTORES
# ---------------------------------------------------------------------

def producto_punto(a, b) -> float:
    vector(a, "producto_punto", "el primer vector")
    vector(b, "producto_punto", "el segundo vector")
    if len(a) != len(b):
        raise ErrorDatos(
            f"producto_punto(): los vectores tienen tamanos distintos "
            f"({len(a)} y {len(b)})")
    return sum(x * y for x, y in zip(a, b))


def norma(v) -> float:
    vector(v, "norma")
    return sum(x * x for x in v) ** 0.5


# ---------------------------------------------------------------------
# MATRICES
# ---------------------------------------------------------------------

def crear_matriz(filas, columnas, valor=0):
    entero_no_negativo(filas, "matriz", "el numero de filas")
    entero_no_negativo(columnas, "matriz", "el numero de columnas")
    if filas == 0 or columnas == 0:
        raise ErrorDatos("matriz(): las dimensiones deben ser mayores que 0")
    numero(valor, "matriz")
    return [[valor] * columnas for _ in range(filas)]


def identidad(n):
    entero_no_negativo(n, "identidad", "el tamano")
    if n == 0:
        raise ErrorDatos("identidad(): el tamano debe ser mayor que 0")
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def matriz_aleatoria(filas, columnas):
    M = crear_matriz(filas, columnas)
    return [[aleatorio() for _ in fila] for fila in M]


def dimension(M):
    f, c = matriz(M, "dimension")
    return [f, c]


def transpuesta(M):
    f, c = matriz(M, "transpuesta")
    return [[M[i][j] for i in range(f)] for j in range(c)]


def sumar_matrices(A, B, signo=1):
    nombre = "sumar_matrices" if signo == 1 else "restar_matrices"
    fa, ca = matriz(A, nombre, "la primera matriz")
    fb, cb = matriz(B, nombre, "la segunda matriz")
    if (fa, ca) != (fb, cb):
        raise ErrorDatos(
            f"{nombre}(): las matrices deben tener la misma dimension "
            f"({fa}x{ca} y {fb}x{cb})")
    return [[A[i][j] + signo * B[i][j] for j in range(ca)] for i in range(fa)]


def mult_matriz(A, B):
    """Producto matricial: (f x n) por (n x c) da (f x c)."""
    fa, ca = matriz(A, "mult_matriz", "la primera matriz")
    fb, cb = matriz(B, "mult_matriz", "la segunda matriz")
    if ca != fb:
        raise ErrorDatos(
            f"mult_matriz(): dimensiones incompatibles {fa}x{ca} por "
            f"{fb}x{cb}; las columnas de la primera deben ser iguales a "
            f"las filas de la segunda")
    Bt = transpuesta(B)
    return [[_pulir(sum(x * y for x, y in zip(fila, col))) for col in Bt]
            for fila in A]


def escalar(k, X):
    """Multiplica un numero por un vector o por una matriz."""
    numero(k, "escalar")
    if isinstance(X, list) and X and all(isinstance(f, list) for f in X):
        matriz(X, "escalar")
        return [[k * x for x in fila] for fila in X]
    vector(X, "escalar")
    return [k * x for x in X]


def traza(M):
    f, c = matriz(M, "traza")
    if f != c:
        raise ErrorDatos(f"traza(): la matriz debe ser cuadrada, es {f}x{c}")
    return sum(M[i][i] for i in range(f))


def _cuadrada(M, funcion):
    f, c = matriz(M, funcion)
    if f != c:
        raise ErrorDatos(f"{funcion}(): la matriz debe ser cuadrada, es {f}x{c}")
    return f


def determinante(M):
    """
    Eliminacion de Gauss con pivoteo parcial: se lleva la matriz a forma
    triangular y el determinante es el producto de la diagonal, cambiando
    el signo cada vez que se intercambian filas.
    """
    n = _cuadrada(M, "determinante")
    A = [[float(x) for x in fila] for fila in M]
    det = 1.0
    for col in range(n):
        pivote = max(range(col, n), key=lambda r: abs(A[r][col]))
        if abs(A[pivote][col]) < 1e-12:
            return 0.0
        if pivote != col:
            A[col], A[pivote] = A[pivote], A[col]
            det = -det
        det *= A[col][col]
        for r in range(col + 1, n):
            factor = A[r][col] / A[col][col]
            for k in range(col, n):
                A[r][k] -= factor * A[col][k]
    det = _limpiar(det)
    redondo = round(det)
    return float(redondo) if abs(det - redondo) < 1e-9 else det


def inversa(M):
    """Gauss-Jordan sobre la matriz aumentada [M | I]."""
    n = _cuadrada(M, "inversa")
    A = [[float(x) for x in fila] + [1.0 if i == j else 0.0 for j in range(n)]
         for i, fila in enumerate(M)]
    for col in range(n):
        pivote = max(range(col, n), key=lambda r: abs(A[r][col]))
        if abs(A[pivote][col]) < 1e-12:
            raise ErrorDatos(
                "inversa(): la matriz no tiene inversa (su determinante es 0)")
        A[col], A[pivote] = A[pivote], A[col]
        p = A[col][col]
        A[col] = [x / p for x in A[col]]
        for r in range(n):
            if r != col:
                factor = A[r][col]
                A[r] = [x - factor * y for x, y in zip(A[r], A[col])]
    return [[_limpiar(x) for x in fila[n:]] for fila in A]
