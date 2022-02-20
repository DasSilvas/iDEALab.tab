# -*- coding: utf-8 -*-
""" Este ficheiro vai servir para fazer as classes para fazer as armaduras
Tentar usar parent class and child classes
"""

import clr
import Revit
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import UnitUtils, UnitTypeId

class Funk:

    @staticmethod
    def internal_units(x, unidade="mm"):
        if unidade == "m":
            x = UnitUtils.ConvertToInternalUnits(x , UnitTypeId.Meters)
        elif unidade == "mm":
            x = UnitUtils.ConvertToInternalUnits(x , UnitTypeId.Millimeters)
        return x

class Element:

    def __init__(self, doc, elemento):

        self.elemento = elemento
        self.type = doc.GetElement(elemento.GetTypeId())
        self.code = self.type.LookupParameter("Type Comments").AsString()
        self.origem = elemento.GetTransform().Origin
        self.vectorX = elemento.GetTransform().BasisX
        self.vectorY = elemento.GetTransform().BasisY
        self.vectorZ = elemento.GetTransform().BasisZ

class Viga(Element):

    def __init__(self, doc, elemento):
        Element.__init__(self, doc, elemento)
        self.largura = self.type.LookupParameter("b").AsDouble()
        self.altura = self.type.LookupParameter("h").AsDouble()
        self.cut_comprimento = elemento.LookupParameter("Cut Length").AsDouble()
        self.comprimento = elemento.LookupParameter("Length").AsDouble()
        self.covertype = doc.GetElement(elemento.LookupParameter("Rebar Cover - Other Faces").AsElementId())
        self.cover_length = self.covertype.LookupParameter("Length").AsDouble()

    def decode(self):

        rdc = self.code.split(".")
        self.diametro_estribo = "Ø" + str(rdc[0])
        self.estribo_espacamento = int(rdc[1])
        self.bs_diametro = "Ø" + str(rdc[2])
        self.nr_bs = int(rdc[3])
        self.bi_diametro = "Ø" + str(rdc[4])
        self.nr_bi = int(rdc[5])
        self.bl = "Ø" + str(rdc[6])
        self.nr_bl = int(rdc[7])
        self.bol = str(rdc[8])
        self.est_ext_diametro = "Ø" + str(rdc[9])
        self.est_ext_espacamento = Funk.internal_units(int(rdc[10]))
        self.cc = Funk.internal_units(int(rdc[11]))

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