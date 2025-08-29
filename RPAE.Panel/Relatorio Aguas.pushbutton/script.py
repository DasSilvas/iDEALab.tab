# -*- coding: utf-8 -*-
"""WIP vistas"""
# Load the Python Standard and DesignScript Libraries
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

# get the absolute path to the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# add the grandparent directory to the system path
sys.path.insert(0, grandparent_dir)

from classes import RvtApi as rvt
from classes import RvtClasses as cls
from classes import RvtApiCategory as cat

class Element:

    def __init__(self, doc, elemento):

        self.elemento = elemento
        self.nome = elemento.Name
        self.type = doc.GetElement(elemento.GetTypeId())
        #self.velocidade = round(elemento.LookupParameter("Velocity").AsDouble()/3.28084, 2)
        self.q_acu = round(elemento.LookupParameter("Flow").AsDouble()*28.317,2)
        self.comprimento = round(elemento.LookupParameter("Length").AsDouble()/3.281,2)
        self.fu = elemento.LookupParameter("Fixture Units").AsDouble()
        self.troco = elemento.LookupParameter("Troço").AsString()
        self.zona = elemento.LookupParameter("Zona").AsString()
        self.dispositivos = 1
        self.lvl_name = self.get_lvl_name()
        self.lvl_elevation = self.get_lvl_elevation()

   
    def get_lvl_name(self):

        lvl = doc.GetElement(self.elemento.LookupParameter("Reference Level").AsElementId())
        lvl_name = lvl.Name 

        return lvl_name
    
    def get_lvl_elevation(self):

        lvl = doc.GetElement(self.elemento.LookupParameter("Reference Level").AsElementId())
        lvl_elevation = round(lvl.Elevation/3.281, 2)

        return lvl_elevation

    def set_dispositivos(self, valor):
        v = self.elemento.LookupParameter("Nr Dispositivos").Set(valor)
        return v

    @classmethod    
    def processar_trocos(cls, lista_trocos):
        """
        Processa uma lista de troços removendo duplicados e calculando o número de dispositivos.
        
        Regras:
        1. Remover duplicados
        2. Por defeito, troços com prefixo numérico têm 1 dispositivo
        3. Quando vários sufixos iguais existem em troços diferentes, 
        o troço com prefixo igual ao sufixo deve somar os números de dispositivos
        4. Considera todos os valores da lista, mesmo os que aparecem depois
        """
        
        # Remover duplicados mantendo a ordem
        trocos_unicos = []
        for item in lista_trocos:
            if item.troco not in trocos_unicos:
                trocos_unicos.append(item.troco)
        
        # Separar prefixos e sufixos
        trocos_info = []
        for troco in trocos_unicos:
            partes = troco.split('-')
            if len(partes) == 2:
                prefixo, sufixo = partes
                trocos_info.append({
                    'original': troco,
                    'prefixo': prefixo,
                    'sufixo': sufixo,
                    'dispositivos': 1 if prefixo.isdigit() else 0
                })
        
        # Criar mapeamentos para análise completa
        # Mapa de sufixos para troços que terminam nesse sufixo
        sufixos_para_trocos = {}
        # Mapa de prefixos para troços que começam com esse prefixo
        prefixos_para_trocos = {}
        
        for info in trocos_info:
            sufixo = info['sufixo']
            prefixo = info['prefixo']
            
            if sufixo not in sufixos_para_trocos:
                sufixos_para_trocos[sufixo] = []
            sufixos_para_trocos[sufixo].append(info)
            
            if prefixo not in prefixos_para_trocos:
                prefixos_para_trocos[prefixo] = []
            prefixos_para_trocos[prefixo].append(info)
        
        # Fazer múltiplas passagens até não haver mais mudanças
        # Isso garante que consideramos todos os valores, mesmo os que aparecem depois
        mudancas = True
        iteracao = 0
        max_iteracoes = len(trocos_info) + 1  # Evitar loop infinito
        
        while mudancas and iteracao < max_iteracoes:
            mudancas = False
            iteracao += 1
            
            for info in trocos_info:
                prefixo = info['prefixo']
                dispositivos_anteriores = info['dispositivos']
                
                # Se este prefixo aparece como sufixo noutros troços
                if prefixo in sufixos_para_trocos:
                    # Somar dispositivos dos troços que terminam neste prefixo
                    dispositivos_a_somar = 0
                    trocos_contribuintes = []
                    
                    for troco_com_sufixo in sufixos_para_trocos[prefixo]:
                        # Só contar troços que têm dispositivos (evitar loops infinitos)
                        if troco_com_sufixo['dispositivos'] > 0:
                            dispositivos_a_somar += troco_com_sufixo['dispositivos']
                            trocos_contribuintes.append(troco_com_sufixo['original'])
                    
                    # Atualizar o número de dispositivos se houver contribuições
                    if dispositivos_a_somar > 0 and not info['prefixo'].isdigit():
                        novo_valor = dispositivos_a_somar
                        if info['dispositivos'] != novo_valor:
                            info['dispositivos'] = novo_valor
                            mudancas = True
    
        # 2. Criar mapa final troco -> dispositivos
        troco_para_dispositivos = {info['original']: info['dispositivos'] for info in trocos_info}
            
        # 3. Atualizar todos os elementos originais (mesmo duplicados)
        for elem in lista_trocos:
            if elem.troco in troco_para_dispositivos:
                elem.dispositivos = troco_para_dispositivos[elem.troco]
            else:
                elem.dispositivos = 1  # fallback
        
        return lista_trocos
    
        #return trocos_info
    """
    @classmethod
    def aninhar_por_zona_troco(cls, lista_elementos):
      
        Retorna lista aninhada: [[elementos_da_zona1], [elementos_da_zona2], ...],
        cada sublista ordenada por troco.
        
        from collections import defaultdict

        zonas = defaultdict(list)
        for e in lista_elementos:
            zonas[e.zona].append(e)

        zonas_ordenadas = sorted(zonas.keys())

        lista_aninhada = []
        for zona in zonas_ordenadas:
            sublista = sorted(zonas[zona], key=lambda e: (e.lvl_elevation, e.troco))
            lista_aninhada.append(sublista)

        return lista_aninhada
    """
    @classmethod
    def aninhar_por_zona_troco(cls, lista_elementos):
        """
        Retorna lista ordenada de elementos, priorizando:
        1) lvl_elevation (mais baixo → mais alto)
        2) zona (alfabético)
        3) troço
        """
        from operator import attrgetter

        # Ordenação múltipla usando tupla: elevation → zona → troço
        lista_ordenada = sorted(
            lista_elementos,
            key=lambda e: (e.lvl_elevation, e.zona, e.troco)
        )
        
        return lista_ordenada


    @classmethod
    def flatten_lista_aninhada(cls, lista_aninhada):
        """
        Recebe lista aninhada e retorna uma lista plana,
        mantendo a ordem de zonas e trocos.
        """
        return [e for sublista in lista_aninhada for e in sublista]

    def q_calculo(self, valor):
        if valor <= 3.5:
            self.q_cal = round(0.5469*valor**0.5137, 2)
        elif 3.5 < valor <=25:
            self.q_cal = round(0.5226*valor**0.5364, 2)
        elif 25 < valor <= 500:
            self.q_cal = round(0.2525*valor**0.7587, 2)
        else:
            self.q_cal = "error"
        return self.q_cal 

    def d_cal(self, valor):
        v = 2

        d = round(math.sqrt((1.273*(valor/1000))/v)*1000, 2)

        return d

    def d_nominal(self, valor):
        if valor < 12:
            d = 16
        elif valor < 16:
            d = 20
        elif valor < 20:
            d = 26
        elif valor < 26:
            d = 32
        elif valor < 32:
            d = 40
        elif valor < 42:
            d = 50
        elif valor < 54:
            d = 63
        else:
            d = 75
        
        return d

    def d_interno(self, valor):
        if valor == 16:
            d_int = 12
        elif valor == 20:
            d_int = 16
        elif valor == 26:
            d_int = 20
        elif valor == 32:
            d_int = 26
        elif valor == 40:
            d_int = 32
        elif valor == 50:
            d_int = 42
        else:
            d_int = 10000

        return float(d_int)

    def velocidade(self, caudal_cal, d_interno):
        vel = round(((caudal_cal*4000)/(math.pi*(d_interno**2))), 2)
        return vel
    
    def perda_carga(self, v, d, b="plastico"):
        if b == "aco":
            b = 0.000152
        else:
            b = 0.000134

        d_meters = d/1000

        j = round(4*b*((v)**(1.75))*((d_meters)**(-1.25)), 6)

        return j

