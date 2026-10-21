"""
test_biblioteca.py
==================
Pruebas de las funciones agregadas en src/biblioteca.py:

    - matematicas y matrices (series de Taylor, Gauss, Gauss-Jordan)
    - gestor de memoria y limite de recursion
    - funciones anonimas y de orden superior
    - entrada por teclado
    - puente entre tablas, listas y matrices; union de tablas
    - archivos de texto, guardar con separador y secuencias de escape

Ejecucion:
    pytest tests/test_biblioteca.py -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tabla import Tabla, leer_csv
from src.visitante_evaluador import ErrorSemantico
from tests.test_terra import evaluar, ejecutar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, "datos", "emisiones_ejemplo.csv")
CARGA = f'fijo d = cargar "{CSV}"\n'


# =====================================================================
# MATEMATICAS
# =====================================================================

def test_seno_y_coseno():
    assert evaluar("fijo r = seno(pi() / 6)\n") == pytest.approx(0.5)
    assert evaluar("fijo r = coseno(pi())\n") == pytest.approx(-1.0)


def test_seno_de_angulo_grande():
    # La reduccion de rango debe funcionar lejos de cero
    assert evaluar("fijo r = seno(100 * pi() + pi() / 2)\n") == pytest.approx(1.0)


def test_tangente():
    assert evaluar("fijo r = tangente(pi() / 4)\n") == pytest.approx(1.0)


def test_tangente_no_definida():
    with pytest.raises(ErrorSemantico, match="no esta definida"):
        evaluar("fijo r = tangente(pi() / 2)\n")


def test_exp_y_ln_son_inversas():
    assert evaluar("fijo r = ln(exp(3))\n") == pytest.approx(3.0)
    assert evaluar("fijo r = exp(1)\n") == pytest.approx(2.718281828459045)


def test_ln_de_cero():
    with pytest.raises(ErrorSemantico, match="mayores que 0"):
        evaluar("fijo r = ln(0)\n")


def test_log_en_base_10_y_base_2():
    assert evaluar("fijo r = log(1000)\n") == 3.0
    assert evaluar("fijo r = log(8, 2)\n") == 3.0


def test_piso_techo_factorial():
    assert evaluar("fijo r = piso(-2.5)\n") == -3
    assert evaluar("fijo r = techo(2.1)\n") == 3
    assert evaluar("fijo r = factorial(10)\n") == 3628800


def test_funcion_con_argumentos_de_mas():
    with pytest.raises(ErrorSemantico, match="recibe 1 argumento"):
        evaluar("fijo r = seno(1, 2)\n")


def test_aleatorio_es_reproducible():
    a = evaluar("semilla(7)\nfijo r = aleatorio()\n")
    b = evaluar("semilla(7)\nfijo r = aleatorio()\n")
    assert a == b
    assert 0 <= a < 1


# =====================================================================
# MATRICES
# =====================================================================

def test_producto_de_matrices():
    r = evaluar("fijo r = mult_matriz([[1, 2, 3], [4, 5, 6]], "
                "[[7, 8], [9, 10], [11, 12]])\n")
    assert r == [[58, 64], [139, 154]]


def test_dimensiones_incompatibles():
    with pytest.raises(ErrorSemantico, match="dimensiones incompatibles"):
        evaluar("fijo r = mult_matriz([[1, 2]], [[1, 2]])\n")


def test_determinante():
    assert evaluar("fijo r = determinante([[4, 7], [2, 6]])\n") == 10.0
    assert evaluar("fijo r = determinante([[1, 2], [2, 4]])\n") == 0.0


def test_inversa_por_matriz_da_identidad():
    r = evaluar("fijo A = [[4, 7], [2, 6]]\n"
                "fijo r = mult_matriz(A, inversa(A))\n")
    assert r == [[1.0, 0.0], [0.0, 1.0]]


def test_matriz_singular_no_tiene_inversa():
    with pytest.raises(ErrorSemantico, match="no tiene inversa"):
        evaluar("fijo r = inversa([[1, 2], [2, 4]])\n")


def test_transpuesta_identidad_dimension():
    assert evaluar("fijo r = transpuesta([[1, 2, 3], [4, 5, 6]])\n") == \
        [[1, 4], [2, 5], [3, 6]]
    assert evaluar("fijo r = identidad(2)\n") == [[1, 0], [0, 1]]
    assert evaluar("fijo r = dimension(ceros(3, 4))\n") == [3, 4]


def test_filas_de_distinto_tamano():
    with pytest.raises(ErrorSemantico, match="distinto tamano"):
        evaluar("fijo r = transpuesta([[1, 2], [3]])\n")


def test_vectores():
    assert evaluar("fijo r = producto_punto([1, 2, 3], [4, 5, 6])\n") == 32
    assert evaluar("fijo r = norma([3, 4])\n") == 5.0


# =====================================================================
# MEMORIA Y RECURSION
# =====================================================================

FACTORIAL = """funcion fact(n):
    si n <= 1:
        retornar 1
    fin
    retornar n * fact(n - 1)
