grammar Terra;

/*----------------------------------------------------------------
  TERRA
  Lenguaje de Dominio Especifico para analisis de datos ambientales
  y de sostenibilidad.

  Paradigma: declarativo / funcional con tuberias (pipelines)
  Herramienta: ANTLR v4  |  Implementacion: Python + patron Visitor
  Extension de archivos: .terra
----------------------------------------------------------------*/

// ================= ESTRUCTURA DEL PROGRAMA =================

programa
    : (NL | sentencia)* EOF
    ;

sentencia
    : declaracion_variable
    | asignacion
    | mostrar_stmt
    | si_stmt
    | mientras_stmt
    | para_stmt
    | guardar_stmt
    | graficar_stmt
    | expresion_stmt
    | funcion_decl
    | retornar_stmt
    ;

bloque
    : (NL | sentencia)*
    ;

// ================= SENTENCIAS BASICAS =================

declaracion_variable
    : FIJO IDENTIFICADOR '=' expresion NL
    | VAR  IDENTIFICADOR '=' expresion NL
    ;

asignacion
    : IDENTIFICADOR '=' expresion NL
    ;

expresion_stmt
    : expresion NL
    ;

mostrar_stmt
    : MOSTRAR '(' (expresion (',' expresion)*)? ')' NL
    ;

// ================= CONTROL DE FLUJO =================

si_stmt
    : SI expresion ':' NL
      bloque
      (SINO SI expresion ':' NL bloque)*
      (SINO ':' NL bloque)?
      FIN NL
    ;

mientras_stmt
    : MIENTRAS expresion ':' NL
      bloque
      FIN NL
    ;

para_stmt
    : PARA IDENTIFICADOR EN expresion ':' NL
      bloque
      FIN NL
    ;
funcion_decl
    : FUNCION IDENTIFICADOR
      '(' ( IDENTIFICADOR ( ',' IDENTIFICADOR )* )? ')' ':' NL
      bloque
      FIN NL
    ;

retornar_stmt
    : RETORNAR expresion? NL
    ;

// ================= DOMINIO: DATOS Y VISUALIZACION =================

guardar_stmt
    : GUARDAR expr COMO expr (CON SEPARADOR expr)? NL
    ;

graficar_stmt
    : GRAFICAR tipo_grafica expr (NL* opcion_grafica)* NL
    ;

tipo_grafica
    : BARRAS
    | LINEAS
    | HISTOGRAMA
    | DISPERSION
    | CAJA
    ;

opcion_grafica
    : EJE_X IDENTIFICADOR
    | EJE_Y IDENTIFICADOR
    | TITULO expr
    | LEYENDA expr
    | GUARDAR COMO expr
    ;

// ================= EXPRESIONES Y TUBERIAS =================

expresion
    : tuberia
    ;

tuberia
    : expr (NL* FLECHA NL* operacion)*
    ;

expr
    : o_logico
    ;

operacion
    : SELECCIONAR lista_columnas
    | FILTRAR DONDE expr
    | CREAR IDENTIFICADOR '=' expr
    | RENOMBRAR IDENTIFICADOR COMO IDENTIFICADOR
    | ORDENAR POR IDENTIFICADOR (ASC | DESC)?
    | ELIMINAR DUPLICADOS
    | ELIMINAR NULOS (EN lista_columnas)?
    | RELLENAR NULOS EN IDENTIFICADOR CON expr
    | CONVERTIR IDENTIFICADOR COMO tipo_dato
    | AGRUPAR POR lista_columnas
    | RESUMIR agregacion (',' NL* agregacion)*
    | LIMITAR expr
    ;

agregacion
    : IDENTIFICADOR '=' expr
    ;

lista_columnas
    : '[' IDENTIFICADOR (',' IDENTIFICADOR)* ']'
    ;

tipo_dato
    : T_NUMERO
    | T_DECIMAL
    | T_TEXTO
    | T_BOOLEANO
    ;

