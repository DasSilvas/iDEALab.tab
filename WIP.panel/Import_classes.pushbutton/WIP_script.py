# Load the Python Standard and DesignScript Libraries
# -*- coding: utf-8 -*-

__title__ = "Fundações"
__doc__ = "wip_Modelacao das armaduras das fundacoes a partir de codigo em Type Comments do elemento"
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
import math

from classes import Element, Pilar, Sapata

# Buscar os elementos necessarios atraves dos filtros

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(BuiltInCategory.OST_StructuralColumns)
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

collector_sapatas = FilteredElementCollector(doc)
filtro_sapatas = ElementCategoryFilter(BuiltInCategory.OST_StructuralFoundation)
elements_sapatas = collector_sapatas.WherePasses(filtro_sapatas).WhereElementIsNotElementType().ToElements()

colunas = []

# elements = [element for element in elements if element.get_Parameter(BuiltInParameter.FLOOR_PARAM_IS_STRUCTURAL) is None]

ele_rebar = [Pilar(doc, element) for element in elements if element.LookupParameter("Comments").AsString() == "Armar"]
"""
for column in ele_rebar:

    # Get the bounding box of the column
    column_bbox = column.bbox
    
    # Get the outline of the bounding box
    outline = Outline(column_bbox.Min, column_bbox.Max)
    
    # Create a BoundingBoxIntersectsFilter with the outline
    filter = BoundingBoxIntersectsFilter(outline)
    
    # Use the filter to retrieve the foundations that intersect with the column's bounding box
    intersecting_foundations = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFoundation).WherePasses(filter).ToElements()
    
    if intersecting_foundations:
        # If any foundations intersect with the column's bounding box, print the name of the column
        sapata.append(intersecting_foundations)
        colunas.append(column)
"""
sapatas = [Sapata(doc, sap) for sap in elements_sapatas]

thick = []

for sapata in sapatas:
    thick.append(sapata.altura)

print(thick)
print(elements_sapatas)


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




buffer = 2.5

#Recipientes para a excucao dos estribos de fundacao

estribo_fund = []
v_x_fund = [] # vector axial
comp_fund = [] # comprimento da distribuicao do estribo
spacing_fund = [] # espacamento do estribo
estribo_diameter_fund = [] # diametro do estribo

#Recipientes para a excucao das barras de fundacao
elementos_est_fund = []
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

ganchos_estribo_fund = []
ganchos_bars_fund = []
rodar_fund = []
rodar_side_fund = []

vigas_fund_h = []
vigas_h = []

# Recipientes para os parametros dos restantes pilares
#Recipientes para a excucao dos estribos
elementos_est = []
estribo = []
v_x = [] # vector axial
comp = [] # comprimento da distribuicao do estribo
spacing = [] # espacamento do estribo
estribo_diameter = [] # diametro do estribo

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

ganchos_estribo = []

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

sapatas, pilares_fund, pilares = Funk.get_element_cruza(pilar, doc, cat.FUNDACAO)

sapatas = [Sapata(doc, sapata) for sapata in sapatas]

vigas_fund, _, _ = Funk.get_element_cruza(pilares_fund, doc, cat.VIGA, "Mid")

vigas, _, _ = Funk.get_element_cruza(pilares, doc, cat.VIGA, "Mid")

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

for i in ciclo(pilares_fund):

    d_estribos_fund.append(pilares_fund[i].diametro_estribo)

    if pilares_fund[i].bol == "N":
        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(0, sapatas[i].altura, 0.0393701, 2*pilares_fund[i].nr_b, pilares_fund[i].b_varao, 2*pilares_fund[i].nr_h, pilares_fund[i].b_varao)
        estribo_fund.append(pilares_fund[i].estribo)
        elementos_est_fund.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        comp_fund.append(pilares_fund[i].cmp)
        spacing_fund.append(pilares_fund[i].estribo_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].diametro_estribo)
       
    elif pilares_fund[i].bol == "Y" and pilares_fund[i].cmp <= buffer*pilares_fund[i].cc + vigas_fund_h[i]:
    
        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(0, sapatas[i].altura, 0.0393701, 2*pilares_fund[i].nr_b, pilares_fund[i].b_varao, 2*pilares_fund[i].nr_h, pilares_fund[i].b_varao)
        estribo_fund.append(pilares_fund[i].estribo)
        elementos_est_fund.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        comp_fund.append(pilares_fund[i].cmp)
        spacing_fund.append(pilares_fund[i].est_ext_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].est_ext_diametro)
        
    else:

        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(0, sapatas[i].altura, 0.0393701, 2*pilares_fund[i].nr_b, pilares_fund[i].b_varao, 2*pilares_fund[i].nr_h, pilares_fund[i].b_varao)
        comp_fund.append(pilares_fund[i].cc_fund(sapatas[i].altura, 0.0393701, 2*pilares_fund[i].nr_b, pilares_fund[i].b_varao, 2*pilares_fund[i].nr_h, pilares_fund[i].b_varao))
        estribo_fund.append(pilares_fund[i].estribo)
        elementos_est_fund.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        spacing_fund.append(pilares_fund[i].est_ext_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].est_ext_diametro)
        
        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(1)
        estribo_fund.append(pilares_fund[i].estribo)
        elementos_est_fund.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        comp_fund.append(pilares_fund[i].cnc_viga(vigas_fund_h[i]))
        spacing_fund.append(pilares_fund[i].estribo_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].diametro_estribo)
        
        ganchos_estribo_fund.append(gancho_estribo)
        pilares_fund[i].estribos(2, altura_viga=vigas_fund_h[i])
        estribo_fund.append(pilares_fund[i].estribo)
        elementos_est_fund.append(pilares_fund[i].elemento)
        v_x_fund.append(pilares_fund[i].vectorZ)
        comp_fund.append(pilares_fund[i].cc_viga(vigas_fund_h[i]))
        spacing_fund.append(pilares_fund[i].est_ext_espacamento)
        estribo_diameter_fund.append(pilares_fund[i].est_ext_diametro)

