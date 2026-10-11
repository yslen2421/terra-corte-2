"""
terra.py
========
Punto de entrada del interprete Terra.

Orquesta el proceso completo: lectura del archivo fuente, analisis
lexico, analisis sintactico y (desde el segundo corte) evaluacion
semantica con el patron Visitor.

Flujo:
    programa .terra
        -> InputStream        (texto a stream de caracteres)
        -> TerraLexer         (texto a tokens)
        -> CommonTokenStream  (buffer de tokens)
        -> TerraParser        (tokens a arbol de analisis)
        -> VisitanteEvaluador (recorrido y ejecucion)

Uso:
    python src/terra.py                              # modo interactivo
    python src/terra.py ejemplos/01_variables.terra  # ejecutar archivo
    python src/terra.py ejemplos/01_variables.terra --arbol
    python src/terra.py ejemplos/01_variables.terra --tokens
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from antlr4 import InputStream, CommonTokenStream
from gramaticas.TerraLexer import TerraLexer
from gramaticas.TerraParser import TerraParser
from src.manejador_errores import ManejadorErrores

EXTENSION = ".terra"


class Terra:
    """
    Interprete principal del lenguaje Terra.

    El visitante mantiene el estado del programa entre llamadas, lo que
    permite que el modo interactivo recuerde las variables declaradas en
    lineas anteriores.
    """

    def __init__(self, modo_interactivo=False):
        self.modo_interactivo = modo_interactivo
        self.visitante = self._cargar_visitante()

    def _cargar_visitante(self):
        """
        Carga el visitante evaluador si ya existe.

        En el primer corte el evaluador aun no esta implementado: el
        interprete se limita a validar la sintaxis. Cuando se agregue
        src/visitante_evaluador.py, este metodo lo detecta solo.
        """
        try:
            from src.visitante_evaluador import VisitanteEvaluador
            return VisitanteEvaluador(modo_interactivo=self.modo_interactivo)
        except ImportError:
            return None

    def analizar(self, codigo: str):
        """
        Ejecuta el lexer y el parser sobre una cadena de codigo.

        Returns:
            tuple: (arbol, parser, manejador_lexico, manejador_sintactico)
                El parser se devuelve porque hace falta para imprimir el
                arbol con nombres de regla en vez de indices numericos.
        """
        if not codigo.endswith("\n"):
            codigo += "\n"

        entrada = InputStream(codigo)

        manejador_lexico = ManejadorErrores(origen="lexico")
        lexer = TerraLexer(entrada)
        lexer.removeErrorListeners()
        lexer.addErrorListener(manejador_lexico)

        tokens = CommonTokenStream(lexer)

        manejador_sintactico = ManejadorErrores(origen="sintactico")
        parser = TerraParser(tokens)
        parser.removeErrorListeners()
        parser.addErrorListener(manejador_sintactico)

        arbol = parser.programa()
        return arbol, parser, manejador_lexico, manejador_sintactico

    def ejecutar_archivo(self, ruta: str, mostrar_arbol=False,
                         mostrar_tokens=False) -> None:
        """Lee y ejecuta un archivo .terra."""
        if not ruta.endswith(EXTENSION):
            print(f"Error: '{ruta}' no tiene extension {EXTENSION}")
            sys.exit(1)
        if not os.path.exists(ruta):
            print(f"Error: no se encuentra el archivo '{ruta}'")
            sys.exit(1)

        with open(ruta, "r", encoding="utf-8") as f:
            codigo = f.read()

        if mostrar_tokens:
            self._imprimir_tokens(codigo)
            return

        self._ejecutar_codigo(codigo, mostrar_arbol=mostrar_arbol)

    def _ejecutar_codigo(self, codigo: str, mostrar_arbol=False) -> None:
        """Analiza el codigo y, si es valido, lo evalua."""
        arbol, parser, err_lex, err_sin = self.analizar(codigo)

        if err_lex.tiene_error or err_sin.tiene_error:
            total = len(err_lex.errores) + len(err_sin.errores)
            print(f"\nEl programa contiene {total} error(es). No se ejecuta.",
                  file=sys.stderr)
            return

        if mostrar_arbol:
            print(arbol.toStringTree(recog=parser))
            return

        if self.visitante is None:
            print("Analisis lexico y sintactico correcto.")
            print("(El evaluador semantico se implementa en el segundo corte.)")
            return

        try:
            self.visitante.visit(arbol)
        except Exception as e:
            print(f"Error en evaluacion: {e}", file=sys.stderr)

    def _imprimir_tokens(self, codigo: str) -> None:
        """
        Imprime la lista de tokens reconocidos por el lexer.

        El mapa tipo -> nombre se construye desde las constantes del lexer
        generado y no desde symbolicNames, porque ese arreglo no incluye
        los literales anonimos ('(', '+', ...) y produce un desfase entre
        el tipo de token y su nombre.
        """
        lexer = TerraLexer(InputStream(codigo))
        tokens = CommonTokenStream(lexer)
        tokens.fill()

        nombres = {valor: nombre for nombre, valor in vars(TerraLexer).items()
                   if isinstance(valor, int) and nombre.isupper()}

        print(f"{'LINEA:COL':<12} {'TOKEN':<18} TEXTO")
        print("-" * 50)
        for token in tokens.tokens:
            if token.type == -1:
                nombre = "EOF"
            else:
                nombre = nombres.get(token.type, f"T{token.type}")
                if nombre.startswith("T__"):
                    nombre = "LITERAL"
            texto = token.text.replace("\n", "\\n")
            print(f"{token.line:>5}:{token.column:<6} {nombre:<18} {texto}")

    def modo_repl(self) -> None:
        """Modo interactivo. Solo admite expresiones de una linea."""
        print("Terra v0.1 - modo interactivo")
        print("Escribe una expresion o 'salir' para terminar")
        print("-" * 50)

        while True:
            try:
                linea = input("terra> ").strip()
                if not linea:
                    continue
                if linea.lower() in ("salir", "exit", "quit"):
                    print("Hasta luego.")
                    break
                self._ejecutar_codigo(linea + "\n")
            except KeyboardInterrupt:
                print("\nHasta luego.")
                break
            except EOFError:
                break


def main():
    """Decide el modo de ejecucion segun los argumentos de consola."""
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    banderas = [a for a in sys.argv[1:] if a.startswith("--")]

    if argumentos:
        interprete = Terra(modo_interactivo=False)
        interprete.ejecutar_archivo(
            argumentos[0],
            mostrar_arbol="--arbol" in banderas,
            mostrar_tokens="--tokens" in banderas,
        )
    else:
        interprete = Terra(modo_interactivo=True)
        interprete.modo_repl()


if __name__ == "__main__":
    main()
