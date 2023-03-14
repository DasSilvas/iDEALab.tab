import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')

# find the path of ui.xaml
xamlfile = "C:\\Users\\hp\\AppData\\Roaming\\pyRevit-Master\\extensions\\ideaLAB.extension\\IdeaLAB.tab\\WIP.panel\\Import_classes.pushbutton\\teste2.xaml"

#script.get_bundle_file('teste2.xaml')

# import WPF creator and base Window
import wpf
from System import Windows

class MyWindow(Windows.Window):
    def __init__(self):
        wpf.LoadComponent(self, xamlfile)


# let's show the window (modal)
MyWindow().ShowDialog()