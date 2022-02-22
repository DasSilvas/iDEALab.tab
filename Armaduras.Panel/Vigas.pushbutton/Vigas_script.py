# -*- coding: utf-8 -*-
"""Modelacao das armaduras das vigas com base no codigo no Type Comments do elemento. Obter codigo a partir do excel que esta no Publico"""
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
import math

def flatten(t):
    return [item for sublist in t for item in sublist]
    
def ciclo(x):
    return range(len(x))

def meters(x):
    x = UnitUtils.ConvertFromInternalUnits(x , UnitTypeId.Meters)
    return x

def rebar_decode(rc):
    rdi = []
    temp = []
    rd = [rc[i].split(".") for i in range(len(rc))]
    
    for sub in rd:
        for item in sub:
            temp.append(item)
        rdi.append(temp)
        temp = []
    return rdi
    
def rebar_type(list , diameters, index):

    #Esta funcao vais buscar o elemento varao segundo a lista diameters

    output = []
    diametros = []
    rebar_type = [rebar for rebar in list if rebar.FamilyName == "Rebar Bar"]
    rebar_typename = [rebar.LookupParameter("Type Name").AsString() for rebar in rebar_type]

    for i in range(len(diameters)):
        for j in range(len(rebar_typename)):
            if rebar_typename[j] == diameters[i]:
                output.append(rebar_type[j])
                diametros.append(rebar_type[j].LookupParameter("Bar Diameter").AsDouble())
                
    if index == 0:
        return output
    elif index == 1:        
        return diametros
	
def rebar_hook(hooks):
    for hook in hooks:
        if hook.LookupParameter("Type Name").AsString() == "Stirrup/Tie Seismic - 135 deg.":
            k = hook
    return k
		    
def iu(x , unit):
    if unit == "m":
        x = UnitUtils.ConvertToInternalUnits(x , UnitTypeId.Meters)
    elif unit == "mm":
        x = UnitUtils.ConvertToInternalUnits(x , UnitTypeId.Millimeters)
    return x

def rebar_estribos(elementos, vector, estilo, hooks, curvas):
    return Rebar.CreateFromCurves(doc, RebarStyle.StirrupTie, estilo, hooks, hooks, elementos, vector, curvas, RebarHookOrientation.Right, RebarHookOrientation.Right, True, True)

def rebar_bars(elementos, vector, estilo, curvas):
    return Rebar.CreateFromCurves(doc, RebarStyle.Standard, estilo, None, None, elementos, vector, curvas, RebarHookOrientation.Right, RebarHookOrientation.Left, True, True)

