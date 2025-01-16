# -*- coding: utf-8 -*-

import os.path
import sys
# get the absolute path to the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# add the grandparent directory to the system path
sys.path.insert(0, grandparent_dir)

"""WIP vistas"""
# Load the Python Standard and DesignScript Libraries
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *
from Autodesk.Revit.UI import *
from pyrevit.forms import WPFWindow
from classes import RvtApiCategory as cat

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

class ModalForm(WPFWindow):
    def __init__(self, xaml_source):
        self.form = WPFWindow.__init__(self,xaml_source)
        self.ShowDialog()
	
    def export(self, sender, e):
        if self.checkbox_dwfx:
            y = DWFXExportOptions()
            y.MergedViews = True
            a=ViewSet()
            t = Transaction(doc, "Export DWFx")
            t.Start()
            collector = FilteredElementCollector(doc)
            filtro = ElementCategoryFilter(cat.SHEETS)
            sheets = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()
            if sheets:
                for s in sheets:
                    a.Insert(s)
            doc.Export("C:\\Users\\joao_\\Desktop\\exports", "teste1",a,y)
            t.Commit()
            self.Close()
    
    @property
    def checkbox_dwfx(self):
        return self.UI_export_dwfx.IsChecked


#export_folder = "C:\\Users\\joao_\\Desktop\\exports"
#export_name = "teste1"

#sel_sheets = forms.select_sheets(title='Select Sheets', use_selection=True)
"""
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
# find the path of ui.xaml
#xamlfile = "C:\\Users\\hp\\AppData\\Roaming\\pyRevit-Master\\extensions\\ideaLAB.extension\\IdeaLAB.tab\\WIP.panel\\Import_classes.pushbutton\\teste2.xaml"

form = ModalForm('la.xaml')
