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

def eh_no(fitting_pipes):
    """
    fitting_pipes: lista de pipes ligados a um fitting
    retorna True se o fitting for nó, False caso contrário
    """
    sufixos = []
    prefixos = []

    for pipe in fitting_pipes:
        troco = pipe.get_Parameter("Troço").AsString()  # Acessar parâmetro troço
        if '-' in troco:
            prefixo, sufixo = troco.strip("[]").split('-')
            prefixos.append(prefixo)
            sufixos.append(sufixo)

    sufixos_unicos = set(sufixos)
    
    # Caso 1: só existe um sufixo → não é nó
    if len(sufixos_unicos) == 1:
        return False

    # Caso 2: verificar se algum sufixo aparece como prefixo → é nó
    for s in sufixos_unicos:
        if s in prefixos:
            return True

    # Caso 3: múltiplos sufixos, mas nenhum aparece como prefixo → não é nó
    return False

def encontrar_pipe(elemento):
    """
    Recebe um elemento (fitting ou pipe)
    Retorna o pipe final ligado, pulando adaptadores/fittings intermediários
    """
    if elemento.Category.Name == "Pipes":  # Ou verifica outro critério de pipe
        return elemento

    # Se não for pipe, tenta seguir os connectors
    if hasattr(elemento, "MEPModel"):
        for connector in elemento.MEPModel.ConnectorManager.Connectors:
            if connector.IsConnected:
                for ref in connector.AllRefs:
                    owner = ref.Owner
                    if owner.Id != elemento.Id:  # Evitar loop infinito
                        pipe_final = encontrar_pipe(owner)
                        if pipe_final:
                            return pipe_final
    return None


doc = __revit__.ActiveUIDocument.Document

piping_system = rvt.get_element_byclass(doc, cls.PIPING_SYSTEM, element_type=False)

elements = rvt.get_elements_bycategory(doc, cat.PIPE_FITTINGS)

fitting_redes =[]
fittings_no = []  # Lista final de fittings que são nó

for ele in elements:
    nome_sistema = ele.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
    if nome_sistema.startswith(("AF", "AQ")):
        fitting_redes.append(ele)

conn_pipes = []

# Iterar fittings filtrados
for fitting in fitting_redes:
    conn_pipes = []

    for connector in fitting.MEPModel.ConnectorManager.Connectors:
        if connector.IsConnected:
            for ref in connector.AllRefs:
                pipe = encontrar_pipe(ref.Owner)
                if pipe:
                    conn_pipes.append(pipe)

    # Aplicar lógica do troço
    sufixos = []
    prefixos = []

    for pipe in conn_pipes:
        troco = pipe.LookupParameter("Troço").AsString()
        if '-' in troco:
            prefixo, sufixo = troco.strip("[]").split('-')
            prefixos.append(prefixo)
            sufixos.append(sufixo)

    sufixos_unicos = set(sufixos)

    if len(sufixos_unicos) > 1 and any(s in prefixos for s in sufixos_unicos):
        fittings_no.append(fitting.Id.Value)  # Guardamos o próprio fitting

print(fittings_no)

"""
refs = []

for x in fitting_redes:
    connset = x.MEPModel.ConnectorManager.Connectors
    conn_pipes = []
    for c in connset:
        if c.IsConnected:
            for lc in c.AllRefs:
                conn_pipes.append(lc.Owner.Name)
            refs.append(conn_pipes)

print(refs)

    sufixos = []
    prefixos = []

    for pipe in conn_pipes:
        troco = pipe.LookupParameter("Troço").AsString()
        if '-' in troco:
            prefixo, sufixo = troco.strip("[]").split('-')
            prefixos.append(prefixo)
            sufixos.append(sufixo)

        sufixos_unicos = set(sufixos)

        if len(sufixos_unicos) > 1 and any(s in prefixos for s in sufixos_unicos):
            fittings_no.append(x)  # Guardamos o próprio fitting

print(fittings_no)

"""
"""
e = elements[0]

parameters = e.GetOrderedParameters()
t = []

# Criar dicionário para guardar elementos por rede
redes = {}

for ele in elements:
    nome_sistema = ele.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
    if nome_sistema.startswith(("AF", "AQ")):
        if nome_sistema not in redes:
            redes[nome_sistema] = []
        redes[nome_sistema].append(ele)


t = Transaction(doc, "Nos")
t.Start()

t.Commit()
"""