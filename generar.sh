#!/usr/bin/env bash
set -e
JAR_PATH="/usr/local/lib/antlr-4.13.2-complete.jar"

if [[ ! -f "$JAR_PATH" ]]; then
    echo "Descargando ANTLR 4.13.2..."
    sudo curl -L -o "$JAR_PATH" \
        "https://www.antlr.org/download/antlr-4.13.2-complete.jar"
fi

if [[ -f venv/bin/activate ]]; then
    source venv/bin/activate
fi

echo "Generando lexer, parser y visitor de Terra..."
rm -f gramaticas/Terra*.py gramaticas/Terra*.interp gramaticas/Terra*.tokens
rm -rf generado

java -jar "$JAR_PATH" \
    -Dlanguage=Python3 \
    -visitor \
    -no-listener \
    -o generado \
    gramaticas/Terra.g4

cp generado/gramaticas/*.py generado/gramaticas/*.interp generado/gramaticas/*.tokens gramaticas/ 2>/dev/null || true
touch gramaticas/__init__.py
rm -rf generado

echo "Listo. Archivos generados:"
ls -la gramaticas/Terra*.py
