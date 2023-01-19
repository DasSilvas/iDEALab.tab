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
from classes import RvtApiCategory as cat
from classes import RvtParameterName as para

def ciclo(x):
    return range(len(x))
    
def rebar_type(list , diameters, index):

    #Esta funcao vais buscar o elemento varao segundo a lista diameters

    rebar_type = [rebar for rebar in list if rebar.FamilyName == "Rebar Bar"]
    rebar_typename = [rebar.LookupParameter("Type Name").AsString() for rebar in rebar_type]

    for j in range(len(rebar_typename)):
        if rebar_typename[j] == diameters:
            output = rebar_type[j]
            diametros = rebar_type[j].LookupParameter("Bar Diameter").AsDouble()
                
    if index == 0:
        return output
    elif index == 1:        
        return diametros

#rebar_stir_fund = rebar_type(rebars , pd[i].est_ext_diametro, 0)

def rebar_hook(hooks, hook_name):
    for hook in hooks:
        if hook.LookupParameter("Type Name").AsString() == hook_name:
            k = hook
    return k

def rebar_estribos(elementos, vector, estilo, hooks, curvas):
    return Rebar.CreateFromCurves(doc, RebarStyle.StirrupTie, estilo, hooks, hooks, elementos, vector, curvas, RebarHookOrientation.Right, RebarHookOrientation.Right, True, True)

def rebar_bars(elementos, vector, estilo, curvas, hk1, hk2):
    return Rebar.CreateFromCurves(doc, RebarStyle.Standard, estilo, hk1, hk2, elementos, vector, curvas, RebarHookOrientation.Right, RebarHookOrientation.Left, True, True)

buffer = 2.5

vigas_fund_h = []
vigas_h = []

# Buscar os elementos necessarios atraves dos filtros

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(cat.PILAR)
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

collector_rebar = FilteredElementCollector(doc).OfCategory(cat.REBAR).WhereElementIsElementType()
rebars = collector_rebar.ToElements()

collector_hooks = FilteredElementCollector(doc).OfClass(RebarHookType).WhereElementIsElementType()
hooks = collector_hooks.ToElements()

# Elementos a armar

pilar = [Pilar(doc, element) for element in elements if element.LookupParameter("Comments").AsString() == "Armar"]

#Separa dos pilares de fundacao dos restantes, output das sapatas (sapatas), pilares que fazem par(pilares_fund) e os restentes pilares (pilares)

sapatas, pd, p = Funk.get_element_cruza(pilar, doc, cat.FUNDACAO)

sapatas = [Sapata(doc, sapata) for sapata in sapatas]

vigas_fund, _, _ = Funk.get_element_cruza(pd, doc, cat.VIGA, "Mid")

vigas, _, _ = Funk.get_element_cruza(p, doc, cat.VIGA, "Mid")

for beams in vigas_fund:
    alturas = []
    for beam in beams:
        alturas.append(Viga(doc, beam).altura)
    vigas_fund_h.append(max(alturas))

for beams in vigas:
    alturas = []
    for beam in beams:
        alturas.append(Viga(doc, beam).altura)
    vigas_h.append(max(alturas))

# Buscar os parametros para os pilares que têm fundacao

gancho_estribo = rebar_hook(hooks, para.HOOK_NAME_ESTRIBO)
gancho_fund = rebar_hook(hooks, para.HOOK_NAME_FUND)

t = Transaction(doc, "Armaduras")
t.Start()