rebar_stir_fund = rebar_type(rebars , estribo_diameter_fund, 0)
 = rebar_type(rebars, d_estribos_fund, 1)

for i in ciclo(pilares_fund):

    ganchos_bars_fund.append(gancho_fund)
    pilares_fund[i].barras_fund([i], sapatas[i].altura, 0.328084, 0.0393701, pilares_fund[i].b_varao)
    bar_fund.append(pilares_fund[i].barras_f1)  
    elementos_bar_fund.append(pilares_fund[i].elemento)
    v_y_fund.append(pilares_fund[i].vectorX)
    bar_diameter_fund.append(pilares_fund[i].b_diametro)
    bar_number_fund.append(pilares_fund[i].nr_b)
    array_fund.append(pilares_fund[i].b_array_length([i]))
    rodar_fund.append(None)

    bar_fund.append(pilares_fund[i].barras_f2)
    elementos_bar_fund.append(pilares_fund[i].elemento)
    v_y_fund.append(pilares_fund[i].vectorX)
    bar_diameter_fund.append(pilares_fund[i].b_diametro)
    bar_number_fund.append(pilares_fund[i].nr_b)
    array_fund.append(pilares_fund[i].b_array_length([i]))
    rodar_fund.append(True)

    if pilares_fund[i].nr_h > 2:
        
        ganchos_bars_fund.append(gancho_fund)
        pilares_fund[i].barras_fund([i], sapatas[i].altura, 0.328084, 0.0393701, pilares_fund[i].b_varao)
        sidebar_fund.append(pilares_fund[i].barras_f3)  
        elementos_sidebar_fund.append(pilares_fund[i].elemento)
        v_z_fund.append(pilares_fund[i].vectorY)
        sidebar_diameter_fund.append(pilares_fund[i].b_diametro)
        sidebar_number_fund.append(pilares_fund[i].nr_h)
        sidearray_fund.append(pilares_fund[i].h_array_length([i]))
        rodar_side_fund.append(None)

        sidebar_fund.append(pilares_fund[i].barras_f4)
        elementos_sidebar_fund.append(pilares_fund[i].elemento)
        v_z_fund.append(pilares_fund[i].vectorY)
        sidebar_diameter_fund.append(pilares_fund[i].b_diametro)
        sidebar_number_fund.append(pilares_fund[i].nr_h)
        sidearray_fund.append(pilares_fund[i].h_array_length([i]))
        rodar_side_fund.append(True)

rebar_bar_fund = rebar_type(rebars, bar_diameter_fund, 0)
rebar_sidebar_fund = rebar_type(rebars, sidebar_diameter_fund, 0)

# Buscar os parametros para os restantes pilares

