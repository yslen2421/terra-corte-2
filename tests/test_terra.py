"""
test_terra.py
=============
Suite de pruebas automatizadas de Terra.

Cubre tres frentes:
    - pruebas positivas: el lenguaje produce el resultado esperado
    - pruebas negativas: los programas invalidos fallan como deben
    - pruebas de front-end: el lexer y el parser reconocen la sintaxis

Ejecucion:
    pytest tests/ -v
    pytest tests/test_terra.py::test_suma -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.terra import Terra
from src.visitante_evaluador import ErrorSemantico


# =====================================================================
# UTILIDADES
# =====================================================================

def ejecutar(codigo: str, capsys) -> str:
    """Ejecuta codigo Terra y devuelve lo que imprimio, sin espacios."""
    interprete = Terra()
    interprete._ejecutar_codigo(codigo)
    return capsys.readouterr().out.strip()


def evaluar(codigo: str):
    """
    Evalua codigo y devuelve el valor de la ultima variable declarada.

    Invoca el visitante directamente y no el CLI, porque
    Terra._ejecutar_codigo atrapa los ErrorSemantico para mostrarlos al
    usuario sin traceback. Aqui necesitamos que la excepcion se propague
    para poder verificarla con pytest.raises.
    """
    interprete = Terra()
    arbol, _, err_lex, err_sin = interprete.analizar(codigo)
    assert not (err_lex.tiene_error or err_sin.tiene_error), \
        "el programa tiene errores sintacticos"

    interprete.visitante.visit(arbol)

    memoria = interprete.visitante.memoria
    if not memoria:
        return None
    ultimo = list(memoria)[-1]
    return memoria[ultimo]["valor"]

def errores_de(codigo: str):
    """Devuelve la lista de errores sintacticos de un programa."""
    interprete = Terra()
    _, _, err_lex, err_sin = interprete.analizar(codigo)
    return err_lex.errores + err_sin.errores


# =====================================================================
# LEXICO Y SINTAXIS
# =====================================================================

def test_programa_valido_sin_errores():
    assert errores_de('fijo x = 5\nmostrar(x)\n') == []


def test_comentario_de_linea_se_ignora():
    assert errores_de('# solo un comentario\nfijo x = 1\n') == []


def test_comentario_de_bloque_se_ignora():
    assert errores_de('/- varias\n   lineas -/\nfijo x = 1\n') == []


def test_identificador_no_puede_empezar_por_digito():
    assert len(errores_de('fijo 2x = 5\n')) > 0


def test_falta_dos_puntos_en_si():
    assert len(errores_de('si 1 > 0\n  mostrar(1)\nfin\n')) > 0


def test_parentesis_sin_cerrar():
    assert len(errores_de('mostrar("hola"\n')) > 0


def test_bloque_sin_fin():
    assert len(errores_de('si 1 > 0:\n  mostrar(1)\n')) > 0


def test_tuberia_se_reconoce():
    codigo = ('fijo t = datos\n'
              '    |> seleccionar [pais, co2]\n'
              '    |> filtrar donde co2 > 0\n')
    assert errores_de(codigo) == []


def test_graficar_se_reconoce():
    codigo = ('graficar barras resumen\n'
              '    eje_x pais\n'
              '    eje_y co2\n'
              '    titulo "Emisiones"\n')
    assert errores_de(codigo) == []


# =====================================================================
# VARIABLES
# =====================================================================

def test_declaracion_fijo():
    assert evaluar('fijo x = 42\n') == 42


def test_declaracion_var():
    assert evaluar('var x = 7\n') == 7


def test_reasignacion_de_var():
    assert evaluar('var x = 1\nx = 99\n') == 99


def test_fijo_no_se_puede_reasignar():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = 1\nx = 2\n')


def test_no_se_puede_redeclarar():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = 1\nfijo x = 2\n')


def test_variable_no_declarada():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo y = x + 1\n')


# =====================================================================
# TIPOS
# =====================================================================

def test_tipo_numero():
    assert evaluar('fijo x = 5\n') == 5


def test_tipo_decimal():
    assert evaluar('fijo x = 3.5\n') == 3.5


def test_tipo_texto():
    assert evaluar('fijo x = "bosque"\n') == "bosque"


def test_tipo_booleano():
    assert evaluar('fijo x = verdadero\n') is True


def test_tipo_nulo():
    assert evaluar('fijo x = nulo\n') is None


def test_tipo_lista():
    assert evaluar('fijo x = [1, 2, 3]\n') == [1, 2, 3]


def test_lista_vacia():
    assert evaluar('fijo x = []\n') == []


# =====================================================================
# ARITMETICA
# =====================================================================

def test_suma():
    assert evaluar('fijo x = 2 + 3\n') == 5


def test_resta():
    assert evaluar('fijo x = 10 - 4\n') == 6


def test_multiplicacion():
    assert evaluar('fijo x = 6 * 7\n') == 42


def test_division():
    assert evaluar('fijo x = 10 / 4\n') == 2.5


def test_modulo():
    assert evaluar('fijo x = 10 % 3\n') == 1


def test_potencia():
    assert evaluar('fijo x = 2 ^ 8\n') == 256


def test_potencia_asocia_a_la_derecha():
    assert evaluar('fijo x = 2 ^ 3 ^ 2\n') == 512


def test_precedencia_multiplicacion_sobre_suma():
    assert evaluar('fijo x = 2 + 3 * 4\n') == 14


def test_parentesis_cambian_precedencia():
    assert evaluar('fijo x = (2 + 3) * 4\n') == 20


def test_negativo_unario():
    assert evaluar('fijo x = -5 + 2\n') == -3


def test_division_por_cero():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = 1 / 0\n')


def test_modulo_por_cero():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = 1 % 0\n')


# =====================================================================
# TIPADO FUERTE
# =====================================================================

def test_no_suma_texto_con_numero():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = "a" + 1\n')


def test_no_multiplica_texto():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = "a" * 3\n')


def test_booleano_no_es_numero():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = verdadero + 1\n')


def test_no_compara_texto_con_numero():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = "a" > 1\n')


def test_and_exige_booleanos():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = 1 && verdadero\n')


def test_negacion_exige_booleano():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = !5\n')


def test_concatenacion_de_textos():
    assert evaluar('fijo x = "eco" + "sistema"\n') == "ecosistema"


def test_union_de_listas():
    assert evaluar('fijo x = [1, 2] + [3]\n') == [1, 2, 3]


# =====================================================================
# RELACIONALES Y LOGICOS
# =====================================================================

def test_mayor_que():
    assert evaluar('fijo x = 5 > 3\n') is True


def test_menor_igual():
    assert evaluar('fijo x = 3 <= 3\n') is True


def test_igualdad_de_textos():
    assert evaluar('fijo x = "a" == "a"\n') is True


def test_desigualdad():
    assert evaluar('fijo x = 1 != 2\n') is True


def test_numero_y_decimal_son_comparables():
    assert evaluar('fijo x = 2 == 2.0\n') is True


def test_and_logico():
    assert evaluar('fijo x = verdadero && falso\n') is False


def test_or_logico():
    assert evaluar('fijo x = verdadero || falso\n') is True


def test_negacion():
    assert evaluar('fijo x = !falso\n') is True


# =====================================================================
# PERTENENCIA E INDICES
# =====================================================================

def test_pertenencia_en_lista():
    assert evaluar('fijo x = 2 en [1, 2, 3]\n') is True


def test_no_pertenencia():
    assert evaluar('fijo x = 9 en [1, 2, 3]\n') is False


def test_pertenencia_en_texto():
    assert evaluar('fijo x = "bos" en "bosque"\n') is True


def test_indice_de_lista():
    assert evaluar('fijo x = [10, 20, 30][1]\n') == 20


def test_indice_de_texto():
    assert evaluar('fijo x = "abc"[0]\n') == "a"


def test_indice_fuera_de_rango():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = [1, 2][5]\n')


def test_indice_debe_ser_entero():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = [1, 2]["a"]\n')


# =====================================================================
# CONTROL DE FLUJO
# =====================================================================

def test_si_verdadero(capsys):
    assert ejecutar('si 1 < 2:\n  mostrar("si")\nfin\n', capsys) == "si"


def test_si_falso_no_ejecuta(capsys):
    assert ejecutar('si 1 > 2:\n  mostrar("no")\nfin\n', capsys) == ""


def test_sino(capsys):
    codigo = 'si 1 > 2:\n  mostrar("a")\nsino:\n  mostrar("b")\nfin\n'
    assert ejecutar(codigo, capsys) == "b"


def test_sino_si(capsys):
    codigo = ('fijo x = 0\n'
              'si x > 0:\n  mostrar("pos")\n'
              'sino si x == 0:\n  mostrar("cero")\n'
              'sino:\n  mostrar("neg")\nfin\n')
    assert ejecutar(codigo, capsys) == "cero"


def test_condicion_debe_ser_booleana():
    with pytest.raises(ErrorSemantico):
        evaluar('si 1:\n  mostrar(1)\nfin\n')


def test_mientras(capsys):
    codigo = 'var i = 0\nmientras i < 3:\n  mostrar(i)\n  i = i + 1\nfin\n'
    assert ejecutar(codigo, capsys) == "0\n1\n2"


def test_para_sobre_lista(capsys):
    codigo = 'para n en [1, 2, 3]:\n  mostrar(n)\nfin\n'
    assert ejecutar(codigo, capsys) == "1\n2\n3"


def test_para_sobre_texto(capsys):
    codigo = 'para c en "eco":\n  mostrar(c)\nfin\n'
    assert ejecutar(codigo, capsys) == "e\nc\no"


def test_para_no_recorre_numeros():
    with pytest.raises(ErrorSemantico):
        evaluar('para n en 5:\n  mostrar(n)\nfin\n')


def test_variable_del_para_es_local():
    codigo = 'fijo n = 100\npara n en [1, 2]:\n  mostrar(n)\nfin\n'
    assert evaluar(codigo) == 100


def test_bloques_anidados(capsys):
    codigo = ('para n en [1, 2, 3]:\n'
              '  si n > 1:\n    mostrar(n)\n  fin\n'
              'fin\n')
    assert ejecutar(codigo, capsys) == "2\n3"


# =====================================================================
# MOSTRAR
# =====================================================================

def test_mostrar_texto(capsys):
    assert ejecutar('mostrar("hola")\n', capsys) == "hola"


def test_mostrar_numero(capsys):
    assert ejecutar('mostrar(42)\n', capsys) == "42"


def test_mostrar_booleano(capsys):
    assert ejecutar('mostrar(verdadero)\n', capsys) == "verdadero"


def test_mostrar_nulo(capsys):
    assert ejecutar('mostrar(nulo)\n', capsys) == "nulo"


def test_mostrar_lista(capsys):
    assert ejecutar('mostrar([1, 2])\n', capsys) == "[1, 2]"


def test_mostrar_lista_de_textos(capsys):
    assert ejecutar('mostrar(["a"])\n', capsys) == '["a"]'


def test_mostrar_varios_valores(capsys):
    assert ejecutar('mostrar("n:", 5)\n', capsys) == "n: 5"


# =====================================================================
# FUNCIONES INCORPORADAS
# =====================================================================

def test_longitud_de_lista():
    assert evaluar('fijo x = longitud([1, 2, 3])\n') == 3


def test_longitud_de_texto():
    assert evaluar('fijo x = longitud("eco")\n') == 3


def test_funcion_suma():
    assert evaluar('fijo x = suma([1, 2, 3])\n') == 6


def test_funcion_media():
    assert evaluar('fijo x = media([2, 4])\n') == 3.0


def test_funcion_mediana_impar():
    assert evaluar('fijo x = mediana([3, 1, 2])\n') == 2


def test_funcion_mediana_par():
    assert evaluar('fijo x = mediana([1, 2, 3, 4])\n') == 2.5


def test_funcion_minimo():
    assert evaluar('fijo x = minimo([5, 2, 9])\n') == 2


def test_funcion_maximo():
    assert evaluar('fijo x = maximo([5, 2, 9])\n') == 9


def test_funcion_desviacion():
    resultado = evaluar('fijo x = desviacion([2, 4, 4, 4, 5, 5, 7, 9])\n')
    assert abs(resultado - 2.13808993) < 0.0001


def test_desviacion_necesita_dos_valores():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = desviacion([1])\n')


def test_funcion_raiz():
    assert evaluar('fijo x = raiz(16)\n') == 4.0


def test_raiz_rechaza_negativos():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = raiz(-1)\n')


def test_funcion_absoluto():
    assert evaluar('fijo x = absoluto(-7)\n') == 7


def test_funcion_redondear():
    assert evaluar('fijo x = redondear(3.7)\n') == 4


def test_redondear_con_decimales():
    assert evaluar('fijo x = redondear(3.14159, 2)\n') == 3.14


def test_conversion_a_numero():
    assert evaluar('fijo x = a_numero("42")\n') == 42


def test_conversion_a_decimal():
    assert evaluar('fijo x = a_decimal("3.5")\n') == 3.5


def test_conversion_a_texto():
    assert evaluar('fijo x = a_texto(42)\n') == "42"


def test_conversion_invalida():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = a_numero("bosque")\n')


def test_funcion_inexistente():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = inventada(1)\n')


def test_media_de_lista_vacia():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = media([])\n')


def test_media_rechaza_textos():
    with pytest.raises(ErrorSemantico):
        evaluar('fijo x = media(["a", "b"])\n')


# =====================================================================
# CASO AMBIENTAL
# =====================================================================

def test_indicador_per_capita():
    codigo = ('fijo co2 = 88.1\n'
              'fijo poblacion = 52.3\n'
              'fijo per_capita = co2 / poblacion\n')
    assert abs(evaluar(codigo) - 1.6845) < 0.001


def test_clasificacion_de_emisiones(capsys):
    codigo = ('para e en [12.4, 8.1, 15.7]:\n'
              '  si e > 10.0:\n    mostrar("alta")\n'
              '  sino:\n    mostrar("moderada")\n  fin\n'
              'fin\n')
    assert ejecutar(codigo, capsys) == "alta\nmoderada\nalta"


def test_promedio_de_serie_anual():
    codigo = 'fijo x = media([86.2, 92.5, 79.8, 88.1])\n'
    assert abs(evaluar(codigo) - 86.65) < 0.01
