# -*- coding: utf-8 -*-
""" Este ficheiro vai servir para fazer as classes para fazer as armaduras
Tentar usar parent class and child classes
"""

import clr
import Revit
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *

def flatten(t):
    return [item for sublist in t for item in sublist]

class RvtApiCategory:

    FUNDACAO = BuiltInCategory.OST_StructuralFoundation
    PILAR = BuiltInCategory.OST_StructuralColumns
    PAREDE = BuiltInCategory.OST_Walls
    VIGA = BuiltInCategory.OST_StructuralFraming
    REBAR = BuiltInCategory.OST_Rebar
    BAR_STANDART = RebarStyle.Standard
    BAR_STIRRUP = RebarStyle.StirrupTie

class RvtParameterName:

    HOOK_NAME_ESTRIBO = "Stirrup/Tie Seismic - 135 deg."
    HOOK_NAME_FUND = "50Ø"
    HOOK_ROTATION = "Hook Rotation At Start"

class RvtClasses:
    VIEW_TYPE = ViewFamilyType
    VIEW = View

class RvtApi:

    @staticmethod
    def get_elements_bycategory(doc, category, element_type=False):
        if element_type:
            elements = FilteredElementCollector(doc).WherePasses(ElementCategoryFilter(category)).WhereElementIsElementType().ToElements()
            return elements
        else:
            elements = FilteredElementCollector(doc).WherePasses(ElementCategoryFilter(category)).WhereElementIsNotElementType().ToElements()
            return elements

    @staticmethod
    def get_element_byclass(doc, classe, element_type=False):
        if element_type:
            e = FilteredElementCollector(doc).OfClass(classe).WhereElementIsElementType().ToElements()
            return e
        else:
            element = FilteredElementCollector(doc).OfClass(classe).WhereElementIsNotElementType().ToElements()
            return element

    @staticmethod
    def criar_vista(doc, vista, origem, x, y, zi, zf, vector_x, vector_y, vector_z, offset):

        t = Transform.Identity
        t.Origin = origem

        xbb_min = -x - offset
        ybb_min = -y - offset
        zzbb_min = -zi
        bb_min = XYZ(xbb_min, ybb_min, zzbb_min)

        xbb_max = x + offset
        ybb_max = y + offset
        zbb_max = zf    
        bb_max = XYZ(xbb_max, ybb_max, zbb_max)

        t.BasisX = vector_x
        t.BasisY = vector_y
        t.BasisZ = vector_z

        corte_aox = BoundingBoxXYZ()
        corte_aox.Transform = t
        corte_aox.Min = bb_min
        corte_aox.Max = bb_max

        section = ViewSection.CreateSection(doc, vista, corte_aox)

        return section

class Funk:

    @staticmethod
    def internal_units(x, unidade="mm"):
        if unidade == "m":
            x = UnitUtils.ConvertToInternalUnits(x , UnitTypeId.Meters)
        elif unidade == "mm":
            x = UnitUtils.ConvertToInternalUnits(x , UnitTypeId.Millimeters)
        elif unidade == "cm":
            x = UnitUtils.ConvertToInternalUnits(x , UnitTypeId.Centimeters)
        return x
    
    @staticmethod
    def get_element_cruza(elementos, doc, alvo, bbox="Min"):

        elemento_pares = []
        elemento_alvo = []
        elemento_impar = []

        for elemento in elementos:

            bbox_min = elemento.bbox.Min
            bbox_max = elemento.bbox.Max
            bbox_mid = XYZ(bbox_min.X, bbox_min.Y, bbox_min.Z + (bbox_max.Z - bbox_min.Z)/2 )

            if bbox == "Mid":

                outline = Outline(bbox_mid, bbox_max)

            else:

                outline = Outline(bbox_min, bbox_max)
            
            filter = BoundingBoxIntersectsFilter(outline)
            elemento_cruza = FilteredElementCollector(doc).OfCategory(alvo).WherePasses(filter).ToElements()

            if elemento_cruza:

                if alvo == RvtApiCategory.FUNDACAO: 

                    elemento_pares.append(elemento)
                    elemento_alvo.append(elemento_cruza[0])

                else:

                    elemento_pares.append(elemento)
                    elemento_alvo.append(elemento_cruza)

            else:
            
                elemento_impar.append(elemento)

        return elemento_alvo, elemento_pares, elemento_impar