def consolidar_output(output_list):
    """
    Remove duplicados do output mantendo informações específicas e somando J e Ltroço.
    
    Mantém:
    - Zona, Troço, Nr Dispositivos, Qacumulado, Qcálculo, Dcálculo, 
      Dnominal, Dinterno, v (do primeiro encontrado)
    
    Soma:
    - J (m/m) -> mantém o valor (assumindo que é igual para o mesmo troço)
    - Ltroço (m) -> soma todos os comprimentos do mesmo troço
    - JxL (m.c.a) -> recalcula baseado no Ltroço somado
    
    Args:
        output_list: Lista de dicionários com os dados calculados
        
    Returns:
        Lista consolidada sem duplicados
    """
    from collections import OrderedDict
    
    # Usar OrderedDict para manter a ordem e agrupar por troço
    trocos_consolidados = OrderedDict()
    
    for item in output_list:
        troco = item["Troço"]
        
        if troco not in trocos_consolidados:
            # Primeira ocorrência - copiar todos os dados
            trocos_consolidados[troco] = item.copy()
        else:
            # Duplicado encontrado - somar apenas Ltroço
            trocos_consolidados[troco]["Ltroço (m)"] += item["Ltroço (m)"]
            #trocos_consolidados[troco]["J (m/m)"] += item["J (m/m)"]
    
    # Recalcular JxL baseado no novo Ltroço somado
    output_consolidado = []
    for troco, dados in trocos_consolidados.items():
        # Recalcular JxL com o comprimento total
        j_valor = dados["J (m/m)"]
        l_total = dados["Ltroço (m)"]
        dados["JxL (m.c.a)"] = round(1.5 * j_valor * l_total, 2)
        
        output_consolidado.append(dados)
    
    return output_consolidado

