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

from classes import Element, Funk
from classes import RvtApiCategory as cat
from classes import RvtApi as rvt
from classes import RvtClasses as cls
from pyrevit import revit
from pyrevit import forms, script

class ViewTemplates(forms.TemplateListItem):
    @property
    def name(self):
        return doc.GetElement(self.item).Name

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(cat.SHEETS)
sheets = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

sel_sheets = forms.select_sheets(title='Select Sheets', use_selection=True)

export_folder = "C:\\Users\\joao_\\Desktop\\exports"
export_name = "teste1"

names = []
dwg_opt = "ISO13567_CAD"
for s in sel_sheets:
	names.append(s.SheetNumber + "-" + s.Name)

def ProcessList(_func, _list):
    return map( lambda x: ProcessList(_func, x) if type(x)==list else _func(x), _list )

def ProcessParallelLists(_func, *lists):
	return map( lambda *xs: ProcessParallelLists(_func, *xs) if all(type(x) is list for x in xs) else _func(*xs), *lists )

def ExportDwg(name, view, folder = export_folder):
	options = None
	settings = FilteredElementCollector(doc).WherePasses(ElementClassFilter(ExportDWGSettings))
	for element in settings:
		if element.Name == dwg_opt:
			options = element.GetDWGExportOptions()
			break 
		
	if options is None:
		options = DWGExportOptions()
	
	options.MergedViews = True
	views = List[ElementId]()
	views.Add(view.Id)
	result = doc.Export(folder, name, views, options)
	return result

ProcessParallelLists(ExportDwg, names, sel_sheets)
"""
settings = FilteredElementCollector(doc).WherePasses(ElementClassFilter(ExportDWGSettings))
views = List[ElementId]()

for element in settings:
	if element.Name == dwg_opt:
		options = element.GetDWGExportOptions()			
options.MergedViews = True

names = []

for s in sel_sheets:
	names.append(s.SheetNumber + "-" + s.Name)

t = Transaction(doc, "Export DWFx")
t.Start()

for s in range(len(sel_sheets)):
	views.Add(sel_sheets[s].Id)
	r = doc.Export(export_folder, names[s], views, options)

t.Commit()

t = Transaction(doc, "Export DWFx")

t.Start()
y = DWFXExportOptions()
y.MergedViews = True
a=ViewSet()

if sel_sheets:
	for s in sel_sheets:
		b= a.Insert(s)
ex = doc.Export(export_folder, export_name,a,y)

t.Commit()
"""	