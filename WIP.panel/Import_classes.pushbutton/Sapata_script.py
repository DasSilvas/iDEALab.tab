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

from classes import Element, Pilar, Sapata, Viga, Funk, Rebares
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

#rebar_stir_fund = rebar_type(rebars , sapata[i].est_ext_diametro, 0)

def rebar_hook(hooks, hook_name):
    for hook in hooks:
        if hook.LookupParameter("Type Name").AsString() == hook_name:
            k = hook
    return k


def rebar_bars(elementos, tipo, vector, estilo, hooks, curvas):
    return Rebar.CreateFromCurves(doc, tipo, estilo, hooks, hooks, elementos, vector, curvas, RebarHookOrientation.Right, RebarHookOrientation.Right, True, True)

buffer = 2.5

# Buscar os elementos necessarios atraves dos filtros

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(cat.FUNDACAO)
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

collector_rebar = FilteredElementCollector(doc).OfCategory(cat.REBAR).WhereElementIsElementType()
rebars = collector_rebar.ToElements()

collector_hooks = FilteredElementCollector(doc).OfClass(RebarHookType).WhereElementIsElementType()
hooks = collector_hooks.ToElements()

# Elementos a armar
bar_bot1 = []
bar_bot2 = []
bar_top1 = []
bar_top2 = []
elementos = []
v_x = []
v_y = []
comp = []
spacing = []
estribo_diameter = []

sapata = [Sapata(doc, element) for element in elements if element.LookupParameter("Comments").AsString() == "Armar"]

for i in ciclo(sapata):
    
    rebar_bar_diameter = rebar_type(rebars, sapata[i].diametro_top_bar, 1)
    sapata[i].barras_bottom1()
    sapata[i].barras_bottom2()
    bar_bot1.append(sapata[i].bot_bar1)
    bar_bot2.append(sapata[i].bot_bar2)
    sapata[i].barras_top1()
    sapata[i].barras_top2()
    bar_top1.append(sapata[i].top_bar1)
    bar_top2.append(sapata[i].top_bar2)
    elementos.append(sapata[i].elemento)
    v_x.append(sapata[i].vectorX)
    v_y.append(sapata[i].vectorY)
    sapata[i].barras_lateral1()
    sapata[i].barras_lateral2()
# Buscar os parametros para os pilares que têm fundacao

t = Transaction(doc, "Armaduras")
t.Start()

for i in ciclo(sapata):

    rebar_bar_diameter_fund = rebar_type(rebars, sapata[i].diametro_bot_bar, 1)
    rebar_bot_bar = rebar_type(rebars, sapata[i].diametro_bot_bar, 0)

    bot_bars1 = rebar_bars(elementos[i], cat.BAR_STIRRUP, v_x[i], rebar_bot_bar, None, bar_bot1[i])
    bot_bars1_spacing = bot_bars1.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(sapata[i].bot_bar_espacamento, sapata[i].bot1_array_length(), True ,True ,True)

    bot_bars2 = rebar_bars(elementos[i], cat.BAR_STIRRUP, v_y[i], rebar_bot_bar, None, bar_bot2[i])
    bot_bars2_spacing = bot_bars2.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(sapata[i].bot_bar_espacamento, sapata[i].bot2_array_length(), True ,True ,True)

    rebar_top_bar = rebar_type(rebars, sapata[i].diametro_top_bar, 0)

    top_bars1 = rebar_bars(elementos[i], cat.BAR_STIRRUP, v_x[i], rebar_top_bar, None, bar_top1[i])
    top_bars1_spacing = top_bars1.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(sapata[i].top_bar_espacamento, sapata[i].top1_array_length(), True ,True ,True)

    top_bars2 = rebar_bars(elementos[i], cat.BAR_STIRRUP, v_y[i], rebar_top_bar, None, bar_top2[i])
    top_bars2_spacing = top_bars2.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(sapata[i].top_bar_espacamento, sapata[i].top2_array_length(), True ,True ,True)

    side_bar1 = rebar_bars(elementos[i], cat.BAR_STANDART, v_y[i], rebar_top_bar, None, sapata[i].lateral_bot1)
    side_bar2 = rebar_bars(elementos[i], cat.BAR_STANDART, v_y[i], rebar_top_bar, None, sapata[i].lateral_bot2)
    side_bar3 = rebar_bars(elementos[i], cat.BAR_STANDART, v_y[i], rebar_top_bar, None, sapata[i].lateral_bot3)
    side_bar4 = rebar_bars(elementos[i], cat.BAR_STANDART, v_y[i], rebar_top_bar, None, sapata[i].lateral_bot4)

    side_bar5 = rebar_bars(elementos[i], cat.BAR_STANDART, v_x[i], rebar_top_bar, None, sapata[i].lateral_bot5)
    side_bar6 = rebar_bars(elementos[i], cat.BAR_STANDART, v_x[i], rebar_top_bar, None, sapata[i].lateral_bot6)
    side_bar7 = rebar_bars(elementos[i], cat.BAR_STANDART, v_x[i], rebar_top_bar, None, sapata[i].lateral_bot7)
    side_bar8 = rebar_bars(elementos[i], cat.BAR_STANDART, v_x[i], rebar_top_bar, None, sapata[i].lateral_bot8)

t.Commit()

end_time = datetime.now()
execution_time = end_time - start_time

print("Runtime: {}".format(execution_time.total_seconds()))
