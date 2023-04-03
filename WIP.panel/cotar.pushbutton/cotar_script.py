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
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# add the grandparent directory to the system path
sys.path.insert(0, grandparent_dir)

from classes import Pilar, Funk
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

OFFSET_DIM = 175
OFFSET_DIM_REC = OFFSET_DIM/2

t = Transaction(doc, "Vistas Pilares")
t.Start()

for pilar in pilares:

    #Create the section "Seccao A" view of the column
    section_A = pilar.criar_vista(doc, vista, 'Seccao A', OFFSET)
    section_A.Name = "2A - {} Secção A".format(pilar.nome)
    section_A_sheet = section_A.LookupParameter("Title on Sheet").Set('{} Secção A'.format(pilar.nome))
    section_A_template = section_A.LookupParameter("View Template").Set(template)

    # Creates the dimensions of b and h of the column for the section view "Secçao A"

    cotar_altura = pilar.create_dimensions(doc, section_A, -pilar.h/2, pilar.h/2, OFFSET_DIM, x_lock_value=pilar.b/2, x_lock=True)
    cotar_largura = pilar.create_dimensions(doc, section_A, -pilar.b/2, pilar.b/2, OFFSET_DIM, y_lock_value=pilar.h/2, y_lock=True)

    # Creates the dimensions for the cover of the column for the section view "Secçao A"

    h_rec1 = -pilar.h/2
    h_rec2 = h_rec1 + pilar.cover_length
    h_rec3 = pilar.h/2 - pilar.cover_length
    h_rec4 = pilar.h/2

    rec_altura1 = pilar.create_dimensions(doc, section_A, h_rec1, h_rec2, OFFSET_DIM_REC, x_lock_value=pilar.b/2, x_lock=True)
    rec_altura2 = pilar.create_dimensions(doc, section_A, h_rec3, h_rec4, OFFSET_DIM_REC, x_lock_value=pilar.b/2, x_lock=True)

    b_rec1 = -pilar.b/2
    b_rec2 = b_rec1 + pilar.cover_length
    b_rec3 = pilar.b/2 - pilar.cover_length
    b_rec4 = pilar.b/2

    rec_altura1 = pilar.create_dimensions(doc, section_A, b_rec1, b_rec2, OFFSET_DIM_REC, y_lock_value=pilar.h/2, y_lock=True)
    rec_altura2 = pilar.create_dimensions(doc, section_A, b_rec3, b_rec4, OFFSET_DIM_REC, y_lock_value=pilar.h/2, y_lock=True)

    #Create the section "Seccao B" view of the column

    section_B = pilar.criar_vista(doc, vista, 'Seccao B', OFFSET)
    section_B.Name = "2B - {} Secção B".format(pilar.nome)
    section_B_sheet = section_B.LookupParameter("Title on Sheet").Set('{} Secção B'.format(pilar.nome))
    section_B_template = section_B.LookupParameter("View Template").Set(template)

    # Creates the dimensions of b and h of the column for the section view "Secçao B"

    cotar_altura = pilar.create_dimensions(doc, section_B, -pilar.h/2, pilar.h/2, OFFSET_DIM, x_lock_value=pilar.b/2, x_lock=True)
    cotar_largura = pilar.create_dimensions(doc, section_B, -pilar.b/2, pilar.b/2, OFFSET_DIM, y_lock_value=pilar.h/2, y_lock=True)

    rec_altura1 = pilar.create_dimensions(doc, section_B, h_rec1, h_rec2, OFFSET_DIM_REC, x_lock_value=pilar.b/2, x_lock=True)
    rec_altura2 = pilar.create_dimensions(doc, section_B, h_rec3, h_rec4, OFFSET_DIM_REC, x_lock_value=pilar.b/2, x_lock=True)

    # Creates the dimensions for the cover of the column for the section view "Secçao B"
    rec_altura1 = pilar.create_dimensions(doc, section_B, b_rec1, b_rec2, OFFSET_DIM_REC, y_lock_value=pilar.h/2, y_lock=True)
    rec_altura2 = pilar.create_dimensions(doc, section_B, b_rec3, b_rec4, OFFSET_DIM_REC, y_lock_value=pilar.h/2, y_lock=True)

    alcado_A = pilar.criar_vista(doc, vista, 'Alcado A', OFFSET)
    alcado_A.Name = "2C - {} Corte A".format(pilar.nome)
    alcado_A_sheet = alcado_A.LookupParameter("Title on Sheet").Set('{} Corte A'.format(pilar.nome))
    alcado_A_template = alcado_A.LookupParameter("View Template").Set(template)

    pilar.create_dimensions(doc, alcado_A, pilar.z, pilar.cmp + pilar.z, OFFSET_DIM, x_lock_value=pilar.b/2, zx_lock=True)

    alcado_B = pilar.criar_vista(doc, vista, 'Alcado B', OFFSET)
    alcado_B.Name = "2C - {} Corte B".format(pilar.nome)
    alcado_B_sheet = alcado_B.LookupParameter("Title on Sheet").Set('{} Corte B'.format(pilar.nome))
    alcado_B_template = alcado_B.LookupParameter("View Template").Set(template)

    pilar.create_dimensions(doc, alcado_B, pilar.z, pilar.cc + pilar.z, OFFSET_DIM, y_lock_value=pilar.h/2, zy_lock=True)


t.Commit()
"""
views_all = rvt.get_element_byclass(doc, cls.VIEW)

elements = rvt.get_elements_bycategory(doc, cat.PILAR)

pilares = [Pilar(doc, element) for element in elements if element.LookupParameter("Criar_vistas").AsInteger() == 1]

for view in views_all:
    if "2A - P1" in view.Name:
        vista = view

t = Transaction(doc, "Cotar WIP")
t.Start()

referencesList = []

for i, pilar in enumerate(pilares):
    if pilar.nome == "P1":
        y_left = -pilar.b/2
        y_right = -1*y_left
        z_top = pilar.h/2 + Funk.internal_units(10, "mm")

        vector_yleft = pilar.vectorY.Multiply(y_left)
        vector_yirght = pilar.vectorY.Multiply(y_right)
        vector_ztop = pilar.vectorZ.Multiply (z_top)

        p1 = pilar.origem.Add(pilar.vectorX).Add(vector_yleft).Add(vector_ztop)
        p2 = pilar.origem.Add(pilar.vectorX).Add(vector_yirght).Add(vector_ztop)
        line = Line.CreateBound(p1, p2)

        referencesList.append(ReferenceArray())
        print(line.GetEndPointReference(1))
        #referencesList[i].Append(line.g)
        #referencesList[i].Append(p2)
        #print(referencesList)
        linha = doc.Create.NewDetailCurve(vista, line)
        curva = linha.GeometryCurve
        referencesList[i].Append(curva.GetEndPointReference(0))
        referencesList[i].Append(curva.GetEndPointReference(1))
        dim = doc.Create.NewDimension(vista, line, referencesList[i])
        print(pilar.nome)

t.Commit()
"""