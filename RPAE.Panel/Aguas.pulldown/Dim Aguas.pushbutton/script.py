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

import os.path
import sys
from System.Collections.Generic import List

# get the absolute path to the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# add the grandparent directory to the system path
sys.path.insert(0, grandparent_dir)

from classes import Element, Funk, Pipes, PlumbingFixture, PipeFitting
from classes import RvtApiCategory as cat
from classes import RvtApi as rvt
from classes import RvtClasses as cls
from classes import RvtParameterName as parameter
import rpae

doc = __revit__.ActiveUIDocument.Document

piping_system = rvt.get_element_byclass(doc, cls.PIPING_SYSTEM, element_type=False)

elements = rvt.get_elements_bycategory(doc, cat.PIPES)

water_pipes = []

for ele in elements:
    nome_sistema = ele.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
    if nome_sistema.startswith(("AF", "AQ")):
        water_pipes.append(Pipes(doc, ele))

t = Transaction(doc, "AA_Qcal")
t.Start()

for p in water_pipes:
    caudal_cal = rpae.aa_qcal(p.aa_q_acumulado)
    d_cal = rpae.aa_d_cal(caudal_cal)
    d_interno = round(p.inside_diameter*304.8)
    velocidade = rpae.aa_velocidade(caudal_cal, d_interno)
    p.set_dcal(d_cal)
    p.set_qcal(caudal_cal)
    p.set_d_interno(d_interno)
    p.set_velocity(velocidade)

t.Commit()




