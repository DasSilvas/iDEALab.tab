# Load the Python Standard and DesignScript Libraries
# -*- coding: utf-8 -*-

__title__ = "Pilares"
__doc__ = "Modelacao das armaduras a partir de codigo em Type Comments do elemento"
__author__ = "Joao Ferreira, OE nº 86233"
from datetime import datetime

start_time = datetime.now()

import clr
clr.AddReference('ProtoGeometry')
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
import math

from classes import Element, Pilar, Sapata, Viga, Funk
    
def ciclo(x):
    return range(len(x))
    
def rebar_type(list , diameters, index):

    #Esta funcao vais buscar o elemento varao segundo a lista diameters

    output = []
    diametros = []
    rebar_type = [rebar for rebar in list if rebar.FamilyName == "Rebar Bar"]
    rebar_typename = [rebar.LookupParameter("Type Name").AsString() for rebar in rebar_type]

    for i in range(len(diameters)):
        for j in range(len(rebar_typename)):
            if rebar_typename[j] == diameters[i]:
                output.append(rebar_type[j])
                diametros.append(rebar_type[j].LookupParameter("Bar Diameter").AsDouble())
                
    if index == 0:
        return output
    elif index == 1:        
        return diametros
	
def rebar_hook(hooks, hook_name):
    for hook in hooks:
        if hook.LookupParameter("Type Name").AsString() == hook_name:
            k = hook
    return k

def rebar_estribos(elementos, vector, estilo, hooks, curvas):
    return Rebar.CreateFromCurves(doc, RebarStyle.StirrupTie, estilo, hooks, hooks, elementos, vector, curvas, RebarHookOrientation.Right, RebarHookOrientation.Right, True, True)

def rebar_bars(elementos, vector, estilo, curvas, hk1, hk2):
    return Rebar.CreateFromCurves(doc, RebarStyle.Standard, estilo, hk1, hk2, elementos, vector, curvas, RebarHookOrientation.Right, RebarHookOrientation.Left, True, True)

def get_element_cruza(elementos, doc, alvo, bbox="Min"):

    elemento_pares = []
    elemento_alvo = []
    elemento_impar = []

    for elemento in elementos:

        bbox_min = elemento.bbox.Min
        bbox_max = elemento.bbox.Max
        bbox_mid = XYZ(bbox_min.X, bbox_min.Y, bbox_min.Z + (bbox_max.Z - bbox_min.Z)/2 )

        if bbox == "Mid":

            outline = Outline(bbox_mid, bbox_max)

        else:

            outline = Outline(bbox_min, bbox_max)
            
        filter = BoundingBoxIntersectsFilter(outline)
        elemento_cruza = FilteredElementCollector(doc).OfCategory(alvo).WherePasses(filter).ToElements()

        if elemento_cruza:

            if alvo == FUNDACAO: 

                elemento_pares.append(elemento)
                elemento_alvo.append(elemento_cruza[0])

            else:

                elemento_pares.append(elemento)
                elemento_alvo.append(elemento_cruza)

        else:
            
            elemento_impar.append(elemento)

    return elemento_alvo, elemento_pares, elemento_impar

elementos = []
buffer = 2.5

#Recipientes para a excucao dos estribos de fundacao

estribo_fund = []
v_x_fund = [] # vector axial
comp_fund = [] # comprimento da distribuicao do estribo
spacing_fund = [] # espacamento do estribo
estribo_diameter_fund = [] # diametro do estribo

#Recipientes para a excucao das barras de fundacao
bar_fund = []
bar_diameter_fund = []
bar_number_fund = []
array_fund = []
d_estribos_fund = []
elementos_bar_fund = []
v_y_fund = []

sidebar_fund = []
sidebar_diameter_fund = []
sidebar_number_fund = []
sidearray_fund = []
elementos_sidebar_fund = []
v_z_fund = []

elementos_fund = []
v_y_fund = []
bar_diameter_fund = []
bar_number_fund = []
ganchos_estribo_fund = []
ganchos_bars_fund = []
rodar_fund = []
rodar_side_fund = []

vigas_fund_h = []

