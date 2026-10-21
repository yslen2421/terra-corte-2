"""
biblioteca.py
=============
Catalogo de las funciones incorporadas de Terra que viven fuera del
evaluador: matematicas, matrices y (en los pasos siguientes) memoria,
orden superior, entrada por teclado y archivos.

Cada funcion se registra con su nombre en Terra y el numero de
argumentos que acepta. El evaluador llama a funciones(evaluador) una
sola vez y envuelve cada funcion para que los ErrorDatos salgan como
ErrorSemantico con la linea del programa.

Para agregar una funcion nueva al lenguaje basta con registrarla aqui:
no hay que tocar la gramatica ni regenerar el parser.
"""

from src import matematicas as m
from src.memoria import GestorMemoria
from src.tabla import ErrorDatos


def _aridad(nombre, funcion, minimo, maximo=None):
    """
    Envuelve una funcion de Python para que verifique cuantos argumentos
    recibe antes de ejecutarse.
    """
    maximo = minimo if maximo is None else maximo

    def llamar(args, linea):
        if not (minimo <= len(args) <= maximo):
            if minimo == maximo:
                esperado = f"{minimo}"
            else:
                esperado = f"entre {minimo} y {maximo}"
            raise ErrorDatos(
                f"{nombre}() recibe {esperado} argumento(s) y recibio "
                f"{len(args)}")
        return funcion(*args)

    return llamar


def _dimensiones_validas(gestor, funcion, que):
    """
    Antes de crear una matriz verifica que no pase del limite de celdas.
    Se revisa antes de crearla, no despues, para no ocupar la memoria.
    """
    def crear(*args):
        filas = args[0]
        columnas = args[0] if que == "cuadrada" else (
            args[1] if len(args) > 1 else 0)
        if (isinstance(filas, int) and isinstance(columnas, int)
                and not isinstance(filas, bool)
                and not isinstance(columnas, bool)):
            gestor.validar_celdas(filas * columnas, "la matriz")
        return funcion(*args)
    return crear


def _matematicas(gestor) -> dict:
    """Funciones de una variable, vectores y matrices."""
    tabla = [
        # nombre            funcion                minimo  maximo
        ("pi",              lambda: m.PI,               0),
        ("e",               lambda: m.E,                0),
        ("seno",            m.seno,                     1),
        ("coseno",          m.coseno,                   1),
        ("tangente",        m.tangente,                 1),
        ("exp",             m.exp,                      1),
        ("ln",              m.ln,                       1),
        ("log",             m.log,                      1, 2),
        ("piso",            m.piso,                     1),
        ("techo",           m.techo,                    1),
        ("factorial",       m.factorial,                1),
        ("aleatorio",       m.aleatorio,                0),
        ("semilla",         lambda n: m.GENERADOR.semilla(n), 1),
        ("producto_punto",  m.producto_punto,           2),
        ("norma",           m.norma,                    1),
        ("matriz",          _dimensiones_validas(gestor, m.crear_matriz, "f x c"), 2, 3),
        ("ceros",           _dimensiones_validas(gestor, lambda f, c: m.crear_matriz(f, c, 0), "f x c"), 2),
        ("unos",            _dimensiones_validas(gestor, lambda f, c: m.crear_matriz(f, c, 1), "f x c"), 2),
        ("identidad",       _dimensiones_validas(gestor, m.identidad, "cuadrada"), 1),
        ("aleatoria",       _dimensiones_validas(gestor, m.matriz_aleatoria, "f x c"), 2),
        ("dimension",       m.dimension,                1),
        ("transpuesta",     m.transpuesta,              1),
        ("sumar_matrices",  m.sumar_matrices,           2),
        ("restar_matrices", lambda a, b: m.sumar_matrices(a, b, -1), 2),
        ("mult_matriz",     m.mult_matriz,              2),
        ("escalar",         m.escalar,                  2),
        ("traza",           m.traza,                    1),
        ("determinante",    m.determinante,             1),
        ("inversa",         m.inversa,                  1),
    ]
    return _registrar(tabla)


def _registrar(tabla) -> dict:
    """Convierte una lista de (nombre, funcion, minimo[, maximo]) en catalogo."""
    catalogo = {}
    for registro in tabla:
        nombre, funcion, minimo = registro[0], registro[1], registro[2]
        maximo = registro[3] if len(registro) > 3 else None
        catalogo[nombre] = _aridad(nombre, funcion, minimo, maximo)
    return catalogo


