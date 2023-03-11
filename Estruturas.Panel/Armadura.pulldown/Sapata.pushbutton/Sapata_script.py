# Load the Python Standard and DesignScript Libraries
# -*- coding: utf-8 -*-

__title__ = "Fundacao"
__doc__ = "Modelacao das armaduras de saptas isoladas a partir de codigo em Type Comments do elemento"
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

import os.path
import sys

# get the absolute path to the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# add the grandparent directory to the system path
sys.path.insert(0, grandparent_dir)

from classes import Sapata
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

sapatas = [Sapata(doc, element) for element in elements if element.LookupParameter("Comments").AsString() == "Armar"]

# Buscar os parametros para os pilares que têm fundacao

t = Transaction(doc, "Armaduras")
t.Start()

for sapata in sapatas:

    rebar_bot_bar = rebar_type(rebars, sapata.diametro_bot_bar, 0)

    sapata.barras_bottom1()
    sapata.barras_bottom2()

    bot_bars1 = rebar_bars(sapata.elemento, cat.BAR_STIRRUP, sapata.vectorX, rebar_bot_bar, None, sapata.bot_bar1)
    bot_bars1_spacing = bot_bars1.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(sapata.bot_bar_espacamento, sapata.bot1_array_length(), True ,True ,True)

    bot_bars2 = rebar_bars(sapata.elemento, cat.BAR_STIRRUP, sapata.vectorY, rebar_bot_bar, None, sapata.bot_bar2)
    bot_bars2_spacing = bot_bars2.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(sapata.bot_bar_espacamento, sapata.bot2_array_length(), True ,True ,True)

    rebar_top_bar = rebar_type(rebars, sapata.diametro_top_bar, 0)

    sapata.barras_top1()
    sapata.barras_top2()

    top_bars1 = rebar_bars(sapata.elemento, cat.BAR_STIRRUP, sapata.vectorX, rebar_top_bar, None, sapata.top_bar1)
    top_bars1_spacing = top_bars1.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(sapata.top_bar_espacamento, sapata.top1_array_length(), True ,True ,True)

    top_bars2 = rebar_bars(sapata.elemento, cat.BAR_STIRRUP, sapata.vectorY, rebar_top_bar, None, sapata.top_bar2)
    top_bars2_spacing = top_bars2.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(sapata.top_bar_espacamento, sapata.top2_array_length(), True ,True ,True)

    sapata.barras_lateral1()
    sapata.barras_lateral2()

    side_bar1 = rebar_bars(sapata.elemento, cat.BAR_STANDART, sapata.vectorY, rebar_top_bar, None, sapata.lateral_bot1)
    side_bar2 = rebar_bars(sapata.elemento, cat.BAR_STANDART, sapata.vectorY, rebar_top_bar, None, sapata.lateral_bot2)
    side_bar3 = rebar_bars(sapata.elemento, cat.BAR_STANDART, sapata.vectorY, rebar_top_bar, None, sapata.lateral_bot3)
    side_bar4 = rebar_bars(sapata.elemento, cat.BAR_STANDART, sapata.vectorY, rebar_top_bar, None, sapata.lateral_bot4)

    side_bar5 = rebar_bars(sapata.elemento, cat.BAR_STANDART, sapata.vectorX, rebar_top_bar, None, sapata.lateral_bot5)
    side_bar6 = rebar_bars(sapata.elemento, cat.BAR_STANDART, sapata.vectorX, rebar_top_bar, None, sapata.lateral_bot6)
    side_bar7 = rebar_bars(sapata.elemento, cat.BAR_STANDART, sapata.vectorX, rebar_top_bar, None, sapata.lateral_bot7)
    side_bar8 = rebar_bars(sapata.elemento, cat.BAR_STANDART, sapata.vectorX, rebar_top_bar, None, sapata.lateral_bot8)

t.Commit()

end_time = datetime.now()
execution_time = end_time - start_time

print("Runtime: {}".format(execution_time.total_seconds()))