PILAR = BuiltInCategory.OST_StructuralColumns
FUNDACAO = BuiltInCategory.OST_StructuralFoundation
VIGA = BuiltInCategory.OST_StructuralFraming
REBAR = BuiltInCategory.OST_Rebar
HOOK_NAME_ESTRIBO = "Stirrup/Tie Seismic - 135 deg."
HOOK_NAME_FUND = "50Ø"
HOOK_ROTATION = "Hook Rotation At Start"

# Buscar os elementos necessarios atraves dos filtros

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(PILAR)
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

collector_rebar = FilteredElementCollector(doc).OfCategory(REBAR).WhereElementIsElementType()
rebars = collector_rebar.ToElements()

collector_hooks = FilteredElementCollector(doc).OfClass(RebarHookType).WhereElementIsElementType()
hooks = collector_hooks.ToElements()

# Elementos a armar

pilar = [Pilar(doc, element) for element in elements if element.LookupParameter("Comments").AsString() == "Armar"]

#Separa dos pilares de fundacao dos restantes, output das sapatas (sapatas), pilares que fazem par(pilares_fund) e os restentes pilares (pilares)

sapatas, pilares_fund, pilares = get_element_cruza(pilar, doc, FUNDACAO)

sapatas = [Sapata(doc, sapata) for sapata in sapatas]

vigas_fund, _, _ = get_element_cruza(pilares_fund, doc, VIGA, "Mid")

print(len(vigas))

for beams in vigas_fund:
    alturas = []
    for beam in beams:
        alturas.append(Viga(doc, beam).altura)
    vigas_fund_h.append(max(alturas))

print(alturas)


gancho_estribo = rebar_hook(hooks, HOOK_NAME_ESTRIBO)
gancho_fund = rebar_hook(hooks, HOOK_NAME_FUND)

for i in ciclo(pilares_fund):

    d_estribos_fund.append(pilares_fund[i].diametro_estribo)

    if pilares_fund[i].bol == "N":
        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(0, sapatas[i].altura, 0.0393701, 2*pilares_fund[i].nr_b, pilares_fund[i].b_varao, 2*pilares_fund[i].nr_h, pilares_fund[i].b_varao)
        estribo_fund.append(pilares_fund[i].estribo)
        elementos.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        comp_fund.append(pilares_fund[i].cmp)
        spacing_fund.append(pilares_fund[i].estribo_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].diametro_estribo)
       
    elif pilares_fund[i].bol == "Y" and pilares_fund[i].cmp <= buffer*pilares_fund[i].cc:
    
        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(0, sapatas[i].altura, 0.0393701, 2*pilares_fund[i].nr_b, pilares_fund[i].b_varao, 2*pilares_fund[i].nr_h, pilares_fund[i].b_varao)
        estribo_fund.append(pilares_fund[i].estribo)
        elementos.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        comp_fund.append(pilares_fund[i].cmp)
        spacing_fund.append(pilares_fund[i].est_ext_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].est_ext_diametro)
        
    else:

        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(0, sapatas[i].altura, 0.0393701, 2*pilares_fund[i].nr_b, pilares_fund[i].b_varao, 2*pilares_fund[i].nr_h, pilares_fund[i].b_varao)
        comp_fund.append(pilares_fund[i].cc_fund(sapatas[i].altura, 0.0393701, 2*pilares_fund[i].nr_b, pilares_fund[i].b_varao, 2*pilares_fund[i].nr_h, pilares_fund[i].b_varao))
        estribo_fund.append(pilares_fund[i].estribo)
        elementos.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        spacing_fund.append(pilares_fund[i].est_ext_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].est_ext_diametro)
        
        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(1)
        estribo_fund.append(pilares_fund[i].estribo)
        elementos.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        comp_fund.append(pilares_fund[i].cnc)
        spacing_fund.append(pilares_fund[i].estribo_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].diametro_estribo)
        
        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(2)
        estribo_fund.append(pilares_fund[i].estribo)
        elementos.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        comp_fund.append(pilares_fund[i].cc)
        spacing_fund.append(pilares_fund[i].est_ext_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].est_ext_diametro)

rebar_stir_fund = rebar_type(rebars , estribo_diameter_fund, 0)
rebar_bar_diameter_fund = rebar_type(rebars, d_estribos_fund, 1)

