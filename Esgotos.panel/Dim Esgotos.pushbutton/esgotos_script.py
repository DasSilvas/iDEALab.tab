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

import os.path
import sys
from System.Collections.Generic import List

# get the absolute path to the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# add the grandparent directory to the system path
sys.path.insert(0, grandparent_dir)

from classes import Element, Funk, Pipes, PlumbingFixture, PipeFitting
from classes import RvtApiCategory as cat
from classes import RvtApi as rvt
from classes import RvtClasses as cls
from classes import RvtParameterName as parameter
from pyrevit import revit
from pyrevit import forms, script
import rpae

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

def obter_diametro(conn_pipes):
    """
    Determina o diâmetro de referência a partir dos pipes ligados.
    Neste caso, devolve o maior diâmetro entre eles.
    """
    diametros = []

    for pipe in conn_pipes:
        # Só considerar se for Tubo de Queda (TQ)
        #if pipe.LookupParameter("Tubo de Queda").AsInteger() == 1:
        diam = pipe.LookupParameter("Diameter").AsDouble()
        diametros.append(diam/2)

    if not diametros:
        return None  # nenhum diâmetro encontrado

    return max(diametros)

tee = "M_Tee - Generic"
elbow = "M_Elbow - Generic"
caixas_visita = "ED&EP FVPS-Camara_Inspeccao"

doc = __revit__.ActiveUIDocument.Document

pipe_fittings = rvt.get_elements_bycategory(doc, cat.PIPE_FITTINGS)
plumbing_fixtures = rvt.get_elements_bycategory(doc, cat.PLUMBING_FIXTURES)
pipe_elements = rvt.get_elements_byparameter(doc, cls.PIPES, parameter.PIPE_SYSTEM_TYPE, "Sanitary")


pipes = [Pipes(doc, pipe) for pipe in pipe_elements]
p_fixtures = [PlumbingFixture(doc, p_f) for p_f in plumbing_fixtures]
p_fittings = [PipeFitting(doc, p_fitting) for p_fitting in pipe_fittings]

fittings_sanitary = PipeFitting.filter_by_system(p_fittings, "Sanitary")
fixtures_sanitary = PlumbingFixture.filter_by_system(p_fixtures, "Sanitary")

caixas = [f for f in fixtures_sanitary if f.type.FamilyName == caixas_visita]

maiores_tq = {}
maiores_rni = {}
maiores_coletor = {}

tg = TransactionGroup(doc, "Dimensionamento Esgotos Domesticos")
tg.Start()

t = Transaction(doc, "TQ e RNI")
t.Start()

for p in pipes:
    if p.tubo_queda.AsInteger() == 1:
        caudal = rpae.q_cal(p.caudal_acumulado)
        diametro_cal = rpae.d_tq(caudal, taxa_ocupacao=0.17)
        diametro_tq = rpae.d_pvc(diametro_cal, "tq")
        maiores_tq[caudal] = caudal
        troco = p.troco
        if p.troco not in maiores_tq or diametro_tq > maiores_tq[troco]:
            maiores_tq[troco] = diametro_tq

for p in pipes:
    if p.rni == 1:
        caudal_rni = rpae.q_cal(p.caudal_acumulado)
        diametro_cal_rni = rpae.d_rni(caudal_rni, rugosidade=100)
        diametro_rni = rpae.d_pvc(diametro_cal_rni)
        tau_rni, v_rni, h_over_D_rni = rpae.calc_h_over_D(caudal_rni, float(diametro_rni)/1000, p.slope)
        troco = p.troco

        if p.troco not in maiores_rni or diametro_rni > maiores_rni[troco]:
            maiores_rni[troco] = diametro_rni
        
        p.set_dcal(diametro_cal_rni)
        p.set_qcal(caudal_rni)
        p.set_tau(tau_rni)
        p.set_velocity(v_rni)
        p.set_h_over_d(h_over_D_rni)
                       
for p in pipes:
    if p.tubo_queda.AsInteger() == 1:
        p.set_diameter(Funk.internal_units(maiores_tq[p.troco]))

for p in pipes:
    if p.rni == 1:
        p.set_diameter(Funk.internal_units(maiores_rni[p.troco]))

