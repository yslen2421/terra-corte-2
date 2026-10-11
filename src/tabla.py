"""
tabla.py
========
Estructura de datos tabular de Terra, escrita desde cero (sin pandas
ni el modulo csv).

Una Tabla guarda:
    columnas: lista con los nombres de las columnas, en orden
    filas:    lista de filas; cada fila es una lista de valores
              alineada con 'columnas'

Cada celda tiene un tipo de Terra: int (numero), float (decimal),
str (texto), bool (booleano) o None (nulo).

Las operaciones nunca modifican la tabla original: siempre devuelven
una Tabla nueva. Asi una tuberia no altera en silencio el resultado
anterior, como pide el enunciado.
"""

# Textos que se interpretan como celda vacia al leer un CSV
VALORES_NULOS = {"", "na", "n/a", "nan", "null", "nulo", "none"}
VALORES_VERDADERO = {"verdadero", "true"}
VALORES_FALSO = {"falso", "false"}


class ErrorDatos(Exception):
    """
    Error al leer, escribir o manipular una tabla.

    No conoce la linea del programa Terra: el evaluador la atrapa y la
    convierte en ErrorSemantico agregando la linea donde ocurrio.
    """


# ---------------------------------------------------------------------
# FORMATO DE VALORES
# ---------------------------------------------------------------------

def formatear_valor(valor) -> str:
    """Convierte un valor de Terra en texto legible para mostrarlo."""
    if valor is None:
        return "nulo"
    if valor is True:
        return "verdadero"
    if valor is False:
        return "falso"
    if isinstance(valor, float):
        texto = f"{valor:.4f}".rstrip("0").rstrip(".")
        return "0" if texto in ("", "-0") else texto
    return str(valor)


def nombre_tipo_valor(valor) -> str:
    """Nombre del tipo de Terra al que pertenece un valor de Python."""
    if valor is None:
        return "nulo"
    if isinstance(valor, bool):
        return "booleano"
    if isinstance(valor, int):
        return "numero"
    if isinstance(valor, float):
        return "decimal"
    return "texto"


# ---------------------------------------------------------------------
# CLASE TABLA
# ---------------------------------------------------------------------

class Tabla:
    """Conjunto de datos en filas y columnas."""

    def __init__(self, columnas, filas=None):
        self.columnas = list(columnas)
        self.filas = [list(fila) for fila in (filas or [])]

        vistos = set()
        for nombre in self.columnas:
            if nombre in vistos:
                raise ErrorDatos(f"la columna '{nombre}' esta repetida")
            vistos.add(nombre)

        for k, fila in enumerate(self.filas):
            if len(fila) != len(self.columnas):
                raise ErrorDatos(
                    f"la fila {k + 1} tiene {len(fila)} valores y la tabla "
                    f"tiene {len(self.columnas)} columnas")

    # ----------------------------- consultas -------------------------

    @property
    def num_filas(self) -> int:
        return len(self.filas)

    @property
    def num_columnas(self) -> int:
        return len(self.columnas)

    def __len__(self):
        return len(self.filas)

    def tiene_columna(self, nombre: str) -> bool:
        return nombre in self.columnas

    def indice(self, nombre: str) -> int:
        """Posicion de una columna; error claro si no existe."""
        if nombre not in self.columnas:
            disponibles = ", ".join(self.columnas)
            raise ErrorDatos(
                f"la columna '{nombre}' no existe. "
                f"Columnas disponibles: {disponibles}")
        return self.columnas.index(nombre)

    def columna(self, nombre: str) -> list:
        """Todos los valores de una columna, como lista."""
        j = self.indice(nombre)
        return [fila[j] for fila in self.filas]

    def fila_como_dict(self, i: int) -> dict:
        """Una fila como diccionario {columna: valor}."""
        return dict(zip(self.columnas, self.filas[i]))

    def tipo_columna(self, nombre: str) -> str:
        """
        Tipo de Terra de una columna, mirando sus valores no nulos.
        Si mezcla numero y decimal se reporta como decimal.
        """
        tipos = {nombre_tipo_valor(v) for v in self.columna(nombre)
                 if v is not None}
        if not tipos:
            return "nulo"
        if tipos == {"numero", "decimal"}:
            return "decimal"
        if len(tipos) == 1:
            return tipos.pop()
        return "mixto"

    def es_numerica(self, nombre: str) -> bool:
        return self.tipo_columna(nombre) in ("numero", "decimal")

    def copiar(self) -> "Tabla":
        return Tabla(self.columnas, self.filas)

    # ----------------------------- presentacion ----------------------

    def como_texto(self, max_filas: int = 10) -> str:
        """Dibuja la tabla en texto, alineada, mostrando hasta max_filas."""
        visibles = self.filas[:max_filas]
        celdas = [[formatear_valor(v) for v in fila] for fila in visibles]

        anchos = [len(c) for c in self.columnas]
        for fila in celdas:
            for j, texto in enumerate(fila):
                anchos[j] = max(anchos[j], len(texto))

        # Los numeros se alinean a la derecha y el texto a la izquierda
        numericas = [self.es_numerica(c) for c in self.columnas]

        def armar(textos):
            partes = []
            for j, texto in enumerate(textos):
                if numericas[j]:
                    partes.append(texto.rjust(anchos[j]))
                else:
                    partes.append(texto.ljust(anchos[j]))
            return " | ".join(partes)

        lineas = [armar(self.columnas),
                  "-+-".join("-" * a for a in anchos)]
        lineas += [armar(fila) for fila in celdas]

        if self.num_filas > max_filas:
            lineas.append(f"... ({self.num_filas - max_filas} filas mas)")
        lineas.append(f"[{self.num_filas} filas x "
                      f"{self.num_columnas} columnas]")
        return "\n".join(lineas)

    def __str__(self):
        return self.como_texto()

    def __repr__(self):
        return (f"Tabla({self.num_filas} filas x "
                f"{self.num_columnas} columnas)")


