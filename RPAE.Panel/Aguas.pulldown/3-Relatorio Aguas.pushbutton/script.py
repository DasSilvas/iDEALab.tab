# -*- coding: utf-8 -*-

__title__ = "3-Exportar Cálculo Excel"

__doc__ = "Exportacao do calculo das redes de água para excel"

__author__ = "Joao Ferreira, OE nº 86233"


# ============================================================
# LOAD LIBRARIES
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

from collections import defaultdict

import os.path
import sys
import math
import xlrd
import xlsxwriter

# ============================================================
# PATH
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
# IMPORTS
# ============================================================

from classes import WaterPipes
from classes import RvtApi as rvt
from classes import RvtClasses as cls
from classes import RvtApiCategory as cat
import os


# ============================================================
# CONSOLIDAR OUTPUT
# ============================================================

def consolidar_output(output_list):

    from collections import OrderedDict

    # Usar OrderedDict para manter a ordem
    # e agrupar por Troço

    trocos_consolidados = OrderedDict()

    for item in output_list:

        troco = item["Troço"]

        if troco not in trocos_consolidados:

            # Primeira ocorrência
            trocos_consolidados[troco] = item.copy()

        else:

            # Duplicado encontrado:
            # apenas somar o comprimento

            trocos_consolidados[troco]["Ltroço (m)"] += (
                item["Ltroço (m)"]
            )

    # --------------------------------------------------------
    # IMPORTANTE:
    #
    # NÃO recalcular J
    # NÃO recalcular JxL
    # NÃO recalcular J acumulado
    #
    # Estes valores já foram calculados no script
    # "2-Cálculo Águas" e gravados nos parâmetros do Revit.
    # --------------------------------------------------------

    output_consolidado = []

    for troco, dados in trocos_consolidados.items():

        dados["Ltroço (m)"] = round(
            dados["Ltroço (m)"],
            2
        )

        output_consolidado.append(dados)

    return output_consolidado


# ============================================================
# DOCUMENT
# ============================================================

doc = __revit__.ActiveUIDocument.Document

doc = __revit__.ActiveUIDocument.Document

# ========================================================
# DEFINIR PASTA DE EXPORTAÇÃO A PARTIR DO RVT
# ========================================================

caminho_rvt = doc.PathName
pasta_bim = os.path.dirname(caminho_rvt)
pasta_wip = os.path.dirname(pasta_bim)
pasta_exportacao = os.path.join(
    pasta_wip,
    "03-DISCIPLINE_FOLDERS",
    "PH-Aguas e Esgotos",
    "WS - Abastecimento Água"
)

# ============================================================
# ELEMENTOS
# ============================================================

piping_system = rvt.get_element_byclass(
    doc,
    cls.PIPING_SYSTEM,
    element_type=False
)

levels = rvt.get_element_byclass(
    doc,
    cls.LEVEL
)

elements = rvt.get_elements_bycategory(
    doc,
    cat.PIPES
)


# ============================================================
# PRESSÃO DA REDE / NÍVEL DE ABASTECIMENTO
# ============================================================

#pressao_rede = 30
project_info = doc.ProjectInformation
pressao_rede = project_info.LookupParameter("Pressão Disponível (mca)").AsDouble()
lvl_abastecimento = project_info.LookupParameter("Cota Abastecimento (m)").AsDouble()

# ============================================================
# CRIAR DICIONÁRIO PARA GUARDAR ELEMENTOS POR REDE
# ============================================================

redes = {}

for ele in elements:

    param_sistema = ele.get_Parameter(
        BuiltInParameter.RBS_SYSTEM_NAME_PARAM
    )

    if param_sistema is None:
        continue

    nome_sistema = param_sistema.AsString()

    if not nome_sistema:
        continue

    if nome_sistema.startswith(("AF", "AQ")):

        if nome_sistema not in redes:

            redes[nome_sistema] = []

        redes[nome_sistema].append(
            WaterPipes(
                doc,
                ele
            )
        )

# ============================================================
# CAMINHO EXCEL
# ============================================================

caminho = (
    r"Z:\865_2026-Sines_Porto"
    r"\01-WIP"
    r"\03-DISCIPLINE_FOLDERS"
    r"\PH-Aguas e Esgotos"
    r"\WS - Abastecimento Água"
    r"\cal_aguas.xlsx"
)


# ============================================================
# TRANSACTION
# ============================================================

t = Transaction(
    doc,
    "Relatorio Aguas"
)

t.Start()


# ============================================================
# OUTPUT POR REDE
# ============================================================

output_por_rede_temp = {}


