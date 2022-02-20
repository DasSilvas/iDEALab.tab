
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

import string

def numering(list, v):
    return range(v, v+len(list)+1)
    
def flatten(t):
    return [item for sublist in t for item in sublist]

doc = __revit__.ActiveUIDocument.Document

#Buscar os elements em questao do modelo revit

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(BuiltInCategory.OST_Grids)
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()


#Variaveis

h_point = [] #pontos das grids horizontais
horizontal = [] #grids horizontais
v_point = []    #pontos das grids vericais
vertical = []   #grids verticais
h_lettering = [] #letras para as grids horizontais

#Identificacao das grids horizontais e verticais

for element in elements:
    if round(element.Curve.Direction.X) != 0:
        h_point.append(element.Curve.Origin.Y)
        horizontal.append(element)
    if round(element.Curve.Direction.Y) != 0:
        v_point.append(element.Curve.Origin.X)
        vertical.append(element)

#Organizar as grids de forma ordenada
#Horizontais estao ordenadas de forma decrescente
#verticais estao ordenadas de forma crescente

horizontal_sorted = [y for _,y in sorted(zip(h_point, horizontal), reverse = True)]
vertical_sorted = [x for _,x in sorted(zip(v_point, vertical))]

#Geracao de alfabeto

l = string.ascii_uppercase

#Ranges 

h_numering = numering(horizontal, 100)
v_numering = numering(vertical, 200)
h_renumering = numering(horizontal , 0)
v_renumering = numering(vertical , 1)

for i in range(len(horizontal)):
    h_lettering.append(l[h_renumering[i]])

#Buscar os parametros para os alterar

h_name = flatten([h.GetParameters("Name") for h in horizontal_sorted])
v_name = flatten([v.GetParameters("Name") for v in vertical_sorted])

tg = TransactionGroup(doc, "Reorder and Rename")
tg.Start()

t = Transaction(doc, "Reorder")
t.Start()

for i in range(len(horizontal)):
    h_name[i].Set(str(h_numering[i]))

for i in range(len(vertical)):
    v_name[i].Set(str(v_numering[i]))

t.Commit()    
 
t = Transaction(doc, 'Rename')
t.Start()

for i in range(len(horizontal)):
    h_name[i].Set(str(h_lettering[i]))

for i in range(len(vertical)):
    v_name[i].Set(str(v_renumering[i]))   

t.Commit()
tg.Assimilate()






