# Generated from gramaticas/Terra.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .TerraParser import TerraParser
else:
    from TerraParser import TerraParser

# This class defines a complete generic visitor for a parse tree produced by TerraParser.

class TerraVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by TerraParser#programa.
    def visitPrograma(self, ctx:TerraParser.ProgramaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#sentencia.
    def visitSentencia(self, ctx:TerraParser.SentenciaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#bloque.
    def visitBloque(self, ctx:TerraParser.BloqueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#declaracion_variable.
    def visitDeclaracion_variable(self, ctx:TerraParser.Declaracion_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#asignacion.
    def visitAsignacion(self, ctx:TerraParser.AsignacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#expresion_stmt.
    def visitExpresion_stmt(self, ctx:TerraParser.Expresion_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#mostrar_stmt.
    def visitMostrar_stmt(self, ctx:TerraParser.Mostrar_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#si_stmt.
    def visitSi_stmt(self, ctx:TerraParser.Si_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#mientras_stmt.
    def visitMientras_stmt(self, ctx:TerraParser.Mientras_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#para_stmt.
    def visitPara_stmt(self, ctx:TerraParser.Para_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#funcion_decl.
    def visitFuncion_decl(self, ctx:TerraParser.Funcion_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#retornar_stmt.
    def visitRetornar_stmt(self, ctx:TerraParser.Retornar_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#guardar_stmt.
    def visitGuardar_stmt(self, ctx:TerraParser.Guardar_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#graficar_stmt.
    def visitGraficar_stmt(self, ctx:TerraParser.Graficar_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#tipo_grafica.
    def visitTipo_grafica(self, ctx:TerraParser.Tipo_graficaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#opcion_grafica.
    def visitOpcion_grafica(self, ctx:TerraParser.Opcion_graficaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#expresion.
    def visitExpresion(self, ctx:TerraParser.ExpresionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#tuberia.
    def visitTuberia(self, ctx:TerraParser.TuberiaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#expr.
    def visitExpr(self, ctx:TerraParser.ExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#operacion.
    def visitOperacion(self, ctx:TerraParser.OperacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#agregacion.
    def visitAgregacion(self, ctx:TerraParser.AgregacionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#lista_columnas.
    def visitLista_columnas(self, ctx:TerraParser.Lista_columnasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#tipo_dato.
    def visitTipo_dato(self, ctx:TerraParser.Tipo_datoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#o_logico.
    def visitO_logico(self, ctx:TerraParser.O_logicoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#y_logico.
    def visitY_logico(self, ctx:TerraParser.Y_logicoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#igualdad.
    def visitIgualdad(self, ctx:TerraParser.IgualdadContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#relacional.
    def visitRelacional(self, ctx:TerraParser.RelacionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#pertenencia.
    def visitPertenencia(self, ctx:TerraParser.PertenenciaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#suma.
    def visitSuma(self, ctx:TerraParser.SumaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#termino.
    def visitTermino(self, ctx:TerraParser.TerminoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#potencia.
    def visitPotencia(self, ctx:TerraParser.PotenciaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#unario.
    def visitUnario(self, ctx:TerraParser.UnarioContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#postfijo.
    def visitPostfijo(self, ctx:TerraParser.PostfijoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#primario.
    def visitPrimario(self, ctx:TerraParser.PrimarioContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#carga.
    def visitCarga(self, ctx:TerraParser.CargaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#opcion_carga.
    def visitOpcion_carga(self, ctx:TerraParser.Opcion_cargaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#llamada.
    def visitLlamada(self, ctx:TerraParser.LlamadaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#lista.
    def visitLista(self, ctx:TerraParser.ListaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TerraParser#funcion_anonima.
    def visitFuncion_anonima(self, ctx:TerraParser.Funcion_anonimaContext):
        return self.visitChildren(ctx)



del TerraParser