for nome_rede, elementos_rede in redes.items():

    print("")
    print(
        "=========================================="
    )
    print(
        "Rede: {}".format(nome_rede)
    )
    print(
        "=========================================="
    )


    # --------------------------------------------------------
    # Ordenar elementos
    # --------------------------------------------------------

    ordenados = (
        WaterPipes.aninhar_por_zona_troco(
            elementos_rede
        )
    )


    # --------------------------------------------------------
    # Processar troços
    #
    # Mantém a lógica original para determinar
    # Nr Dispositivos.
    # --------------------------------------------------------

    contagem = (
        WaterPipes.processar_trocos(
            ordenados
        )
    )


    output = []


    # ========================================================
    # ELEMENTOS DA REDE
    # ========================================================

    for c in contagem:

        # ----------------------------------------------------
        # Número de dispositivos
        # ----------------------------------------------------

        c.set_dispositivos(
            c.dispositivos
        )


        # ----------------------------------------------------
        # Q cálculo
        #
        # JÁ EXISTENTE NO REVIT
        # ----------------------------------------------------

        q_cal = c.get_qcal()


        # ----------------------------------------------------
        # D cálculo
        #
        # JÁ EXISTENTE NO REVIT
        # ----------------------------------------------------

        d_cal = c.get_dcal()


        # ----------------------------------------------------
        # Diâmetro nominal
        #
        # Mantido da lógica original
        # ----------------------------------------------------

        d_nom = c.d_nominal(
            d_cal
        )


        # ----------------------------------------------------
        # Diâmetro interno
        #
        # Mantido da lógica original
        # ----------------------------------------------------

        d_int = c.d_interno(
            d_nom
        )


        # ----------------------------------------------------
        # Velocidade
        #
        # JÁ EXISTENTE NO REVIT
        # ----------------------------------------------------

        velocidade = c.get_velocidade()


        # ====================================================
        # J - PERDA DE CARGA
        #
        # ANTES:
        #
        # perda_carga = rpae.perda_carga(
        #     velocidade,
        #     d_int
        # )
        #
        # AGORA:
        # Ler diretamente do parâmetro "Perda de Carga"
        # ====================================================

        perda_carga = c.get_perda_carga()

        # ====================================================
        # JxL
        #
        # ANTES:
        #
        # j_mca = round(
        #     1.5 * perda_carga * c.comprimento,
        #     4
        # )
        #
        # AGORA:
        # Ler diretamente do parâmetro "JxL"
        # ====================================================

        j_mca = c.get_jl()


        # ====================================================
        # J ACUMULADO
        #
        # ANTES:
        #
        # era calculado posteriormente pela função
        # calcular_jacumulado()
        #
        # AGORA:
        # Ler diretamente do parâmetro "J acumulado"
        # ====================================================

        jacumulado = c.get_jacumulado()

        # ====================================================
        # DIFERENÇA DE COTA
        # ====================================================

        diferenca_cota = (
            2 +
            (
                c.lvl_elevation -
                lvl_abastecimento
            )
        )


        # ====================================================
        # OUTPUT
        # ====================================================

        output.append({

            "Elemento": c,

            "Piso": c.lvl_name,

            "Zona": c.zona,

            "Troço": c.troco,

            "Nr Dispositivos": c.dispositivos,

            "Qacumulado (l/s)": c.caudal_acumulado,

            "Qcálculo (l/s)": q_cal,

            "Dcálculo (mm)": d_cal,

            "Dnominal (mm)": d_nom,

            "Dinterno (mm)": d_int,

            "v (m/s)": velocidade,

            "J (m/m)": perda_carga,

            "Ltroço (m)": c.comprimento,

            "JxL (m.c.a)": j_mca,

            "Jacumulado (m.c.a)": jacumulado,

            "Diferença de cota (m)": diferenca_cota

        })

    # ========================================================
    # CONSOLIDAR TROÇOS
    # ========================================================

    x = consolidar_output(
        output
    )


    # ========================================================
    # PRESSÕES
    #
    # J acumulado já vem do Revit.
    # Apenas usamos esse valor para a verificação.
    # ========================================================

    for r in x:

        r[
            "Pressão de abastecimento (m.c.a)"
        ] = pressao_rede


        r[
            "Pressão verificada (m.c.a)"
        ] = round(
            r[
                "Pressão de abastecimento (m.c.a)"
            ]
            -
            (
                r[
                    "Jacumulado (m.c.a)"
                ]
                +
                r[
                    "Diferença de cota (m)"
                ]
            ),
            2
        )


    # --------------------------------------------------------
    # Guardar resultado da rede
    # --------------------------------------------------------

    output_por_rede_temp[
        nome_rede
    ] = x


# ============================================================
# ORGANIZAR POR PISO
# ============================================================

output_por_piso = {}