o_logico    : y_logico ('||' y_logico)* ;
y_logico    : igualdad ('&&' igualdad)* ;
igualdad    : relacional (('==' | '!=') relacional)* ;
relacional  : pertenencia (('>' | '<' | '>=' | '<=') pertenencia)* ;
pertenencia : suma (EN suma)? ;
suma        : termino (('+' | '-') termino)* ;
termino     : potencia (('*' | '/' | '%') potencia)* ;
potencia    : unario ('^' potencia)? ;

unario
    : '-' unario
    | '!' unario
    | postfijo
    ;

postfijo
    : primario ('[' expr ']')*
    ;

primario
    : NUMERO
    | DECIMAL
    | TEXTO
    | BOOLEANO
    | NULO
    | carga
    | llamada
    | funcion_anonima
    | IDENTIFICADOR
    | lista
    | '(' expresion ')'
    ;

carga
    : CARGAR expr (CON opcion_carga)*
    ;

opcion_carga
    : SEPARADOR expr
    | ENCABEZADO expr
    ;

llamada
    : IDENTIFICADOR '(' (expr (',' expr)*)? ')'
    ;

lista
    : '[' (expr (',' expr)*)? ']'
    ;

funcion_anonima
    : FUNCION '(' (IDENTIFICADOR (',' IDENTIFICADOR)*)? ')' FLECHA_FUNCION expr
    ;
// ================= LEXICO =================
// Las palabras reservadas van ANTES de IDENTIFICADOR.

FIJO         : 'fijo';
VAR          : 'var';
SI           : 'si';
SINO         : 'sino';
FIN          : 'fin';
MIENTRAS     : 'mientras';
PARA         : 'para';
EN           : 'en';
MOSTRAR      : 'mostrar';
FUNCION      : 'funcion';
RETORNAR     : 'retornar';

CARGAR       : 'cargar';
GUARDAR      : 'guardar';
COMO         : 'como';
CON          : 'con';
ENCABEZADO   : 'encabezado';
SEPARADOR    : 'separador';

SELECCIONAR  : 'seleccionar';
FILTRAR      : 'filtrar';
DONDE        : 'donde';
CREAR        : 'crear';
RENOMBRAR    : 'renombrar';
ORDENAR      : 'ordenar';
POR          : 'por';
ASC          : 'asc';
DESC         : 'desc';
ELIMINAR     : 'eliminar';
DUPLICADOS   : 'duplicados';
NULOS        : 'nulos';
RELLENAR     : 'rellenar';
CONVERTIR    : 'convertir';
AGRUPAR      : 'agrupar';
RESUMIR      : 'resumir';
LIMITAR      : 'limitar';

GRAFICAR     : 'graficar';
BARRAS       : 'barras';
LINEAS       : 'lineas';
HISTOGRAMA   : 'histograma';
DISPERSION   : 'dispersion';
CAJA         : 'caja';
EJE_X        : 'eje_x';
EJE_Y        : 'eje_y';
TITULO       : 'titulo';
LEYENDA      : 'leyenda';

T_NUMERO     : 'numero';
T_DECIMAL    : 'decimal';
T_TEXTO      : 'texto';
T_BOOLEANO   : 'booleano';

BOOLEANO     : 'verdadero' | 'falso';
NULO         : 'nulo';

FLECHA       : '|>';
FLECHA_FUNCION : '=>';
AND          : '&&';
OR           : '||';
IGUAL        : '==';
DIFERENTE    : '!=';
MAYOR_IGUAL  : '>=';
MENOR_IGUAL  : '<=';

DECIMAL       : DIGITO+ '.' DIGITO+;
NUMERO        : DIGITO+;
TEXTO         : '"' ( ~["\r\n] | '\\"' )* '"';
IDENTIFICADOR : LETRA (LETRA | DIGITO | '_')*;

fragment LETRA  : [a-zA-ZáéíóúñÁÉÍÓÚÑ];
fragment DIGITO : [0-9];

NL                : ('\r'? '\n')+;
WS                : [ \t]+ -> skip;
COMENTARIO_LINEA  : '#' ~[\r\n]* -> skip;
COMENTARIO_BLOQUE : '/-' .*? '-/' -> skip;
