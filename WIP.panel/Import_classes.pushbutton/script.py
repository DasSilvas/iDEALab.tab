# -*- coding: utf-8 -*-

import os.path
import sys
# get the absolute path to the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# add the grandparent directory to the system path
sys.path.insert(0, grandparent_dir)

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System")

"""WIP vistas"""
# Load the Python Standard and DesignScript Libraries
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *
from Autodesk.Revit.UI import *
from pyrevit.forms import WPFWindow
from classes import RvtApiCategory as cat

from System.Windows.Controls import Orientation, CheckBox, DockPanel, Button,ComboBoxItem, TextBox, ListBoxItem, StackPanel, TextBlock, WrapPanel, Border, ScrollViewer
from System.Collections.Generic import List
from System.Windows             import Visibility
import wpf

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

dwg_opt = "ISO13567_CAD"

class ListItem:
    """Helper Class for displaying selected sheets in my custom GUI."""
    def __init__(self,  Name='Unnamed', element = None, checked = False):
        self.Name       = Name
        self.element    = element
        self.IsChecked  = checked

def ProcessParallelLists(_func, *lists):
	return map( lambda *xs: ProcessParallelLists(_func, *xs) if all(type(x) is list for x in xs) else _func(*xs), *lists )

class ModalForm(WPFWindow):
    def __init__(self, xaml_source):
        self.form = WPFWindow.__init__(self,xaml_source)
        self.populate_views_listbox()
        self.ShowDialog()

    def get_sheets_collector(self):
         collector = FilteredElementCollector(doc)
         filtro = ElementCategoryFilter(cat.SHEETS)
         return collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

    def get_sheets(self):
        return self.get_sheets_collector()

    def populate_views_listbox(self):
        """Populate the ListBox with sheets in the project."""
        # Get Views
        views = self.get_sheets()
        
        # Create list of view names for binding
        self.sheet_items =sorted([ListItem('{} - {}'.format(view.SheetNumber, view.Name), view) for view in views], key=lambda item: item.Name)
        self.UI_CheckboxList.ItemsSource = self.sheet_items 

    def get_selected_sheets(self):
        """Retrieve selected sheets."""
        selected_sheets = []
        for item in self.sheet_items:
            if item.IsChecked:
                selected_sheets.append(item.element)
        return selected_sheets

    def create_sheet_name(self):
        sheets_name = []
        for item in self.sheet_items:
            if item.IsChecked:
                sheets_name.append(item.Name)
        return sheets_name

    def export_dwfx(self,sheets):
        y = DWFXExportOptions()
        y.MergedViews = True
        a=ViewSet()
        for s in sheets:
            a.Insert(s)
        doc.Export(self.save_path, self.dwfx_name,a,y)
        """
    def export_dwfx(self):
        y = DWFXExportOptions()
        y.MergedViews = True
        a=ViewSet()
        for item in self.sheet_items:
            if item.IsChecked:
                a.Insert(item.element)
        doc.Export(self.save_path, self.dwfx_name,a,y)
        """
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
         ProcessParallelLists(self.ext_dwg, self.create_sheet_name(), self.get_selected_sheets())

    def export_sheets(self, sender, e):
        tg = TransactionGroup(doc, "Export")
        tg.Start()

        t = Transaction(doc, "Export DWFx")
        t.Start()
        if self.checkbox_dwfx:
            self.export_dwfx(self.get_selected_sheets())
        t.Commit()    
 
        t = Transaction(doc, 'Export DWG')
        t.Start()
        if self.checkbox_dwg:
            self.export_dwg()
        t.Commit()

        tg.Assimilate()

    def check_all(self, sender,e):
        # Set IsCheked to True for all items in the ListBox
        for item in self.UI_CheckboxList.ItemsSource:
            item.IsChecked = True
        
        # Refrest the ListBox to reflect changes
        self.UI_CheckboxList.ItemsSource = None
        self.UI_CheckboxList.ItemsSource = self.sheet_items

    def check_none(self, sender,e):
        # Set IsCheked to False for all items in the ListBox
        for item in self.UI_CheckboxList.ItemsSource:
            item.IsChecked = False
        
        # Refrest the ListBox to reflect changes
        self.UI_CheckboxList.ItemsSource = None
        self.UI_CheckboxList.ItemsSource = self.sheet_items

    def SearchBox_TextChanged(self, sender, e):
        """Filter the ListBox items based on the search text."""
        search_text = self.UI_SearchBox.Text.lower()
        
        if search_text:
            filtered_items = [
                item for item in self.sheet_items if search_text in item.Name.lower()
            ]
            self.UI_CheckboxList.ItemsSource = filtered_items
        else:
            self.UI_CheckboxList.ItemsSource = self.sheet_items
 
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