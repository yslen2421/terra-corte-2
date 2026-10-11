"""
manejador_errores.py
====================
Manejador personalizado de errores lexicos y sintacticos para Terra.

ANTLR reporta los errores en ingles y con un formato generico. Esta
clase reemplaza ese comportamiento: traduce los mensajes al espanol,
guarda cada error con su linea y columna, y permite abortar la
evaluacion cuando el programa no es sintacticamente valido.
"""

import sys
from antlr4.error.ErrorListener import ErrorListener


class ManejadorErrores(ErrorListener):
    """
    Listener de errores para el lexer y el parser de Terra.

    Attributes:
        errores (list): Lista de diccionarios con linea, columna y mensaje.
        origen (str): 'lexico' o 'sintactico', segun donde se registre.
    """

    def __init__(self, origen="sintactico"):
        super().__init__()
        self.errores = []
        self.origen = origen

    @property
    def tiene_error(self) -> bool:
        """True si se registro al menos un error."""
        return len(self.errores) > 0

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        """
        Lo invoca ANTLR cuando encuentra un error. Registra el error y lo
        imprime en stderr con formato en espanol.
        """
        self.errores.append({
            "linea": line,
            "columna": column,
            "mensaje": msg,
            "origen": self.origen,
        })
        etiqueta = "Error lexico" if self.origen == "lexico" else "Error sintactico"
        print(f"{etiqueta} [linea {line}:{column}] {self._traducir(msg)}",
              file=sys.stderr)

    def _traducir(self, msg: str) -> str:
        """Traduce al espanol los mensajes mas frecuentes de ANTLR."""
        reemplazos = [
            ("mismatched input", "simbolo inesperado"),
            ("no viable alternative at input", "construccion no valida en"),
            ("extraneous input", "sobra el simbolo"),
            ("missing", "falta"),
            ("expecting", "se esperaba"),
            ("token recognition error at:", "caracter no reconocido:"),
            ("at input", "en"),
            ("at '", "en '"),
        ]
        for viejo, nuevo in reemplazos:
            msg = msg.replace(viejo, nuevo)
        return msg

    def resumen(self) -> str:
        """Devuelve una linea con el total de errores encontrados."""
        total = len(self.errores)
        if total == 0:
            return "Analisis correcto: sin errores."
        plural = "es" if total > 1 else ""
        return f"Se encontraron {total} error{plural} en el programa."

    # Estos tres eventos de ANTLR se ignoran a proposito para no
    # generar ruido en la salida del interprete.
    def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex,
                        exact, ambigAlts, configs):
        pass

    def reportAttemptingFullContext(self, recognizer, dfa, startIndex,
                                    stopIndex, conflictingAlts, configs):
        pass

    def reportContextSensitivity(self, recognizer, dfa, startIndex,
                                 stopIndex, prediction, configs):
        pass