# chave = Piso
# valor = dict {"AF": [...], "AQ": [...]}

for nome_rede, dados in (
    output_por_rede_temp.items()
):

    partes = nome_rede.split(
        "_",
        1
    )

    rede_tipo = partes[0]

    piso = (
        partes[1]
        if len(partes) > 1
        else "Sem Piso"
    )


    if piso not in output_por_piso:

        output_por_piso[piso] = {}


    output_por_piso[piso][
        rede_tipo
    ] = dados

# ============================================================
# CRIAR WORKBOOK
# ============================================================

caminho_excel = os.path.join(
    pasta_exportacao,
    "Calculo_Aguas.xlsx"
)

workbook = xlsxwriter.Workbook(caminho_excel)


# ============================================================
# KEYS
# ============================================================

keys = [

    "Piso",
    "Zona",
    "Troço",
    "Nr Dispositivos",
    "Qacumulado (l/s)",
    "Qcálculo (l/s)",
    "Dcálculo (mm)",
    "Dnominal (mm)",
    "Dinterno (mm)",
    "v (m/s)",
    "J (m/m)",
    "Ltroço (m)",
    "JxL (m.c.a)",
    "Jacumulado (m.c.a)",
    "Pressão de abastecimento (m.c.a)",
    "Diferença de cota (m)",
    "Pressão verificada (m.c.a)"

]


# ============================================================
# FORMATOS
# ============================================================

titulo_format = workbook.add_format({

    "bold": True,

    "align": "center",

    "valign": "vcenter",

    "bg_color": "#0a5e55",

    "border": 1,

    "font_color": "#ffffff"

})


header_format = workbook.add_format({

    "bold": True,

    "bg_color": "#08544c",

    "border": 1,

    "align": "center",

    "font_color": "#ffffff",

    "rotation": 90,

    "text_wrap": True

})


cell_format = workbook.add_format({

    "border": 1,

    "valign": "vcenter",

    "align": "center"

})


# ============================================================
# CRIAR FOLHAS POR PISO
# ============================================================

