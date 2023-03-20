# -*- coding: utf-8 -*-
"""WIP cotar pecas desenhadas"""
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

doc = __revit__.ActiveUIDocument.Document

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