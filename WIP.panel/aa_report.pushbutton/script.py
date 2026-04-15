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
from collections import deque

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
        self.troco_auto = self.troco
        self.zona = elemento.LookupParameter("Zona").AsString()
        self.dispositivos = 1
        self.contador = elemento.LookupParameter("Contador").AsInteger()
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
        prefixos_validos = {"CH", "MLL", "MLR", "LV", "LL", "BR", "BA", "BD","BRE","LV1","LV2","TE"}
        for troco in trocos_unicos:
            partes = troco.split('-')
            if len(partes) == 2:
                prefixo, sufixo = partes
                trocos_info.append({
                    'original': troco,
                    'prefixo': prefixo,
                    'sufixo': sufixo,
                    'dispositivos': 1 if prefixo in prefixos_validos else 0
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
        elif valor < 67:
            d = 75
        elif valor < 82:
            d = 90
        else:
            d = 110
        
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
        elif valor == 63:
            d_int = 56
        elif valor == 75:   
            d_int = 66
        elif valor == 90:
            d_int = 73
        elif valor == 110:
            d_int = 90
        else:
            d_int = "error"

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

class PipeFitting:
    """Wrapper mínimo para fittings — só para construir o grafo"""
    def __init__(self, doc, elemento):
        self.elemento = elemento
        self.nome = elemento.Name
        self.troco_auto = None
        self.contador = 0
        try:
            self.system_type = elemento.LookupParameter("System Type").AsValueString()
        except:
            self.system_type = None

    def get_nome_sistema(self):
        try:
            from Autodesk.Revit.DB import BuiltInParameter
            return self.elemento.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
        except:
            return None

    @staticmethod
    def filter_by_system(lista, prefixo):
        return [f for f in lista if f.get_nome_sistema() and 
                f.get_nome_sistema().startswith(prefixo)]

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

"""
def gerar_trocos_automatico(elementos):

    # 🔹 Mapear ID -> elemento (NORMALIZADO)
    id_to_elem = {}
    ligacoes = {}

    for elem in elementos:
        elem_id = elem.elemento.Id
        id_to_elem[elem_id] = elem
        ligacoes[elem_id] = []

    # 🔹 Criar grafo
    for elem in elementos:
        elem_id = elem.elemento.Id

        try:
            connectors = elem.elemento.ConnectorManager.Connectors
        except:
            continue

        for c in connectors:
            for ref in c.AllRefs:
                owner = ref.Owner
                if owner:
                    other_id = owner.Id

                    if other_id in id_to_elem and other_id != elem_id:
                        if other_id not in ligacoes[elem_id]:
                            ligacoes[elem_id].append(other_id)

    # 🔍 encontrar contador (ROBUSTO)
    contador_id = None

    for elem in elementos:
        p = elem.elemento.LookupParameter("Contador")
        if p and p.AsInteger() == 1:
            contador_id = elem.elemento.Id
            print(contador_id )
            break

    #if contador_id is None:
        #raise Exception("❌ Não foi encontrado contador")

    # 🔁 BFS
    distancias = {}
    visitados = set()
    fila = [(contador_id, 0)]

    while fila:
        atual, dist = fila.pop(0)

        if atual in visitados:
            continue

        visitados.add(atual)
        distancias[atual] = dist

        for vizinho in ligacoes.get(atual, []):
            if vizinho not in visitados:
                fila.append((vizinho, dist + 1))

    # 📊 ordenar
    elementos_ordenados = sorted(
        elementos,
        key=lambda e: distancias.get(e.elemento.Id, 0),
        reverse=True
    )

    # 🏷️ atribuir troco (NÃO destrói original)
    for i, elem in enumerate(elementos_ordenados, 1):
        elem.troco_auto = "T{0:03d}".format(i)
        elem.elemento.LookupParameter("Comments").Set(elem.troco_auto)

    return elementos_ordenados
"""

def get_connector_manager(elemento):
    """Obtém ConnectorManager independentemente do tipo de elemento"""
    try:
        # Pipes e outros MEP elements
        return elemento.ConnectorManager
    except AttributeError:
        pass
    try:
        # FamilyInstance (fittings, válvulas, etc.)
        return elemento.MEPModel.ConnectorManager
    except:
        return None

def e_fitting_T(elemento):
    """True se fitting com 3+ conectores (bifurcação)"""
    try:
        cm = get_connector_manager(elemento)
        if cm is None:
            return False
        it = cm.Connectors.ForwardIterator()
        count = 0
        while it.MoveNext():
            count += 1
        return count >= 3
    except:
        return False

def gerar_trocos_automatico(elementos):
    from collections import deque

    id_to_elem = {}
    ligacoes = {}

    for elem in elementos:
        elem_id = elem.elemento.Id.Value  # ✅ int
        id_to_elem[elem_id] = elem
        ligacoes[elem_id] = []

    # 🔹 Construir grafo
    for elem in elementos:
        elem_id = elem.elemento.Id.Value  # ✅ int
        try:
            cm = get_connector_manager(elem.elemento)
            if cm is None:
                continue
            it = cm.Connectors.ForwardIterator()
            while it.MoveNext():
                c = it.Current
                refs_it = c.AllRefs.ForwardIterator()
                while refs_it.MoveNext():
                    ref = refs_it.Current
                    owner = ref.Owner
                    if owner:
                        other_id = owner.Id.Value  # ✅ int
                        if other_id in id_to_elem and other_id != elem_id:
                            if other_id not in ligacoes[elem_id]:
                                ligacoes[elem_id].append(other_id)
        except Exception as ex:
            print("Erro grafo ID {0}: {1}".format(elem_id, ex))
            continue

    # 🔍 Encontrar origem da rede
    contador_id = None
    
    # Primeiro tenta pelo parâmetro Contador = 1 (AF)
    for elem in elementos:
        if isinstance(elem, Element) and elem.contador == 1:
            contador_id = elem.elemento.Id.Value
            print("Contador encontrado: ID {0}".format(contador_id))
            break

    # Se não encontrou, procura termoacumulador (AQ)
    if contador_id is None:
        for elem_id, vizinhos in ligacoes.items():
            elem = id_to_elem[elem_id]
            try:
                from Autodesk.Revit.DB import BuiltInCategory
                cat_id = elem.elemento.Category.Id.Value
                if cat_id == int(BuiltInCategory.OST_PlumbingFixtures):
                    nome_lower = elem.elemento.Name.lower()
                    if "termoacumulador" in nome_lower:
                        # o pipe vizinho do TA é a origem
                        if vizinhos:
                            contador_id = vizinhos[0]
                            print("Termoacumulador encontrado — origem: ID {0}".format(contador_id))
                            break
            except:
                continue

    if contador_id is None:
        print("⚠️ Origem não encontrada — usando primeiro pipe como raiz")
        for elem in elementos:
            if isinstance(elem, Element):
                contador_id = elem.elemento.Id.Value
                break
    # ✅ Debug fixtures no grafo
    from Autodesk.Revit.DB import BuiltInCategory
    for elem_id, elem in id_to_elem.items():
        try:
            cat_id = elem.elemento.Category.Id.Value
            if cat_id == int(BuiltInCategory.OST_PlumbingFixtures):
                print("Fixture {0} | vizinhos: {1}".format(
                    elem.elemento.Name,
                    ligacoes.get(elem_id, [])))
        except:
            continue

    # ✅ Devolver grafo completo incluindo contador_id
    return elementos, ligacoes, id_to_elem, contador_id

def gerar_nomenclatura(elementos, ligacoes, id_to_elem, contador_id, nome_rede=""):
    from collections import deque

    def letra_de_indice(n):
        resultado = ""
        n += 1
        while n > 0:
            n, r = divmod(n - 1, 26)
            resultado = chr(65 + r) + resultado
        return resultado

    def e_no_principal(elemento):
        try:
            p = elemento.LookupParameter("No Principal")
            return p and p.AsInteger() == 1
        except:
            return False

    def e_fixture(elemento, rede=""):
        try:
            from Autodesk.Revit.DB import BuiltInCategory
            cat_id = elemento.Category.Id.Value
            if cat_id != int(BuiltInCategory.OST_PlumbingFixtures):
                return False
            if rede.startswith("AQ"):
                nome_lower = elemento.Name.lower()
                if "termoacumulador" in nome_lower:
                    return False
            return True
        except:
            return False

    def prefixo_fixture(nome):
        nome_lower = nome.lower()
        if "lava-louça" in nome_lower or "lava louça" in nome_lower:
            return "LL"
        elif "lavatório" in nome_lower or "lavatorio" in nome_lower:
            return "LV"
        elif "banheira" in nome_lower:
            return "BA"
        elif "chuveiro" in nome_lower:
            return "CH"
        elif "sanita" in nome_lower or "autoclismo" in nome_lower:
            return "BR"
        elif "bidé" in nome_lower or "bide" in nome_lower:
            return "BD"
        elif "máquina" in nome_lower or "maquina" in nome_lower:
            return "MQ"
        elif "boca" in nome_lower or "rega" in nome_lower:
            return "BDR"
        elif "piscina" in nome_lower:
            return "P"
        elif "termoacumulador" in nome_lower:
            return "TA"
        else:
            return "XX"

    no_map = {}
    troco_map = {}
    indice_no_principal = [0]
    contadores_derivacoes = {}

    def novo_no_principal():
        nome = letra_de_indice(indice_no_principal[0])
        indice_no_principal[0] += 1
        return nome

    def nova_derivacao(nome_pai):
        if nome_pai not in contadores_derivacoes:
            contadores_derivacoes[nome_pai] = 1
        else:
            contadores_derivacoes[nome_pai] += 1
        return "{0}.{1}".format(nome_pai, contadores_derivacoes[nome_pai])

    # 🔹 BFS
    visitados = set()

    if nome_rede.startswith("AQ"):
        no_origem = "TA"
    else:
        no_origem = "CONTADOR"

    no_map[contador_id] = no_origem
    troco_map[contador_id] = "{0}-?".format(no_origem)  # ✅ resolve na segunda passagem
    fila = deque([(contador_id, no_origem)])

    while fila:
        atual, no_atual = fila.popleft()

        if atual in visitados:
            continue
        visitados.add(atual)

        vizinhos = [v for v in ligacoes.get(atual, []) if v not in visitados]

        for vizinho_id in vizinhos:
            elem_vizinho = id_to_elem[vizinho_id].elemento

            # ✅ Fixture terminal
            if e_fixture(elem_vizinho, nome_rede):
                nome_lower = elem_vizinho.Name.lower()
                if "termoacumulador" in nome_lower:
                    # ✅ TA na AF é nó especial
                    troco_map[vizinho_id] = "TA"
                    no_map[vizinho_id] = "TA"
                else:
                    prefixo = prefixo_fixture(elem_vizinho.Name)
                    troco = "{0}.{1}".format(prefixo, no_atual)
                    troco_map[vizinho_id] = troco
                    no_map[vizinho_id] = troco
                visitados.add(vizinho_id)
                continue

            # ✅ Fitting T — cria nó novo
            if e_fitting_T(elem_vizinho):
                if e_no_principal(elem_vizinho):
                    novo_no = novo_no_principal()
                else:
                    novo_no = nova_derivacao(no_atual)

                no_map[vizinho_id] = novo_no
                troco_map[vizinho_id] = "{0}-{1}".format(no_atual, novo_no)
                fila.append((vizinho_id, novo_no))

            # ✅ Pipe ou válvula
            else:
                troco_map[vizinho_id] = "{0}-?".format(no_atual)
                fila.append((vizinho_id, no_atual))

    # 🔹 Segunda passagem — resolver os "?"
    for elem_id in list(troco_map.keys()):
        troco = troco_map[elem_id]
        if not troco.endswith("-?"):
            continue

        no_origem = troco.split("-?")[0]
        no_destino = None

        fila_busca = list(ligacoes.get(elem_id, []))
        visitados_busca = set([elem_id])

        while fila_busca and no_destino is None:
            vizinho_id = fila_busca.pop(0)
            if vizinho_id in visitados_busca:
                continue
            visitados_busca.add(vizinho_id)

            if vizinho_id in no_map:
                no_candidato = no_map[vizinho_id]
                if no_candidato != no_origem:
                    elem_candidato = id_to_elem[vizinho_id].elemento
                    nome_lower = elem_candidato.Name.lower()
                    if "termoacumulador" in nome_lower:
                        # ✅ TA é destino válido na AF
                        no_destino = no_candidato
                    elif not e_fixture(elem_candidato, nome_rede):
                        # ✅ nó normal (fitting T)
                        no_destino = no_candidato
                    else:
                        # ✅ fixture normal — usa só o prefixo como destino
                        no_destino = prefixo_fixture(elem_candidato.Name)
            else:
                fila_busca.extend(ligacoes.get(vizinho_id, []))

        if no_destino:
            troco_map[elem_id] = "{0}-{1}".format(no_destino, no_origem)
        else:
            troco_map[elem_id] = no_origem

    # 🔹 Aplicar ao modelo
    for elem in elementos:
        elem_id = elem.elemento.Id.Value
        troco = troco_map.get(elem_id, "?")
        elem.troco_auto = troco

        p = elem.elemento.LookupParameter("Comments")
        if p and not p.IsReadOnly:
            p.Set(troco)

    return elementos, troco_map, no_map

doc = __revit__.ActiveUIDocument.Document

piping_system = rvt.get_element_byclass(doc, cls.PIPING_SYSTEM, element_type=False)
pipe_fittings = rvt.get_elements_bycategory(doc, cat.PIPE_FITTINGS)
pipe_accessories  = rvt.get_elements_bycategory(doc, cat.PIPE_ACCESSORIES)
plumbing_fixtures = rvt.get_elements_bycategory(doc, cat.PLUMBING_FIXTURES)

fittings_wrapped = [PipeFitting(doc, f) for f in pipe_fittings]
accessories_wrapped = [PipeFitting(doc, a) for a in pipe_accessories]
fixtures_wrapped     = [PipeFitting(doc, pf) for pf in plumbing_fixtures]

levels = rvt.get_element_byclass(doc, cls.LEVEL)

elements = rvt.get_elements_bycategory(doc, cat.PIPES)

e = elements[0]

parameters = e.GetOrderedParameters()
t = []

pressao_rede = 30

# Criar dicionário para guardar elementos por rede
redes = {}

for ele in elements:
    nome_sistema = ele.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
    if nome_sistema.startswith(("AF", "AQ")):
        if nome_sistema not in redes:
            redes[nome_sistema] = []
        redes[nome_sistema].append(Element(doc, ele))

# Fittings + Acessórios — lógica normal
for elem in fittings_wrapped + accessories_wrapped:
    try:
        nome_sistema = elem.elemento.get_Parameter(
            BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
    except:
        continue
    if nome_sistema and nome_sistema in redes:
        redes[nome_sistema].append(elem)

# ✅ Fixtures — lógica especial, pode pertencer a múltiplas redes
for fixture in fixtures_wrapped:
    try:
        nome_sistema = fixture.elemento.get_Parameter(
            BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
    except:
        continue
    if not nome_sistema:
        continue
    # separar sistemas múltiplos ex: "AF,quente" -> ["AF", "quente"]
    sistemas = [s.strip() for s in nome_sistema.split(",")]
    for sistema in sistemas:
        if sistema in redes:
            if fixture not in redes[sistema]:  # evitar duplicados
                redes[sistema].append(fixture)

for l in levels:
    if l.Name == "RUA":
        lvl_abastecimento = round(l.Elevation/3.281)

t = Transaction(doc, "Relatorio Aguas")
t.Start()


output_por_rede_temp = {}  # guarda resultados finais por rede
for nome_rede, elementos_rede in redes.items():

    # 1. Gerar troços automaticamente
    elementos_rede, ligacoes, id_to_elem, contador_id = gerar_trocos_automatico(elementos_rede)

    # 2. Gerar nomenclatura
    elementos_com_troco, troco_map, no_map = gerar_nomenclatura(
        elementos_rede, ligacoes, id_to_elem, contador_id)

print("Fixtures recolhidos: {0}".format(len(fixtures_wrapped)))
for f in fixtures_wrapped[:3]:
    try:
        cat_id = f.elemento.Category.Id.Value  # ✅
        nome_sistema = f.elemento.get_Parameter(
            BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
        print("  Nome: {0} | Cat ID: {1} | Sistema: {2}".format(
            f.nome, cat_id, nome_sistema))
    except Exception as ex:
        print("  Erro: {0}".format(ex))

from Autodesk.Revit.DB import BuiltInCategory
print("OST_PlumbingFixtures ID: {0}".format(
    int(BuiltInCategory.OST_PlumbingFixtures)))
t.Commit()