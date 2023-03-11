# -*- coding: utf-8 -*-
"""Vistas Pilares"""
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

from classes import Pilar
from classes import RvtApiCategory as cat
from classes import RvtApi as rvt
from classes import RvtClasses as cls

doc = __revit__.ActiveUIDocument.Document

elements = rvt.get_elements(doc, cat.PILAR)

#ViewFamTypes = FilteredElementCollector(doc).OfClass(ViewFamilyType).WhereElementIsElementType().ToElements()
ViewFamTypes = rvt.get_type_element_byclass(doc, cls.VIEW_TYPE)

def get_section(vistas):
    for view in vistas:
        if view.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == "Building Section":
            return view

vista = get_section(ViewFamTypes).Id

pilares = [Pilar(doc, element) for element in elements if element.LookupParameter("Criar_vistas").AsInteger() == 1]

OFFSET = 0.65

t = Transaction(doc, "Vistas Pilares")
t.Start()

for pilar in pilares:

    section_A = pilar.criar_vista(doc, vista, 'Seccao A', OFFSET)
    section_A.Name = "2A - {} Secção A".format(pilar.nome)
    sectiom_A_sheet = section_A.LookupParameter("Title on Sheet").Set('{} Secção A'.format(pilar.nome))

    section_B = pilar.criar_vista(doc, vista, 'Seccao B', OFFSET)
    section_B.Name = "2B - {} Secção B".format(pilar.nome)
    sectiom_B_sheet = section_B.LookupParameter("Title on Sheet").Set('{} Secção B'.format(pilar.nome))

    alcado_A = pilar.criar_vista(doc, vista, 'Alcado A', OFFSET)
    alcado_A.Name = "2C - {} Corte A".format(pilar.nome)
    alcado_A_sheet = alcado_A.LookupParameter("Title on Sheet").Set('{} Corte A'.format(pilar.nome))

    alcado_B = pilar.criar_vista(doc, vista, 'Alcado B', OFFSET)
    alcado_B.Name = "2C - {} Corte B".format(pilar.nome)
    alcado_B_sheet = alcado_B.LookupParameter("Title on Sheet").Set('{} Corte B'.format(pilar.nome))

t.Commit()