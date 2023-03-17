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
from pyrevit import forms, script

class ViewTemplates(forms.TemplateListItem):
    @property
    def name(self):
        return doc.GetElement(self.item).Name

def get_section(vistas):
    for view in vistas:
        if view.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == "Building Section":
            return view

doc = __revit__.ActiveUIDocument.Document

elements = rvt.get_elements_bycategory(doc, cat.PILAR)

ViewFamTypes = rvt.get_element_byclass(doc, cls.VIEW_TYPE, element_type=True)

views_all = rvt.get_element_byclass(doc, cls.VIEW)
templates_all = [v.Id for v in views_all if v.IsTemplate]

vista = get_section(ViewFamTypes).Id

pilares = [Pilar(doc, element) for element in elements if element.LookupParameter("Criar_vistas").AsInteger() == 1]

OFFSET = 0.65

template = forms.SelectFromList.show(
    [ViewTemplates(v) for v in templates_all],
    title = "Escolher View Template",
    width = 500,
    button_name = "Executar")

if not template:
    script.exit()

t = Transaction(doc, "Vistas Pilares")
t.Start()

for pilar in pilares:

    section_A = pilar.criar_vista(doc, vista, 'Seccao A', OFFSET)
    section_A.Name = "2A - {} Secção A".format(pilar.nome)
    section_A_sheet = section_A.LookupParameter("Title on Sheet").Set('{} Secção A'.format(pilar.nome))
    section_A_template = section_A.LookupParameter("View Template").Set(template)

    section_B = pilar.criar_vista(doc, vista, 'Seccao B', OFFSET)
    section_B.Name = "2B - {} Secção B".format(pilar.nome)
    section_B_sheet = section_B.LookupParameter("Title on Sheet").Set('{} Secção B'.format(pilar.nome))
    section_B_template = section_B.LookupParameter("View Template").Set(template)

    alcado_A = pilar.criar_vista(doc, vista, 'Alcado A', OFFSET)
    alcado_A.Name = "2C - {} Corte A".format(pilar.nome)
    alcado_A_sheet = alcado_A.LookupParameter("Title on Sheet").Set('{} Corte A'.format(pilar.nome))
    alcado_A_template = alcado_A.LookupParameter("View Template").Set(template)

    alcado_B = pilar.criar_vista(doc, vista, 'Alcado B', OFFSET)
    alcado_B.Name = "2C - {} Corte B".format(pilar.nome)
    alcado_B_sheet = alcado_B.LookupParameter("Title on Sheet").Set('{} Corte B'.format(pilar.nome))
    alcado_B_template = alcado_B.LookupParameter("View Template").Set(template)

t.Commit()
