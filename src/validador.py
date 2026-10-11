"""
validador.py
============
Modo de validacion interactiva de Terra.

Lee lo que el usuario escribe y responde unicamente si el lenguaje
acepta o rechaza esa entrada, sin ejecutarla. Sirve para comprobar la
gramatica de forma rapida, que es la evidencia central del primer
corte: reconocimiento de programas correctos y rechazo de incorrectos.

Uso:
    python src/validador.py

Las construcciones de varias lineas (si, mientras, para) se escriben
completas: el validador acumula lineas hasta encontrar 'fin' o hasta
recibir una linea vacia.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.terra import Terra


def veredicto(interprete: Terra, codigo: str) -> None:
    """Analiza el codigo e imprime si Terra lo acepta o lo rechaza."""
    _, _, err_lex, err_sin = interprete.analizar(codigo)
    errores = err_lex.errores + err_sin.errores

    if not errores:
        print("  ACEPTADO: Terra reconoce esta construccion.\n")
        return

    print(f"  RECHAZADO: {len(errores)} error(es).")
    for e in errores:
        origen = "lexico" if e["origen"] == "lexico" else "sintactico"
        print(f"    linea {e['linea']}:{e['columna']}  ({origen}) "
              f"{e['mensaje']}")
    print()


def necesita_mas_lineas(buffer: list) -> bool:
    """
    Decide si la construccion sigue abierta.

    Cuenta los bloques abiertos (lineas que terminan en ':') contra los
    cerrados ('fin'). Mientras haya mas aperturas que cierres, el
    validador sigue pidiendo lineas.
    """
    abiertos = 0
    for linea in buffer:
        limpia = linea.split("#")[0].strip()
        if limpia.endswith(":"):
            abiertos += 1
        elif limpia == "fin":
            abiertos -= 1
    return abiertos > 0


def main():
    """Bucle de validacion interactiva."""
    interprete = Terra()

    print("=" * 60)
    print("  TERRA - validador de sintaxis")
    print("=" * 60)
    print("  Escribe una construccion y te digo si el lenguaje la acepta.")
    print("  Los bloques (si, mientras, para) se cierran con 'fin'.")
    print("  Escribe 'salir' para terminar.")
    print("-" * 60)

    buffer = []

    while True:
        try:
            prompt = "  ... " if buffer else "terra? "
            linea = input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\nHasta luego.")
            break

        if not buffer and linea.strip().lower() in ("salir", "exit", "quit"):
            print("Hasta luego.")
            break

        if not linea.strip() and not buffer:
            continue

        buffer.append(linea)

        # Una linea vacia fuerza el cierre de un bloque incompleto:
        # asi el usuario puede comprobar que Terra lo rechaza.
        if linea.strip() == "" or not necesita_mas_lineas(buffer):
            codigo = "\n".join(buffer) + "\n"
            veredicto(interprete, codigo)
            buffer = []


if __name__ == "__main__":
    main()