class Element:

    def __init__(self, doc, elemento):

        self.elemento = elemento
        self.nome = elemento.Name
        self.type = doc.GetElement(elemento.GetTypeId())
        self.code = self.type.LookupParameter("Type Comments").AsString()
        self.origem = elemento.GetTransform().Origin
        self.vectorX = elemento.GetTransform().BasisX
        self.vectorY = elemento.GetTransform().BasisY
        self.vectorZ = elemento.GetTransform().BasisZ
        self.bbox = elemento.get_BoundingBox(None)
        
    def create_dimensions(self, doc, vista, ponto1, ponto2, offset, x_lock=False, y_lock=False):
        
        if x_lock:

            x = self.b/2 + Funk.internal_units(offset, "mm")
            y_left = ponto1
            y_right = ponto2

            vector_x = self.vectorX.Multiply(x)
            vector_yleft = self.vectorY.Multiply(y_left)
            vector_yright = self.vectorY.Multiply(y_right)

            p1 = self.origem.Add(vector_x).Add(vector_yleft)
            p2 = self.origem.Add(vector_x).Add(vector_yright)

            line1 = Line.CreateBound(p1, p2)

            reference = ReferenceArray()
            linha1 = doc.Create.NewDetailCurve(vista, line1)
            curva1 = linha1.GeometryCurve
            reference.Append(curva1.GetEndPointReference(0))
            reference.Append(curva1.GetEndPointReference(1))
            doc.Create.NewDimension(vista, line1, reference)
        
        elif y_lock:

            y = self.h/2 + Funk.internal_units(offset, "mm")
            x_left = ponto1
            x_right = ponto2

            vector_y = self.vectorY.Multiply(y)
            vector_xleft = self.vectorX.Multiply(x_left)
            vector_xright = self.vectorX.Multiply(x_right)

            p3 = self.origem.Add(vector_xleft).Add(vector_y)
            p4 = self.origem.Add(vector_xright).Add(vector_y)

            line2 = Line.CreateBound(p3, p4)

            reference = ReferenceArray()
            linha2 = doc.Create.NewDetailCurve(vista, line2)
            curva2 = linha2.GeometryCurve
            reference.Append(curva2.GetEndPointReference(0))
            reference.Append(curva2.GetEndPointReference(1))
            doc.Create.NewDimension(vista, line2, reference)
        
class Viga(Element):

    def __init__(self, doc, elemento):

        Element.__init__(self, doc, elemento)
        self.largura = self.type.LookupParameter("b").AsDouble()
        self.altura = self.type.LookupParameter("h").AsDouble()
        self.cut_comprimento = elemento.LookupParameter("Cut Length").AsDouble()
        self.comprimento = elemento.LookupParameter("Length").AsDouble()
        self.covertype = doc.GetElement(elemento.LookupParameter("Rebar Cover - Other Faces").AsElementId())
        self.cover_length = self.covertype.LookupParameter("Length").AsDouble()
        rdc = self.code.split(".")
        self.diametro_estribo = "Ø" + str(rdc[0])
        self.estribo_espacamento = Funk.internal_units(int(rdc[1]))
        self.bs_diametro = "Ø" + str(rdc[2])
        self.nr_bs = int(rdc[3])
        self.bi_diametro = "Ø" + str(rdc[4])
        self.nr_bi = int(rdc[5])
        self.nr_bl = int(rdc[6])
        self.bl_diametro = "Ø" + str(rdc[7])
        self.bol = str(rdc[8])
        self.est_ext_diametro = "Ø" + str(rdc[9])
        self.est_ext_espacamento = Funk.internal_units(int(rdc[10]))
        self.cc = Funk.internal_units(int(rdc[11]))
        self.cnc = self.cut_comprimento - 2*(self.cc + self.estribo_espacamento)

    def array_length(self, d_estribo):
        return self.largura - 2*(self.cover_length + d_estribo)

    def sidearray_length(self, d_estribo):
        return self.altura - 2*(self.cover_length + d_estribo)

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

        p_side1 = self.origem.Add(x_vector_i).Add(y_vector_right).Add(z_vector_bottom)
        p_side2 = self.origem.Add(x_vector_f).Add(y_vector_right).Add(z_vector_bottom)
        self.barras_side = [Line.CreateBound(p_side1 , p_side2)]

    def estribos(self, indice):

        l1_est = []
        l2_est = []
        l3_est = []
        l4_est = []

        if indice == 0:
           x_est = -self.cut_comprimento/2
        elif indice == 1:
            x_est = -self.cut_comprimento/2 + self.cc + self.estribo_espacamento
        elif indice == 2:
            x_est = self.cut_comprimento/2 - self.cc
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

    def criar_vista(self, doc, vista, tipo, offset):

        t = Transform.Identity
        t.Origin = self.origem

        if tipo == 'Alcado':
            
            bb_min = XYZ(-self.altura - offset, -self.comprimento/2 - offset, 0)
            bb_max = XYZ(self.altura + offset, self.comprimento/2 + offset, self.largura/2)

            t.BasisX = self.vectorZ
            t.BasisY = self.vectorX
            t.BasisZ = self.vectorY

        elif tipo == 'Seccao A':

            bb_min = XYZ(-self.largura/2 - offset, -self.altura/2 - offset, -(self.cut_comprimento - self.cc)/2)
            bb_max = XYZ(self.largura/2 + offset, self.altura/2 + offset, -(self.cut_comprimento - self.cc)/2 + self.largura/2)

            t.BasisX = self.vectorY
            t.BasisY = self.vectorZ
            t.BasisZ = self.vectorX
    
        elif tipo == 'Seccao B':

            bb_min = XYZ(-self.largura/2 - offset, -self.altura/2 - offset, 0)
            bb_max = XYZ(self.largura/2 + offset, self.altura/2 + offset, self.largura/2)

            t.BasisX = self.vectorY
            t.BasisY = self.vectorZ
            t.BasisZ = self.vectorX

        corte_aox = BoundingBoxXYZ()
        corte_aox.Transform = t
        corte_aox.Min = bb_min
        corte_aox.Max = bb_max

        section = ViewSection.CreateSection(doc, vista, corte_aox)

        return section
          