def calcular_jacumulado(output_list):
    """
    Calcula JxL acumulado propagando do jusante para o montante.
    
    Exemplo: B-C alimenta A-B (porque B é o nó comum).
    """
    
    # Copiar lista
    output_processado = []
    for item in output_list:
        novo_item = item.copy()
        novo_item['Jacumulado (m.c.a)'] = novo_item['JxL (m.c.a)']
        output_processado.append(novo_item)

    mudancas = True
    iteracao = 0
    max_iteracoes = len(output_processado) + 2

    while mudancas and iteracao < max_iteracoes:
        mudancas = False
        iteracao += 1

        for item in output_processado:
            troco = item['Troço']
            if '-' not in troco:
                continue
            
            prefixo, sufixo = troco.split('-', 1)

            # procurar troços que começam neste sufixo (jusante)
            for outro_item in output_processado:
                outro_troco = outro_item['Troço']
                if '-' not in outro_troco or outro_troco == troco:
                    continue

                outro_prefixo, outro_sufixo = outro_troco.split('-', 1)

                # se este sufixo (do montante) == prefixo do jusante
                if sufixo == outro_prefixo:
                    acumulado_novo = round(item['JxL (m.c.a)'] + outro_item['Jacumulado (m.c.a)'], 2)
                    if abs(item['Jacumulado (m.c.a)'] - acumulado_novo) > 0.0001:
                        item['Jacumulado (m.c.a)'] = acumulado_novo
                        mudancas = True

    return output_processado

doc = __revit__.ActiveUIDocument.Document

piping_system = rvt.get_element_byclass(doc, cls.PIPING_SYSTEM, element_type=False)

levels = rvt.get_element_byclass(doc, cls.LEVEL)

elements = rvt.get_elements_bycategory(doc, cat.PIPES)

e = elements[0]

parameters = e.GetOrderedParameters()
t = []

pressao_rede = 35

# Criar dicionário para guardar elementos por rede
redes = {}

for ele in elements:
    nome_sistema = ele.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
    if nome_sistema.startswith(("AF", "AQ")):
        if nome_sistema not in redes:
            redes[nome_sistema] = []
        redes[nome_sistema].append(Element(doc, ele))


for l in levels:
    if l.Name == "Soleira":
        lvl_abastecimento = round(l.Elevation/3.281)

caminho = r"C:\Users\jf\Desktop\Nova pasta\meu_excel.xlsx"

t = Transaction(doc, "Relatorio Aguas")
t.Start()

