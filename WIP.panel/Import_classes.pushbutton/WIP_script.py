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