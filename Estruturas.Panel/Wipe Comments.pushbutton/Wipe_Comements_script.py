# -*- coding: utf-8 -*-
"""Apaga os comentarios do elemento que digam Armar"""
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
import math

def flatten(t):
    return [item for sublist in t for item in sublist]
    
def ciclo(x):
    return range(len(x))

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(BuiltInCategory.OST_StructuralFraming)
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

collector_rebar = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rebar).WhereElementIsElementType()
rebars = collector_rebar.ToElements()

collector_hooks = FilteredElementCollector(doc).OfClass(RebarHookType).WhereElementIsElementType()
hooks = collector_hooks.ToElements()

# Transcao com o REVIT para fazer as armaduras

t = Transaction(doc, "Wipe Beam Comments")
t.Start()

for element in elements:
    if element.LookupParameter("Comments").AsString() == "Armar":
        element.LookupParameter("Comments").Set("")
    else:
        pass

t.Commit()