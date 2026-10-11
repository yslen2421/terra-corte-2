"""
test_corte2.py
==============
Pruebas automatizadas del segundo corte de Terra:

    - lector y escritor de CSV escritos desde cero (src/tabla.py)
    - cargar y guardar desde el lenguaje, con opciones
    - operaciones de tuberia: seleccionar, filtrar, crear, renombrar,
      ordenar, duplicados, nulos, convertir y limitar
    - agrupar, resumir y las funciones de agregacion
    - describir
    - errores semanticos de cada operacion

Ejecucion:
    pytest tests/test_corte2.py -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tabla import Tabla, ErrorDatos, leer_csv, escribir_csv
from src.visitante_evaluador import ErrorSemantico
from tests.test_terra import evaluar, ejecutar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, "datos", "emisiones_ejemplo.csv")
CARGA = f'fijo d = cargar "{CSV}"\n'


# =====================================================================
# UTILIDADES
# =====================================================================

def escribir(ruta, contenido: str) -> str:
    """Crea un archivo de prueba y devuelve su ruta como texto."""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    return str(ruta)


def buscar(tabla: Tabla, columna: str, valor) -> dict:
    """Primera fila (como diccionario) cuya columna tiene el valor dado."""
    for i in range(tabla.num_filas):
        fila = tabla.fila_como_dict(i)
        if fila[columna] == valor:
            return fila
    raise AssertionError(f"no hay fila con {columna} = {valor}")


# =====================================================================
# LECTOR Y ESCRITOR DE CSV (src/tabla.py)
# =====================================================================

def test_csv_infiere_tipos():
    t = leer_csv(CSV)
    assert t.num_filas == 16 and t.num_columnas == 5
    tipos = [t.tipo_columna(c) for c in t.columnas]
    assert tipos == ["texto", "numero", "decimal", "numero", "decimal"]


def test_csv_celda_vacia_es_nulo():
    t = leer_csv(CSV)
    assert t.columna("energia_renovable").count(None) == 2


def test_csv_comillas_protegen_el_separador(tmp_path):
    ruta = escribir(tmp_path / "a.csv", 'nombre,nota\n"Perez, Ana",4.5\n')
    assert leer_csv(ruta).filas == [["Perez, Ana", 4.5]]


def test_csv_comillas_escapadas(tmp_path):
    ruta = escribir(tmp_path / "a.csv", 'frase\n"dijo ""hola"""\n')
    assert leer_csv(ruta).filas == [['dijo "hola"']]


def test_csv_sin_encabezado_y_otro_separador(tmp_path):
    ruta = escribir(tmp_path / "a.csv", "1;2\n3;4\n")
    t = leer_csv(ruta, ";", encabezado=False)
    assert t.columnas == ["col1", "col2"]
    assert t.filas == [[1, 2], [3, 4]]


def test_csv_fila_con_campos_de_mas(tmp_path):
    ruta = escribir(tmp_path / "a.csv", "a,b\n1,2\n3,4,5\n")
    with pytest.raises(ErrorDatos, match="linea 3"):
        leer_csv(ruta)


def test_csv_archivo_inexistente():
    with pytest.raises(ErrorDatos, match="no se encontro"):
        leer_csv("no_existe.csv")


def test_csv_columna_repetida(tmp_path):
    ruta = escribir(tmp_path / "a.csv", "a,a\n1,2\n")
    with pytest.raises(ErrorDatos, match="repetida"):
        leer_csv(ruta)


def test_csv_detecta_separador_equivocado():
    with pytest.raises(ErrorDatos, match="separador"):
        leer_csv(CSV, ";")


def test_csv_escribir_y_releer(tmp_path):
    t = leer_csv(CSV)
    ruta = str(tmp_path / "copia.csv")
    escribir_csv(t, ruta)
    copia = leer_csv(ruta)
    assert copia.columnas == t.columnas
    assert copia.filas == t.filas


# =====================================================================
# CARGAR Y GUARDAR DESDE EL LENGUAJE
# =====================================================================

def test_cargar_devuelve_tabla():
    t = evaluar(CARGA)
    assert isinstance(t, Tabla)
    assert t.num_filas == 16


def test_cargar_con_opciones(tmp_path):
    ruta = escribir(tmp_path / "a.csv", "Colombia;86.2\nPeru;52.4\n")
    t = evaluar(f'fijo d = cargar "{ruta}" con encabezado falso '
                f'con separador ";"\n')
    assert t.columnas == ["col1", "col2"]
    assert t.filas[1] == ["Peru", 52.4]


def test_cargar_ruta_no_texto():
    with pytest.raises(ErrorSemantico):
        evaluar("fijo d = cargar 5\n")