for i in ciclo(pilares_fund):

    ganchos_bars_fund.append(gancho_fund)
    pilares_fund[i].barras_fund(rebar_bar_diameter_fund[i], sapatas[i].altura, 0.328084, 0.0393701, pilares_fund[i].b_varao)
    bar_fund.append(pilares_fund[i].barras_f1)  
    elementos_bar_fund.append(pilares_fund[i].elemento)
    v_y_fund.append(pilares_fund[i].vectorX)
    bar_diameter_fund.append(pilares_fund[i].b_diametro)
    bar_number_fund.append(pilares_fund[i].nr_b)
    array_fund.append(pilares_fund[i].b_array_length(rebar_bar_diameter_fund[i]))
    rodar_fund.append(None)

    bar_fund.append(pilares_fund[i].barras_f2)
    elementos_bar_fund.append(pilares_fund[i].elemento)
    v_y_fund.append(pilares_fund[i].vectorX)
    bar_diameter_fund.append(pilares_fund[i].b_diametro)
    bar_number_fund.append(pilares_fund[i].nr_b)
    array_fund.append(pilares_fund[i].b_array_length(rebar_bar_diameter_fund[i]))
    rodar_fund.append(True)

    if pilares_fund[i].nr_h > 2:
        
        ganchos_bars_fund.append(gancho_fund)
        pilares_fund[i].barras_fund(rebar_bar_diameter_fund[i], sapatas[i].altura, 0.328084, 0.0393701, pilares_fund[i].b_varao)
        sidebar_fund.append(pilares_fund[i].barras_f3)  
        elementos_sidebar_fund.append(pilares_fund[i].elemento)
        v_z_fund.append(pilares_fund[i].vectorY)
        sidebar_diameter_fund.append(pilares_fund[i].b_diametro)
        sidebar_number_fund.append(pilares_fund[i].nr_h)
        sidearray_fund.append(pilares_fund[i].h_array_length(rebar_bar_diameter_fund[i]))
        rodar_side_fund.append(None)

        sidebar_fund.append(pilares_fund[i].barras_f4)
        elementos_sidebar_fund.append(pilares_fund[i].elemento)
        v_z_fund.append(pilares_fund[i].vectorY)
        sidebar_diameter_fund.append(pilares_fund[i].b_diametro)
        sidebar_number_fund.append(pilares_fund[i].nr_h)
        sidearray_fund.append(pilares_fund[i].h_array_length(rebar_bar_diameter_fund[i]))
        rodar_side_fund.append(True)

rebar_bar_fund = rebar_type(rebars, bar_diameter_fund, 0)
rebar_sidebar_fund = rebar_type(rebars, sidebar_diameter_fund, 0)

t = Transaction(doc, "Armaduras")
t.Start()

for i in ciclo(elementos):
    
    estribos = rebar_estribos(elementos[i], v_x_fund[i], rebar_stir_fund[i], ganchos_estribo_fund[i], estribo_fund[i])
    estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(spacing_fund[i], comp_fund[i], True ,True ,True)

for i in ciclo(elementos_bar_fund):

    bars = rebar_bars(elementos_bar_fund[i], v_y_fund[i], rebar_bar_fund[i], bar_fund[i], ganchos_bars_fund[i], None)
    bars_number = bars.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(bar_number_fund[i], array_fund[i], True, True, True)

    if rodar_fund[i]:
        bars.LookupParameter(HOOK_ROTATION).Set(3.14159)
 
for i in ciclo(elementos_sidebar_fund):

    sidebars = rebar_bars(elementos_sidebar_fund[i], v_z_fund[i], rebar_sidebar_fund[i], sidebar_fund[i], ganchos_bars_fund[i], None)
    sidebars_number = sidebars.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(sidebar_number_fund[i], sidearray_fund[i], True, False, False)

    if rodar_side_fund[i]:
        sidebars.LookupParameter(HOOK_ROTATION).Set(3.14159)

t.Commit()

end_time = datetime.now()
execution_time = end_time - start_time

print("Runtime: {}".format(execution_time.total_seconds()))
