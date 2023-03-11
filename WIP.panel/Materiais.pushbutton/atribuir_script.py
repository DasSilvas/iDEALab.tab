# -*- coding: utf-8 -*-
"""WIP dar material a elementos estruturais"""
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

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(BuiltInCategory.OST_StructuralFraming)
vigas = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

# create a filtered element collector for materials
collector2 = FilteredElementCollector(doc).OfClass(Material)

# retrieve all materials in the collector
materials = collector2.ToElements()

t = Transaction(doc, "Materiais")
t.Start()

# iterate through the materials and do something with them
for material in materials:
    # do something with material
    if material.Name == "Concrete C20/25":
        mat = material.Id
        print(mat)

for viga in vigas:
    mate = viga.LookupParameter("Structural Material").Set(mat)

t.Commit()