class Pilar(Element):

    def __init__(self, doc, elemento):
        Element.__init__(self, doc, elemento)
        self.b = self.type.LookupParameter("b").AsDouble()
        self.h = self.type.LookupParameter("h").AsDouble()
        self.cmp = elemento.get_Parameter(BuiltInParameter.INSTANCE_LENGTH_PARAM).AsDouble()
        self.comprimento = elemento.LookupParameter("Length").AsDouble()
        self.covertype = doc.GetElement(elemento.LookupParameter("Rebar Cover - Other Faces").AsElementId())
        self.cover_length = self.covertype.LookupParameter("Length").AsDouble()
        rdc = self.code.split(".")
        self.diametro_estribo = "Ø" + str(rdc[0])
        self.estribo_espacamento = Funk.internal_units(int(rdc[1]))
        self.b_diametro = "Ø" + str(rdc[2])
        self.b_varao = Funk.internal_units(int(rdc[2]))
        self.nr_b = int(rdc[3])
        self.nr_h = int(rdc[4])
        self.bol = str(rdc[5])
        self.est_ext_diametro = "Ø" + str(rdc[6])
        self.est_ext_espacamento = Funk.internal_units(int(rdc[7]))
        self.cc = Funk.internal_units(int(rdc[8]))
        self.cnc = self.cmp - 2*(self.cc + self.estribo_espacamento)
        lvl = doc.GetElement(self.elemento.LookupParameter("Base Level").AsElementId())
        base_offset = self.elemento.LookupParameter("Base Offset").AsDouble()
        base_lvl = lvl.LookupParameter("Elevation").AsDouble()
        self.z = base_lvl + base_offset

    def b_array_length(self, d_estribo):
        return self.b - 2*(self.cover_length + d_estribo)

    def h_array_length(self, d_estribo):
        return self.h - 2*(self.cover_length + d_estribo)

    def barras(self, d_estribo):
        
        xi = self.z
        xf = self.cmp + xi
        y_left = -self.b/2 + self.cover_length + d_estribo
        y_right = -1*y_left
        z_top = self.h/2 - self.cover_length - d_estribo
        z_bottom = -1*z_top

        z_vector_i = self.vectorZ.Multiply(xi)
        z_vector_f = self.vectorZ.Multiply(xf)
        x_vector_left = self.vectorX.Multiply(y_left)
        x_vector_right = self.vectorX.Multiply(y_right)
        y_vector_top = self.vectorY.Multiply(z_top)
        y_vector_bottom = self.vectorY.Multiply(z_bottom)

        # Pontos e linha para definir a barra inferior

        p_inf1 = self.origem.Add(z_vector_i).Add(x_vector_left).Add(y_vector_bottom)
        p_inf2 = self.origem.Add(z_vector_f).Add(x_vector_left).Add(y_vector_bottom)
        self.barras_bot = [Line.CreateBound(p_inf1 , p_inf2)]

        # Pontos e linha para definir a barra inferior

        p_top1 = self.origem.Add(z_vector_i).Add(x_vector_left).Add(y_vector_top)
        p_top2 = self.origem.Add(z_vector_f).Add(x_vector_left).Add(y_vector_top)
        self.barras_top = [Line.CreateBound(p_top1 , p_top2)]

        p_side1 = self.origem.Add(z_vector_i).Add(x_vector_right).Add(y_vector_bottom)
        p_side2 = self.origem.Add(z_vector_f).Add(x_vector_right).Add(y_vector_bottom)
        self.barras_side = [Line.CreateBound(p_side1 , p_side2)]

    def barras_fund(self, d_estribo, altura=0, recobrimento=0.50, varao_sapata=0, varao_pilar=0):
        
        xi = self.z
        xi1 = self.z - (altura - recobrimento - varao_sapata)
        xi2 = self.z - (altura - recobrimento - varao_sapata - 2*varao_pilar)
        xi3 = self.z - (altura - recobrimento - varao_sapata - 3*varao_pilar)
        xi4 = self.z - (altura - recobrimento - varao_sapata - 4*varao_pilar)
        xf = self.cmp + xi
        y_left = -self.b/2 + self.cover_length + d_estribo
        y_right = -1*y_left
        z_top = self.h/2 - self.cover_length - d_estribo
        z_bottom = -1*z_top

        #Face 1 do pilar vai ate ao maximo
        z_vector_i1 = self.vectorZ.Multiply(xi1)
        z_vector_i2 = self.vectorZ.Multiply(xi2)
        z_vector_i3 = self.vectorZ.Multiply(xi3)
        z_vector_i4 = self.vectorZ.Multiply(xi4)
        z_vector_f = self.vectorZ.Multiply(xf)
        x_vector_left = self.vectorX.Multiply(y_left)
        x_vector_right = self.vectorX.Multiply(y_right)
        y_vector_top = self.vectorY.Multiply(z_top)
        y_vector_bottom = self.vectorY.Multiply(z_bottom)

        #Linhas para fazer a face 1

        p_inf1 = self.origem.Add(z_vector_i1).Add(x_vector_left).Add(y_vector_bottom)
        p_inf2 = self.origem.Add(z_vector_f).Add(x_vector_left).Add(y_vector_bottom)
        self.barras_f1 = [Line.CreateBound(p_inf1 , p_inf2)]

        #Linhas para fazer a face 2

        p_top1 = self.origem.Add(z_vector_i2).Add(x_vector_left).Add(y_vector_top)
        p_top2 = self.origem.Add(z_vector_f).Add(x_vector_left).Add(y_vector_top)
        self.barras_f2 = [Line.CreateBound(p_top1 , p_top2)]

        #Linhas para fazer a face 3

        p_side1 = self.origem.Add(z_vector_i3).Add(x_vector_right).Add(y_vector_bottom)
        p_side2 = self.origem.Add(z_vector_f).Add(x_vector_right).Add(y_vector_bottom)
        self.barras_f3 = [Line.CreateBound(p_side1 , p_side2)]

        #Linhas para fazer a face 4

        p_side3 = self.origem.Add(z_vector_i4).Add(x_vector_left).Add(y_vector_bottom)
        p_side4 = self.origem.Add(z_vector_f).Add(x_vector_left).Add(y_vector_bottom)
        self.barras_f4 = [Line.CreateBound(p_side3 , p_side4)]

    def estribos(self, indice, altura=0, varao_sapata=0, n=0, varao_pilar_b=0, m=0, varao_pilar_h=0, altura_viga=0):

        l1_est = []
        l2_est = []
        l3_est = []
        l4_est = []

        if indice == 0:
           z_est = self.z - (altura - 2*varao_sapata - n*varao_pilar_b - (m*varao_pilar_h))
        elif indice == 1:
            z_est = self.z + self.cc + self.estribo_espacamento
        elif indice == 2:
            z_est = self.z + self.cmp - (self.cc + altura_viga)
        x_est_left = -self.b/2 + self.cover_length
        x_est_right = -1*x_est_left
        y_est_top = self.h/2 - self.cover_length
        y_est_bottom = -1*y_est_top
    
        z_vector = self.vectorZ.Multiply(z_est)
        x_vector_left = self.vectorX.Multiply(x_est_left)
        x_vector_right = self.vectorX.Multiply(x_est_right)
        y_vector_top = self.vectorY.Multiply(y_est_top)
        y_vector_bottom = self.vectorY.Multiply(y_est_bottom)
    
        p1_est = self.origem.Add(z_vector).Add(x_vector_right).Add(y_vector_top)
        p2_est = self.origem.Add(z_vector).Add(x_vector_right).Add(y_vector_bottom)
        p3_est = self.origem.Add(z_vector).Add(x_vector_left).Add(y_vector_bottom)
        p4_est = self.origem.Add(z_vector).Add(x_vector_left).Add(y_vector_top)
    
        l1_est.append(Line.CreateBound(p1_est , p2_est))
        l2_est.append(Line.CreateBound(p2_est , p3_est))
        l3_est.append(Line.CreateBound(p3_est , p4_est))
        l4_est.append(Line.CreateBound(p4_est , p1_est))
        lines = [l1_est , l2_est , l3_est , l4_est]
        self.estribo = flatten([list(x1) for x1 in zip(*lines)])

    def cc_fund(self,altura=0, varao_sapata=0, n=0, varao_pilar_b=0, m=0, varao_pilar_h=0):
        self.cc_sapata = self.cc + (altura - 2*varao_sapata - n*varao_pilar_b - (m*varao_pilar_h))
        return self.cc_sapata

    def cc_viga(self, altura_viga):
        self.cc_viga = self.cc + altura_viga
        return self.cc_viga

    def cnc_viga(self, altura_viga):
        self.cnc_viga = self.cnc - altura_viga
        return self.cnc_viga

    def criar_vista(self, doc, vista, tipo, offset):

        t = Transform.Identity
        t.Origin = self.origem

        if tipo == 'Alcado A':
            
            bb_min = XYZ(-self.comprimento/2 - offset, -self.b - offset, 0)
            bb_max = XYZ(self.comprimento + offset, self.b + offset, self.h/2)

            t.BasisX = self.vectorZ
            t.BasisY = self.vectorX
            t.BasisZ = self.vectorY

        if tipo == 'Alcado B':
            
            bb_min = XYZ(-self.h - offset, -self.comprimento/2 - offset, 0)
            bb_max = XYZ(self.h + offset, self.comprimento + offset, self.b/2)

            t.BasisX = self.vectorY
            t.BasisY = self.vectorZ
            t.BasisZ = self.vectorX

        elif tipo == 'Seccao A':

            bb_min = XYZ(-self.b/2 - offset, -self.h/2 - offset, 0)
            bb_max = XYZ(self.b/2 + offset, self.h/2 + offset, self.b/2)

            t.BasisX = self.vectorX
            t.BasisY = self.vectorY
            t.BasisZ = self.vectorZ
    
        elif tipo == 'Seccao B':

            bb_min = XYZ(-self.b/2 - offset, -self.h/2 - offset, (self.comprimento - self.cnc)/2)
            bb_max = XYZ(self.b/2 + offset, self.h/2 + offset, (self.comprimento - self.cnc)/2 + self.b)

            t.BasisX = self.vectorX
            t.BasisY = self.vectorY
            t.BasisZ = self.vectorZ

        corte_aox = BoundingBoxXYZ()
        corte_aox.Transform = t
        corte_aox.Min = bb_min
        corte_aox.Max = bb_max

        section = ViewSection.CreateSection(doc, vista, corte_aox)

        return section

