#!/usr/bin/env bash
set -e
JAR_PATH="/usr/local/lib/antlr-4.13.2-complete.jar"
ARCHIVO="$1"
MODO="${2:--tree}"

if [[ -z "$ARCHIVO" ]]; then
    echo "Uso: ./arbol.sh <archivo.terra> [-tree|-gui|-tokens]"
    exit 1
fi

rm -rf .arbol && mkdir -p .arbol
java -jar "$JAR_PATH" -o .arbol gramaticas/Terra.g4
javac -cp "$JAR_PATH" -d .arbol .arbol/gramaticas/*.java
java -cp "$JAR_PATH:.arbol" org.antlr.v4.gui.TestRig Terra programa "$MODO" "$ARCHIVO"