for i in ciclo(pd):

    rebar_bar_diameter_fund = rebar_type(rebars, pd[i].diametro_estribo, 1)
    rebar_bar_fund = rebar_type(rebars, pd[i].b_diametro, 0)

    pd[i].barras_fund(rebar_bar_diameter_fund, sapatas[i].altura, 0.328084, 0.0393701, pd[i].b_varao)
    bars_fund1 = rebar_bars(pd[i].elemento, pd[i].vectorX, rebar_bar_fund, pd[i].barras_f1, gancho_fund, None)
    bars_number_fund1 = bars_fund1.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(pd[i].nr_b, pd[i].b_array_length(rebar_bar_diameter_fund), True, True, True)

    bars_fund2 = rebar_bars(pd[i].elemento, pd[i].vectorX, rebar_bar_fund, pd[i].barras_f2, gancho_fund, None)
    bars_number_fund2 = bars_fund2.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(pd[i].nr_b, pd[i].b_array_length(rebar_bar_diameter_fund), True, True, True)
    bars_fund2.LookupParameter(para.HOOK_ROTATION).Set(3.14159) 

    if pd[i].nr_h > 2:

        pd[i].barras_fund(rebar_bar_diameter_fund, sapatas[i].altura, 0.328084, 0.0393701, pd[i].b_varao)
        bars_fund3 = rebar_bars(pd[i].elemento, pd[i].vectorY, rebar_bar_fund, pd[i].barras_f3, gancho_fund, None)
        bars_number_fund3 = bars_fund3.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(pd[i].nr_h, pd[i].h_array_length(rebar_bar_diameter_fund), True, False, False)

        bars_fund4 = rebar_bars(pd[i].elemento, pd[i].vectorY, rebar_bar_fund, pd[i].barras_f4, gancho_fund, None)
        bars_number_fund4 = bars_fund4.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(pd[i].nr_h, pd[i].h_array_length(rebar_bar_diameter_fund), True, False, False)
        bars_fund4.LookupParameter(para.HOOK_ROTATION).Set(3.14159)

    if pd[i].bol == "N":

        rebar_stir_fund = rebar_type(rebars , pd[i].est_ext_diametro, 0)
        pd[i].estribos(0, sapatas[i].altura, 0.0393701, 2*pd[i].nr_b, pd[i].b_varao, 2*pd[i].nr_h, pd[i].b_varao)
        estribos_fund = rebar_estribos(pd[i].elemento, pd[i].vectorZ, rebar_stir_fund, gancho_estribo, pd[i].estribo)
        estribo_esp_fund = estribos_fund.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(pd[i].estribo_espacamento, pd[i].cmp, True ,True ,True)

    elif pd[i].bol == "Y" and pd[i].cmp <= buffer*pd[i].cc + vigas_fund_h[i]:
        
        rebar_stir_fund = rebar_type(rebars , pd[i].est_ext_diametro, 0)
        pd[i].estribos(0, sapatas[i].altura, 0.0393701, 2*pd[i].nr_b, pd[i].b_varao, 2*pd[i].nr_h, pd[i].b_varao)
        estribos_fund = rebar_estribos(pd[i].elemento, pd[i].vectorZ, rebar_stir_fund, gancho_estribo, pd[i].estribo)
        estribo_esp_fund = estribos_fund.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(pd[i].estribo_espacamento, pd[i].cmp, True ,True ,True)

    else:
        rebar_stir_fund = rebar_type(rebars , pd[i].est_ext_diametro, 0)
        pd[i].estribos(0, sapatas[i].altura, 0.0393701, 2*pd[i].nr_b, pd[i].b_varao, 2*pd[i].nr_h, pd[i].b_varao)
        pd[i].cc_fund(sapatas[i].altura, 0.0393701, 2*pd[i].nr_b, pd[i].b_varao, 2*pd[i].nr_h, pd[i].b_varao)
        estribos_fund = rebar_estribos(pd[i].elemento, pd[i].vectorZ, rebar_stir_fund, gancho_estribo, pd[i].estribo)
        estribo_esp_fund = estribos_fund.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(pd[i].est_ext_espacamento, pd[i].cc_sapata, True ,True ,True)
        
        pd[i].estribos(1)
        estribos_fund = rebar_estribos(pd[i].elemento, pd[i].vectorZ, rebar_stir_fund, gancho_estribo, pd[i].estribo)
        estribo_esp_fund = estribos_fund.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(pd[i].estribo_espacamento, pd[i].cnc_viga(vigas_fund_h[i]), True ,True ,True)
        
        pd[i].estribos(2, altura_viga=vigas_fund_h[i])
        estribos_fund = rebar_estribos(pd[i].elemento, pd[i].vectorZ, rebar_stir_fund, gancho_estribo, pd[i].estribo)
        estribo_esp_fund = estribos_fund.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(pd[i].est_ext_espacamento, pd[i].cc_viga(vigas_fund_h[i]), True ,True ,True)

for i in ciclo(p):

    rebar_bar_diameter = rebar_type(rebars, p[i].diametro_estribo, 1)
    rebar_bar = rebar_type(rebars, p[i].b_diametro, 0)

    p[i].barras(rebar_bar_diameter)
    bars_bot = rebar_bars(p[i].elemento, p[i].vectorX, rebar_bar, p[i].barras_bot, None, None)
    bars_number_bot = bars_bot.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(p[i].nr_b, p[i].b_array_length(rebar_bar_diameter), True, True, True)

    bars_top = rebar_bars(p[i].elemento, p[i].vectorX, rebar_bar, p[i].barras_top, None, None)
    bars_number_top = bars_top.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(p[i].nr_b, p[i].b_array_length(rebar_bar_diameter), True, True, True)

    if p[i].nr_h > 2:

        p[i].barras_fund(rebar_bar_diameter)
        bars_side1 = rebar_bars(p[i].elemento, p[i].vectorY, rebar_bar, p[i].barras_side, None, None)
        bars_number_side1 = bars_side1.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(p[i].nr_h, p[i].h_array_length(rebar_bar_diameter), True, False, False)

        bars_side2 = rebar_bars(p[i].elemento, p[i].vectorY, rebar_bar, p[i].barras_bot, None, None)
        bars_number_side2 = bars_side2.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(p[i].nr_h, p[i].h_array_length(rebar_bar_diameter), True, False, False)

    if p[i].bol == "N":
        
        rebar_stir = rebar_type(rebars , p[i].est_ext_diametro, 0)
        p[i].estribos(0)
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].estribo_espacamento, p[i].cmp, True ,True ,True)

    elif p[i].bol == "Y" and p[i].cmp <= buffer*p[i].cc + vigas_h[i]:
        
        rebar_stir = rebar_type(rebars , p[i].est_ext_diametro, 0)
        p[i].estribos(0)
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].estribo_espacamento, p[i].cmp, True ,True ,True)

    else:

        rebar_stir = rebar_type(rebars , p[i].est_ext_diametro, 0)
        p[i].estribos(0)
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].est_ext_espacamento, p[i].cc, True ,True ,True)
        
        p[i].estribos(1)
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].estribo_espacamento, p[i].cnc_viga(vigas_h[i]), True ,True ,True)
        
        p[i].estribos(2, altura_viga=vigas_h[i])
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].est_ext_espacamento, p[i].cc_viga(vigas_h[i]), True ,True ,True)

t.Commit()

end_time = datetime.now()
execution_time = end_time - start_time

print("Runtime: {}".format(execution_time.total_seconds()))