class Sapata(Element):
        
    def __init__(self, doc, elemento):
        # Este parametro serve para distinguir das fundacoes que sao Isolated ou se sao modeladas como Slabs
        self.elemento = elemento
        self.doc = doc
        floor = elemento.get_Parameter(BuiltInParameter.FLOOR_PARAM_IS_STRUCTURAL)

        if floor is not None:

            self.altura = elemento.LookupParameter("Thickness").AsDouble()
            self.largura = elemento.LookupParameter("Width").AsDouble()
            self.comprimento = elemento.LookupParameter("Length").AsDouble()

        else:

            Element.__init__(self, doc, elemento)
            self.largura = self.type.LookupParameter("Width").AsDouble()
            self.altura = self.type.LookupParameter("Thickness").AsDouble()
            self.comprimento = self.type.LookupParameter("Length").AsDouble()
            self.top_covertype = doc.GetElement(elemento.LookupParameter("Rebar Cover - Top Face").AsElementId())
            self.top_cover_length = self.top_covertype.LookupParameter("Length").AsDouble()
            self.bot_covertype = doc.GetElement(elemento.LookupParameter("Rebar Cover - Bottom Face").AsElementId())
            self.bot_cover_length = self.bot_covertype.LookupParameter("Length").AsDouble()
            rdc = self.code.split(".")
            self.diametro_top_bar = "Ø" + str(rdc[0])
            self.top_varao = Funk.internal_units(int(rdc[0]))
            self.top_bar_espacamento = Funk.internal_units(int(rdc[1]))
            self.diametro_bot_bar = "Ø" + str(rdc[2])
            self.bot_varao = Funk.internal_units(int(rdc[2]))
            self.bot_bar_espacamento = Funk.internal_units(int(rdc[3]))

    def barras_bottom1(self):
        
        l1_est = []
        l2_est = []
        l3_est = []
        l4_est = []

        x_est = -self.largura/2 + self.top_cover_length
        y_est_left = -self.comprimento/2 + self.top_cover_length
        y_est_right = -1*y_est_left
        z_est_top = -self.altura/2 + 5*self.bot_varao
        z_est_bottom = -self.altura + self.bot_cover_length
    
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
        lines = [l1_est , l2_est , l3_est]
        self.bot_bar1 = flatten([list(x1) for x1 in zip(*lines)])

    def bot1_array_length(self):
        return self.largura - 2*self.top_cover_length

    def barras_bottom2(self):
        
        l1_est = []
        l2_est = []
        l3_est = []
        l4_est = []

        x_est_left = -self.largura/2 + self.top_cover_length
        x_est_right = -1*x_est_left
        y_est = -self.comprimento/2 + self.top_cover_length + 3*self.bot_varao
        z_est_top = -self.altura/2 + 5*self.bot_varao
        z_est_bottom = -self.altura + self.bot_cover_length + 1.5*self.bot_varao
    
        x_vector_left = self.vectorX.Multiply(x_est_left)
        x_vector_right = self.vectorX.Multiply(x_est_right)
        y_vector = self.vectorY.Multiply(y_est)
        z_vector_top = self.vectorZ.Multiply(z_est_top)
        z_vector_bottom = self.vectorZ.Multiply(z_est_bottom)
    
        p1_est = self.origem.Add(x_vector_right).Add(y_vector).Add(z_vector_top)
        p2_est = self.origem.Add(x_vector_right).Add(y_vector).Add(z_vector_bottom)
        p3_est = self.origem.Add(x_vector_left).Add(y_vector).Add(z_vector_bottom)
        p4_est = self.origem.Add(x_vector_left).Add(y_vector).Add(z_vector_top)
    
        l1_est.append(Line.CreateBound(p1_est , p2_est))
        l2_est.append(Line.CreateBound(p2_est , p3_est))
        l3_est.append(Line.CreateBound(p3_est , p4_est))
        l4_est.append(Line.CreateBound(p4_est , p1_est))
        lines = [l1_est , l2_est , l3_est]
        self.bot_bar2 = flatten([list(x1) for x1 in zip(*lines)])

    def bot2_array_length(self):
        return self.comprimento - 2*(self.top_cover_length + 3*self.bot_varao)

    def barras_top1(self):
        
        l1_est = []
        l2_est = []
        l3_est = []
        l4_est = []

        x_est = -self.largura/2 + self.top_cover_length + 1.5*self.bot_varao
        y_est_left = -self.comprimento/2 + self.top_cover_length + 1.5*self.bot_varao
        y_est_right = -1*y_est_left
        z_est_top = -self.top_cover_length
        z_est_bottom = -(self.altura/2) - 5*self.bot_varao
    
        x_vector = self.vectorX.Multiply(x_est)
        y_vector_left = self.vectorY.Multiply(y_est_left)
        y_vector_right = self.vectorY.Multiply(y_est_right)
        z_vector_top = self.vectorZ.Multiply(z_est_top)
        z_vector_bottom = self.vectorZ.Multiply(z_est_bottom)
    
        p1_est = self.origem.Add(x_vector).Add(y_vector_right).Add(z_vector_bottom)
        p2_est = self.origem.Add(x_vector).Add(y_vector_right).Add(z_vector_top)
        p3_est = self.origem.Add(x_vector).Add(y_vector_left).Add(z_vector_top)
        p4_est = self.origem.Add(x_vector).Add(y_vector_left).Add(z_vector_bottom)
    
        l1_est.append(Line.CreateBound(p1_est , p2_est))
        l2_est.append(Line.CreateBound(p2_est , p3_est))
        l3_est.append(Line.CreateBound(p3_est , p4_est))
        l4_est.append(Line.CreateBound(p4_est , p1_est))
        lines = [l1_est , l2_est , l3_est]
        self.top_bar1 = flatten([list(x1) for x1 in zip(*lines)])

    def top1_array_length(self):
        return self.largura - 2*(self.top_cover_length + 1.5*self.bot_varao)

    def barras_top2(self):
        
        l1_est = []
        l2_est = []
        l3_est = []
        l4_est = []

        x_est_left = -self.largura/2 + self.top_cover_length + 1.5*self.bot_varao
        x_est_right = -1*x_est_left
        y_est = -self.comprimento/2 + self.top_cover_length + 1.5*(1.5*self.bot_varao + self.top_varao)
        z_est_top = -self.top_cover_length - 1.5*self.top_varao
        z_est_bottom = -self.altura/2 - 5*self.bot_varao
    
        x_vector_left = self.vectorX.Multiply(x_est_left)
        x_vector_right = self.vectorX.Multiply(x_est_right)
        y_vector = self.vectorY.Multiply(y_est)
        z_vector_top = self.vectorZ.Multiply(z_est_top)
        z_vector_bottom = self.vectorZ.Multiply(z_est_bottom)
    
        p1_est = self.origem.Add(x_vector_right).Add(y_vector).Add(z_vector_bottom)
        p2_est = self.origem.Add(x_vector_right).Add(y_vector).Add(z_vector_top)
        p3_est = self.origem.Add(x_vector_left).Add(y_vector).Add(z_vector_top)
        p4_est = self.origem.Add(x_vector_left).Add(y_vector).Add(z_vector_bottom)
    
        l1_est.append(Line.CreateBound(p1_est , p2_est))
        l2_est.append(Line.CreateBound(p2_est , p3_est))
        l3_est.append(Line.CreateBound(p3_est , p4_est))
        l4_est.append(Line.CreateBound(p4_est , p1_est))
        lines = [l1_est , l2_est , l3_est]
        self.top_bar2 = flatten([list(x1) for x1 in zip(*lines)])

    def top2_array_length(self):
        return self.comprimento - 2*(self.top_cover_length + 1.5*(self.bot_varao + 1.5*self.top_varao))

    def barras_lateral1(self):

        x_est_left = -self.largura/2 + self.top_cover_length
        x_est_right = -1*x_est_left
        y_est_left = -self.comprimento/2 + self.top_cover_length + self.bot_varao + self.top_varao
        y_est_right = -1*y_est_left
        z_est_top = -self.altura/2 + 5*self.bot_varao - self.top_varao/2
        z_est_bottom = -self.altura/2 - 5*self.bot_varao + self.top_varao/2
    
        x_vector_left = self.vectorX.Multiply(x_est_left)
        x_vector_right = self.vectorX.Multiply(x_est_right)
        y_vector_left = self.vectorY.Multiply(y_est_left)
        y_vector_right = self.vectorY.Multiply(y_est_right)
        z_vector_top = self.vectorZ.Multiply(z_est_top)
        z_vector_bottom = self.vectorZ.Multiply(z_est_bottom)
    
        p1_est = self.origem.Add(x_vector_right).Add(y_vector_left).Add(z_vector_bottom)
        p2_est = self.origem.Add(x_vector_left).Add(y_vector_left).Add(z_vector_bottom)
        p3_est = self.origem.Add(x_vector_right).Add(y_vector_left).Add(z_vector_top)
        p4_est = self.origem.Add(x_vector_left).Add(y_vector_left).Add(z_vector_top)

        p5_est = self.origem.Add(x_vector_right).Add(y_vector_right).Add(z_vector_bottom)
        p6_est = self.origem.Add(x_vector_left).Add(y_vector_right).Add(z_vector_bottom)
        p7_est = self.origem.Add(x_vector_right).Add(y_vector_right).Add(z_vector_top)
        p8_est = self.origem.Add(x_vector_left).Add(y_vector_right).Add(z_vector_top)
    
        self.lateral_bot1 = [Line.CreateBound(p1_est , p2_est)]
        self.lateral_bot2 = [Line.CreateBound(p3_est , p4_est)]

        self.lateral_bot3 = [Line.CreateBound(p5_est , p6_est)]
        self.lateral_bot4 = [Line.CreateBound(p7_est , p8_est)]

    def barras_lateral2(self):

        x_est_left = -self.largura/2 + self.top_cover_length + self.bot_varao + self.top_varao
        x_est_right = -1*x_est_left
        y_est_left = -self.comprimento/2 + self.top_cover_length + self.bot_varao + self.top_varao
        y_est_right = -1*y_est_left
        z_est_top = -self.altura/2 + 5*self.bot_varao - 3*self.top_varao/2
        z_est_bottom = -self.altura/2 - 5*self.bot_varao + 3*self.top_varao/2
    
        x_vector_left = self.vectorX.Multiply(x_est_left)
        x_vector_right = self.vectorX.Multiply(x_est_right)
        y_vector_left = self.vectorY.Multiply(y_est_left)
        y_vector_right = self.vectorY.Multiply(y_est_right)
        z_vector_top = self.vectorZ.Multiply(z_est_top)
        z_vector_bottom = self.vectorZ.Multiply(z_est_bottom)
    
        p1_est = self.origem.Add(x_vector_left).Add(y_vector_right).Add(z_vector_bottom)
        p2_est = self.origem.Add(x_vector_left).Add(y_vector_left).Add(z_vector_bottom)
        p3_est = self.origem.Add(x_vector_left).Add(y_vector_right).Add(z_vector_top)
        p4_est = self.origem.Add(x_vector_left).Add(y_vector_left).Add(z_vector_top)

        p5_est = self.origem.Add(x_vector_right).Add(y_vector_right).Add(z_vector_bottom)
        p6_est = self.origem.Add(x_vector_right).Add(y_vector_left).Add(z_vector_bottom)
        p7_est = self.origem.Add(x_vector_right).Add(y_vector_right).Add(z_vector_top)
        p8_est = self.origem.Add(x_vector_right).Add(y_vector_left).Add(z_vector_top)
    
        self.lateral_bot5 = [Line.CreateBound(p1_est , p2_est)]
        self.lateral_bot6 = [Line.CreateBound(p3_est , p4_est)]

        self.lateral_bot7 = [Line.CreateBound(p5_est , p6_est)]
        self.lateral_bot8 = [Line.CreateBound(p7_est , p8_est)]

    def criar_vistas(self, vista, offset, template):

        prof = Funk.internal_units(0.15, "m")

        planta = RvtApi.criar_vista(self.doc, vista, self.origem, self.largura, self.comprimento, prof, self.altura/2, self.vectorX, self.vectorY.Negate(), self.vectorZ.Negate(), offset)
        planta.Name = "1A - Planta {}".format(self.nome)
        planta.LookupParameter("Title on Sheet").Set('Planta {}'.format(self.nome))
        planta.LookupParameter("View Template").Set(template)

        corte_a = RvtApi.criar_vista(self.doc, vista, self.origem, self.altura, self.largura, 0, prof, self.vectorZ, self.vectorX, self.vectorY, offset)
        corte_a.Name = "1B - {} Corte A".format(self.nome)
        corte_a.LookupParameter("Title on Sheet").Set('{} Corte A'.format(self.nome))
        corte_a.LookupParameter("View Template").Set(template)

        corte_b = RvtApi.criar_vista(self.doc, vista, self.origem, self.comprimento, self.altura, 0, prof, self.vectorY, self.vectorZ, self.vectorX, offset)
        corte_b.Name = "1C - {} Corte B".format(self.nome)
        corte_b.LookupParameter("Title on Sheet").Set('{} Corte B'.format(self.nome))
        corte_b.LookupParameter("View Template").Set(template)