def test_cargar_encabezado_no_booleano():
    with pytest.raises(ErrorSemantico, match="encabezado"):
        evaluar(f'fijo d = cargar "{CSV}" con encabezado 1\n')


def test_cargar_opcion_repetida():
    with pytest.raises(ErrorSemantico, match="repetida"):
        evaluar(f'fijo d = cargar "{CSV}" con separador "," '
                f'con separador ","\n')


def test_cargar_archivo_inexistente():
    with pytest.raises(ErrorSemantico, match="no se encontro"):
        evaluar('fijo d = cargar "no_existe.csv"\n')


def test_guardar_y_volver_a_cargar(tmp_path):
    salida = str(tmp_path / "salida.csv")
    t = evaluar(CARGA + f'guardar d como "{salida}"\n'
                        f'fijo r = cargar "{salida}"\n')
    assert t.filas == leer_csv(CSV).filas


def test_guardar_algo_que_no_es_tabla(tmp_path):
    salida = str(tmp_path / "x.csv")
    with pytest.raises(ErrorSemantico, match="necesita una tabla"):
        evaluar(f'guardar 5 como "{salida}"\n')


# =====================================================================
# OPERACIONES DE TUBERIA
# =====================================================================

def test_seleccionar():
    t = evaluar(CARGA + "fijo r = d |> seleccionar [co2, pais]\n")
    assert t.columnas == ["co2", "pais"]
    assert t.num_filas == 16


def test_seleccionar_columna_inexistente():
    with pytest.raises(ErrorSemantico, match="no existe"):
        evaluar(CARGA + "fijo r = d |> seleccionar [temperatura]\n")


def test_filtrar():
    t = evaluar(CARGA + "fijo r = d |> filtrar donde anio >= 2021 && co2 > 50\n")
    assert t.num_filas > 0
    assert all(f[1] >= 2021 and f[2] > 50 for f in t.filas)


def test_filtrar_condicion_no_booleana():
    with pytest.raises(ErrorSemantico, match="booleana"):
        evaluar(CARGA + "fijo r = d |> filtrar donde co2 + 1\n")


def test_crear_columna_calculada():
    t = evaluar(CARGA + "fijo r = d |> crear doble = co2 * 2\n")
    assert t.columnas[-1] == "doble"
    assert buscar(t, "anio", 2015)["doble"] == pytest.approx(172.4)


def test_crear_con_nulos_es_error():
    with pytest.raises(ErrorSemantico):
        evaluar(CARGA + "fijo r = d |> crear x = energia_renovable + 1\n")


def test_renombrar():
    t = evaluar(CARGA + "fijo r = d |> renombrar energia_renovable como renovable\n")
    assert "renovable" in t.columnas
    assert "energia_renovable" not in t.columnas


def test_renombrar_a_columna_existente():
    with pytest.raises(ErrorSemantico, match="ya existe"):
        evaluar(CARGA + "fijo r = d |> renombrar co2 como pais\n")


def test_ordenar_ascendente():
    t = evaluar(CARGA + "fijo r = d |> ordenar por co2\n")
    assert t.columna("co2") == sorted(t.columna("co2"))


def test_ordenar_descendente():
    t = evaluar(CARGA + "fijo r = d |> ordenar por co2 desc\n")
    assert t.columna("co2")[0] == 92.5


def test_ordenar_deja_nulos_al_final():
    t = evaluar(CARGA + "fijo r = d |> ordenar por energia_renovable\n")
    assert t.columna("energia_renovable")[-2:] == [None, None]


def test_eliminar_duplicados():
    t = evaluar(CARGA + "fijo r = d |> seleccionar [pais] |> eliminar duplicados\n")
    assert t.columna("pais") == ["Colombia", "Peru", "Chile", "Ecuador"]


def test_eliminar_nulos():
    t = evaluar(CARGA + "fijo r = d |> eliminar nulos\n")
    assert t.num_filas == 14


def test_eliminar_nulos_solo_en_columnas_indicadas():
    t = evaluar(CARGA + "fijo r = d |> eliminar nulos en [co2]\n")
    assert t.num_filas == 16


def test_rellenar_nulos():
    t = evaluar(CARGA + "fijo r = d |> rellenar nulos en energia_renovable con 0\n")
    columna = t.columna("energia_renovable")
    assert None not in columna
    assert columna.count(0.0) == 2


def test_rellenar_nulos_con_tipo_incompatible():
    with pytest.raises(ErrorSemantico, match="rellenar"):
        evaluar(CARGA + 'fijo r = d |> rellenar nulos en energia_renovable con "cero"\n')


def test_convertir_a_texto():
    t = evaluar(CARGA + "fijo r = d |> convertir anio como texto\n")
    assert all(isinstance(v, str) for v in t.columna("anio"))