# Iterar fittings filtrados
for fitting in fittings_sanitary:
    conn_pipes = []

    if fitting.type.FamilyName == tee or fitting.type.FamilyName == elbow:

        for connector in fitting.elemento.MEPModel.ConnectorManager.Connectors:
            if connector.IsConnected:
                for ref in connector.AllRefs:
                    pipe = encontrar_pipe(ref.Owner)
                    if pipe:
                        conn_pipes.append(pipe)
        
        diametro_ref = obter_diametro(conn_pipes)
        fitting.elemento.LookupParameter("Nominal Radius").Set((diametro_ref))

#Intersecção de pipes com as caixas de visita
t.Commit()

#all_pipes porque esta função apanha mesmo as tubagens que não pertencem ao sistema sanitary
all_pipes_inter, ca, _ = Funk.get_element_cruza(caixas, doc, cat.PIPES)

#estou a retirar os pipes que interceptam as caixas de visita e que são do sistema pluvial
pipes_inter = [
    [pip for pip in pipess if pip.LookupParameter("System Type").AsValueString() != "Pluvial"]
    for pipess in all_pipes_inter
]

max_iteracoes = len(ca)
iteracao = 0

while iteracao < max_iteracoes:
    iteracao += 1
    mudou = False  # flag para verificar se houve atualização
    total_caudal = []
    t = Transaction(doc, "Caudal Acumulado Caixas")
    t.Start()

    for i, pipes_i in enumerate(pipes_inter):
        caudal_acumulado_caixa = []
        
        # ids dos pipes ligados à caixa i
        ids_pipes_ligados = set()
        for conn in ca[i].elemento.MEPModel.ConnectorManager.Connectors:
            if conn.IsConnected:
                for ref in conn.AllRefs:
                    if ref.Owner.Category.Name == "Pipes":
                        ids_pipes_ligados.add(ref.Owner.Id)
        
        for pipee in pipes_i:
            if pipee.Id in ids_pipes_ligados:
                continue  # ignora pipe ligado à caixa
            valor = pipee.get_Parameter(parameter.FIXTURE_UNITS).AsDouble()
            caudal_acumulado_caixa.append(valor)
    
        total_caudal.append(sum(caudal_acumulado_caixa))


    for c, caudal in zip(ca, total_caudal):

        c.elemento.LookupParameter("Caudal acumulado").Set(caudal)
        mudou = True

    t.Commit()

t = Transaction(doc, "Colectores")
t.Start()

#Neste calculo do caudal acumulado foi preciso atualizar o valor das fixtures units

for caixa in caixas:

    for conn in caixa.elemento.MEPModel.ConnectorManager.Connectors:
        if conn.IsConnected:
            for ref in conn.AllRefs:
                if ref.Owner.Category.Name == "Pipes":
                    p_slope = ref.Owner.get_Parameter(BuiltInParameter.RBS_PIPE_SLOPE).AsDouble()

    caudal_caixa = rpae.q_cal(caixa.elemento.LookupParameter("Caudal acumulado").AsDouble())
    diametro_cal_caixa = rpae.d_rni(caudal_caixa, inclinacao=p_slope, rugosidade=100)
    diametro_caixa = rpae.d_pvc(diametro_cal_caixa, item="colector")
    caixa.elemento.LookupParameter("Diâmetro").Set(Funk.internal_units(diametro_caixa))     

for p in pipes:
    if p.colector == 1:

        caudal_colector = rpae.q_cal(p.elemento.get_Parameter(parameter.FIXTURE_UNITS).AsDouble())
        diametro_cal_colector = rpae.d_rni(caudal_colector, inclinacao=p.slope, rugosidade=100)
        diametro_colector = rpae.d_pvc(diametro_cal_colector, item="colector")
        tau, v, h_over_D = rpae.calc_h_over_D(caudal_colector, float(diametro_colector)/1000, p.slope)
        p.set_diameter(Funk.internal_units(diametro_colector))
        p.set_dcal(diametro_cal_colector)
        p.set_qcal(caudal_colector)
        p.set_tau(tau)
        p.set_velocity(v)
        p.set_h_over_d(h_over_D)
        print(diametro_colector)

t.Commit()

tg.Assimilate()