# ---------------------------------------------------------------------
# LECTURA DE CSV (desde cero)
# ---------------------------------------------------------------------

def _dividir_registros(contenido: str, separador: str) -> list:
    """
    Parte el texto del archivo en registros (filas) y campos.

    Es un pequeno automata con dos estados: dentro o fuera de comillas.
    - Fuera de comillas, el separador corta el campo y el salto de
      linea corta el registro.
    - Dentro de comillas, el separador y el salto de linea son texto
      normal; dos comillas seguidas ("") representan una comilla.

    Devuelve una lista de (linea_del_archivo, [campos]).
    """
    # Atajo: sin comillas no hay campos protegidos, asi que cada linea
    # se parte directamente por el separador. Da el mismo resultado que
    # el automata y es mucho mas rapido en archivos grandes.
    if '"' not in contenido:
        rapidos = []
        for numero, texto in enumerate(contenido.split("\n"), start=1):
            texto = texto.rstrip("\r")
            if texto.strip():
                rapidos.append((numero, texto.split(separador)))
        return rapidos
    registros = []
    registro = []
    campo = []
    en_comillas = False
    linea = 1
    inicio = 1          # linea donde empezo el registro actual
    i = 0
    n = len(contenido)

    while i < n:
        c = contenido[i]

        if en_comillas:
            if c == '"':
                if i + 1 < n and contenido[i + 1] == '"':
                    campo.append('"')          # comilla escapada
                    i += 2
                    continue
                en_comillas = False            # cierre de comillas
            else:
                if c == "\n":
                    linea += 1
                campo.append(c)

        else:
            if c == '"' and not campo:
                en_comillas = True             # campo entre comillas
            elif contenido.startswith(separador, i):
                registro.append("".join(campo))
                campo = []
                i += len(separador)
                continue
            elif c == "\r":
                pass                           # finales de linea Windows
            elif c == "\n":
                registro.append("".join(campo))
                registros.append((inicio, registro))
                campo, registro = [], []
                linea += 1
                inicio = linea
            else:
                campo.append(c)

        i += 1

    if en_comillas:
        raise ErrorDatos(
            f"hay comillas sin cerrar en el registro que empieza en la "
            f"linea {inicio} del archivo")

    if campo or registro:
        registro.append("".join(campo))
        registros.append((inicio, registro))

    # Las lineas en blanco no son registros
    return [(l, r) for l, r in registros
            if not (len(r) == 1 and r[0].strip() == "")]


def _es_nulo(texto: str) -> bool:
    return texto.strip().lower() in VALORES_NULOS


def _es_entero(texto: str) -> bool:
    s = texto[1:] if texto[:1] in "+-" else texto
    return s.isascii() and s.isdigit()


def _es_decimal(texto: str) -> bool:
    if not texto or any(ch not in "0123456789.+-eE" for ch in texto):
        return False
    try:
        float(texto)
        return True
    except ValueError:
        return False


def _inferir_columna(textos: list) -> list:
    """
    Decide el tipo de una columna completa y convierte sus valores.

    Se decide por columna y no por celda, para que una columna no
    quede con numeros en unas filas y textos en otras. El orden de
    prueba es: booleano, numero, decimal y, si nada encaja, texto.
    Las celdas vacias quedan como nulo en cualquier caso.
    """
    limpios = [t.strip() for t in textos]
    no_nulos = [t for t in limpios if not _es_nulo(t)]

    if not no_nulos:
        return [None] * len(limpios)

    if all(t.lower() in VALORES_VERDADERO | VALORES_FALSO for t in no_nulos):
        return [None if _es_nulo(t) else t.lower() in VALORES_VERDADERO
                for t in limpios]

    if all(_es_entero(t) for t in no_nulos):
        return [None if _es_nulo(t) else int(t) for t in limpios]

    if all(_es_decimal(t) for t in no_nulos):
        return [None if _es_nulo(t) else float(t) for t in limpios]

    return [None if _es_nulo(t) else t for t in limpios]