class Ele_Rebar:

    def __init__(self, elemento):

        self.elemento = elemento
        self.type = doc.GetElement(elemento.GetTypeId())
        self.code = self.type.LookupParameter("Type Comments").AsString()
        self.largura = self.type.LookupParameter("b").AsDouble()
        self.altura = self.type.LookupParameter("h").AsDouble()
        self.cut_comprimento = elemento.LookupParameter("Cut Length").AsDouble()
        self.comprimento = elemento.LookupParameter("Length").AsDouble()
        self.origem = elemento.GetTransform().Origin
        self.vectorX = elemento.GetTransform().BasisX
        self.vectorY = elemento.GetTransform().BasisY
        self.vectorZ = elemento.GetTransform().BasisZ
        self.covertype = doc.GetElement(elemento.LookupParameter("Rebar Cover - Other Faces").AsElementId())
        self.cover_length = self.covertype.LookupParameter("Length").AsDouble()

    def barras(self, d_estribo):
        
        xi = -self.comprimento/2
        xf = -1*xi
        y_left = -self.largura/2 + self.cover_length + d_estribo
        y_right = -1*y_left
        z_top = self.altura/2 - self.cover_length - d_estribo
        z_bottom = -1*z_top

        x_vector_i = self.vectorX.Multiply(xi)
        x_vector_f = self.vectorX.Multiply(xf)
        y_vector_left = self.vectorY.Multiply(y_left)
        y_vector_right = self.vectorY.Multiply(y_right)
        z_vector_top = self.vectorZ.Multiply(z_top)
        z_vector_bottom = self.vectorZ.Multiply(z_bottom)

        # Pontos e linha para definir a barra inferior

        p_inf1 = self.origem.Add(x_vector_i).Add(y_vector_left).Add(z_vector_bottom)
        p_inf2 = self.origem.Add(x_vector_f).Add(y_vector_left).Add(z_vector_bottom)
        self.barras_bot = [Line.CreateBound(p_inf1 , p_inf2)]

        # Pontos e linha para definir a barra inferior

        p_top1 = self.origem.Add(x_vector_i).Add(y_vector_left).Add(z_vector_top)
        p_top2 = self.origem.Add(x_vector_f).Add(y_vector_left).Add(z_vector_top)
        self.barras_top = [Line.CreateBound(p_top1 , p_top2)]

    def estribos(self, cc, espacamento, indice):

        l1_est = []
        l2_est = []
        l3_est = []
        l4_est = []

        if indice == 0:
           x_est = -self.cut_comprimento/2
        elif indice == 1:
            x_est = -self.cut_comprimento/2 + cc + espacamento
        elif indice == 2:
            x_est = self.cut_comprimento/2 - cc
        y_est_left = -self.largura/2 + self.cover_length
        y_est_right = -1*y_est_left
        z_est_top = self.altura/2 - self.cover_length
        z_est_bottom = -1*z_est_top
    
        x_vector = self.vectorX.Multiply(x_est)
        y_vector_left = self.vectorY.Multiply(y_est_left)
        y_vector_right = self.vectorY.Multiply(y_est_right)
        z_vector_top = self.vectorZ.Multiply(z_est_top)
        z_vector_bottom = self.vectorZ.Multiply(z_est_bottom)
    
        p1_est = self.origem.Add(x_vector).Add(y_vector_right).Add(z_vector_top)
        p2_est = self.origem.Add(x_vector).Add(y_vector_right).Add(z_vector_bottom)
        p3_est = self.origem.Add(x_vector).Add(y_vector_left).Add(z_vector_bottom)
        p4_est = self.origem.Add(x_vector).Add(y_vector_left).Add(z_vector_top)
    
        l1_est.append(Line.CreateBound(p1_est , p2_est))
        l2_est.append(Line.CreateBound(p2_est , p3_est))
        l3_est.append(Line.CreateBound(p3_est , p4_est))
        l4_est.append(Line.CreateBound(p4_est , p1_est))
        lines = [l1_est , l2_est , l3_est , l4_est]
        self.estribo = flatten([list(x1) for x1 in zip(*lines)])

# Recipientes para descodificar o codigo do type comments

elementos = []
rebar_code = []
est = [] # Estribos
esp = [] # Espacamento
bs = [] # Barras superiores
nbs = [] # Nr bs
bi = [] # Barras inferiores
nbi = [] # Nr bi
nh = [] # Nr bh
bh = [] # Barras intermedias
est_bol = [] # Identificador se e uniforme
est_ext = [] # Estribos da extremidade
est_ext_esp = [] #Espacamento dos estribos de extremidade
est_cc = [] # comprimento critico
estribo_esp = [] # Distribuicao dos estribos
buffer = 2.1*3.2808

# Recipientes para a execucao dos estribos

estribo = []
v_x = [] # vector axial 
comp = [] # comprimento da distribuicao do estribo
spacing = [] # espacamento do estribo
estribo_diameter = [] # diametro do estribo

# Recipientes para execucao das barras

bar = []
elementos_bar = []
v_y = []
bar_diameter = []
bar_number = []
array = []

# Buscar os elementos necessarios atraves dos filtros

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc)
filtro = ElementCategoryFilter(BuiltInCategory.OST_StructuralFraming)
elements = collector.WherePasses(filtro).WhereElementIsNotElementType().ToElements()

collector_rebar = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rebar).WhereElementIsElementType()
rebars = collector_rebar.ToElements()

collector_hooks = FilteredElementCollector(doc).OfClass(RebarHookType).WhereElementIsElementType()
hooks = collector_hooks.ToElements()

# Elementos a armar

ele_rebar = [Ele_Rebar(element) for element in elements if element.LookupParameter("Comments").AsString() == "Armar"]

# Caracteristicas do elemento a armar 

#Descodificar a configuracao da armadura

for i in ciclo(ele_rebar):
    rebar_code.append(ele_rebar[i].code)

