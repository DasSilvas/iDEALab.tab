# -*- coding: utf-8 -*-

__title__ = "2-Cálculo Águas"
__doc__ = "Calculo e preenchimento dos parametros de cálculo de Águas"
__author__ = "Joao Ferreira, OE nº 86233"


# ============================================================
# IMPORTS
# ============================================================

import clr

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript import Geometry as geom

clr.AddReference("RevitNodes")
import Revit
from Revit import Elements

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

import os.path
import sys

from System.Collections.Generic import List


# ============================================================
# PATH DAS CLASSES
# ============================================================

grandparent_dir = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        '..'
    )
)

sys.path.insert(0, grandparent_dir)


# ============================================================
# CLASSES / MÓDULOS
# ============================================================

from classes import WaterPipes
from classes import RvtApiCategory as cat
from classes import RvtApi as rvt
from classes import RvtClasses as cls
from classes import RvtParameterName as parameter

import rpae


# ============================================================
# CONSOLIDAR TROÇOS
# ============================================================

def consolidar_output(output_list):

    from collections import OrderedDict

    trocos_consolidados = OrderedDict()

    for item in output_list:

        troco = item["Troço"]

        if not troco:
            continue

        if troco not in trocos_consolidados:

            # Primeira ocorrência
            trocos_consolidados[troco] = item.copy()

        else:

            # ------------------------------------------------
            # IMPORTANTE:
            # Mantém a tua lógica original.
            # Não soma J.
            # Soma apenas o comprimento.
            # ------------------------------------------------

            trocos_consolidados[troco]["Ltroço (m)"] += (
                item["Ltroço (m)"]
            )


    # --------------------------------------------------------
    # Recalcular JxL com comprimento total
    # --------------------------------------------------------

    output_consolidado = []

    for troco, dados in trocos_consolidados.items():

        j_valor = dados["J (m/m)"]

        l_total = dados["Ltroço (m)"]

        dados["Ltroço (m)"] = round(
            l_total,
            2
        )

        dados["JxL (m.c.a)"] = round(
            1.5 *
            j_valor *
            l_total,
            2
        )

        output_consolidado.append(
            dados
        )


    return output_consolidado


# ============================================================
# CALCULAR J ACUMULADO
# ============================================================

def calcular_jacumulado(output_list):

    """
    Calcula o JxL acumulado desde jusante para montante.

    Exemplo:

        A-B
         |
        B-C
         |
        C-D

    Resultado:

        C-D = JxL C-D

        B-C = JxL B-C + J acumulado C-D

        A-B = JxL A-B + J acumulado B-C
    """

    output_processado = []


    # --------------------------------------------------------
    # Inicializar Jacumulado
    # --------------------------------------------------------

    for item in output_list:

        novo_item = item.copy()

        novo_item["Jacumulado (m.c.a)"] = round(
            novo_item["JxL (m.c.a)"],
            2
        )

        output_processado.append(
            novo_item
        )


    # --------------------------------------------------------
    # Propagar acumulado
    # --------------------------------------------------------

    mudancas = True

    iteracao = 0

    max_iteracoes = len(
        output_processado
    ) + 2


    while mudancas and iteracao < max_iteracoes:

        mudancas = False

        iteracao += 1


        for item in output_processado:

            troco = item["Troço"]


            if not troco or "-" not in troco:
                continue


            # ------------------------------------------------
            # Separar prefixo / sufixo
            # ------------------------------------------------

            prefixo, sufixo = troco.split(
                "-",
                1
            )


            # ------------------------------------------------
            # Procurar troço imediatamente a jusante
            # ------------------------------------------------

            for outro_item in output_processado:

                outro_troco = outro_item["Troço"]


                if not outro_troco:
                    continue


                if "-" not in outro_troco:
                    continue


                if outro_troco == troco:
                    continue


                outro_prefixo, outro_sufixo = (
                    outro_troco.split(
                        "-",
                        1
                    )
                )


                # ------------------------------------------------
                # Exemplo:
                #
                # A-B
                # B-C
                #
                # B é o nó comum
                # ------------------------------------------------

                if sufixo == outro_prefixo:

                    acumulado_novo = round(
                        item["JxL (m.c.a)"] +
                        outro_item[
                            "Jacumulado (m.c.a)"
                        ],
                        2
                    )


                    if abs(
                        item[
                            "Jacumulado (m.c.a)"
                        ] -
                        acumulado_novo
                    ) > 0.0001:

                        item[
                            "Jacumulado (m.c.a)"
                        ] = acumulado_novo

                        mudancas = True


    return output_processado


# ============================================================
# DOCUMENTO
# ============================================================

doc = __revit__.ActiveUIDocument.Document


# ============================================================
# OBTER PIPES
# ============================================================

elements = rvt.get_elements_bycategory(
    doc,
    cat.PIPES
)


water_pipes = []


for ele in elements:

    parametro_sistema = ele.get_Parameter(
        BuiltInParameter.RBS_SYSTEM_NAME_PARAM
    )


    if parametro_sistema is None:
        continue


    nome_sistema = parametro_sistema.AsString()


    if not nome_sistema:
        continue


    if nome_sistema.startswith(
        ("AF", "AQ")
    ):

        water_pipes.append(
            WaterPipes(
                doc,
                ele
            )
        )