def _memoria(gestor) -> dict:
    """Consulta y control de memoria."""
    return _registrar([
        ("memoria_info",            gestor.info,                    0),
        ("memoria_estado",          gestor.estado,                  0),
        ("liberar",                 gestor.liberar,                 1),
        ("fijar_limite_recursion",  gestor.fijar_limite_recursion,  1),
    ])


# ---------------------------------------------------------------------
# FUNCIONES COMO VALORES
# ---------------------------------------------------------------------

class FuncionAnonima:
    """
    Valor que produce 'funcion(x, y) => expresion'.

    Guarda los parametros y el nodo del arbol con el cuerpo; el cuerpo
    solo se evalua cuando alguien llama a la funcion.
    """

    def __init__(self, parametros, cuerpo):
        self.parametros = parametros
        self.cuerpo = cuerpo

    def __str__(self):
        return f"<funcion({', '.join(self.parametros)})>"


class FuncionNombrada:
    """
    Valor que produce escribir el nombre de una funcion sin parentesis,
    por ejemplo 'mapear(lista, raiz)' o 'mapear(lista, mi_funcion)'.
    """

    def __init__(self, nombre):
        self.nombre = nombre

    def __str__(self):
        return f"<funcion {self.nombre}>"


def es_funcion(valor) -> bool:
    return isinstance(valor, (FuncionAnonima, FuncionNombrada,
                              FuncionCompuesta))


def llamar_funcion(evaluador, funcion, argumentos, linea):
    """
    Llama a cualquier valor de tipo funcion.

    - Una funcion anonima ve las variables del programa (asi puede usar,
      por ejemplo, un factor declarado afuera) y sus parametros las
      ocultan mientras se evalua. Al terminar se restaura la memoria.
    - Una funcion nombrada se resuelve igual que una llamada normal:
      primero las incorporadas y despues las del usuario.
    """
    if isinstance(funcion, FuncionAnonima):
        if len(argumentos) != len(funcion.parametros):
            raise ErrorDatos(
                f"la funcion anonima espera {len(funcion.parametros)} "
                f"argumento(s) y recibio {len(argumentos)}")
        anterior = evaluador.memoria
        evaluador.memoria = dict(anterior)
        for nombre, valor in zip(funcion.parametros, argumentos):
            evaluador.memoria[nombre] = {"valor": valor, "mutable": False}
        try:
            return evaluador.visit(funcion.cuerpo)
        finally:
            evaluador.memoria = anterior

    if isinstance(funcion, FuncionNombrada):
        incorporadas = evaluador._incorporadas()
        if funcion.nombre in incorporadas:
            return incorporadas[funcion.nombre](argumentos, linea)
        return evaluador._invocar(funcion.nombre, argumentos, linea)

    if isinstance(funcion, FuncionCompuesta):
        intermedio = llamar_funcion(evaluador, funcion.g, argumentos, linea)
        return llamar_funcion(evaluador, funcion.f, [intermedio], linea)

    raise ErrorDatos("el valor que se intento llamar no es una funcion")


# ---------------------------------------------------------------------
# FUNCIONES DE ORDEN SUPERIOR
# ---------------------------------------------------------------------

