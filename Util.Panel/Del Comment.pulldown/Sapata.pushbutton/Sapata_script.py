# -*- coding: utf-8 -*-
"""Apaga os comentarios das vigas"""
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

from classes import RvtApiCategory as cat

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(cat.FUNDACAO)
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

# Transcao com o REVIT para fazer as armaduras

t = Transaction(doc, "Wipe Beam Comments")
t.Start()

for element in elements:
    element.LookupParameter("Comments").Set("")

t.Commit()