for piso, redes_piso in sorted(
    output_por_piso.items()
):

    worksheet = workbook.add_worksheet(
        piso[:31]
    )


    print(
        "Worksheet criada: {}".format(
            piso
        )
    )


    row_offset = 0


    # ========================================================
    # CASO EXISTAM AF E AQ NO MESMO PISO
    # ========================================================

    if (
        "AF" in redes_piso
        and
        "AQ" in redes_piso
    ):

        dados_af = redes_piso["AF"]

        dados_aq = redes_piso["AQ"]


        # ----------------------------------------------------
        # Troço AF que começa por "AQS"
        # ----------------------------------------------------

        troco_af_aqs = next(

            (
                r
                for r in dados_af
                if r.get(
                    "Troço",
                    ""
                ).startswith("AQS")
            ),

            None

        )


        if troco_af_aqs:

            jacumulado_af_aqs = (
                troco_af_aqs.get(
                    "Jacumulado (m.c.a)",
                    0
                )
            )


            # ------------------------------------------------
            # Somar o J acumulado da AF-AQS à AQ
            # ------------------------------------------------

            for r in dados_aq:

                r[
                    "Jacumulado (m.c.a)"
                ] += jacumulado_af_aqs


                # --------------------------------------------
                # Atualizar pressão verificada
                # --------------------------------------------

                r[
                    "Pressão verificada (m.c.a)"
                ] = (

                    r.get(
                        "Pressão de abastecimento (m.c.a)",
                        0
                    )

                    -

                    (
                        r[
                            "Jacumulado (m.c.a)"
                        ]

                        +

                        r.get(
                            "Diferença de cota (m)",
                            0
                        )
                    )

                )


    # ========================================================
    # ESCREVER AF E AQ
    # ========================================================

    for rede_tipo in [
        "AF",
        "AQ"
    ]:

        if rede_tipo not in redes_piso:

            continue


        dados = redes_piso[
            rede_tipo
        ]


        if not dados:

            continue


        # ----------------------------------------------------
        # TÍTULO
        # ----------------------------------------------------

        worksheet.merge_range(

            row_offset,

            0,

            row_offset,

            len(keys) - 1,

            "Rede {}".format(
                rede_tipo
            ),

            titulo_format

        )


        row_offset += 1


        # ----------------------------------------------------
        # CABEÇALHOS
        # ----------------------------------------------------

        for col, key in enumerate(
            keys
        ):

            worksheet.write(

                row_offset,

                col,

                key,

                header_format

            )


        worksheet.set_row(
            row_offset,
            82.5
        )


        row_offset += 1


        # ----------------------------------------------------
        # MERGE DE PISOS
        # ----------------------------------------------------

        piso_atual = None

        start_merge = row_offset


        max_lens = [

            len(str(k))
            for k in keys

        ]

        # ========================================================
        # ORDENAR DADOS
        #
        # 1.º Nr Dispositivos - maior para menor
        # 2.º Troço - ordem crescente
        # ========================================================
        dados = sorted(
            dados,
            key=lambda x: (
                -x.get("Nr Dispositivos", 0),
                x.get("Troço", "")
            )
        )

        # ====================================================
        # ESCREVER DADOS
        # ====================================================

        for item in dados:

            valor_piso = item[
                "Piso"
            ]


            # ------------------------------------------------
            # Merge do bloco anterior se piso muda
            # ------------------------------------------------

            if (

                piso_atual is not None

                and

                valor_piso != piso_atual

            ):

                if (
                    row_offset -
                    start_merge
                    > 1
                ):

                    worksheet.merge_range(

                        start_merge,

                        0,

                        row_offset - 1,

                        0,

                        piso_atual,

                        cell_format

                    )


                start_merge = row_offset


            piso_atual = valor_piso


            # ------------------------------------------------
            # Escrever colunas
            # ------------------------------------------------

            for col_idx, key in enumerate(
                keys
            ):

                valor = item.get(
                    key,
                    ""
                )


                worksheet.write(

                    row_offset,

                    col_idx,

                    valor,

                    cell_format

                )


                if valor is not None:

                    max_lens[
                        col_idx
                    ] = max(

                        max_lens[
                            col_idx
                        ],

                        len(
                            str(valor)
                        )

                    )


            row_offset += 1


        # ----------------------------------------------------
        # Merge do último bloco de piso
        # ----------------------------------------------------

        if (
            row_offset -
            start_merge
            > 1
        ):

            worksheet.merge_range(

                start_merge,

                0,

                row_offset - 1,

                0,

                piso_atual,

                cell_format

            )


        # ====================================================
        # LARGURA DAS COLUNAS
        # ====================================================

        for col_idx, key in enumerate(
            keys
        ):

            if key in [

                "Pressão verificada (m.c.a)",

                "Pressão de abastecimento (m.c.a)"

            ]:

                worksheet.set_column(

                    col_idx,

                    col_idx,

                    8.71

                )

            else:

                valores_coluna = [

                    str(
                        item.get(
                            key,
                            ""
                        )
                    )

                    for item in dados

                ]


                if valores_coluna:

                    largura_max = max(

                        len(v)

                        for v in valores_coluna

                    )


                    worksheet.set_column(

                        col_idx,

                        col_idx,

                        largura_max + 2

                    )


        # ----------------------------------------------------
        # Espaço entre AF e AQ
        # ----------------------------------------------------

        row_offset += 3


# ============================================================
# TROÇO DE ALIMENTAÇÃO
# ============================================================
#
# Mantido comentado nesta fase, tal como no código original.
#
# Vamos tratar esta parte separadamente depois, porque aqui
# existe um cálculo independente para o troço equivalente.
#
# ============================================================


"""
# --- aba do troço equivalente ---

worksheet_eq = workbook.add_worksheet(
    "Troço Alimentação"
)

headers_eq = [

    "Qacumulado Total (l/s)",

    "Qcálculo Total",

    "Dcálculo Total",

    "Dnominal Total",

    "Dinterno Total",

    "Velocidade Total (m/s)",

    "Perda de Carga Total (m.ca)"

]

values_eq = [

    soma_qacu,

    q_cal_total,

    d_cal_total,

    d_nom_total,

    d_int_total,

    velocidade_total,

    perdar_carga_total

]

worksheet_eq.merge_range(

    0,
    0,
    0,
    len(headers_eq) - 1,

    "Troço de Alimentação",

    titulo_format

)

row_offset = 1

for col, key in enumerate(
    headers_eq
):

    worksheet_eq.write(

        row_offset,
        col,
        key,
        header_format

    )

for col, val in enumerate(
    values_eq
):

    worksheet_eq.write(

        row_offset + 1,
        col,
        val,
        cell_format

    )

for col_idx, val in enumerate(
    values_eq
):

    largura_max = len(
        str(val)
    )

    worksheet_eq.set_column(

        col_idx,
        col_idx,

        largura_max + 2

    )

worksheet_eq.set_row(
    row_offset,
    82.5
)
"""


# ============================================================
# FECHAR WORKBOOK
# ============================================================

workbook.close()


print("")
print(
    "=========================================="
)
print(
    "Excel exportado com sucesso."
)
print(
    "=========================================="
)
print(
    "Ficheiro: {}".format(
        caminho
    )
)
print("")


# ============================================================
# COMMIT
# ============================================================

t.Commit()