def test_convertir_texto_invalido_a_numero():
    with pytest.raises(ErrorSemantico, match="convertir"):
        evaluar(CARGA + "fijo r = d |> convertir pais como numero\n")


def test_limitar():
    t = evaluar(CARGA + "fijo r = d |> limitar 3\n")
    assert t.num_filas == 3


def test_limitar_negativo():
    with pytest.raises(ErrorSemantico, match="limitar"):
        evaluar(CARGA + "fijo r = d |> limitar -1\n")


def test_tuberia_sobre_algo_que_no_es_tabla():
    with pytest.raises(ErrorSemantico, match="tabla"):
        evaluar("fijo x = 5\nfijo r = x |> limitar 1\n")


def test_tuberia_no_modifica_la_tabla_original():
    t = evaluar(CARGA + "fijo r = d |> eliminar nulos |> limitar 2\n"
                        "fijo original = d\n")
    assert t.num_filas == 16


# =====================================================================
# AGRUPAR Y RESUMIR
# =====================================================================

def test_agrupar_y_resumir():
    t = evaluar(CARGA + """fijo r = d
    |> agrupar por [pais]
    |> resumir total = suma(co2), n = contar()
""")
    assert t.columnas == ["pais", "total", "n"]
    assert t.num_filas == 4
    colombia = buscar(t, "pais", "Colombia")
    assert colombia["total"] == pytest.approx(346.6)
    assert colombia["n"] == 4


def test_resumir_estadisticas():
    t = evaluar(CARGA + """fijo r = d
    |> agrupar por [pais]
    |> resumir m = media(co2), me = mediana(co2), mi = minimo(co2),
               ma = maximo(co2), de = desviacion(co2)
""")
    colombia = buscar(t, "pais", "Colombia")
    assert colombia["m"] == pytest.approx(86.65)
    assert colombia["me"] == pytest.approx(87.15)
    assert colombia["mi"] == 79.8
    assert colombia["ma"] == 92.5
    assert colombia["de"] == pytest.approx(5.27, abs=0.01)


def test_resumir_ignora_nulos():
    t = evaluar(CARGA + "fijo r = d |> resumir m = media(energia_renovable)\n")
    assert t.filas[0][0] == pytest.approx(27.85)


def test_resumir_sin_agrupar():
    t = evaluar(CARGA + "fijo r = d |> resumir con_dato = "
                        "contar(energia_renovable), filas = contar()\n")
    assert t.filas == [[14, 16]]


def test_agrupar_por_dos_columnas():
    t = evaluar(CARGA + "fijo r = d |> agrupar por [pais, anio] "
                        "|> resumir n = contar()\n")
    assert t.columnas == ["pais", "anio", "n"]
    assert t.num_filas == 16


def test_agrupar_sin_resumir():
    with pytest.raises(ErrorSemantico, match="falta 'resumir'"):
        evaluar(CARGA + "fijo r = d |> agrupar por [pais]\n")


def test_agrupar_seguido_de_otra_operacion():
    with pytest.raises(ErrorSemantico, match="debe venir 'resumir'"):
        evaluar(CARGA + "fijo r = d |> agrupar por [pais] |> limitar 2\n")


def test_agrupar_columna_inexistente():
    with pytest.raises(ErrorSemantico, match="no existe"):
        evaluar(CARGA + "fijo r = d |> agrupar por [region] "
                        "|> resumir n = contar()\n")


def test_agregacion_debe_producir_un_valor():
    with pytest.raises(ErrorSemantico, match="un solo valor"):
        evaluar(CARGA + "fijo r = d |> resumir x = co2\n")


def test_contar_fuera_de_resumir():
    with pytest.raises(ErrorSemantico, match="resumir"):
        evaluar("fijo n = contar()\n")


# =====================================================================
# DESCRIBIR Y MOSTRAR
# =====================================================================

def test_describir():
    t = evaluar(CARGA + "fijo r = describir(d)\n")
    assert t.num_filas == 5
    pais = buscar(t, "columna", "pais")
    assert pais["distintos"] == 4
    assert pais["mas_frecuente"] == "Colombia"
    renovable = buscar(t, "columna", "energia_renovable")
    assert renovable["conteo"] == 14
    assert renovable["nulos"] == 2
    assert renovable["media"] == pytest.approx(27.85)


def test_describir_requiere_tabla():
    with pytest.raises(ErrorSemantico, match="necesita una tabla"):
        evaluar("fijo r = describir(5)\n")


def test_mostrar_tabla(capsys):
    salida = ejecutar(CARGA + "mostrar(d)\n", capsys)
    assert "energia_renovable" in salida
    assert "[16 filas x 5 columnas]" in salida
