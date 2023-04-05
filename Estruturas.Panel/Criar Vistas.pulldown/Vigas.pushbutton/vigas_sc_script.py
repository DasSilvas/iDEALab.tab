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
from pyrevit import forms, script

class ViewTemplates(forms.TemplateListItem):
    @property
    def name(self):
        return doc.GetElement(self.item).Name

doc = __revit__.ActiveUIDocument.Document

elements = rvt.get_elements_bycategory(doc, cat.VIGA)

ViewFamTypes = rvt.get_element_byclass(doc, cls.VIEW_TYPE, element_type=True)

views_all = rvt.get_element_byclass(doc, cls.VIEW)
templates_all = [v.Id for v in views_all if v.IsTemplate]

def get_section(vistas):
    for view in vistas:
        if view.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == "Building Section":
            return view

vista = get_section(ViewFamTypes).Id

vigas = [Viga(doc, element) for element in elements if element.LookupParameter("Criar_vistas").AsInteger() == 1]

template = forms.SelectFromList.show(
    [ViewTemplates(v) for v in templates_all],
    title = "Escolher View Template",
    width = 500,
    button_name = "Executar")

if not template:
    script.exit()

OFFSET_SECTION = 1
OFFSET_ALCADO = 3

OFFSET_DIM = 175
OFFSET_DIM_REC = OFFSET_DIM/2

t = Transaction(doc, "Vistas Vigas")
t.Start()

for viga in vigas:

    #Create the section "Seccao A" view of the beam
    section_A = viga.criar_vista(doc, vista, 'Seccao A', OFFSET_SECTION)
    section_A.Name = "3A - {} Secção A".format(viga.nome)
    sectiom_A_sheet = section_A.LookupParameter("Title on Sheet").Set('{} Secção A'.format(viga.nome))
    section_A_template = section_A.LookupParameter("View Template").Set(template)

    #Store variables for the points of the lines for the dimension annotation

    p1_altura = -viga.altura/2 #first point, bottom of the beam
    p2_altura = viga.altura/2 # second point, top fo the beam

    p1_largura = -viga.largura/2 #first point, left side of the beam
    p2_largura = viga.largura/2 #second point, right side of the beam

    p1_altura_rec = p1_altura + viga.cover_length #cover length for the bottom of the beam
    p2_altura_rec = p2_altura - viga.cover_length #cover length for the top of the beam

    p1_largura_rec = p1_largura + viga.cover_length #cover length for the left side of the beam
    p2_largura_rec = p2_largura - viga.cover_length #cover length for the right side of the beam

    #Creates the dimensions for the height, including top and bottom cover length of the beam, for the section view "Secçao A"
    cotar_altura = viga.create_dimensions(doc, section_A, p1_altura, p2_altura, OFFSET_DIM, y_lock_value=p2_largura, zy_lock=True)
    rec_altura1 = viga.create_dimensions(doc, section_A, p1_altura, p1_altura_rec, OFFSET_DIM_REC, y_lock_value=p2_largura, zy_lock=True)
    rec_altura2 = viga.create_dimensions(doc, section_A, p2_altura_rec, p2_altura, OFFSET_DIM_REC, y_lock_value=p2_largura, zy_lock=True)

    #Creates the dimensions for the width, including left and right cover length of the beam, for the section view "Secçao A"
    cotar_largura = viga.create_dimensions(doc, section_A, p1_largura, p2_largura, OFFSET_DIM, z_lock_value=p2_altura, yz_lock=True)
    rec_largura1 = viga.create_dimensions(doc, section_A, p1_largura, p1_largura_rec, OFFSET_DIM_REC, z_lock_value=p2_altura, yz_lock=True)
    rec_largura2 = viga.create_dimensions(doc, section_A, p2_largura_rec, p2_largura, OFFSET_DIM_REC, z_lock_value=p2_altura, yz_lock=True)

    #Create the section "Seccao B" view of the beam
    section_B = viga.criar_vista(doc, vista, 'Seccao B', OFFSET_SECTION)
    section_B.Name = "3B - {} Secção B".format(viga.nome)
    sectiom_B_sheet = section_B.LookupParameter("Title on Sheet").Set('{} Secção B'.format(viga.nome))
    section_B_template = section_B.LookupParameter("View Template").Set(template)

    #Creates the dimensions for the height, including top and bottom cover length of the beam, for the section view "Secçao B"
    cotar_altura = viga.create_dimensions(doc, section_B, p1_altura, p2_altura, OFFSET_DIM, y_lock_value=p2_largura, zy_lock=True)
    rec_altura1 = viga.create_dimensions(doc, section_B, p1_altura, p1_altura_rec, OFFSET_DIM_REC, y_lock_value=p2_largura, zy_lock=True)
    rec_altura2 = viga.create_dimensions(doc, section_B, p2_altura_rec, p2_altura, OFFSET_DIM_REC, y_lock_value=p2_largura, zy_lock=True)

    #Creates the dimensions for the width, including left and right cover length of the beam, for the section view "Secçao B"
    cotar_largura = viga.create_dimensions(doc, section_B, p1_largura, p2_largura, OFFSET_DIM, z_lock_value=p2_altura, yz_lock=True)
    rec_largura1 = viga.create_dimensions(doc, section_B, p1_largura, p1_largura_rec, OFFSET_DIM_REC, z_lock_value=p2_altura, yz_lock=True)
    rec_largura2 = viga.create_dimensions(doc, section_B, p2_largura_rec, p2_largura, OFFSET_DIM_REC, z_lock_value=p2_altura, yz_lock=True)

    #Create the section view along of the beam
    alcado = viga.criar_vista(doc, vista, 'Alcado', OFFSET_ALCADO)
    alcado.Name = "3C - {} Corte".format(viga.nome)
    alcado_sheet = alcado.LookupParameter("Title on Sheet").Set('Corte {}'.format(viga.nome))
    alcado_template = alcado.LookupParameter("View Template").Set(template)

    p1_comprimento = -viga.cut_comprimento/2 #first point, left side of the beam along the length
    p2_comprimento = viga.cut_comprimento/2 #second point, right side of the beam along the length

    cotar_comprimento = viga.create_dimensions(doc, alcado, p1_comprimento, p2_comprimento, OFFSET_DIM, z_lock_value=p2_altura, xz_lock=True)

t.Commit()
