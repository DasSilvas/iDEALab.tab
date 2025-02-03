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
import System.Windows.Input as Input
from System.Windows import Window
from System.Windows.Forms import FolderBrowserDialog, DialogResult, OpenFileDialog

from System.Collections.Generic import List
from System.Windows             import Visibility
import wpf

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
last_selected_index = None 

class ListItem():
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
        self.populate_combo_box()
        self.dwg_setup = None
        self.last_selected_index = None  # Store last selected index for Shift+Click
        self.ShowDialog()

    def get_sheets_collector(self):
         collector = FilteredElementCollector(doc)
         filtro = ElementCategoryFilter(cat.SHEETS)
         return collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

    def get_sheets(self):
        return self.get_sheets_collector()
    
    def get_dwg_opts(self):
        dwg_settings = FilteredElementCollector(doc).WherePasses(ElementClassFilter(ExportDWGSettings))
        settings = [ListItem(setting.Name, setting.GetDWGExportOptions()) for setting in dwg_settings]
        return settings

    def populate_views_listbox(self):
        """Populate the ListBox with sheets in the project."""
        # Get Views
        views = self.get_sheets()
        
        # Create list of view names for binding
        self.sheet_items =sorted([ListItem('{} - {}'.format(view.SheetNumber, view.Name), view) for view in views], key=lambda item: item.Name)
        self.UI_CheckboxList.ItemsSource = self.sheet_items 

    def populate_combo_box(self):
        dwg_options = self.get_dwg_opts()
        self.UI_dwg_opts.ItemsSource = dwg_options

    def on_combo_box_selection_changed(self, sender, e):
        self.dwg_setup = self.UI_dwg_opts.SelectedValue   # Gets the 'Element' value
    
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
        
    def ext_dwg(self, name, sheet):
        if self.dwg_setup is None:
            options = DWGExportOptions()
        else:
            options = self.dwg_setup

        options.MergedViews = True
        sheets = List[ElementId]()
        sheets.Add(sheet.Id)

        if self.create_dwg_folder:
            dwg_folder = os.path.join(self.save_path, "DWG")
            if not os.path.exists(dwg_folder):
                os.makedirs(dwg_folder)   
        else:
            dwg_folder = self.save_path

        result = doc.Export(dwg_folder, name, sheets, options)
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
   
    def on_item_clicked(self, sender, e):
        """Handles Shift+Click selection for checkboxes in the ListBox."""
        listbox = self.UI_CheckboxList
        items = listbox.ItemsSource
        clicked_item = listbox.SelectedItem

        if not clicked_item:
            return

        # Get the index of the clicked item
        current_index = listbox.Items.IndexOf(clicked_item)

        # If Shift key is pressed, select a range of items and check/uncheck them
        if Input.Keyboard.IsKeyDown(Input.Key.LeftShift) or Input.Keyboard.IsKeyDown(Input.Key.RightShift):
            if self.last_selected_index is not None:
                # Sort the selected range to ensure the indices are in order
                start, end = sorted((self.last_selected_index, current_index))

                for i in range(start, end + 1):
                    items[i].IsChecked = True  # ✅ Check all checkboxes in the range

                # Refresh the ListBox to reflect the checkbox changes
                self.UI_CheckboxList.ItemsSource = None
                self.UI_CheckboxList.ItemsSource = self.sheet_items  # Reset the ItemsSource

            # Update last selected item
            self.last_selected_index = current_index
        else:
            # If Shift is not pressed, just select the item without checking
            self.last_selected_index = current_index  # Update last selected item
            clicked_item.IsChecked = not clicked_item.IsChecked  # Toggle checkbox when not Shift-clicking

    def save_button(self, sender, e):
            """Handles the Save button click event and opens the folder picker."""
            folder_dialog = FolderBrowserDialog()

            # Show the folder picker dialog
            result = folder_dialog.ShowDialog()

            if result == DialogResult.OK:
                # If a folder is selected, update the TextBox with the folder path
                selected_path = folder_dialog.SelectedPath
                self.UI_save_path.Text = selected_path  # Set the selected path to the TextBox

    @property
    def create_dwg_folder(self):
        return self.UI_create_dwg_folder.IsChecked

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