fin
"""


def test_recursion_profunda_dentro_del_limite():
    assert evaluar(FACTORIAL + "fijo r = fact(150)\n") > 10 ** 260


def test_recursion_infinita_se_detiene():
    with pytest.raises(ErrorSemantico, match="limite"):
        evaluar("funcion f(n):\n    retornar f(n + 1)\nfin\n"
                "fijo r = f(1)\n")


def test_fijar_limite_de_recursion():
    with pytest.raises(ErrorSemantico, match="10"):
        evaluar("fijar_limite_recursion(10)\n" + FACTORIAL +
                "fijo r = fact(50)\n")


def test_limite_de_recursion_maximo():
    with pytest.raises(ErrorSemantico, match="maximo"):
        evaluar("fijar_limite_recursion(999999)\nfijo r = 1\n")


def test_matriz_demasiado_grande():
    with pytest.raises(ErrorSemantico, match="limite de memoria"):
        evaluar("fijo r = ceros(10000, 10000)\n")


def test_memoria_info():
    t = evaluar("fijo x = 5\nfijo lista = [1, 2, 3]\n"
                "fijo r = memoria_info()\n")
    assert isinstance(t, Tabla)
    assert t.columna("variable")[-1] == "TOTAL"
    assert "lista" in t.columna("variable")


def test_liberar_elimina_la_variable():
    with pytest.raises(ErrorSemantico, match="no ha sido declarada"):
        evaluar('var x = 5\nliberar("x")\nfijo r = x\n')


def test_liberar_variable_inexistente():
    with pytest.raises(ErrorSemantico, match="no existe"):
        evaluar('liberar("nada")\nfijo r = 1\n')


# =====================================================================
# FUNCIONES ANONIMAS Y DE ORDEN SUPERIOR
# =====================================================================

def test_mapear_con_funcion_anonima():
    assert evaluar("fijo r = mapear([1, 2, 3], funcion(x) => x * 2)\n") == \
        [2, 4, 6]


def test_filtro():
    assert evaluar("fijo r = filtro(rango(1, 11), "
                   "funcion(n) => n % 2 == 0)\n") == [2, 4, 6, 8, 10]


def test_reducir_con_y_sin_valor_inicial():
    assert evaluar("fijo r = reducir([1, 2, 3, 4], "
                   "funcion(a, b) => a + b)\n") == 10
    assert evaluar("fijo r = reducir([1, 2, 3, 4], "
                   "funcion(a, b) => a * b, 1)\n") == 24


def test_variable_que_guarda_una_funcion():
    assert evaluar("fijo doble = funcion(x) => x * 2\n"
                   "fijo r = doble(21)\n") == 42


def test_funcion_con_nombre_como_valor():
    assert evaluar("funcion cuadrado(x):\n    retornar x * x\nfin\n"
                   "fijo r = mapear([1, 2, 3], cuadrado)\n") == [1, 4, 9]
    assert evaluar("fijo r = mapear([1, 4, 9], raiz)\n") == [1, 2, 3]


def test_funcion_anonima_usa_variables_del_programa():
    assert evaluar("fijo factor = 10\n"
                   "fijo r = mapear([1, 2], funcion(x) => x * factor)\n") == \
        [10, 20]


def test_ordenar_por_todos_alguno():
    assert evaluar('fijo r = ordenar_por([3, 1, 2], funcion(x) => x, '
                   '"desc")\n') == [3, 2, 1]
    assert evaluar("fijo r = todos([2, 4], funcion(x) => x % 2 == 0)\n") is True
    assert evaluar("fijo r = alguno([1, 3], funcion(x) => x > 5)\n") is False


def test_componer_y_aplicar_matriz():
    assert evaluar("fijo f = componer(funcion(x) => x + 1, "
                   "funcion(x) => x * 2)\nfijo r = f(5)\n") == 11
    assert evaluar("fijo r = aplicar_matriz([[1, 2], [3, 4]], "
                   "funcion(x) => x * 10)\n") == [[10, 20], [30, 40]]


def test_mapear_sin_funcion():
    with pytest.raises(ErrorSemantico, match="debe ser una funcion"):
        evaluar("fijo r = mapear([1, 2], 5)\n")


def test_filtro_con_funcion_no_booleana():
    with pytest.raises(ErrorSemantico, match="verdadero o falso"):
        evaluar("fijo r = filtro([1, 2], funcion(x) => x * 2)\n")


def test_funcion_anonima_con_argumentos_de_mas():
    with pytest.raises(ErrorSemantico, match="espera 1"):
        evaluar("fijo f = funcion(x) => x\nfijo r = f(1, 2)\n")


def test_parametro_repetido():
    with pytest.raises(ErrorSemantico, match="repetido"):
        evaluar("fijo r = funcion(x, x) => x\n")


def test_rango():
    assert evaluar("fijo r = rango(5)\n") == [0, 1, 2, 3, 4]
    assert evaluar("fijo r = rango(10, 0, -3)\n") == [10, 7, 4, 1]


# =====================================================================
# ENTRADA POR TECLADO
# =====================================================================

def _teclado(monkeypatch, respuestas):
    datos = iter(respuestas)
    monkeypatch.setattr("builtins.input", lambda mensaje="": next(datos))


def test_leer_texto(monkeypatch):
    _teclado(monkeypatch, ["Natalia"])
    assert evaluar('fijo r = leer("Nombre: ")\n') == "Natalia"


def test_leer_numero_reintenta(monkeypatch, capsys):
    _teclado(monkeypatch, ["abc", "3.5"])
    assert evaluar('fijo r = leer_numero("Valor: ")\n') == 3.5
    assert "no es un numero" in capsys.readouterr().out


def test_leer_sin_datos(monkeypatch):
    def sin_datos(mensaje=""):
        raise EOFError
    monkeypatch.setattr("builtins.input", sin_datos)
    with pytest.raises(ErrorSemantico, match="no hay mas datos"):
        evaluar("fijo r = leer()\n")


# =====================================================================
# TABLAS, LISTAS Y MATRICES
# =====================================================================

def test_columna_de_tabla_a_lista():
    r = evaluar(CARGA + 'fijo r = media(columna(d, "co2"))\n')
    assert r == pytest.approx(65.9625)


def test_nombres_filas_y_unicos():
    assert evaluar(CARGA + "fijo r = num_filas(d)\n") == 16
    assert evaluar(CARGA + 'fijo r = valores_unicos(d, "pais")\n') == \
        ["Colombia", "Peru", "Chile", "Ecuador"]


def test_tabla_desde_y_a_matriz():
    t = evaluar('fijo r = tabla_desde(["a", "b"], [[1, 2], [3, 4]])\n')
    assert t.filas == [[1, 2], [3, 4]]
    assert evaluar('fijo t = tabla_desde(["a", "b"], [[1, 2], [3, 4]])\n'
                   'fijo r = a_matriz(t)\n') == [[1, 2], [3, 4]]


def test_a_matriz_con_texto():
    with pytest.raises(ErrorSemantico, match="no numerico"):
        evaluar(CARGA + "fijo r = a_matriz(d)\n")


def test_unir_interna_e_izquierda():
    base = (CARGA +
            "fijo d21 = d |> filtrar donde anio == 2021\n"
            'fijo metas = tabla_desde(["pais", "meta"], '
            '[["Colombia", 70], ["Chile", 80]])\n')
    interna = evaluar(base + 'fijo r = unir(d21, metas, "pais")\n')
    izquierda = evaluar(base + 'fijo r = unir(d21, metas, "pais", "izquierda")\n')
    assert interna.num_filas == 2
    assert izquierda.num_filas == 4
    assert izquierda.columna("meta").count(None) == 2


def test_unir_con_columnas_repetidas():
    with pytest.raises(ErrorSemantico, match="existe en las dos"):
        evaluar(CARGA + 'fijo r = unir(d, d, "pais")\n')


def test_concatenar():
    assert evaluar(CARGA + "fijo r = num_filas(concatenar(d, d))\n") == 32


# =====================================================================
# ARCHIVOS, SEPARADOR AL GUARDAR Y ESCAPES
# =====================================================================

def test_archivos_de_texto(tmp_path):
    ruta = str(tmp_path / "registro.txt")
    r = evaluar(f'escribir_archivo("{ruta}", "uno\\n")\n'
                f'agregar_archivo("{ruta}", "dos\\n")\n'
                f'fijo r = leer_lineas("{ruta}")\n')
    assert r == ["uno", "dos"]


def test_existe_y_borrar_archivo(tmp_path):
    ruta = str(tmp_path / "x.txt")
    assert evaluar(f'escribir_archivo("{ruta}", "x")\n'
                   f'borrar_archivo("{ruta}")\n'
                   f'fijo r = existe_archivo("{ruta}")\n') is False


def test_leer_archivo_inexistente():
    with pytest.raises(ErrorSemantico, match="no se encontro"):
        evaluar('fijo r = leer_archivo("no_existe.txt")\n')


def test_guardar_con_separador(tmp_path):
    ruta = str(tmp_path / "salida.csv")
    evaluar(CARGA + f'guardar d como "{ruta}" con separador ";"\nfijo r = 1\n')
    assert ";" in open(ruta, encoding="utf-8").readline()
    assert leer_csv(ruta, ";").filas == leer_csv(CSV).filas


def test_secuencias_de_escape():
    assert evaluar('fijo r = "a\\nb\\tc"\n') == "a\nb\tc"