for i in ciclo(pilares):

    d_estribos.append(pilares[i].diametro_estribo)

    if pilares[i].bol == "N":
        ganchos_estribo.append(gancho_estribo)
        pilares[i].estribos(0)
        estribo.append(pilares[i].estribo)
        elementos_est.append(pilares[i].elemento)
        v_x.append(pilares[i].vectorZ)
        comp.append(pilares[i].cmp)
        spacing.append(pilares[i].estribo_espacamento)
        estribo_diameter.append(pilares[i].diametro_estribo)
       
    elif pilares[i].bol == "Y" and pilares[i].cmp <= buffer*(pilares[i].cc) + vigas_h[i]:
    
        ganchos_estribo.append(gancho_estribo)
        pilares[i].estribos(0)
        estribo.append(pilares[i].estribo)
        elementos_est.append(pilares[i].elemento)
        v_x.append(pilares[i].vectorZ)
        comp.append(pilares[i].cmp)
        spacing.append(pilares[i].est_ext_espacamento)
        estribo_diameter.append(pilares[i].est_ext_diametro)
        
    else:

        ganchos_estribo.append(gancho_estribo)
        pilares[i].estribos(0)
        comp.append(pilares[i].cc)
        estribo.append(pilares[i].estribo)
        elementos_est.append(pilares[i].elemento)
        v_x.append(pilares[i].vectorZ)
        spacing.append(pilares[i].est_ext_espacamento)
        estribo_diameter.append(pilares[i].est_ext_diametro)
        
        ganchos_estribo.append(gancho_estribo)
        pilares[i].estribos(1)
        estribo.append(pilares[i].estribo)
        elementos_est.append(pilares[i].elemento)
        v_x.append(pilares[i].vectorZ)
        comp.append(pilares[i].cnc_viga(vigas_h[i]))
        spacing.append(pilares[i].estribo_espacamento)
        estribo_diameter.append(pilares[i].diametro_estribo)
        
        ganchos_estribo.append(gancho_estribo)
        pilares[i].estribos(2, altura_viga=vigas_h[i])
        estribo.append(pilares[i].estribo)
        elementos_est.append(pilares[i].elemento)
        v_x.append(pilares[i].vectorZ)
        comp.append(pilares[i].cc_viga(vigas_h[i]))
        spacing.append(pilares[i].est_ext_espacamento)
        estribo_diameter.append(pilares[i].est_ext_diametro)

rebar_stir = rebar_type(rebars , estribo_diameter, 0)
rebar_bar_diameter = rebar_type(rebars, d_estribos, 1)

for i in ciclo(pilares):

    pilares[i].barras(rebar_bar_diameter[i])
    bar.append(pilares[i].barras_bot)  
    elementos_bar.append(pilares[i].elemento)
    v_y.append(pilares[i].vectorX)
    bar_diameter.append(pilares[i].b_diametro)
    bar_number.append(pilares[i].nr_b)
    array.append(pilares[i].b_array_length(rebar_bar_diameter[i]))

    bar.append(pilares[i].barras_top)
    elementos_bar.append(pilares[i].elemento)
    v_y.append(pilares[i].vectorX)
    bar_diameter.append(pilares[i].b_diametro)
    bar_number.append(pilares[i].nr_b)
    array.append(pilares[i].b_array_length(rebar_bar_diameter[i]))

    if pilares[i].nr_h > 2:
        
        ganchos_bars_fund.append(gancho_fund)
        pilares[i].barras(rebar_bar_diameter[i])
        sidebar.append(pilares[i].barras_side)  
        elementos_sidebar.append(pilares[i].elemento)
        v_z.append(pilares[i].vectorY)
        sidebar_diameter.append(pilares[i].b_diametro)
        sidebar_number.append(pilares[i].nr_h)
        sidearray.append(pilares[i].h_array_length(rebar_bar_diameter[i]))

        sidebar.append(pilares[i].barras_bot)
        elementos_sidebar.append(pilares[i].elemento)
        v_z.append(pilares[i].vectorY)
        sidebar_diameter.append(pilares[i].b_diametro)
        sidebar_number.append(pilares[i].nr_h)
        sidearray.append(pilares[i].h_array_length(rebar_bar_diameter[i]))

rebar_bar = rebar_type(rebars, bar_diameter, 0)
rebar_sidebar = rebar_type(rebars, sidebar_diameter, 0)

t = Transaction(doc, "Armaduras")
t.Start()

for i in ciclo(elementos_est_fund):
    
    estribos_fund = rebar_estribos(elementos_est_fund[i], v_x_fund[i], rebar_stir_fund[i], ganchos_estribo_fund[i], estribo_fund[i])
    estribo_esp_fund = estribos_fund.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(spacing_fund[i], comp_fund[i], True ,True ,True)

for i in ciclo(elementos_bar_fund):

    bars_fund = rebar_bars(elementos_bar_fund[i], v_y_fund[i], rebar_bar_fund[i], bar_fund[i], ganchos_bars_fund[i], None)
    bars_number_fund = bars_fund.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(bar_number_fund[i], array_fund[i], True, True, True)

    if rodar_fund[i]:
        bars_fund.LookupParameter(para.HOOK_ROTATION).Set(3.14159)
 
