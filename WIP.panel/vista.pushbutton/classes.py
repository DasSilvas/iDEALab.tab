# -*- coding: utf-8 -*-
""" Este ficheiro vai servir para fazer as classes para fazer as armaduras
Tentar usar parent class and child classes
"""

import clr
import Revit
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

def flatten(t):
    return [item for sublist in t for item in sublist]

class RvtApiCategory:

    FUNDACAO = BuiltInCategory.OST_StructuralFoundation
    PILAR = BuiltInCategory.OST_StructuralColumns
    FUNDACAO = BuiltInCategory.OST_StructuralFoundation
    VIGA = BuiltInCategory.OST_StructuralFraming
    REBAR = BuiltInCategory.OST_Rebar

class RvtParameterName:

    HOOK_NAME_ESTRIBO = "Stirrup/Tie Seismic - 135 deg."
    HOOK_NAME_FUND = "50Ø"
    HOOK_ROTATION = "Hook Rotation At Start"

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
        self.type = doc.GetElement(elemento.GetTypeId())
        self.code = self.type.LookupParameter("Type Comments").AsString()
        self.origem = elemento.GetTransform().Origin
        self.vectorX = elemento.GetTransform().BasisX
        self.vectorY = elemento.GetTransform().BasisY
        self.vectorZ = elemento.GetTransform().BasisZ
        self.bbox = elemento.get_BoundingBox(None)
        self.name = elemento.Name
    
class Viga(Element):

    def __init__(self, doc, elemento):

        Element.__init__(self, doc, elemento)
        self.nome = self.elemento.Name
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
            bb_max = XYZ(self.largura/2 + offset, self.altura/2 + offset, self.largura/2)

            t.BasisX = self.vectorY
            t.BasisY = self.vectorZ
            t.BasisZ = self.vectorX
    
        elif tipo == 'Seccao B':

            bb_min = XYZ(-self.largura/2 - offset, -self.altura/2 - offset, 0)
            bb_max = XYZ(self.largura/2 + offset, self.altura/2 + offset, self.largura/2)

            t.BasisX = self.vectorY
            t.BasisY = self.vectorZ
            t.BasisZ = self.vectorX

        section_box = BoundingBoxXYZ()
        section_box.Transform = t
        section_box.Min = bb_min
        section_box.Max = bb_max

        section = ViewSection.CreateSection(doc, vista, section_box)

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
        base_offset = self.elemento.LookupParameter("Base offset").AsDouble()
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

class Sapata(Element):
        
    def __init__(self, doc, elemento):

        # Este parametro serve para distinguir das fundacoes que sao Isolated ou se sao modeladas como Slabs
        self.elemento = elemento
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