# ============================================================
# TRANSACTION
# ============================================================

t = Transaction(
    doc,
    "AA_Qcal + J acumulado"
)

t.Start()


try:

    # ========================================================
    # ORGANIZAR PIPES POR REDE
    # ========================================================

    redes = {}


    for p in water_pipes:

        sistema = p.system_type


        if sistema not in redes:

            redes[sistema] = []


        redes[sistema].append(p)


    # ========================================================
    # RESULTADOS FINAIS
    #
    # Aqui vamos guardar:
    #
    # rede -> resultados dos troços
    #
    # para só escrever no Revit depois de todos os cálculos.
    # ========================================================

    output_por_rede = {}


    # ========================================================
    # PROCESSAR CADA REDE
    # ========================================================

    for rede, elementos_rede in redes.items():


        # ----------------------------------------------------
        # 1. ORDENAR POR:
        #
        #    cota
        #    zona
        #    troço
        # ----------------------------------------------------

        ordenados = WaterPipes.aninhar_por_zona_troco(
            elementos_rede
        )


        # ----------------------------------------------------
        # 2. PROCESSAR TROÇOS
        #
        # Esta é a tua lógica original para determinar
        # os dispositivos de cada troço.
        # ----------------------------------------------------

        contagem = WaterPipes.processar_trocos(
            ordenados
        )


        # ----------------------------------------------------
        # 3. CALCULAR VALORES
        # ----------------------------------------------------

        output = []


        for c in contagem:


            # ------------------------------------------------
            # Caudal de cálculo
            # ------------------------------------------------

            caudal_cal = rpae.aa_qcal(
                c.caudal_acumulado
            )


            # ------------------------------------------------
            # Diâmetro de cálculo
            # ------------------------------------------------

            d_cal = rpae.aa_d_cal(
                caudal_cal
            )


            # ------------------------------------------------
            # Diâmetro interior
            # ------------------------------------------------

            d_interno = round(
                c.inside_diameter * 304.8
            )


            # ------------------------------------------------
            # Velocidade
            # ------------------------------------------------

            velocidade = rpae.aa_velocidade(
                caudal_cal,
                d_interno
            )


            # ------------------------------------------------
            # Perda de carga unitária
            # ------------------------------------------------

            perda_carga = rpae.perda_carga(
                velocidade,
                d_interno
            )


            # ------------------------------------------------
            # JxL
            # ------------------------------------------------

            j_mca = round(
                1.5 *
                perda_carga *
                c.comprimento,
                4
            )


            # ------------------------------------------------
            # Escrever parâmetros hidráulicos
            # ------------------------------------------------

            c.set_dcal(
                d_cal
            )

            c.set_qcal(
                caudal_cal
            )

            c.set_d_interno(
                d_interno
            )

            c.set_velocity(
                velocidade
            )

            c.set_perda_carga(
                perda_carga
            )

            c.set_jl(
                j_mca
            )


            # ------------------------------------------------
            # Guardar dados
            # ------------------------------------------------

            output.append({

                "Troço": c.troco,

                "Ltroço (m)": c.comprimento,

                "J (m/m)": perda_carga,

                "JxL (m.c.a)": j_mca

            })


        # ----------------------------------------------------
        # 4. CONSOLIDAR TROÇOS
        # ----------------------------------------------------

        output_consolidado = consolidar_output(
            output
        )


        # ----------------------------------------------------
        # 5. CALCULAR J ACUMULADO
        # ----------------------------------------------------

        output_jacumulado = calcular_jacumulado(
            output_consolidado
        )


        # ----------------------------------------------------
        # 6. GUARDAR RESULTADO DA REDE
        # ----------------------------------------------------

        output_por_rede[rede] = (
            output_jacumulado
        )


    # ========================================================
    # CRIAR MAPA FINAL:
    #
    # Troço -> Jacumulado
    #
    # Ex:
    #
    # A-B -> 5.32
    # B-C -> 3.15
    # C-D -> 1.72
    #
    # ========================================================

    jacumulados = {}


    for rede, resultados in output_por_rede.items():

        for item in resultados:

            troco = item.get(
                "Troço"
            )


            if not troco:
                continue


            valor = item.get(
                "Jacumulado (m.c.a)",
                0
            )


            jacumulados[troco] = valor


    # ========================================================
    # ESCREVER J ACUMULADO NOS PIPES
    #
    # TODOS os pipes pertencentes ao mesmo Troço recebem
    # exatamente o mesmo Jacumulado.
    #
    # ========================================================

    for p in water_pipes:

        troco = p.troco


        if not troco:
            continue


        if troco not in jacumulados:
            continue


        valor = jacumulados[troco]


        parametro_j = p.set_jacumulado(valor)


    t.Commit()


except Exception as ex:

    # --------------------------------------------------------
    # Se houver erro, fazer rollback
    # --------------------------------------------------------

    t.RollBack()

    print(
        "ERRO no cálculo de águas:"
    )

    print(
        str(ex)
    )

    raise