output_por_rede_temp = {}  # guarda resultados finais por rede
for nome_rede, elementos_rede in redes.items():
    
    ordenados = Element.aninhar_por_zona_troco(elementos_rede)
    #ordenados = Element.flatten_lista_aninhada(ordenados1)
    contagem = Element.processar_trocos(ordenados)

    output = []
    for c in contagem:
        c.set_dispositivos(c.dispositivos)
        q_cal = c.q_calculo(c.q_acu)
        d_cal = c.d_cal(c.q_cal)
        d_nom = c.d_nominal(d_cal)
        d_int = c.d_interno(d_nom)
        velocidade = c.velocidade(c.q_cal, d_int)
        perda_carga = c.perda_carga(velocidade, d_int)
        j_mca = round(1.5 * perda_carga * c.comprimento, 4)

        output.append({
            "Elemento": c,
            "Piso": c.lvl_name,
            "Zona": c.zona,
            "Troço": c.troco,
            "Nr Dispositivos": c.dispositivos,
            "Qacumulado (l/s)": c.q_acu,
            "Qcálculo (l/s)": c.q_cal,
            "Dcálculo (mm)": d_cal,
            "Dnominal (mm)": d_nom,
            "Dinterno (mm)": d_int,
            "v (m/s)": velocidade,
            "J (m/m)": perda_carga,
            "Ltroço (m)": c.comprimento,
            "JxL (m.c.a)": j_mca,
            "Diferença de cota (m)": 2 + (c.lvl_elevation - lvl_abastecimento)
        })

    x = consolidar_output(output)
    y = calcular_jacumulado(x)

    # Acrescentar colunas adicionais
    for r in y:
        r["Pressão de abastecimento (m.c.a)"] = pressao_rede
        r["Pressão verificada (m.c.a)"] = r["Pressão de abastecimento (m.c.a)"] - (r["Jacumulado (m.c.a)"] + r["Diferença de cota (m)"])
        
    output_por_rede_temp[nome_rede] = y

output_por_piso = {}  # chave = Piso, valor = dict{"AF": [...], "AQ": [...]}

for nome_rede, dados in output_por_rede_temp.items():
    partes = nome_rede.split(" ", 1)
    rede_tipo = partes[0]         # "AF" ou "AQ"
    piso = partes[1] if len(partes) > 1 else "Sem Piso"

    if piso not in output_por_piso:
        output_por_piso[piso] = {}

    output_por_piso[piso][rede_tipo] = dados


trocos_contador_por_rede = {}
soma_qacu = 0
modelo_elem = None  # referência ao elemento para usar as funções da classe

for nome_rede, dados in output_por_rede_temp.items():
    troco_contador = next(
        (row for row in dados if str(row.get("Troço", "")).endswith("Contador")),
        None
    )
    
    if troco_contador:
        elem = troco_contador["Elemento"]   # objeto Element original
        soma_qacu += elem.q_acu
        trocos_contador_por_rede[nome_rede] = troco_contador
        
        # guarda o primeiro modelo_elem encontrado
        if modelo_elem is None:
            modelo_elem = elem

# Agora podemos usar modelo_elem para calcular o troço equivalente baseado na soma
if modelo_elem:

    q_cal_total = modelo_elem.q_calculo(soma_qacu)
    d_cal_total = modelo_elem.d_cal(q_cal_total)
    d_nom_total = modelo_elem.d_nominal(d_cal_total)
    d_int_total = modelo_elem.d_interno(d_nom_total)
    velocidade_total = modelo_elem.velocidade(q_cal_total, d_int_total)
    perdar_carga_total = modelo_elem.perda_carga(velocidade_total, d_int_total)

print(soma_qacu)
    # Criar workbook e worksheet
workbook = xlsxwriter.Workbook(caminho)

keys = [
    "Piso","Zona","Troço","Nr Dispositivos","Qacumulado (l/s)","Qcálculo (l/s)",
    "Dcálculo (mm)","Dnominal (mm)","Dinterno (mm)","v (m/s)","J (m/m)",
    "Ltroço (m)","JxL (m.c.a)","Jacumulado (m.c.a)","Pressão de abastecimento (m.c.a)",
    "Diferença de cota (m)","Pressão verificada (m.c.a)"
]

titulo_format = workbook.add_format({"bold": True,"align": "center","valign": "vcenter","bg_color": "#0a5e55","border": 1, "font_color": "#ffffff"})
header_format = workbook.add_format({"bold": True,"bg_color": "#08544c","border": 1, "align": "center", "font_color": "#ffffff", "rotation": 90, "text_wrap": True})
cell_format = workbook.add_format({"border": 1, "valign": "vcenter", "align": "center"})