def _orden_superior(evaluador) -> dict:
    """
    Funciones que reciben otras funciones. Cada una valida que reciba
    una lista y una funcion antes de empezar.
    """

    def lista_y_funcion(nombre, lista, f):
        if not isinstance(lista, list):
            raise ErrorDatos(f"{nombre}(): el primer argumento debe ser una lista")
        if not es_funcion(f):
            raise ErrorDatos(
                f"{nombre}(): el segundo argumento debe ser una funcion, "
                f"por ejemplo funcion(x) => x * 2")

    def booleano(nombre, valor):
        if not isinstance(valor, bool):
            raise ErrorDatos(
                f"{nombre}(): la funcion debe devolver verdadero o falso")
        return valor

    def mapear(args, linea):
        lista, f = args
        lista_y_funcion("mapear", lista, f)
        return [llamar_funcion(evaluador, f, [x], linea) for x in lista]

    def filtro(args, linea):
        lista, f = args
        lista_y_funcion("filtro", lista, f)
        return [x for x in lista
                if booleano("filtro", llamar_funcion(evaluador, f, [x], linea))]

    def reducir(args, linea):
        lista, f = args[0], args[1]
        lista_y_funcion("reducir", lista, f)
        if len(args) == 3:
            acumulado, resto = args[2], lista
        else:
            if not lista:
                raise ErrorDatos(
                    "reducir(): la lista esta vacia y no se dio valor inicial")
            acumulado, resto = lista[0], lista[1:]
        for x in resto:
            acumulado = llamar_funcion(evaluador, f, [acumulado, x], linea)
        return acumulado

    def ordenar_por(args, linea):
        lista, f = args[0], args[1]
        lista_y_funcion("ordenar_por", lista, f)
        descendente = False
        if len(args) == 3:
            if args[2] not in ("asc", "desc"):
                raise ErrorDatos(
                    "ordenar_por(): el tercer argumento debe ser \"asc\" o \"desc\"")
            descendente = args[2] == "desc"
        claves = [llamar_funcion(evaluador, f, [x], linea) for x in lista]
        try:
            orden = sorted(range(len(lista)), key=lambda i: claves[i],
                           reverse=descendente)
        except TypeError:
            raise ErrorDatos(
                "ordenar_por(): la funcion devolvio valores que no se pueden "
                "comparar entre si")
        return [lista[i] for i in orden]

    def todos(args, linea):
        lista, f = args
        lista_y_funcion("todos", lista, f)
        return all(booleano("todos", llamar_funcion(evaluador, f, [x], linea))
                   for x in lista)

    def alguno(args, linea):
        lista, f = args
        lista_y_funcion("alguno", lista, f)
        return any(booleano("alguno", llamar_funcion(evaluador, f, [x], linea))
                   for x in lista)

    def aplicar_matriz(args, linea):
        M, f = args
        m.matriz(M, "aplicar_matriz")
        if not es_funcion(f):
            raise ErrorDatos("aplicar_matriz(): el segundo argumento debe ser una funcion")
        return [[llamar_funcion(evaluador, f, [x], linea) for x in fila]
                for fila in M]

    def aplicar(args, linea):
        if not args or not es_funcion(args[0]):
            raise ErrorDatos("aplicar(): el primer argumento debe ser una funcion")
        return llamar_funcion(evaluador, args[0], list(args[1:]), linea)

    def componer(args, linea):
        f, g = args
        if not (es_funcion(f) and es_funcion(g)):
            raise ErrorDatos("componer(): los dos argumentos deben ser funciones")
        return FuncionCompuesta(f, g)

    def rango(args, linea):
        for a in args:
            if isinstance(a, bool) or not isinstance(a, int):
                raise ErrorDatos("rango() solo recibe numeros enteros")
        if len(args) == 1:
            inicio, fin, paso = 0, args[0], 1
        else:
            inicio, fin = args[0], args[1]
            paso = args[2] if len(args) == 3 else 1
        if paso == 0:
            raise ErrorDatos("rango(): el paso no puede ser 0")
        cantidad = max(0, (fin - inicio + paso - (1 if paso > 0 else -1)) // paso)
        if evaluador is not None and hasattr(evaluador, "gestor_memoria"):
            evaluador.gestor_memoria.validar_celdas(cantidad, "la lista de rango()")
        resultado = []
        x = inicio
        while (x < fin) if paso > 0 else (x > fin):
            resultado.append(x)
            x += paso
        return resultado

    def con_aridad(nombre, funcion, minimo, maximo=None):
        maximo = minimo if maximo is None else maximo

        def llamar(args, linea):
            if not (minimo <= len(args) <= maximo):
                esperado = (f"{minimo}" if minimo == maximo
                            else f"entre {minimo} y {maximo}")
                raise ErrorDatos(
                    f"{nombre}() recibe {esperado} argumento(s) y recibio "
                    f"{len(args)}")
            return funcion(args, linea)
        return llamar

    return {
        "mapear":         con_aridad("mapear", mapear, 2),
        "filtro":         con_aridad("filtro", filtro, 2),
        "reducir":        con_aridad("reducir", reducir, 2, 3),
        "ordenar_por":    con_aridad("ordenar_por", ordenar_por, 2, 3),
        "todos":          con_aridad("todos", todos, 2),
        "alguno":         con_aridad("alguno", alguno, 2),
        "aplicar_matriz": con_aridad("aplicar_matriz", aplicar_matriz, 2),
        "aplicar":        con_aridad("aplicar", aplicar, 1, 20),
        "componer":       con_aridad("componer", componer, 2),
        "rango":          con_aridad("rango", rango, 1, 3),
    }


class FuncionCompuesta:
    """componer(f, g) devuelve x => f(g(x))."""

    def __init__(self, f, g):
        self.f = f
        self.g = g

    def __str__(self):
        return f"<funcion compuesta>"


# ---------------------------------------------------------------------
# ENTRADA POR TECLADO
# ---------------------------------------------------------------------

def _entrada() -> dict:
    """
    leer(mensaje)         -> texto que escribe el usuario
    leer_numero(mensaje)  -> el texto convertido a numero o decimal

    leer_numero insiste hasta recibir un numero valido, para que un error
    de digitacion no detenga el programa.
    """

    def pedir(args):
        mensaje = args[0] if args else ""
        if not isinstance(mensaje, str):
            raise ErrorDatos("el mensaje de leer() debe ser texto")
        try:
            return input(mensaje)
        except EOFError:
            raise ErrorDatos("no hay mas datos de entrada para leer()")

    def leer(args, linea):
        return pedir(args)

    def leer_numero(args, linea):
        while True:
            texto = pedir(args).strip()
            s = texto[1:] if texto[:1] in "+-" else texto
            if s.isdigit():
                return int(texto)
            try:
                if s and all(c in "0123456789.eE+-" for c in s):
                    return float(texto)
            except ValueError:
                pass
            print(f"  '{texto}' no es un numero, intenta de nuevo")

    def con_aridad(nombre, funcion):
        def llamar(args, linea):
            if len(args) > 1:
                raise ErrorDatos(
                    f"{nombre}() recibe entre 0 y 1 argumento(s) y recibio "
                    f"{len(args)}")
            return funcion(args, linea)
        return llamar

    return {
        "leer": con_aridad("leer", leer),
        "leer_numero": con_aridad("leer_numero", leer_numero),
    }


# ---------------------------------------------------------------------
# TABLAS Y ARCHIVOS
# ---------------------------------------------------------------------

def _tablas_y_archivos() -> dict:
    """
    Puente entre tablas y listas, combinacion de tablas y archivos de
    texto. Asi una columna de una tabla se puede pasar a mapear, filtro,
    media o a las funciones de matrices.
    """
    import os
    from src.tabla import Tabla

    TIPOS_CELDA = (bool, int, float, str)

    def tabla(t, funcion, que="el primer argumento"):
        if not isinstance(t, Tabla):
            raise ErrorDatos(f"{funcion}(): {que} debe ser una tabla")
        return t

    def texto(x, funcion, que):
        if not isinstance(x, str):
            raise ErrorDatos(f"{funcion}(): {que} debe ser texto")
        return x

    # ------------------------------------------------ tabla <-> listas

    def columna(t, nombre):
        tabla(t, "columna")
        texto(nombre, "columna", "el nombre de la columna")
        return t.columna(nombre)

    def nombres(t):
        return list(tabla(t, "nombres").columnas)

    def num_filas(t):
        return tabla(t, "num_filas").num_filas

    def fila(t, i):
        tabla(t, "fila")
        if isinstance(i, bool) or not isinstance(i, int):
            raise ErrorDatos("fila(): la posicion debe ser un numero entero")
        if not 0 <= i < t.num_filas:
            raise ErrorDatos(
                f"fila(): la posicion {i} no existe; la tabla tiene "
                f"{t.num_filas} filas (de 0 a {t.num_filas - 1})")
        return list(t.filas[i])

    def tabla_desde(columnas, filas):
        if not isinstance(columnas, list) or not all(
                isinstance(c, str) for c in columnas):
            raise ErrorDatos(
                "tabla_desde(): el primer argumento debe ser una lista de "
                "nombres de columnas")
        if not isinstance(filas, list) or not all(
                isinstance(f, list) for f in filas):
            raise ErrorDatos(
                "tabla_desde(): el segundo argumento debe ser una lista de filas")
        for f in filas:
            for v in f:
                if v is not None and not isinstance(v, TIPOS_CELDA):
                    raise ErrorDatos(
                        "tabla_desde(): las celdas solo pueden ser numeros, "
                        "decimales, textos, booleanos o nulos")
        return Tabla(columnas, filas)

    def a_matriz(t, columnas=None):
        tabla(t, "a_matriz")
        columnas = t.columnas if columnas is None else columnas
        if not isinstance(columnas, list) or not columnas:
            raise ErrorDatos("a_matriz(): las columnas deben ir en una lista")
        indices = [t.indice(c) for c in columnas]
        M = []
        for k, f in enumerate(t.filas):
            fila_m = []
            for j in indices:
                v = f[j]
                if not m.es_numero(v):
                    raise ErrorDatos(
                        f"a_matriz(): la fila {k + 1} tiene un valor no "
                        f"numerico o nulo en la columna '{t.columnas[j]}'; "
                        f"limpia los datos antes de convertir")
                fila_m.append(v)
            M.append(fila_m)
        if not M:
            raise ErrorDatos("a_matriz(): la tabla no tiene filas")
        return M

    # ------------------------------------------------ combinar tablas

    def concatenar(a, b):
        """Pone las filas de b debajo de las de a (mismas columnas)."""
        tabla(a, "concatenar")
        tabla(b, "concatenar", "el segundo argumento")
        if sorted(a.columnas) != sorted(b.columnas):
            raise ErrorDatos(
                "concatenar(): las tablas deben tener las mismas columnas")
        orden = [b.indice(c) for c in a.columnas]
        filas = a.filas + [[f[j] for j in orden] for f in b.filas]
        return Tabla(a.columnas, filas)

    def unir(a, b, clave, modo="interna"):
        """
        Une dos tablas por una columna comun (join).
        modo "interna": solo las filas cuya clave esta en las dos tablas.
        modo "izquierda": todas las filas de a; si no hay pareja en b,
        las columnas de b quedan en nulo.
        """
        tabla(a, "unir")
        tabla(b, "unir", "el segundo argumento")
        texto(clave, "unir", "la columna clave")
        if modo not in ("interna", "izquierda"):
            raise ErrorDatos(
                'unir(): el modo debe ser "interna" o "izquierda"')
        ja, jb = a.indice(clave), b.indice(clave)
        resto_b = [j for j in range(b.num_columnas) if j != jb]
        for j in resto_b:
            if b.columnas[j] in a.columnas:
                raise ErrorDatos(
                    f"unir(): la columna '{b.columnas[j]}' existe en las dos "
                    f"tablas; renombrala en una de ellas antes de unir")
        por_clave = {}
        for f in b.filas:
            por_clave.setdefault(f[jb], []).append(f)
        filas = []
        for f in a.filas:
            parejas = por_clave.get(f[ja], []) if f[ja] is not None else []
            for g in parejas:
                filas.append(f + [g[j] for j in resto_b])
            if not parejas and modo == "izquierda":
                filas.append(f + [None] * len(resto_b))
        return Tabla(a.columnas + [b.columnas[j] for j in resto_b], filas)

    def valores_unicos(t, nombre):
        tabla(t, "valores_unicos")
        texto(nombre, "valores_unicos", "el nombre de la columna")
        vistos = []
        conjunto = set()
        for v in t.columna(nombre):
            if v not in conjunto:
                conjunto.add(v)
                vistos.append(v)
        return vistos

    # ------------------------------------------------ archivos de texto

    def _abrir(ruta, modo, funcion):
        texto(ruta, funcion, "la ruta")
        try:
            return open(ruta, modo, encoding="utf-8")
        except FileNotFoundError:
            raise ErrorDatos(
                f"{funcion}(): no se encontro el archivo o la carpeta de "
                f"'{ruta}'")
        except IsADirectoryError:
            raise ErrorDatos(f"{funcion}(): '{ruta}' es una carpeta")
        except PermissionError:
            raise ErrorDatos(f"{funcion}(): no hay permiso sobre '{ruta}'")

    def leer_archivo(ruta):
        with _abrir(ruta, "r", "leer_archivo") as f:
            return f.read()

    def leer_lineas(ruta):
        with _abrir(ruta, "r", "leer_lineas") as f:
            return f.read().splitlines()

    def escribir_archivo(ruta, contenido):
        texto(contenido, "escribir_archivo", "el contenido")
        with _abrir(ruta, "w", "escribir_archivo") as f:
            f.write(contenido)

    def agregar_archivo(ruta, contenido):
        texto(contenido, "agregar_archivo", "el contenido")
        with _abrir(ruta, "a", "agregar_archivo") as f:
            f.write(contenido)

    def existe_archivo(ruta):
        texto(ruta, "existe_archivo", "la ruta")
        return os.path.isfile(ruta)

    def borrar_archivo(ruta):
        texto(ruta, "borrar_archivo", "la ruta")
        if not os.path.isfile(ruta):
            raise ErrorDatos(f"borrar_archivo(): no existe el archivo '{ruta}'")
        os.remove(ruta)
        return True

    return _registrar([
        ("columna",          columna,          2),
        ("nombres",          nombres,          1),
        ("num_filas",        num_filas,        1),
        ("fila",             fila,             2),
        ("tabla_desde",      tabla_desde,      2),
        ("a_matriz",         a_matriz,         1, 2),
        ("concatenar",       concatenar,       2),
        ("unir",             unir,             3, 4),
        ("valores_unicos",   valores_unicos,   2),
        ("leer_archivo",     leer_archivo,     1),
        ("leer_lineas",      leer_lineas,      1),
        ("escribir_archivo", escribir_archivo, 2),
        ("agregar_archivo",  agregar_archivo,  2),
        ("existe_archivo",   existe_archivo,   1),
        ("borrar_archivo",   borrar_archivo,   1),
    ])


# ---------------------------------------------------------------------
# AYUDA DEL LENGUAJE
# ---------------------------------------------------------------------

# categoria -> lista de (nombre, forma de escribirlo, que hace, ejemplo)
GUIA = {
    "datos": [
        ("cargar", 'cargar "ruta.csv" [con separador ";"] [con encabezado falso]',
         "lee un CSV y devuelve una tabla",
         'fijo d = cargar "datos/emisiones_ejemplo.csv"'),
        ("guardar", 'guardar tabla como "ruta.csv" [con separador ";"]',
         "escribe una tabla en un CSV",
         'guardar d como "salidas/copia.csv"'),
        ("seleccionar", "|> seleccionar [col1, col2]",
         "deja solo esas columnas", "d |> seleccionar [pais, co2]"),
        ("filtrar", "|> filtrar donde condicion",
         "deja las filas que cumplen la condicion",
         "d |> filtrar donde co2 > 80"),
        ("crear", "|> crear nombre = expresion",
         "agrega una columna calculada",
         "d |> crear per_capita = co2 * 1000000 / poblacion"),
        ("renombrar", "|> renombrar viejo como nuevo",
         "cambia el nombre de una columna",
         "d |> renombrar co2 como emisiones"),
        ("ordenar", "|> ordenar por columna [asc | desc]",
         "ordena las filas", "d |> ordenar por co2 desc"),
        ("eliminar", "|> eliminar duplicados  /  |> eliminar nulos [en [cols]]",
         "quita filas repetidas o con nulos", "d |> eliminar nulos"),
        ("rellenar", "|> rellenar nulos en columna con valor",
         "reemplaza los nulos", "d |> rellenar nulos en energia_renovable con 0.0"),
        ("convertir", "|> convertir columna como tipo",
         "cambia el tipo de una columna", "d |> convertir anio como texto"),
        ("limitar", "|> limitar n", "deja las primeras n filas", "d |> limitar 5"),
        ("agrupar", "|> agrupar por [cols] |> resumir nombre = agregacion, ...",
         "una fila por grupo con sus estadisticas",
         "d |> agrupar por [pais] |> resumir total = suma(co2), n = contar()"),
        ("describir", "describir(tabla)",
         "estadisticas de cada columna", "mostrar(describir(d))"),
    ],
    "estadistica": [
        ("suma", "suma(lista)", "suma de los valores", "suma([1, 2, 3])"),
        ("media", "media(lista)", "promedio", "media([1, 2, 3])"),
        ("mediana", "mediana(lista)", "valor central", "mediana([3, 1, 2])"),
        ("minimo", "minimo(lista) / maximo(lista)", "extremos", "maximo([3, 9, 2])"),
        ("desviacion", "desviacion(lista)", "desviacion estandar muestral",
         "desviacion([2, 4, 6])"),
        ("contar", "contar() / contar(lista)",
         "filas del grupo (en resumir) o elementos", "contar([1, 2, 3])"),
        ("redondear", "redondear(x, decimales)", "redondea", "redondear(3.14159, 2)"),
        ("raiz", "raiz(x) / absoluto(x)", "raiz cuadrada y valor absoluto", "raiz(16)"),
        ("longitud", "longitud(lista)", "cantidad de elementos", "longitud([4, 5, 6])"),
        ("a_numero", "a_numero(x) / a_decimal(x) / a_texto(x)",
         "conversiones de tipo", 'a_numero("42")'),
    ],
    "matematicas": [
        ("pi", "pi() / e()", "constantes", "pi()"),
        ("seno", "seno(x) / coseno(x) / tangente(x)",
         "trigonometricas, x en radianes", "seno(pi() / 6)"),
        ("exp", "exp(x)", "e elevado a x", "exp(1)"),
        ("ln", "ln(x) / log(x) / log(x, base)", "logaritmos", "log(8, 2)"),
        ("piso", "piso(x) / techo(x)", "redondeo hacia abajo / arriba", "piso(2.7)"),
        ("factorial", "factorial(n)", "n!", "factorial(5)"),
        ("aleatorio", "aleatorio() / semilla(n)",
         "decimal al azar en [0, 1); la semilla lo hace reproducible",
         "semilla(42)"),
    ],
    "matrices": [
        ("matriz", "matriz(f, c, valor) / ceros(f, c) / unos(f, c)",
         "crea una matriz", "ceros(2, 3)"),
        ("identidad", "identidad(n) / aleatoria(f, c)",
         "identidad o matriz al azar", "identidad(3)"),
        ("dimension", "dimension(M)", "[filas, columnas]", "dimension([[1, 2], [3, 4]])"),
        ("transpuesta", "transpuesta(M)", "intercambia filas y columnas",
         "transpuesta([[1, 2, 3]])"),
        ("mult_matriz", "mult_matriz(A, B)", "producto matricial",
         "mult_matriz([[1, 2]], [[3], [4]])"),
        ("sumar_matrices", "sumar_matrices(A, B) / restar_matrices(A, B)",
         "suma o resta elemento a elemento", "sumar_matrices(A, B)"),
        ("escalar", "escalar(k, M)", "multiplica por un numero", "escalar(2, [[1, 2]])"),
        ("determinante", "determinante(M) / inversa(M) / traza(M)",
         "por eliminacion de Gauss y Gauss-Jordan", "determinante([[4, 7], [2, 6]])"),
        ("producto_punto", "producto_punto(a, b) / norma(v)",
         "operaciones con vectores", "norma([3, 4])"),
    ],
    "funciones": [
        ("funcion", "funcion nombre(a, b):  ...  retornar valor  fin",
         "define una funcion (cada parte en su propia linea)",
         "funcion doble(x):  |  retornar x * 2  |  fin"),
        ("anonima", "funcion(x) => expresion",
         "funcion sin nombre que se guarda o se pasa como valor",
         "fijo doble = funcion(x) => x * 2"),
        ("mapear", "mapear(lista, f)", "aplica f a cada elemento",
         "mapear([1, 2, 3], funcion(x) => x * 2)"),
        ("filtro", "filtro(lista, f)", "deja los elementos donde f es verdadero",
         "filtro([1, 2, 3, 4], funcion(x) => x % 2 == 0)"),
        ("reducir", "reducir(lista, f [, inicial])", "combina todo en un valor",
         "reducir([1, 2, 3], funcion(a, b) => a + b)"),
        ("ordenar_por", 'ordenar_por(lista, f [, "desc"])', "ordena segun f",
         'ordenar_por(["ab", "c"], funcion(t) => longitud(t))'),
        ("todos", "todos(lista, f) / alguno(lista, f)",
         "si todos o alguno cumplen", "alguno([1, 5], funcion(x) => x > 3)"),
        ("componer", "componer(f, g) / aplicar(f, a, b, ...)",
         "funcion que calcula f(g(x)) / llama a f con esos argumentos",
         "componer(raiz, absoluto)"),
        ("aplicar_matriz", "aplicar_matriz(M, f)", "aplica f a cada celda",
         "aplicar_matriz([[1, 2]], funcion(x) => x ^ 2)"),
        ("rango", "rango(fin) / rango(inicio, fin [, paso])", "lista de enteros",
         "rango(1, 6)"),
    ],
    "tablas": [
        ("columna", 'columna(tabla, "nombre")', "la columna como lista",
         'media(columna(d, "co2"))'),
        ("nombres", "nombres(tabla) / num_filas(tabla) / fila(tabla, i)",
         "estructura de la tabla", "num_filas(d)"),
        ("valores_unicos", 'valores_unicos(tabla, "columna")',
         "valores distintos en orden de aparicion", 'valores_unicos(d, "pais")'),
        ("tabla_desde", "tabla_desde(columnas, filas)", "crea una tabla",
         'tabla_desde(["a", "b"], [[1, 2], [3, 4]])'),
        ("a_matriz", "a_matriz(tabla [, columnas])", "tabla numerica a matriz",
         'a_matriz(d, ["anio", "co2"])'),
        ("unir", 'unir(t1, t2, "clave" [, "izquierda"])',
         "une dos tablas por una columna", 'unir(d, metas, "pais")'),
        ("concatenar", "concatenar(t1, t2)", "pone las filas de t2 debajo de t1",
         "concatenar(d, extra)"),
    ],
    "archivos": [
        ("leer_archivo", 'leer_archivo("ruta") / leer_lineas("ruta")',
         "lee un archivo de texto", 'leer_lineas("salidas/registro.txt")'),
        ("escribir_archivo", 'escribir_archivo("ruta", texto) / agregar_archivo("ruta", texto)',
         "escribe o agrega texto", 'agregar_archivo("log.txt", "listo\\n")'),
        ("existe_archivo", 'existe_archivo("ruta") / borrar_archivo("ruta")',
         "consulta o borra un archivo", 'existe_archivo("log.txt")'),
        ("leer", 'leer("mensaje") / leer_numero("mensaje")',
         "pide un dato por teclado", 'fijo kwh = leer_numero("kWh: ")'),
    ],
    "memoria": [
        ("memoria_info", "memoria_info()", "variables, tipo y memoria que ocupan",
         "mostrar(memoria_info())"),
        ("memoria_estado", "memoria_estado()", "limites y uso actual",
         "mostrar(memoria_estado())"),
        ("liberar", 'liberar("variable")', "elimina una variable", 'liberar("M")'),
        ("fijar_limite_recursion", "fijar_limite_recursion(n)",
         "cambia el limite de llamadas anidadas (maximo 2000)",
         "fijar_limite_recursion(500)"),
    ],
}


def _ayuda() -> dict:
    """
    ayuda()             -> lista las categorias
    ayuda("matrices")   -> todas las funciones de una categoria
    ayuda("mapear")     -> como se escribe una funcion, con ejemplo
    """

    def mostrar_entrada(nombre, forma, descripcion, ejemplo):
        print(f"  {forma}")
        print(f"      {descripcion}")
        print(f"      ejemplo: {ejemplo}")

    def ayuda(args, linea):
        if len(args) > 1:
            raise ErrorDatos("ayuda() recibe 0 o 1 argumento")
        if not args:
            print("Terra - ayuda del lenguaje")
            print("Escribe ayuda(\"categoria\") o ayuda(\"funcion\").")
            print("Categorias:")
            for categoria, entradas in GUIA.items():
                nombres = ", ".join(e[0] for e in entradas)
                print(f"  {categoria:<12} {nombres}")
            return None

        tema = args[0]
        if not isinstance(tema, str):
            raise ErrorDatos("ayuda() recibe un texto, por ejemplo ayuda(\"mapear\")")
        if tema in GUIA:
            print(f"Categoria: {tema}")
            for entrada in GUIA[tema]:
                mostrar_entrada(*entrada)
            return None
        for categoria, entradas in GUIA.items():
            for entrada in entradas:
                if entrada[0] == tema or f"{tema}(" in entrada[1]:
                    print(f"[{categoria}]")
                    mostrar_entrada(*entrada)
                    return None
        raise ErrorDatos(
            f"no hay ayuda para '{tema}'. Escribe ayuda() para ver las categorias")

    return {"ayuda": ayuda}


def funciones(evaluador) -> dict:
    """
    Todas las funciones de la biblioteca: {nombre: funcion(args, linea)}.

    Recibe el evaluador porque algunas funciones de los pasos siguientes
    (memoria, orden superior) necesitan consultar su estado.
    """
    gestor = GestorMemoria(evaluador)
    evaluador.gestor_memoria = gestor

    catalogo = {}
    catalogo.update(_matematicas(gestor))
    catalogo.update(_memoria(gestor))
    catalogo.update(_orden_superior(evaluador))
    catalogo.update(_entrada())
    catalogo.update(_tablas_y_archivos())
    catalogo.update(_ayuda())
    return catalogo