rebar_parameters = rebar_decode(rebar_code)

for sublista in rebar_parameters:

	est.append("Ø" + str(sublista[0]))
	esp.append(iu(int(sublista[1]), "mm"))
	bs.append("Ø" + str(sublista[2]))
	nbs.append(int(sublista[3]))
	bi.append("Ø" + str(sublista[4]))
	nbi.append(int(sublista[5]))
	nh.append(int(sublista[6]))
	bh.append("Ø" + str(sublista[7]))
	est_bol.append(str(sublista[8]))
	est_ext.append("Ø" + str(sublista[9]))
	est_ext_esp.append(iu(int(sublista[10]), "mm"))
	est_cc.append(iu(int(sublista[11]), "mm"))

# Preenchimento dos recipientes

for i in ciclo(ele_rebar):

    if est_bol[i] == "N":
    
        ele_rebar[i].estribos(est_cc[i], est_ext_esp[i], 0)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(ele_rebar[i].cut_comprimento)
        spacing.append(esp[i])
        estribo_diameter.append(est[i])
        
    elif est_bol[i] == "Y" and ele_rebar[i].cut_comprimento <= buffer*est_cc[i]:
    
        ele_rebar[i].estribos(est_cc[i], est_ext_esp[i], 0)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(ele_rebar[i].cut_comprimento)
        spacing.append(est_ext_esp[i])
        estribo_diameter.append(est_ext[i])
        
    else:

        ele_rebar[i].estribos(est_cc[i], est_ext_esp[i], 0)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(est_cc[i])
        spacing.append(est_ext_esp[i])
        estribo_diameter.append(est_ext[i])
        
        ele_rebar[i].estribos(est_cc[i], esp[i], 1)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(ele_rebar[i].cut_comprimento - 2*est_cc[i] - 2*esp[i])
        spacing.append(esp[i])
        estribo_diameter.append(est[i])
        
        ele_rebar[i].estribos(est_cc[i], esp[i], 2)
        estribo.append(ele_rebar[i].estribo)
        elementos.append(ele_rebar[i].elemento)
        v_x.append(ele_rebar[i].vectorX)
        comp.append(est_cc[i])
        spacing.append(est_ext_esp[i])
        estribo_diameter.append(est_ext[i])       
 
rebar_bar_diameter = rebar_type(rebars, est, 1) # Diametro dos estribos para as contas do array length e posicao da barra inicial

for i in ciclo(ele_rebar):

    ele_rebar[i].barras(rebar_bar_diameter[i])
    bar.append(ele_rebar[i].barras_bot)  
    elementos_bar.append(ele_rebar[i].elemento)
    v_y.append(ele_rebar[i].vectorY)
    bar_diameter.append(bi[i])
    bar_number.append(nbi[i])
    array.append(ele_rebar[i].largura -2*(ele_rebar[i].cover_length + rebar_bar_diameter[i]))
    bar.append(ele_rebar[i].barras_top)
    elementos_bar.append(ele_rebar[i].elemento)
    v_y.append(ele_rebar[i].vectorY)
    bar_diameter.append(bs[i])
    bar_number.append(nbs[i])
    array.append(ele_rebar[i].largura -2*(ele_rebar[i].cover_length + rebar_bar_diameter[i]))
  
rebar_stir = rebar_type(rebars , estribo_diameter, 0) # Diametro do estribos para a execucao da transacao
rebar_bar = rebar_type(rebars, bar_diameter, 0) # Diametro das barras para a execucao da transacao

print(estribo)
# Transcao com o REVIT para fazer as armaduras

t = Transaction(doc, "Armaduras")
t.Start()

#for i in ciclo(elementos):
	
 #   estribos = rebar_estribos(elementos[i], v_x[i], rebar_stir[i], rebar_hook(hooks), estribo[i])
  #  estribo_esp = estribos.GetShapeDrivenAccessor().SetLayoutAsMaximumSpacing(spacing[i], comp[i], True ,True ,True)

#for i in ciclo(elementos_bar):

 #   bars = rebar_bars(elementos_bar[i], v_y[i], rebar_bar[i], bar[i])
  #  bars_number = bars.GetShapeDrivenAccessor().SetLayoutAsFixedNumber(bar_number[i], array[i], True, True, True)
	
t.Commit()