for piso, redes_piso in sorted(output_por_piso.items()):
    worksheet = workbook.add_worksheet(piso[:31])
    row_offset = 0

    if "AF" in redes_piso and "AQ" in redes_piso:
        dados_af = redes_piso["AF"]
        dados_aq = redes_piso["AQ"]

        # 1️⃣ Troço AF que começa por "AQS"
        troco_af_aqs = next((r for r in dados_af if r.get("Troço","").startswith("AQS")), None)

        if troco_af_aqs:
            jacumulado_af_aqs = troco_af_aqs.get("Jacumulado (m.c.a)", 0)

            # 2️⃣ Somar esse valor a todos os Jacumulados de AQ
            for r in dados_aq:
                r["Jacumulado (m.c.a)"] += jacumulado_af_aqs
                # atualizar Pressão verificada
                r["Pressão verificada (m.c.a)"] = (
                    r.get("Pressão de abastecimento (m.c.a)", 0) -
                    (r["Jacumulado (m.c.a)"] + r.get("Diferença de cota (m)", 0))
                )

    for rede_tipo in ["AF", "AQ"]:
        if rede_tipo in redes_piso:
            dados = redes_piso[rede_tipo]
            if not dados:
                continue

            # título
            worksheet.merge_range(row_offset, 0, row_offset, len(keys)-1, "Rede {}".format(rede_tipo), titulo_format)
            row_offset += 1

            # Cabeçalhos
            for col, key in enumerate(keys):
                worksheet.write(row_offset, col, key, header_format)

            worksheet.set_row(row_offset, 82.5)
            row_offset += 1

            # Inicializar variáveis para merge de pisos
            piso_atual = None
            start_merge = row_offset
            max_lens = [len(str(k)) for k in keys]

            # Escrever dados
            for item in dados:
                valor_piso = item["Piso"]

                # Merge do bloco anterior se piso muda
                if piso_atual is not None and valor_piso != piso_atual:
                    if row_offset - start_merge > 1:
                        worksheet.merge_range(start_merge, 0, row_offset-1, 0, piso_atual, cell_format)
                    start_merge = row_offset

                piso_atual = valor_piso

                # Escrever colunas
                for col_idx, key in enumerate(keys):
                    valor = item.get(key, "")
                    worksheet.write(row_offset, col_idx, valor, cell_format)
                    if valor is not None:
                        max_lens[col_idx] = max(max_lens[col_idx], len(str(valor)))
                row_offset += 1

            # Merge do último bloco de piso
            if row_offset - start_merge > 1:
                worksheet.merge_range(start_merge, 0, row_offset-1, 0, piso_atual, cell_format)


            # Ajustar largura de cada coluna apenas pelos dados (sem contar header)
            for col_idx, key in enumerate(keys):
                if key in ["Pressão verificada (m.c.a)", "Pressão de abastecimento (m.c.a)"]:
                    worksheet.set_column(col_idx, col_idx, 8.71)  # largura fixa
                else:
                    valores_coluna = [str(item.get(key, "")) for item in dados]
                    if valores_coluna:  # só se houver valores
                        largura_max = max(len(v) for v in valores_coluna)
                        worksheet.set_column(col_idx, col_idx, largura_max + 2)


            # Adicionar 3 linhas de espaço antes da próxima rede
            row_offset += 3

# --- aba do troço equivalente ---
worksheet_eq = workbook.add_worksheet("Troço Alimentação")

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

# Escrever o título na primeira linha, merge em todas as colunas
worksheet_eq.merge_range(0, 0, 0, len(headers_eq)-1, "Troço de Alimentação", titulo_format)

# Linha inicial para os cabeçalhos dos dados
row_offset = 1

# Escrever cabeçalhos
for col, key in enumerate(headers_eq):
    worksheet_eq.write(row_offset, col, key, header_format)

# Escrever valores
for col, val in enumerate(values_eq):
    worksheet_eq.write(row_offset + 1, col, val, cell_format)

# Ajustar largura das colunas baseado apenas nos dados
for col_idx, val in enumerate(values_eq):
    largura_max = len(str(val))  # comprimento do dado
    worksheet_eq.set_column(col_idx, col_idx, largura_max + 2)  # adicionar 2 para margem

# Definir altura da linha do cabeçalho e moldar texto
worksheet_eq.set_row(row_offset, 82.5)

# Fechar workbook
workbook.close()
print("Excel exportado com abas por piso (AF e AQ) e aba do troço equivalente.")


t.Commit()
