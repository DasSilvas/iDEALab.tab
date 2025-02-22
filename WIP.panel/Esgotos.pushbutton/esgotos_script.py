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

from classes import Element, Funk, Pipes, PlumbingFixture, PipeFitting
from classes import RvtApiCategory as cat
from classes import RvtApi as rvt
from classes import RvtClasses as cls
from classes import RvtParameterName as parameter
from pyrevit import revit
from pyrevit import forms, script
import rpae

doc = __revit__.ActiveUIDocument.Document

#pipes = rvt.get_elements_bycategory(doc, cat.PIPES)
pipe_fittings = rvt.get_elements_bycategory(doc, cat.PIPE_FITTINGS)
plumbing_fixtures = rvt.get_elements_bycategory(doc, cat.PLUMBING_FIXTURES)
teste1 = []

pipe_elements = rvt.get_elements_byparameter(doc, cls.PIPES, parameter.PIPE_SYSTEM_TYPE, "Sanitary")

pipes = [Pipes(doc, pipe) for pipe in pipe_elements]
p_fixtures = [PlumbingFixture(doc, p_f) for p_f in plumbing_fixtures]
p_fittings = [PipeFitting(doc, p_fitting) for p_fitting in pipe_fittings]

fittings_sanitary = PipeFitting.filter_by_system(p_fittings, "Sanitary")
fixtures_sanitary = PlumbingFixture.filter_by_system(p_fixtures, "Sanitary")

caixas = [f for f in fixtures_sanitary if f.type.FamilyName == 'ED&EP FVPS - Caixa' ]

refs = []

for x in fittings_sanitary:
	connset = x.elemento.MEPModel.ConnectorManager.Connectors
	conn_pipes = []
	for c in connset:
		if c.IsConnected:
			for lc in c.AllRefs:
				conn_pipes.append(lc.Owner)
	refs.append(conn_pipes)

t = Transaction(doc, "Pipes")
t.Start()

for p in pipes:
	if p.tubo_queda.AsInteger() == 1:
		caudal = rpae.q_cal(p.caudal_acumulado)
		diametro_cal = rpae.d_tq(caudal, taxa_ocupacao=0.17)
		diametro_tq = rpae.d_pvc(diametro_cal, "tq")
		p.set_diameter(Funk.internal_units(diametro_tq))
t.Commit()

#print(teste1)




#for pipe in pipes:
    #param.append(pipe.get_Parameter(parameter.FIXTURE_UNITS).AsDouble())

#for pipe in pipe_fittings:
    #param.append(pipe.get_Parameter(parameter.PIPE_SYSTEM_TYPE))

#fitting = pipe_fittings[0].LookupParameter("System Classification").AsString()

#para_pf = pipe_fittings[0].LookupParameter("System Type").AsElementId()

#system_type = doc.GetElement(para_pf).GetOrderedParameters()

#ele = []
#for para in fitting:
    #ele.append(para.Definition.Name)
#for paramter in para_pf:
    #print(paramter.AsString())

