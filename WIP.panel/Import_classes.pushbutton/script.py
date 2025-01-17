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
from System.Collections.Generic import List

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

dwg_opt = "ISO13567_CAD"

def ProcessParallelLists(_func, *lists):
	return map( lambda *xs: ProcessParallelLists(_func, *xs) if all(type(x) is list for x in xs) else _func(*xs), *lists )

class ModalForm(WPFWindow):
    def __init__(self, xaml_source):
        self.form = WPFWindow.__init__(self,xaml_source)
        self.ShowDialog()
    
    def get_sheets_collector(self):
         collector = FilteredElementCollector(doc)
         filtro = ElementCategoryFilter(cat.SHEETS)
         return collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

    def get_sheets(self):
        return self.get_sheets_collector()

    def create_sheet_name(self):
        sheets = self.get_sheets_collector()
        return [s.SheetNumber + "-" + s.Name for s in sheets]
           
    def export_dwfx(self, sheets):
        y = DWFXExportOptions()
        y.MergedViews = True
        a=ViewSet()
        if sheets:
            for s in sheets:
                a.Insert(s)
        doc.Export(self.save_path, self.dwfx_name,a,y)

    def ext_dwg(self, name, sheet):
        options = None
        settings = FilteredElementCollector(doc).WherePasses(ElementClassFilter(ExportDWGSettings))
        for element in settings:
            if element.Name == "ISO13567_CAD":
                options = element.GetDWGExportOptions()
                break 
            if options is None:
                 options = DWGExportOptions()
        options.MergedViews = True
        sheets = List[ElementId]()
        sheets.Add(sheet.Id)
        result = doc.Export(self.save_path, name, sheets, options)
        return result
        
    def export_dwg(self):
         ProcessParallelLists(self.ext_dwg, self.create_sheet_name(), self.get_sheets())

    def export_sheets(self, sender, e):
        tg = TransactionGroup(doc, "Export")
        tg.Start()

        t = Transaction(doc, "Export DWFx")
        t.Start()
        if self.checkbox_dwfx:
            self.export_dwfx(self.get_sheets())
        t.Commit()    
 
        t = Transaction(doc, 'Export DWG')
        t.Start()
        if self.checkbox_dwg:
            self.export_dwg()
        t.Commit()

        tg.Assimilate()

    @property
    def checkbox_dwfx(self):
        return self.UI_export_dwfx.IsChecked
    
    @property
    def checkbox_dwg(self):
        return self.UI_export_dwg.IsChecked
    
    @property
    def save_path(self):
        return self.UI_save_path.Text
    
    @property
    def dwfx_name(self):
        return self.UI_dwfx_name.Text
    
    @staticmethod
    def ProcessParallelLists(_func, *lists):
	    return map( lambda *xs: ProcessParallelLists(_func, *xs) if all(type(x) is list for x in xs) else _func(*xs), *lists )

form = ModalForm('MainWindow.xaml')