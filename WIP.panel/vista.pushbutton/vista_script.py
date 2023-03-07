# -*- coding: utf-8 -*-
"""WIP vistas"""
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
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

ViewFamTypes = FilteredElementCollector(doc).OfClass(ViewFamilyType).WhereElementIsElementType().ToElements()

def get_section(vistas):
    for view in vistas:
        if view.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == "Building Section":
            return view

vista = get_section(ViewFamTypes).Id

vigas = [element for element in elements if element.LookupParameter("Criar_vistas").AsInteger() == 1]

t = Transaction(doc, "vistas")
t.Start()

for viga in vigas:

    section = ViewSection.CreateSection(doc, vista, viga.get_BoundingBox(None))
    section.Name = 'Section View Along Beam'
    #section.SetSectionBox(section_box)

    #view_range = view.get_Parameter(BuiltInParameter.VIEWER_BOUND_OFFSET_FAR).AsDouble()
    #section_range = view_range / 2.0
    #section.ViewRange = ViewRange(section_range - 10, section_range + 10)

t.Commit()
