"""
visitante_evaluador.py
======================
Evaluador semantico de Terra: implementa el patron Visitor sobre el
arbol de analisis generado por ANTLR.

Responsabilidades de este modulo (nucleo del lenguaje):
    - Memoria de variables con inmutabilidad (fijo) y mutabilidad (var)
    - Tipado dinamico y fuerte: ninguna conversion implicita entre tipos
    - Validacion de tipos en todos los operadores
    - Estructuras de control: si / sino si / sino, mientras, para ... en
    - Funciones incorporadas de matematicas y estadistica
    - Salida con mostrar()

Las operaciones de datos (cargar, tuberias, guardar, graficar) se
reconocen sintacticamente pero su evaluacion corresponde a los cortes
siguientes: aqui producen un error semantico explicito.

Tipos de Terra y su representacion en Python:
    numero    -> int
    decimal   -> float
    texto     -> str
    booleano  -> bool
    nulo      -> None
    lista     -> list
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gramaticas.TerraParser import TerraParser
from gramaticas.TerraVisitor import TerraVisitor
from src.tabla import Tabla, ErrorDatos, leer_csv, escribir_csv
from src import operaciones as ops
from src import biblioteca

class RetornoSenal(Exception):
    """
    Senal interna que transporta el valor de 'retornar' hasta la llamada.

    No es un error: se usa como mecanismo de salto. Cuando una funcion
    ejecuta 'retornar', esta excepcion sube por la pila de visitas
    atravesando ciclos y condicionales, y la captura _invocar().
    """

    def __init__(self, valor):
        self.valor = valor
        super().__init__("retorno de funcion")

class ErrorSemantico(Exception):
    """Error detectado durante la evaluacion del arbol."""

    def __init__(self, mensaje, linea=None):
        self.linea = linea
        if linea is not None:
            mensaje = f"[linea {linea}] {mensaje}"
        super().__init__(mensaje)


# =====================================================================
# UTILIDADES DE TIPO
# =====================================================================

def nombre_tipo(valor) -> str:
    """Devuelve el nombre del tipo Terra de un valor de Python."""
    if isinstance(valor, bool):
        return "booleano"
    if isinstance(valor, int):
        return "numero"
    if isinstance(valor, float):
        return "decimal"
    if isinstance(valor, str):
        return "texto"
    if isinstance(valor, list):
        return "lista"
    if valor is None:
        return "nulo"
    if isinstance(valor, Tabla):
        return "tabla"
    if biblioteca.es_funcion(valor):
        return "funcion"
    return "desconocido"


def es_numero(valor) -> bool:
    """
    True si el valor es numerico.

    La comprobacion de bool va primero porque en Python bool es
    subclase de int: sin ella, verdadero + 1 seria valido y Terra
    perderia el tipado fuerte.
    """
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def formatear(valor, anidado=False) -> str:
    """Convierte un valor a su representacion textual en Terra."""
    if valor is None:
        return "nulo"
    if isinstance(valor, bool):
        return "verdadero" if valor else "falso"
    if isinstance(valor, list):
        return "[" + ", ".join(formatear(v, True) for v in valor) + "]"
    if isinstance(valor, str):
        return f'"{valor}"' if anidado else valor
    if isinstance(valor, Tabla):
        return valor.como_texto()	    
    return str(valor)


# =====================================================================
# VISITANTE
# =====================================================================

class VisitanteEvaluador(TerraVisitor):
    """
    Recorre el arbol de analisis y ejecuta el programa.

    Attributes:
        memoria (dict): nombre -> {"valor": ..., "mutable": bool}
        modo_interactivo (bool): si es True, las expresiones sueltas
            imprimen su resultado automaticamente.
    """

    LIMITE_RECURSION = 200

    def __init__(self, modo_interactivo=False):
        self.memoria = {}
        self.funciones = {}
        self.profundidad = 0
        self.modo_interactivo = modo_interactivo
    # -----------------------------------------------------------------
    # ESTRUCTURA
    # -----------------------------------------------------------------

    def visitPrograma(self, ctx: TerraParser.ProgramaContext):
        """Ejecuta cada sentencia del programa en orden."""
        for hijo in ctx.children or []:
            if isinstance(hijo, TerraParser.SentenciaContext):
                self.visit(hijo)
        return None

    def visitBloque(self, ctx: TerraParser.BloqueContext):
        """Ejecuta las sentencias de un bloque, ignorando lineas vacias."""
        for hijo in ctx.children or []:
            if isinstance(hijo, TerraParser.SentenciaContext):
                self.visit(hijo)
        return None

    def visitSentencia(self, ctx: TerraParser.SentenciaContext):
        return self.visit(ctx.getChild(0))

    # -----------------------------------------------------------------
    # VARIABLES
    # -----------------------------------------------------------------

    def visitDeclaracion_variable(self, ctx):
        """
        Declara una variable.

        'fijo' crea una variable inmutable y 'var' una mutable. Ninguna
        de las dos puede redeclararse: el scope es unico y explicito.
        """
        nombre = ctx.IDENTIFICADOR().getText()
        linea = ctx.start.line

        if nombre in self.memoria:
            raise ErrorSemantico(
                f"la variable '{nombre}' ya fue declarada", linea)

        valor = self.visit(ctx.expresion())
        self.memoria[nombre] = {
            "valor": valor,
            "mutable": ctx.VAR() is not None,
        }
        return None

    def visitAsignacion(self, ctx: TerraParser.AsignacionContext):
        """Reasigna una variable mutable ya declarada."""
        nombre = ctx.IDENTIFICADOR().getText()
        linea = ctx.start.line

        if nombre not in self.memoria:
            raise ErrorSemantico(
                f"la variable '{nombre}' no ha sido declarada", linea)
        if not self.memoria[nombre]["mutable"]:
            raise ErrorSemantico(
                f"'{nombre}' se declaro con 'fijo' y no puede reasignarse",
                linea)

        self.memoria[nombre]["valor"] = self.visit(ctx.expresion())
        return None

    def visitExpresion_stmt(self, ctx):
        """
        Evalua una expresion suelta.

        En modo interactivo imprime el resultado con el prefijo '>',
        como hace cualquier REPL.
        """
        valor = self.visit(ctx.expresion())
        if self.modo_interactivo and valor is not None:
            print(">", formatear(valor))
        return valor

    def visitMostrar_stmt(self, ctx: TerraParser.Mostrar_stmtContext):
        """Imprime uno o varios valores separados por espacio."""
        partes = [formatear(self.visit(e)) for e in ctx.expresion()]
        print(" ".join(partes))
        return None

    # -----------------------------------------------------------------
    # CONTROL DE FLUJO
    # -----------------------------------------------------------------

    def _condicion(self, ctx_expresion) -> bool:
        """Evalua una condicion y exige que sea booleana."""
        valor = self.visit(ctx_expresion)
        if not isinstance(valor, bool):
            raise ErrorSemantico(
                f"la condicion debe ser booleana, se recibio "
                f"{nombre_tipo(valor)}", ctx_expresion.start.line)
        return valor

    def visitSi_stmt(self, ctx: TerraParser.Si_stmtContext):
        """
        Ejecuta el primer bloque cuya condicion sea verdadera.

        Las condiciones (si y sino si) llegan en ctx.expresion() y los
        bloques en ctx.bloque(), alineados por indice. Si hay un bloque
        mas que condiciones, el ultimo corresponde al 'sino'.
        """
        condiciones = ctx.expresion()
        bloques = ctx.bloque()

        for i, condicion in enumerate(condiciones):
            if self._condicion(condicion):
                self.visit(bloques[i])
                return None

        if len(bloques) > len(condiciones):
            self.visit(bloques[-1])
        return None

    def visitMientras_stmt(self, ctx: TerraParser.Mientras_stmtContext):
        """Repite el bloque mientras la condicion sea verdadera."""
        limite = 1_000_000
        vueltas = 0
        while self._condicion(ctx.expresion()):
            self.visit(ctx.bloque())
            vueltas += 1
            if vueltas > limite:
                raise ErrorSemantico(
                    "el ciclo 'mientras' supero el limite de iteraciones; "
                    "revisa la condicion de salida", ctx.start.line)
        return None

    def visitPara_stmt(self, ctx: TerraParser.Para_stmtContext):
        """
        Recorre una lista o un texto.

        La variable del ciclo es local: se declara al entrar y se retira
        al terminar, sin sobrescribir una variable del mismo nombre.
        """
        nombre = ctx.IDENTIFICADOR().getText()
        linea = ctx.start.line
        iterable = self.visit(ctx.expresion())

        if not isinstance(iterable, (list, str)):
            raise ErrorSemantico(
                f"solo se puede recorrer una lista o un texto, se recibio "
                f"{nombre_tipo(iterable)}", linea)

        previo = self.memoria.get(nombre)
        for elemento in iterable:
            self.memoria[nombre] = {"valor": elemento, "mutable": True}
            self.visit(ctx.bloque())

        if previo is not None:
            self.memoria[nombre] = previo
        else:
            self.memoria.pop(nombre, None)
        return None

    # -----------------------------------------------------------------
    # DOMINIO: PENDIENTE PARA LOS CORTES SIGUIENTES
    # -----------------------------------------------------------------

    def visitGuardar_stmt(self, ctx: TerraParser.Guardar_stmtContext):
        """
        guardar tabla como "ruta.csv"
        Escribe una Tabla en un archivo CSV.
        """
        linea = ctx.start.line
        tabla = self.visit(ctx.expr(0))
        ruta = self.visit(ctx.expr(1))

        if not isinstance(tabla, Tabla):
            raise ErrorSemantico(
                f"'guardar' necesita una tabla, se recibio "
                f"{nombre_tipo(tabla)}", linea)
        if not isinstance(ruta, str):
            raise ErrorSemantico(
                f"la ruta de 'guardar' debe ser texto, se recibio "
                f"{nombre_tipo(ruta)}", linea)

        try:
            separador = ","
            if ctx.SEPARADOR():
                separador = self.visit(ctx.expr(2))
                if not isinstance(separador, str):
                    raise ErrorSemantico(
                        f"el separador debe ser texto, se recibio "
                        f"{nombre_tipo(separador)}", linea)
            escribir_csv(tabla, ruta, separador)
        except ErrorDatos as e:
            raise ErrorSemantico(str(e), linea)
        return None

    def visitGraficar_stmt(self, ctx):
        raise ErrorSemantico(
            "'graficar' se reconoce sintacticamente pero su ejecucion "
            "corresponde al tercer corte", ctx.start.line)

    def visitCarga(self, ctx: TerraParser.CargaContext):
        """
        cargar "ruta.csv" [con separador ";"] [con encabezado falso]
        Lee un archivo CSV y devuelve una Tabla con tipos inferidos.
        Las opciones pueden ir en cualquier orden, pero sin repetirse.
        """
        linea = ctx.start.line
        ruta = self.visit(ctx.expr())
        if not isinstance(ruta, str):
            raise ErrorSemantico(
                f"la ruta de 'cargar' debe ser texto, se recibio "
                f"{nombre_tipo(ruta)}", linea)

        separador = ","
        encabezado = True
        usadas = set()

        for opcion in ctx.opcion_carga():
            nombre = "separador" if opcion.SEPARADOR() else "encabezado"
            if nombre in usadas:
                raise ErrorSemantico(
                    f"la opcion '{nombre}' aparece repetida en 'cargar'",
                    linea)
            usadas.add(nombre)
            valor = self.visit(opcion.expr())

            if nombre == "separador":
                if not isinstance(valor, str):
                    raise ErrorSemantico(
                        f"el separador debe ser texto, se recibio "
                        f"{nombre_tipo(valor)}", linea)
                separador = valor
            else:
                if not isinstance(valor, bool):
                    raise ErrorSemantico(
                        f"la opcion 'encabezado' debe ser verdadero o "
                        f"falso, se recibio {nombre_tipo(valor)}", linea)
                encabezado = valor

        try:
            return leer_csv(ruta, separador, encabezado)
        except ErrorDatos as e:
            raise ErrorSemantico(str(e), linea)
    # -----------------------------------------------------------------
    # EXPRESIONES
    # -----------------------------------------------------------------

    def visitExpresion(self, ctx: TerraParser.ExpresionContext):
        return self.visit(ctx.tuberia())

    def visitTuberia(self, ctx: TerraParser.TuberiaContext):
        """
        Sin '|>' es una expresion normal.
        Con '|>' el valor inicial debe ser una tabla; cada operacion
        recibe la tabla que produjo la anterior y devuelve una nueva.
        """
        valor = self.visit(ctx.expr())
        operaciones = ctx.operacion()
        if not operaciones:
            return valor

        if not isinstance(valor, Tabla):
            raise ErrorSemantico(
                f"una tuberia '|>' debe empezar con una tabla, se recibio "
                f"{nombre_tipo(valor)}", ctx.start.line)

        for operacion in operaciones:
            valor = self._aplicar_operacion(valor, operacion)
        if isinstance(valor, ops.Agrupada):
            raise ErrorSemantico(
                "la tuberia termina en 'agrupar': falta 'resumir'",
                ctx.start.line)
        return valor

    def _columnas(self, ctx_lista):
        """Nombres de una lista_columnas: [a, b, c] -> ['a', 'b', 'c']."""
        return [t.getText() for t in ctx_lista.IDENTIFICADOR()]

    def _nombres_usados(self, ctx_expr):
        """
        Conjunto de identificadores que aparecen en una expresion.

        Recorre el subarbol una sola vez y guarda el resultado, para
        que filtrar, crear y resumir declaren solo las columnas que la
        expresion realmente usa, y no todas las de la tabla.
        """
        if not hasattr(self, "_cache_nombres"):
            self._cache_nombres = {}
        if ctx_expr not in self._cache_nombres:
            nombres = set()
            pendientes = [ctx_expr]
            while pendientes:
                nodo = pendientes.pop()
                if hasattr(nodo, "symbol"):
                    if nodo.symbol.type == TerraParser.IDENTIFICADOR:
                        nombres.add(nodo.getText())
                else:
                    pendientes.extend(nodo.getChildren())
            self._cache_nombres[ctx_expr] = nombres
        return self._cache_nombres[ctx_expr]
    def _evaluar_en_fila(self, tabla, i, ctx_expr):
        """
        Evalua una expresion usando la fila i de la tabla.

        Las columnas de la fila se declaran como variables temporales
        (no reasignables) y al terminar se restaura la memoria tal como
        estaba. Asi 'filtrar donde co2 > 50' puede usar 'co2' como si
        fuera una variable.
        """
        respaldo = {}
        usados = self._nombres_usados(ctx_expr)
        for nombre, valor in zip(tabla.columnas, tabla.filas[i]):
            if nombre not in usados:
                continue
            respaldo[nombre] = self.memoria.get(nombre)
            self.memoria[nombre] = {"valor": valor, "mutable": False}
        try:
            return self.visit(ctx_expr)
        finally:
            for nombre, previo in respaldo.items():
                if previo is None:
                    self.memoria.pop(nombre, None)
                else:
                    self.memoria[nombre] = previo

    def _evaluar_en_grupo(self, tabla, indices, ctx_expr):
        """
        Evalua una agregacion sobre un grupo de filas.

        Cada columna se declara como la LISTA de sus valores en el
        grupo, sin nulos. Asi suma(co2) o media(co2) reutilizan las
        funciones incorporadas de Terra. contar() devuelve el numero
        de filas del grupo. Al terminar se restaura la memoria.
        """
        respaldo = {}
        usados = self._nombres_usados(ctx_expr)
        for j, nombre in enumerate(tabla.columnas):
            if nombre not in usados:
                continue
            valores = [tabla.filas[i][j] for i in indices
                       if tabla.filas[i][j] is not None]
            respaldo[nombre] = self.memoria.get(nombre)
            self.memoria[nombre] = {"valor": valores, "mutable": False}

        tamano_previo = getattr(self, "_tamano_grupo", None)
        self._tamano_grupo = len(indices)
        try:
            return self.visit(ctx_expr)
        finally:
            self._tamano_grupo = tamano_previo
            for nombre, previo in respaldo.items():
                if previo is None:
                    self.memoria.pop(nombre, None)
                else:
                    self.memoria[nombre] = previo

    def _resumir(self, origen, agregaciones, linea):
        """
        resumir nombre = expresion, ...
        Con 'agrupar' antes: una fila por grupo, con las columnas clave.
        Sin 'agrupar': una sola fila que resume toda la tabla.
        """
        if isinstance(origen, ops.Agrupada):
            tabla, claves, grupos = origen.tabla, origen.claves, origen.grupos
        else:
            tabla, claves = origen, []
            grupos = [((), list(range(origen.num_filas)))]

        nombres = [a.IDENTIFICADOR().getText() for a in agregaciones]
        filas = []
        for clave, indices in grupos:
            fila = list(clave)
            for nombre, agregacion in zip(nombres, agregaciones):
                valor = self._evaluar_en_grupo(tabla, indices,
                                               agregacion.expr())
                if (valor is not None
                        and not isinstance(valor, ops.TIPOS_CELDA)):
                    raise ErrorSemantico(
                        f"la agregacion '{nombre}' debe producir un solo "
                        f"valor (por ejemplo con suma, media o contar), "
                        f"se obtuvo {nombre_tipo(valor)}",
                        agregacion.start.line)
                fila.append(valor)
            filas.append(fila)

        return Tabla(claves + nombres, filas)
    def _aplicar_operacion(self, tabla, op):
        """Ejecuta una operacion de la tuberia sobre una tabla."""
        linea = op.start.line
        if isinstance(tabla, ops.Agrupada) and not op.RESUMIR():
            raise ErrorSemantico(
                "despues de 'agrupar' debe venir 'resumir'", linea)
        try:
            if op.SELECCIONAR():
                return ops.seleccionar(
                    tabla, self._columnas(op.lista_columnas()))

            if op.FILTRAR():
                def condicion(i):
                    resultado = self._evaluar_en_fila(tabla, i, op.expr())
                    if not isinstance(resultado, bool):
                        raise ErrorSemantico(
                            f"la condicion de 'filtrar' debe ser booleana, "
                            f"se obtuvo {nombre_tipo(resultado)}", linea)
                    return resultado
                return ops.filtrar(tabla, condicion)

            if op.CREAR():
                nombre = op.IDENTIFICADOR(0).getText()
                return ops.crear(
                    tabla, nombre,
                    lambda i: self._evaluar_en_fila(tabla, i, op.expr()))

            if op.RENOMBRAR():
                return ops.renombrar(tabla,
                                     op.IDENTIFICADOR(0).getText(),
                                     op.IDENTIFICADOR(1).getText())

            if op.ORDENAR():
                return ops.ordenar(tabla, op.IDENTIFICADOR(0).getText(),
                                   descendente=op.DESC() is not None)

            if op.ELIMINAR() and op.DUPLICADOS():
                return ops.eliminar_duplicados(tabla)

            if op.ELIMINAR() and op.NULOS():
                columnas = (self._columnas(op.lista_columnas())
                            if op.lista_columnas() else None)
                return ops.eliminar_nulos(tabla, columnas)

            if op.RELLENAR():
                valor = self.visit(op.expr())
                return ops.rellenar_nulos(
                    tabla, op.IDENTIFICADOR(0).getText(), valor)

            if op.CONVERTIR():
                return ops.convertir(tabla, op.IDENTIFICADOR(0).getText(),
                                     op.tipo_dato().getText())

            if op.LIMITAR():
                n = self.visit(op.expr())
                if isinstance(n, bool) or not isinstance(n, int) or n < 0:
                    raise ErrorSemantico(
                        "'limitar' necesita un numero entero mayor o "
                        "igual a 0", linea)
                return ops.limitar(tabla, n)

            if op.AGRUPAR():
                return ops.agrupar(
                    tabla, self._columnas(op.lista_columnas()))

            if op.RESUMIR():
                return self._resumir(tabla, op.agregacion(), linea)
            raise ErrorSemantico(
                f"operacion desconocida '{op.getText()}'", linea)

        except ErrorDatos as e:
            raise ErrorSemantico(str(e), linea)
    def visitExpr(self, ctx: TerraParser.ExprContext):
        return self.visit(ctx.o_logico())

    def visitO_logico(self, ctx: TerraParser.O_logicoContext):
        """Disyuncion logica. Ambos operandos deben ser booleanos."""
        operandos = ctx.y_logico()
        resultado = self.visit(operandos[0])
        if len(operandos) == 1:
            return resultado

        self._exigir_booleano(resultado, "||", ctx.start.line)
        for i in range(1, len(operandos)):
            derecho = self.visit(operandos[i])
            self._exigir_booleano(derecho, "||", ctx.start.line)
            resultado = resultado or derecho
        return resultado

    def visitY_logico(self, ctx: TerraParser.Y_logicoContext):
        """Conjuncion logica. Ambos operandos deben ser booleanos."""
        operandos = ctx.igualdad()
        resultado = self.visit(operandos[0])
        if len(operandos) == 1:
            return resultado

        self._exigir_booleano(resultado, "&&", ctx.start.line)
        for i in range(1, len(operandos)):
            derecho = self.visit(operandos[i])
            self._exigir_booleano(derecho, "&&", ctx.start.line)
            resultado = resultado and derecho
        return resultado

    def visitIgualdad(self, ctx: TerraParser.IgualdadContext):
        """
        Igualdad y desigualdad.

        Exige que ambos lados sean del mismo tipo, con una excepcion:
        numero y decimal se comparan entre si porque ambos son valores
        numericos.
        """
        operandos = ctx.relacional()
        resultado = self.visit(operandos[0])

        for i in range(1, len(operandos)):
            operador = ctx.getChild(2 * i - 1).getText()
            derecho = self.visit(operandos[i])
            linea = ctx.start.line

            compatibles = (nombre_tipo(resultado) == nombre_tipo(derecho)
                           or (es_numero(resultado) and es_numero(derecho)))
            if not compatibles:
                raise ErrorSemantico(
                    f"no se puede comparar {nombre_tipo(resultado)} con "
                    f"{nombre_tipo(derecho)} usando '{operador}'", linea)

            resultado = (resultado == derecho if operador == "=="
                         else resultado != derecho)
        return resultado

    def visitRelacional(self, ctx: TerraParser.RelacionalContext):
        """Comparaciones de orden. Solo entre valores numericos."""
        operandos = ctx.pertenencia()
        resultado = self.visit(operandos[0])

        for i in range(1, len(operandos)):
            operador = ctx.getChild(2 * i - 1).getText()
            derecho = self.visit(operandos[i])
            linea = ctx.start.line

            if not (es_numero(resultado) and es_numero(derecho)):
                raise ErrorSemantico(
                    f"'{operador}' solo compara numeros, se recibio "
                    f"{nombre_tipo(resultado)} y {nombre_tipo(derecho)}",
                    linea)

            if operador == ">":
                resultado = resultado > derecho
            elif operador == "<":
                resultado = resultado < derecho
            elif operador == ">=":
                resultado = resultado >= derecho
            else:
                resultado = resultado <= derecho
        return resultado

    def visitPertenencia(self, ctx: TerraParser.PertenenciaContext):
        """Operador 'en': pertenencia a una lista o subcadena de un texto."""
        operandos = ctx.suma()
        izquierdo = self.visit(operandos[0])
        if len(operandos) == 1:
            return izquierdo

        derecho = self.visit(operandos[1])
        linea = ctx.start.line

        if isinstance(derecho, list):
            return izquierdo in derecho
        if isinstance(derecho, str):
            if not isinstance(izquierdo, str):
                raise ErrorSemantico(
                    "para buscar dentro de un texto el valor buscado debe "
                    f"ser texto, se recibio {nombre_tipo(izquierdo)}", linea)
            return izquierdo in derecho

        raise ErrorSemantico(
            f"'en' opera sobre listas o textos, se recibio "
            f"{nombre_tipo(derecho)}", linea)

    def visitSuma(self, ctx: TerraParser.SumaContext):
        """
        Suma y resta.

        '+' tambien concatena textos y une listas; '-' solo opera sobre
        numeros. No hay conversion implicita: "a" + 1 es un error.
        """
        operandos = ctx.termino()
        resultado = self.visit(operandos[0])

        for i in range(1, len(operandos)):
            operador = ctx.getChild(2 * i - 1).getText()
            derecho = self.visit(operandos[i])
            linea = ctx.start.line

            if operador == "+":
                if es_numero(resultado) and es_numero(derecho):
                    resultado = resultado + derecho
                elif isinstance(resultado, str) and isinstance(derecho, str):
                    resultado = resultado + derecho
                elif isinstance(resultado, list) and isinstance(derecho, list):
                    resultado = resultado + derecho
                else:
                    raise ErrorSemantico(
                        f"no se puede sumar {nombre_tipo(resultado)} con "
                        f"{nombre_tipo(derecho)}", linea)
            else:
                self._exigir_numeros(resultado, derecho, "-", linea)
                resultado = resultado - derecho
        return resultado

    def visitTermino(self, ctx: TerraParser.TerminoContext):
        """Multiplicacion, division y modulo. Solo entre numeros."""
        operandos = ctx.potencia()
        resultado = self.visit(operandos[0])

        for i in range(1, len(operandos)):
            operador = ctx.getChild(2 * i - 1).getText()
            derecho = self.visit(operandos[i])
            linea = ctx.start.line

            self._exigir_numeros(resultado, derecho, operador, linea)

            if operador == "*":
                resultado = resultado * derecho
            elif operador == "/":
                if derecho == 0:
                    raise ErrorSemantico("division por cero", linea)
                resultado = resultado / derecho
            else:
                if derecho == 0:
                    raise ErrorSemantico("modulo por cero", linea)
                resultado = resultado % derecho
        return resultado

    def visitPotencia(self, ctx: TerraParser.PotenciaContext):
        """Potencia, asociativa a la derecha: 2 ^ 3 ^ 2 es 2 ^ (3 ^ 2)."""
        base = self.visit(ctx.unario())
        if ctx.potencia() is None:
            return base

        exponente = self.visit(ctx.potencia())
        self._exigir_numeros(base, exponente, "^", ctx.start.line)
        return base ** exponente

    def visitUnario(self, ctx: TerraParser.UnarioContext):
        """Negativo aritmetico y negacion logica."""
        if ctx.postfijo() is not None:
            return self.visit(ctx.postfijo())

        operador = ctx.getChild(0).getText()
        valor = self.visit(ctx.unario())
        linea = ctx.start.line

        if operador == "-":
            if not es_numero(valor):
                raise ErrorSemantico(
                    f"el negativo solo aplica a numeros, se recibio "
                    f"{nombre_tipo(valor)}", linea)
            return -valor

        if not isinstance(valor, bool):
            raise ErrorSemantico(
                f"'!' solo aplica a booleanos, se recibio "
                f"{nombre_tipo(valor)}", linea)
        return not valor

    def visitPostfijo(self, ctx: TerraParser.PostfijoContext):
        """Indexacion de listas y textos: lista[0], texto[2]."""
        valor = self.visit(ctx.primario())
        linea = ctx.start.line

        for indice_ctx in ctx.expr():
            indice = self.visit(indice_ctx)

            if not isinstance(valor, (list, str)):
                raise ErrorSemantico(
                    f"solo se puede indexar una lista o un texto, se "
                    f"recibio {nombre_tipo(valor)}", linea)
            if isinstance(indice, bool) or not isinstance(indice, int):
                raise ErrorSemantico(
                    f"el indice debe ser un numero entero, se recibio "
                    f"{nombre_tipo(indice)}", linea)
            if indice < 0 or indice >= len(valor):
                raise ErrorSemantico(
                    f"indice {indice} fuera de rango (longitud "
                    f"{len(valor)})", linea)

            valor = valor[indice]
        return valor

    def visitPrimario(self, ctx: TerraParser.PrimarioContext):
        """Literales, variables, listas, llamadas y parentesis."""
        linea = ctx.start.line

        if ctx.NUMERO() is not None:
            return int(ctx.NUMERO().getText())
        if ctx.DECIMAL() is not None:
            return float(ctx.DECIMAL().getText())
        if ctx.TEXTO() is not None:
            crudo = ctx.TEXTO().getText()[1:-1]
            # Secuencias de escape: \n salto de linea, \t tabulador,
            # \" comilla y \\ barra invertida
            return (crudo.replace("\\\\", "\x00")
                    .replace('\\"', '"')
                    .replace("\\n", "\n")
                    .replace("\\t", "\t")
                    .replace("\x00", "\\"))
        if ctx.BOOLEANO() is not None:
            return ctx.BOOLEANO().getText() == "verdadero"
        if ctx.NULO() is not None:
            return None
        if ctx.carga() is not None:
            return self.visit(ctx.carga())
        if ctx.llamada() is not None:
            return self.visit(ctx.llamada())
        if ctx.lista() is not None:
            return self.visit(ctx.lista())
        if ctx.expresion() is not None:
            return self.visit(ctx.expresion())

        if ctx.funcion_anonima() is not None:
            return self.visit(ctx.funcion_anonima())

        nombre = ctx.IDENTIFICADOR().getText()
        if nombre not in self.memoria:
            # El nombre de una funcion escrito sin parentesis es un valor
            # de tipo funcion: asi se puede pasar a mapear, filtro, etc.
            if nombre in self.funciones or nombre in self._incorporadas():
                return biblioteca.FuncionNombrada(nombre)
            raise ErrorSemantico(
                f"la variable '{nombre}' no ha sido declarada", linea)
        return self.memoria[nombre]["valor"]

    def visitFuncion_anonima(self, ctx):
        """
        funcion(x, y) => expresion
        Crea un valor de tipo funcion. El cuerpo no se evalua aqui, sino
        cada vez que alguien llama a la funcion.
        """
        parametros = [t.getText() for t in ctx.IDENTIFICADOR()]
        if len(set(parametros)) != len(parametros):
            raise ErrorSemantico(
                "un parametro aparece repetido en la funcion anonima",
                ctx.start.line)
        return biblioteca.FuncionAnonima(parametros, ctx.expr())

    def visitLista(self, ctx: TerraParser.ListaContext):
        return [self.visit(e) for e in ctx.expr()]

    # -----------------------------------------------------------------
    # FUNCIONES INCORPORADAS
    # -----------------------------------------------------------------

    def _incorporadas(self):
        """
        Catalogo de funciones que trae el lenguaje.

        Se arma una sola vez y se guarda, porque visitLlamada lo consulta
        en cada llamada (en un 'filtrar' eso es una vez por fila). A las
        funciones propias del evaluador se suman las de src/biblioteca.py:
        matematicas, matrices y las de los pasos siguientes.
        """
        if getattr(self, "_catalogo", None) is None:
            self._catalogo = {
                "longitud": self._f_longitud,
                "suma": self._f_suma,
                "describir": self._f_describir,
                "contar": self._f_contar,
                "media": self._f_media,
                "mediana": self._f_mediana,
                "minimo": self._f_minimo,
                "maximo": self._f_maximo,
                "desviacion": self._f_desviacion,
                "raiz": self._f_raiz,
                "absoluto": self._f_absoluto,
                "redondear": self._f_redondear,
                "a_numero": self._f_a_numero,
                "a_decimal": self._f_a_decimal,
                "a_texto": self._f_a_texto,
            }
            for nombre, funcion in biblioteca.funciones(self).items():
                self._catalogo[nombre] = self._envolver(funcion)
        return self._catalogo

    def _envolver(self, funcion):
        """
        Adapta una funcion de la biblioteca: los ErrorDatos que lance se
        convierten en ErrorSemantico con la linea de la llamada.
        """
        def llamar(args, linea):
            try:
                return funcion(args, linea)
            except ErrorDatos as e:
                raise ErrorSemantico(str(e), linea)
        return llamar

    def visitLlamada(self, ctx: TerraParser.LlamadaContext):
        """
        Resuelve una llamada a funcion.

        Primero busca entre las incorporadas y despues entre las que
        definio el usuario. Ese orden garantiza que una definicion
        propia nunca oculte una del lenguaje.
        """
        nombre = ctx.IDENTIFICADOR().getText()
        linea = ctx.start.line
        argumentos = [self.visit(a) for a in ctx.expr()]

        incorporadas = self._incorporadas()
        if nombre in incorporadas:
            return incorporadas[nombre](argumentos, linea)
        if nombre in self.funciones:
            return self._invocar(nombre, argumentos, linea)

                # Una variable que guarda una funcion tambien se puede llamar
        if nombre in self.memoria and biblioteca.es_funcion(
                self.memoria[nombre]["valor"]):
            try:
                return biblioteca.llamar_funcion(
                    self, self.memoria[nombre]["valor"], argumentos, linea)
            except ErrorDatos as e:
                raise ErrorSemantico(str(e), linea)
        raise ErrorSemantico(f"la funcion '{nombre}' no existe", linea)

    def visitFuncion_decl(self, ctx):
        """
        Registra una funcion definida por el usuario.

        No ejecuta el cuerpo: solo guarda sus parametros y el nodo del
        bloque para visitarlo cuando alguien la llame.
        """
        identificadores = ctx.IDENTIFICADOR()
        nombre = identificadores[0].getText()
        parametros = [t.getText() for t in identificadores[1:]]
        linea = ctx.start.line

        if nombre in self._incorporadas():
            raise ErrorSemantico(
                f"'{nombre}' es una funcion incorporada del lenguaje y no "
                f"puede redefinirse", linea)
        if nombre in self.funciones:
            raise ErrorSemantico(
                f"la funcion '{nombre}' ya fue definida", linea)
        if len(set(parametros)) != len(parametros):
            raise ErrorSemantico(
                f"la funcion '{nombre}' repite el nombre de un parametro",
                linea)

        self.funciones[nombre] = {
            "parametros": parametros,
            "cuerpo": ctx.bloque(),
        }
        return None

    def _invocar(self, nombre, argumentos, linea):
        """
        Ejecuta una funcion del usuario y devuelve su resultado.

        El cuerpo se evalua con una memoria propia que contiene solo los
        parametros: la funcion no ve las variables del programa principal
        ni puede modificarlas. Al terminar se restaura la memoria
        anterior, de modo que la llamada no deja rastro.

        Una funcion sin 'retornar' devuelve nulo.
        """
        definicion = self.funciones[nombre]
        parametros = definicion["parametros"]

        if len(argumentos) != len(parametros):
            raise ErrorSemantico(
                f"la funcion '{nombre}' espera {len(parametros)} "
                f"argumento(s) y recibio {len(argumentos)}", linea)

        if self.profundidad >= self.LIMITE_RECURSION:
            raise ErrorSemantico(
                f"la funcion '{nombre}' supero el limite de "
                f"{self.LIMITE_RECURSION} llamadas anidadas; revisa el caso "
                f"base de la recursion", linea)

        memoria_anterior = self.memoria
        self.memoria = {
            p: {"valor": v, "mutable": True}
            for p, v in zip(parametros, argumentos)
        }
        self.profundidad += 1

        try:
            self.visit(definicion["cuerpo"])
            resultado = None
        except RetornoSenal as senal:
            resultado = senal.valor
        except RecursionError:
            raise ErrorSemantico(
                f"la funcion '{nombre}' se llamo demasiadas veces de forma "
                f"anidada y se agoto la pila; revisa el caso base de la "
                f"recursion", linea)
        finally:
            self.memoria = memoria_anterior
            self.profundidad -= 1

        return resultado

    def visitRetornar_stmt(self, ctx):
        """Interrumpe la funcion actual y entrega un valor a la llamada."""
        if self.profundidad == 0:
            raise ErrorSemantico(
                "'retornar' solo puede usarse dentro de una funcion",
                ctx.start.line)

        valor = (self.visit(ctx.expresion())
                 if ctx.expresion() is not None else None)
        raise RetornoSenal(valor)

    def _lista_numerica(self, argumentos, linea, funcion):
        """Valida que el argumento sea una lista de numeros y la devuelve."""
        if len(argumentos) != 1 or not isinstance(argumentos[0], list):
            raise ErrorSemantico(
                f"{funcion}() espera una lista de numeros", linea)
        datos = argumentos[0]
        if not datos:
            raise ErrorSemantico(
                f"{funcion}() no puede operar sobre una lista vacia", linea)
        for valor in datos:
            if not es_numero(valor):
                raise ErrorSemantico(
                    f"{funcion}() solo acepta numeros, encontro "
                    f"{nombre_tipo(valor)}", linea)
        return datos

    def _un_numero(self, argumentos, linea, funcion):
        """Valida que haya exactamente un argumento numerico."""
        if len(argumentos) != 1 or not es_numero(argumentos[0]):
            raise ErrorSemantico(
                f"{funcion}() espera un numero", linea)
        return argumentos[0]

    def _f_longitud(self, args, linea):
        if len(args) != 1 or not isinstance(args[0], (list, str)):
            raise ErrorSemantico("longitud() espera una lista o un texto",
                                 linea)
        return len(args[0])

    def _f_describir(self, args, linea):
        """describir(tabla) -> tabla con estadisticas de cada columna."""
        if len(args) != 1 or not isinstance(args[0], Tabla):
            recibido = ", ".join(nombre_tipo(a) for a in args) or "nada"
            raise ErrorSemantico(
                f"describir() necesita una tabla, se recibio {recibido}",
                linea)
        return ops.describir(args[0])

    def _f_contar(self, args, linea):
        """
        contar()      -> numero de filas del grupo (solo en 'resumir')
        contar(lista) -> cantidad de elementos de la lista
        """
        if not args:
            tamano = getattr(self, "_tamano_grupo", None)
            if tamano is None:
                raise ErrorSemantico(
                    "contar() sin argumentos solo puede usarse dentro "
                    "de 'resumir'", linea)
            return tamano
        if len(args) == 1 and isinstance(args[0], list):
            return len(args[0])
        raise ErrorSemantico(
            "contar() recibe una lista o ningun argumento", linea)
    def _f_suma(self, args, linea):
        return sum(self._lista_numerica(args, linea, "suma"))

    def _f_media(self, args, linea):
        datos = self._lista_numerica(args, linea, "media")
        return sum(datos) / len(datos)

    def _f_mediana(self, args, linea):
        datos = sorted(self._lista_numerica(args, linea, "mediana"))
        n = len(datos)
        medio = n // 2
        if n % 2 == 1:
            return datos[medio]
        return (datos[medio - 1] + datos[medio]) / 2

    def _f_minimo(self, args, linea):
        return min(self._lista_numerica(args, linea, "minimo"))

    def _f_maximo(self, args, linea):
        return max(self._lista_numerica(args, linea, "maximo"))

    def _f_desviacion(self, args, linea):
        """Desviacion estandar muestral, calculada sin librerias."""
        datos = self._lista_numerica(args, linea, "desviacion")
        if len(datos) < 2:
            raise ErrorSemantico(
                "desviacion() necesita al menos dos valores", linea)
        promedio = sum(datos) / len(datos)
        varianza = sum((x - promedio) ** 2 for x in datos) / (len(datos) - 1)
        return varianza ** 0.5

    def _f_raiz(self, args, linea):
        valor = self._un_numero(args, linea, "raiz")
        if valor < 0:
            raise ErrorSemantico(
                "raiz() no acepta numeros negativos", linea)
        return valor ** 0.5

    def _f_absoluto(self, args, linea):
        return abs(self._un_numero(args, linea, "absoluto"))

    def _f_redondear(self, args, linea):
        """redondear(x) o redondear(x, decimales)."""
        if not args or not es_numero(args[0]):
            raise ErrorSemantico("redondear() espera un numero", linea)
        if len(args) == 1:
            return round(args[0])
        if isinstance(args[1], bool) or not isinstance(args[1], int):
            raise ErrorSemantico(
                "el segundo argumento de redondear() debe ser un entero",
                linea)
        return round(args[0], args[1])

    def _f_a_numero(self, args, linea):
        """Conversion explicita a numero entero."""
        if len(args) != 1:
            raise ErrorSemantico("a_numero() espera un argumento", linea)
        valor = args[0]
        if es_numero(valor):
            return int(valor)
        if isinstance(valor, str):
            try:
                return int(float(valor))
            except ValueError:
                raise ErrorSemantico(
                    f"no se puede convertir \"{valor}\" a numero", linea)
        raise ErrorSemantico(
            f"no se puede convertir {nombre_tipo(valor)} a numero", linea)

    def _f_a_decimal(self, args, linea):
        """Conversion explicita a decimal."""
        if len(args) != 1:
            raise ErrorSemantico("a_decimal() espera un argumento", linea)
        valor = args[0]
        if es_numero(valor):
            return float(valor)
        if isinstance(valor, str):
            try:
                return float(valor)
            except ValueError:
                raise ErrorSemantico(
                    f"no se puede convertir \"{valor}\" a decimal", linea)
        raise ErrorSemantico(
            f"no se puede convertir {nombre_tipo(valor)} a decimal", linea)

    def _f_a_texto(self, args, linea):
        """Conversion explicita a texto."""
        if len(args) != 1:
            raise ErrorSemantico("a_texto() espera un argumento", linea)
        return formatear(args[0])

    # -----------------------------------------------------------------
    # VALIDACIONES COMPARTIDAS
    # -----------------------------------------------------------------

    def _exigir_numeros(self, izquierdo, derecho, operador, linea):
        """Aborta si alguno de los dos operandos no es numerico."""
        if not (es_numero(izquierdo) and es_numero(derecho)):
            raise ErrorSemantico(
                f"'{operador}' solo opera sobre numeros, se recibio "
                f"{nombre_tipo(izquierdo)} y {nombre_tipo(derecho)}", linea)

    def _exigir_booleano(self, valor, operador, linea):
        """Aborta si el valor no es booleano."""
        if not isinstance(valor, bool):
            raise ErrorSemantico(
                f"'{operador}' solo opera sobre booleanos, se recibio "
                f"{nombre_tipo(valor)}", linea)
