# Load the Python Standard and DesignScript Libraries
# -*- coding: utf-8 -*-

__title__ = "Vigas"
__doc__ = "Modelacao das armaduras a partir de codigo em Type Comments do elemento"
__author__ = "Joao Ferreira, OE nº 86233"

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

from classes import Viga
    
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
    
def rebar_hook(hooks):
    for hook in hooks:
        if hook.LookupParameter("Type Name").AsString() == "Stirrup/Tie Seismic - 135 deg.":
            k = hook
    return k
            
def rebar_estribos(elementos, vector, estilo, hooks, curvas):
    return Rebar.CreateFromCurves(doc, RebarStyle.StirrupTie, estilo, hooks, hooks, elementos, vector, curvas, RebarHookOrientation.Right, RebarHookOrientation.Right, True, True)

def rebar_bars(elementos, vector, estilo, curvas):
    return Rebar.CreateFromCurves(doc, RebarStyle.Standard, estilo, None, None, elementos, vector, curvas, RebarHookOrientation.Right, RebarHookOrientation.Left, True, True)

elementos = []
buffer = 2.1

#Recipientes para a excucao dos estribos

estribo = []
v_x = [] # vector axial
comp = [] # comprimento da distribuicao do estribo
spacing = [] # espacamento do estribo
estribo_diameter = [] # diametro do estribo

#Recipientes para a excucao das barras
bar = []
bar_diameter = []
bar_number = []
array = []
d_estribos = []
elementos_bar = []
v_y = []

sidebar = []
sidebar_diameter = []
sidebar_number = []
sidearray = []
elementos_sidebar = []
v_z = []

# Buscar os elementos necessarios atraves dos filtros

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(BuiltInCategory.OST_StructuralFraming)
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

collector_rebar = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rebar).WhereElementIsElementType()
rebars = collector_rebar.ToElements()

collector_hooks = FilteredElementCollector(doc).OfClass(RebarHookType).WhereElementIsElementType()
hooks = collector_hooks.ToElements()

# Elementos a armar

ele_rebar = [Viga(doc, element) for element in elements if element.LookupParameter("Comments").AsString() == "Armar"]

for i in ciclo(ele_rebar):

    d_estribos.append(ele_rebar[i].diametro_estribo)

    if ele_rebar[i].bol == "N":
    
        ele_rebar[i].estribos(0)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(ele_rebar[i].cut_comprimento)
        spacing.append(ele_rebar[i].estribo_espacamento)
        estribo_diameter.append(ele_rebar[i].diametro_estribo)
        
    elif ele_rebar[i].bol == "Y" and ele_rebar[i].cut_comprimento <= buffer*ele_rebar[i].cc:
    
        ele_rebar[i].estribos(0)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(ele_rebar[i].cut_comprimento)
        spacing.append(ele_rebar[i].est_ext_espacamento)
        estribo_diameter.append(ele_rebar[i].est_ext_diametro)
        
    else:

        ele_rebar[i].estribos(0)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(ele_rebar[i].cc)
        spacing.append(ele_rebar[i].est_ext_espacamento)
        estribo_diameter.append(ele_rebar[i].est_ext_diametro)
        
        ele_rebar[i].estribos(1)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(ele_rebar[i].cnc)
        spacing.append(ele_rebar[i].estribo_espacamento)
        estribo_diameter.append(ele_rebar[i].diametro_estribo)
        
        ele_rebar[i].estribos(2)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(ele_rebar[i].cc)
        spacing.append(ele_rebar[i].est_ext_espacamento)
        estribo_diameter.append(ele_rebar[i].est_ext_diametro)

rebar_stir = rebar_type(rebars , estribo_diameter, 0)
rebar_bar_diameter = rebar_type(rebars, d_estribos, 1)

for i in ciclo(ele_rebar):

    ele_rebar[i].barras(rebar_bar_diameter[i])
    bar.append(ele_rebar[i].barras_bot)  
    elementos_bar.append(ele_rebar[i].elemento)
    v_y.append(ele_rebar[i].vectorY)
    bar_diameter.append(ele_rebar[i].bi_diametro)
    bar_number.append(ele_rebar[i].nr_bi)
    array.append(ele_rebar[i].array_length(rebar_bar_diameter[i]))
    bar.append(ele_rebar[i].barras_top)
    elementos_bar.append(ele_rebar[i].elemento)
    v_y.append(ele_rebar[i].vectorY)
    bar_diameter.append(ele_rebar[i].bs_diametro)
    bar_number.append(ele_rebar[i].nr_bs)
    array.append(ele_rebar[i].array_length(rebar_bar_diameter[i]))

    if ele_rebar[i].nr_bl > 2:

        ele_rebar[i].barras(rebar_bar_diameter[i])
        sidebar.append(ele_rebar[i].barras_side)  
        elementos_sidebar.append(ele_rebar[i].elemento)
        v_z.append(ele_rebar[i].vectorZ)
        sidebar_diameter.append(ele_rebar[i].bl_diametro)
        sidebar_number.append(ele_rebar[i].nr_bl)
        sidearray.append(ele_rebar[i].sidearray_length(rebar_bar_diameter[i]))
        sidebar.append(ele_rebar[i].barras_bot)
        elementos_sidebar.append(ele_rebar[i].elemento)
        v_z.append(ele_rebar[i].vectorZ)
        sidebar_diameter.append(ele_rebar[i].bl_diametro)
        sidebar_number.append(ele_rebar[i].nr_bl)
        sidearray.append(ele_rebar[i].sidearray_length(rebar_bar_diameter[i]))

rebar_bar = rebar_type(rebars, bar_diameter, 0)
rebar_sidebar = rebar_type(rebars, sidebar_diameter, 0)

t = Transaction(doc, "Armaduras")
t.Start()

for i in ciclo(elementos):
    
    estribos = rebar_estribos(elementos[i], v_x[i], rebar_stir[i], rebar_hook(hooks), estribo[i])
    estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(spacing[i], comp[i], True ,True ,True)

for i in ciclo(elementos_bar):

    bars = rebar_bars(elementos_bar[i], v_y[i], rebar_bar[i], bar[i])
    bars_number = bars.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(bar_number[i], array[i], True, True, True)
    
for i in ciclo(elementos_sidebar):

    sidebars = rebar_bars(elementos_sidebar[i], v_z[i], rebar_sidebar[i], sidebar[i])
    sidebars_number = sidebars.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(sidebar_number[i], sidearray[i], True, False, False)
    
t.Commit()