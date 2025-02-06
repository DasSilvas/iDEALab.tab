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
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# add the grandparent directory to the system path
sys.path.insert(0, grandparent_dir)

from classes import Element, Funk, Pipes, PlumbingFixture
from classes import RvtApiCategory as cat
from classes import RvtApi as rvt
from classes import RvtClasses as cls
from classes import RvtParameterName as parameter
from pyrevit import revit
from pyrevit import forms, script

doc = __revit__.ActiveUIDocument.Document

pipes = rvt.get_elements_bycategory(doc, cat.PIPES)
pipe_fittings = rvt.get_elements_bycategory(doc, cat.PIPE_FITTINGS)
plumbing_fixtures = rvt.get_elements_bycategory(doc, cat.PLUMBING_FIXTURES)
param = []

pipe_elements = rvt.get_elements_byparameter(doc, cls.PIPES, parameter.PIPE_SYSTEM_TYPE, "Sanitary")

pipes = [Pipes(doc, pipe) for pipe in pipe_elements]
pf = [PlumbingFixture(doc, p_f) for p_f in plumbing_fixtures]

#for pipe in pipes:
    #param.append(pipe.get_Parameter(parameter.FIXTURE_UNITS).AsDouble())

for pipe in pf:
    param.append(pipe.get_system_name())

print(param)