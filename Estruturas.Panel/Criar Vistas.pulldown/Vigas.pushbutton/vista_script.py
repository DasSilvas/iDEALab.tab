# -*- coding: utf-8 -*-
"""Vistas Vigas"""
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

import os.path
import sys

# get the absolute path to the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# add the grandparent directory to the system path
sys.path.insert(0, grandparent_dir)

from classes import Viga
from classes import RvtApiCategory as cat
from classes import RvtApi as rvt
from classes import RvtClasses as cls

doc = __revit__.ActiveUIDocument.Document

elements = rvt.get_elements(doc, cat.VIGA)

#ViewFamTypes = FilteredElementCollector(doc).OfClass(ViewFamilyType).WhereElementIsElementType().ToElements()
ViewFamTypes = rvt.get_type_element_byclass(doc, cls.VIEW_TYPE)

def get_section(vistas):
    for view in vistas:
        if view.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == "Building Section":
            return view

vista = get_section(ViewFamTypes).Id

vigas = [Viga(doc, element) for element in elements if element.LookupParameter("Criar_vistas").AsInteger() == 1]

OFFSET = 0.65

t = Transaction(doc, "Vistas Vigas")
t.Start()

for viga in vigas:

    section_A = viga.criar_vista(doc, vista, 'Seccao A', OFFSET)
    section_A.Name = "3A - {} Secção A".format(viga.nome)
    sectiom_A_sheet = section_A.LookupParameter("Title on Sheet").Set('{} Secção A'.format(viga.nome))

    section_B = viga.criar_vista(doc, vista, 'Seccao B', OFFSET)
    section_B.Name = "3B - {} Secção B".format(viga.nome)
    sectiom_B_sheet = section_B.LookupParameter("Title on Sheet").Set('{} Secção B'.format(viga.nome))

    alcado = viga.criar_vista(doc, vista, 'Alcado', OFFSET)
    alcado.Name = "3C - {} Corte".format(viga.nome)
    alcado_sheet = alcado.LookupParameter("Title on Sheet").Set('Corte {}'.format(viga.nome))

t.Commit()
