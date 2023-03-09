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

from classes import Funk, Viga

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

vigas = [Viga(doc, element) for element in elements if element.LookupParameter("Criar_vistas").AsInteger() == 1]

OFFSET = 0.65

t = Transaction(doc, "vistas")
t.Start()

for viga in vigas:

    section_A = viga.criar_vista(doc, vista, 'Seccao A', OFFSET)
    section_A.Name = "{} - Secção A".format(viga.nome)
    sectiom_A_sheet = section_A.LookupParameter("Title on Sheet").Set('Secção {}A'.format(viga.nome))

    section_B = viga.criar_vista(doc, vista, 'Seccao B', OFFSET)
    section_B.Name = "{} - Secção B".format(viga.nome)
    sectiom_B_sheet = section_B.LookupParameter("Title on Sheet").Set('Secção {}B'.format(viga.nome))

    alcado = viga.criar_vista(doc, vista, 'Alcado', OFFSET)
    alcado.Name = "{} - Corte".format(viga.nome)
    alcado_sheet = alcado.LookupParameter("Title on Sheet").Set('Corte {}'.format(viga.nome))

t.Commit()