for i in ciclo(elementos_sidebar_fund):

    sidebars_fund = rebar_bars(elementos_sidebar_fund[i], v_z_fund[i], rebar_sidebar_fund[i], sidebar_fund[i], ganchos_bars_fund[i], None)
    sidebars_number_fund = sidebars_fund.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(sidebar_number_fund[i], sidearray_fund[i], True, False, False)

    if rodar_side_fund[i]:
        sidebars_fund.LookupParameter(para.HOOK_ROTATION).Set(3.14159)

for i in ciclo(elementos_est):
    
    estribos = rebar_estribos(elementos_est[i], v_x[i], rebar_stir[i], ganchos_estribo[i], estribo[i])
    estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(spacing[i], comp[i], True, True, True)

for i in ciclo(elementos_bar):

    bars = rebar_bars(elementos_bar[i], v_y[i], rebar_bar[i], bar[i], None, None)
    bars_number = bars.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(bar_number[i], array[i], True, True, True)
 
for i in ciclo(elementos_sidebar):

    sidebars = rebar_bars(elementos_sidebar[i], v_z[i], rebar_sidebar[i], sidebar[i], None, None)
    sidebars_number = sidebars.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(sidebar_number[i], sidearray[i], True, False, False)

t.Commit()

end_time = datetime.now()
execution_time = end_time - start_time

print("Runtime: {}".format(execution_time.total_seconds()))


for i in ciclo(p):

    rebar_bar_diameter = rebar_type(rebars, p[i].diametro_estribo, 1)
    rebar_bar = rebar_type(rebars, p[i].b_diametro, 0)

    p[i].barras(rebar_bar_diameter, sapatas[i].altura, 0.328084, 0.0393701, p[i].b_varao)
    bars_bot = rebar_bars(p[i].elemento, p[i].vectorX, rebar_bar, p[i].barras_bot, None, None)
    bars_number_bot = bars_bot.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(p[i].nr_b, p[i].b_array_length(), True, True, True)

    bars_top = rebar_bars(p[i].elemento, p[i].vectorX, rebar_bar, p[i].barras_bot, None, None)
    bars_number_top = bars_top.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(p[i].nr_b, p[i].b_array_length(), True, True, True)

    if p[i].nr_h > 2:

        p[i].barras_fund(rebar_bar_diameter, sapatas[i].altura, 0.328084, 0.0393701, p[i].b_varao)
        bars_side1 = rebar_bars(p[i].elemento, p[i].vectorY, rebar_bar_fund, p[i].barras_side, None, None)
        bars_number_side1 = bars_side1.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(p[i].nr_h, p[i].h_array_length(), True, False, False)

        bars_side2 = rebar_bars(p[i].elemento, p[i].vectorY, rebar_bar_fund, p[i].barras_bot, None, None)
        bars_number_side2 = bars_side2.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(p[i].nr_h, p[i].h_array_length(), True, False, False)

    if p[i].bol == "N":

        rebar_stir = rebar_type(rebars , p[i].est_ext_diametro, 0)
        p[i].estribos(0, sapatas[i].altura, 0.0393701, 2*p[i].nr_b, p[i].b_varao, 2*p[i].nr_h, p[i].b_varao)
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].estribo_espacamento, p[i].cmp, True ,True ,True)

    elif p[i].bol == "Y" and p[i].cmp <= buffer*p[i].cc + vigas_fund_h[i]:
        
        rebar_stir = rebar_type(rebars , p[i].est_ext_diametro, 0)
        p[i].estribos(0, sapatas[i].altura, 0.0393701, 2*p[i].nr_b, p[i].b_varao, 2*p[i].nr_h, p[i].b_varao)
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].estribo_espacamento, p[i].cmp, True ,True ,True)

    else:
        rebar_stir = rebar_type(rebars , p[i].est_ext_diametro, 0)
        p[i].estribos(0, sapatas[i].altura, 0.0393701, 2*p[i].nr_b, p[i].b_varao, 2*p[i].nr_h, p[i].b_varao)
        p[i].cc_fund(sapatas[i].altura, 0.0393701, 2*p[i].nr_b, p[i].b_varao, 2*p[i].nr_h, p[i].b_varao)
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].est_ext_espacamento, p[i].cc_sapata, True ,True ,True)
        
        p[i].estribos(1)
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo_esp = estribos_fund.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].estribo_espacamento, p[i].cnc_viga(vigas_h[i]), True ,True ,True)
        
        p[i].estribos(2, altura_viga=vigas_fund_h[i])
        estribos = rebar_estribos(p[i].elemento, p[i].vectorZ, rebar_stir, gancho_estribo, p[i].estribo)
        estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(p[i].est_ext_espacamento, p[i].cc_viga(vigas_h[i]), True ,True ,True)