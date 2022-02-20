# Load the Python Standard and DesignScript Libraries
# -*- coding: utf-8 -*-
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
import math

from classes import Element, Viga

def flatten(t):
    return [item for sublist in t for item in sublist]
    
def ciclo(x):
    return range(len(x))

def meters(x):
    x = UnitUtils.ConvertFromInternalUnits(x , UnitTypeId.Meters)
    return x
    
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
		    
def iu(x , unit):
    if unit == "m":
        x = UnitUtils.ConvertToInternalUnits(x , UnitTypeId.Meters)
    elif unit == "mm":
        x = UnitUtils.ConvertToInternalUnits(x , UnitTypeId.Millimeters)
    return x

output = []
elementos = []
l = [] # Length
cover_length = []
t_x = []
t_y = []
estribo_esp = [] # Distribuicao dos estribos
buffer = 2.1

#Recipientes para a excucao dos estribos

v_x = [] # vector axial
comp = [] # comprimento da distribuicao do estribo
spacing = [] # espacamento do estribo
estribo_diameter = [] # diametro do estribo

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

for element in ele_rebar:
    element.decode()
    rebar_code.append(element.code)
    output.append(element.cc)

print(output)
print(esp)