def leer_csv(ruta: str, separador: str = ",",
             encabezado: bool = True) -> Tabla:
    """
    Lee un archivo CSV y devuelve una Tabla con los tipos inferidos.

    ruta:       ruta del archivo
    separador:  caracter (o texto) que separa los campos
    encabezado: si es True, la primera fila trae los nombres de las
                columnas; si es False, se nombran col1, col2, ...
    """
    if not separador:
        raise ErrorDatos("el separador no puede estar vacio")

    try:
        # utf-8-sig ignora la marca BOM que agrega Excel
        with open(ruta, encoding="utf-8-sig") as archivo:
            contenido = archivo.read()
    except FileNotFoundError:
        raise ErrorDatos(f"no se encontro el archivo '{ruta}'")
    except IsADirectoryError:
        raise ErrorDatos(f"'{ruta}' es una carpeta, no un archivo")
    except PermissionError:
        raise ErrorDatos(f"no hay permiso para leer '{ruta}'")
    except UnicodeDecodeError:
        raise ErrorDatos(f"el archivo '{ruta}' no esta codificado en UTF-8")

    registros = _dividir_registros(contenido, separador)
    if not registros:
        raise ErrorDatos(f"el archivo '{ruta}' esta vacio")

    # Si el primer registro quedo como un solo campo que contiene otro
    # separador comun, casi seguro se eligio el separador equivocado.
    primer_registro = registros[0][1]
    if len(primer_registro) == 1:
        for otro in (",", ";", "\t", "|"):
            if otro != separador and otro in primer_registro[0]:
                visible = "tabulador" if otro == "\t" else f"'{otro}'"
                raise ErrorDatos(
                    f"el archivo parece usar {visible} como separador, "
                    f"no '{separador}'. Revisa la opcion 'con separador'")
    if encabezado:
        columnas = [c.strip() for c in registros[0][1]]
        datos = registros[1:]
        for k, nombre in enumerate(columnas):
            if not nombre:
                raise ErrorDatos(
                    f"la columna {k + 1} del encabezado no tiene nombre")
    else:
        columnas = [f"col{k + 1}" for k in range(len(registros[0][1]))]
        datos = registros

    for linea, campos in datos:
        if len(campos) != len(columnas):
            raise ErrorDatos(
                f"la linea {linea} del archivo tiene {len(campos)} campos "
                f"y el encabezado tiene {len(columnas)}. "
                f"Revisa el separador o el contenido de esa fila")

    crudos = [campos for _, campos in datos]
    por_columna = [_inferir_columna([fila[j] for fila in crudos])
                   for j in range(len(columnas))]
    filas = [[por_columna[j][i] for j in range(len(columnas))]
             for i in range(len(crudos))]

    return Tabla(columnas, filas)


# ---------------------------------------------------------------------
# ESCRITURA DE CSV (desde cero)
# ---------------------------------------------------------------------

def _campo_csv(valor, separador: str) -> str:
    """Convierte un valor en un campo CSV, con comillas si hace falta."""
    if valor is None:
        texto = ""
    elif valor is True:
        texto = "verdadero"
    elif valor is False:
        texto = "falso"
    else:
        texto = str(valor)

    if (separador in texto or '"' in texto
            or "\n" in texto or "\r" in texto):
        texto = '"' + texto.replace('"', '""') + '"'
    return texto


def escribir_csv(tabla: Tabla, ruta: str, separador: str = ",") -> None:
    """Guarda una Tabla en un archivo CSV con encabezado."""
    if not separador:
        raise ErrorDatos("el separador no puede estar vacio")

    lineas = [separador.join(_campo_csv(c, separador)
                             for c in tabla.columnas)]
    for fila in tabla.filas:
        lineas.append(separador.join(_campo_csv(v, separador)
                                     for v in fila))

    try:
        with open(ruta, "w", encoding="utf-8", newline="") as archivo:
            archivo.write("\n".join(lineas) + "\n")
    except FileNotFoundError:
        raise ErrorDatos(
            f"no se pudo guardar '{ruta}': la carpeta de destino no existe")
    except IsADirectoryError:
        raise ErrorDatos(f"'{ruta}' es una carpeta, no un archivo")
    except PermissionError:
        raise ErrorDatos(f"no hay permiso para escribir en '{ruta}'")
