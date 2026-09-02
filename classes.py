# -*- coding: utf-8 -*-
""" Este ficheiro vai servir para fazer as classes para fazer as armaduras
Tentar usar parent class and child classes
"""

import clr

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
    SHEETS = BuiltInCategory.OST_Sheets
    PIPES = BuiltInCategory.OST_PipeCurves
    PIPE_FITTINGS = BuiltInCategory.OST_PipeFitting
    PLUMBING_FIXTURES = BuiltInCategory.OST_PlumbingFixtures
    PIPE_ACCESSORIES = BuiltInCategory.OST_PipeAccessory

class RvtParameterName:

    HOOK_NAME_ESTRIBO = "Stirrup/Tie Seismic - 135 deg."
    HOOK_NAME_FUND = "50Ø"
    HOOK_ROTATION = "Hook Rotation At Start"
    PIPE_SYSTEM_TYPE = BuiltInParameter.RBS_PIPING_SYSTEM_TYPE_PARAM
    FIXTURE_UNITS = BuiltInParameter.RBS_PIPE_FIXTURE_UNITS_PARAM
    PIPE_SYSTEM_CLASSIFICATION = "System Classsification"
    PIPE_FITTING_DIAMETER = BuiltInParameter.RBS_PIPE_DIAMETER_PARAM
    PIPE_SYSTEM_NAME = BuiltInParameter.RBS_SYSTEM_NAME_PARAM
    FLOW = BuiltInParameter.RBS_PIPE_FLOW_PARAM
    PIPE_INSIDE_DIAMETER = BuiltInParameter.RBS_PIPE_INNER_DIAM_PARAM

class RvtClasses:
    VIEW_TYPE = ViewFamilyType
    VIEW = View
    PIPING_SYSTEM = MEPSystem
    PIPES = MEPCurve
    LEVEL = Level
    
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
    def get_elements_byparameter(doc, element_class, filter_parameter, filter_value):
        #Parameter to filter
        f_parameter = ParameterValueProvider(ElementId(filter_parameter))
        #Create a rule
        f_rule = FilterStringRule(f_parameter, FilterStringEquals(), filter_value)
        filter_system = ElementParameterFilter(f_rule)
        elements = FilteredElementCollector(doc).OfClass(element_class).WherePasses(filter_system).ToElements()
        return elements

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
            bbox_xmid = XYZ(bbox_min.X, (bbox_min.Y + 0.65), bbox_min.Z)

            if bbox == "Mid":

                outline = Outline(bbox_mid, bbox_max)

            elif bbox == "XMid":

                outline = Outline(bbox_xmid, bbox_max)

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
        
    def create_dimensions(self, doc, vista, ponto1, ponto2, offset, x_lock_value=0, y_lock_value=0, z_lock_value=0, x_lock=False, y_lock=False, xz_lock=False, yz_lock=False, zx_lock=False, zy_lock=False):
        
        if x_lock:

            x = x_lock_value + Funk.internal_units(offset, "mm")
            y_left = ponto1
            y_right = ponto2

            vector_x = self.vectorX.Multiply(x)
            vector_yleft = self.vectorY.Multiply(y_left)
            vector_yright = self.vectorY.Multiply(y_right)

            p1 = self.origem.Add(vector_x).Add(vector_yleft)
            p2 = self.origem.Add(vector_x).Add(vector_yright)
        
        elif xz_lock:

            z = z_lock_value + Funk.internal_units(offset, "mm")
            x_left = ponto1
            x_right = ponto2

            vector_z = self.vectorZ.Multiply(z)
            vector_xleft = self.vectorX.Multiply(x_left)
            vector_xright = self.vectorX.Multiply(x_right)

            p1 = self.origem.Add(vector_xleft).Add(vector_z)
            p2 = self.origem.Add(vector_xright).Add(vector_z)

        elif y_lock:

            y = y_lock_value + Funk.internal_units(offset, "mm")
            x_left = ponto1
            x_right = ponto2

            vector_y = self.vectorY.Multiply(y)
            vector_xleft = self.vectorX.Multiply(x_left)
            vector_xright = self.vectorX.Multiply(x_right)

            p1 = self.origem.Add(vector_xleft).Add(vector_y)
            p2 = self.origem.Add(vector_xright).Add(vector_y)

        elif yz_lock:

            z = z_lock_value + Funk.internal_units(offset, "mm")
            y_left = ponto1
            y_right = ponto2

            vector_z = self.vectorZ.Multiply(z)
            vector_yleft = self.vectorY.Multiply(y_left)
            vector_yright = self.vectorY.Multiply(y_right)

            p1 = self.origem.Add(vector_yleft).Add(vector_z)
            p2 = self.origem.Add(vector_yright).Add(vector_z)

        elif zx_lock:

            x = x_lock_value + Funk.internal_units(offset, "mm")
            z_left = ponto1
            z_right = ponto2

            vector_x = self.vectorX.Multiply(x)
            vector_zleft = self.vectorZ.Multiply(z_left)
            vector_zright = self.vectorZ.Multiply(z_right)

            p1 = self.origem.Add(vector_zleft).Add(vector_x)
            p2 = self.origem.Add(vector_zright).Add(vector_x)

        elif zy_lock:

            y = y_lock_value + Funk.internal_units(offset, "mm")
            z_left = ponto1
            z_right = ponto2

            vector_y = self.vectorY.Multiply(y)
            vector_zleft = self.vectorZ.Multiply(z_left)
            vector_zright = self.vectorZ.Multiply(z_right)

            p1 = self.origem.Add(vector_zleft).Add(vector_y)
            p2 = self.origem.Add(vector_zright).Add(vector_y)

        line = Line.CreateBound(p1, p2)
        reference = ReferenceArray()
        linha = doc.Create.NewDetailCurve(vista, line)
        curva = linha.GeometryCurve
        reference.Append(curva.GetEndPointReference(0))
        reference.Append(curva.GetEndPointReference(1))
        doc.Create.NewDimension(vista, line, reference)
        
class Viga(Element):

    def __init__(self, doc, elemento):

        Element.__init__(self, doc, elemento)
        self.largura = self.type.LookupParameter("b").AsDouble()
        self.altura = self.type.LookupParameter("h").AsDouble()
        self.cut_comprimento = elemento.LookupParameter("Cut Length").AsDouble()
        self.comprimento = elemento.LookupParameter("System Length").AsDouble()
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
        self.comprimento = elemento.LookupParameter("System Length").AsDouble()
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
            self.altura = self.type.LookupParameter("Foundation Thickness").AsDouble()
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

class Pipes():

    def __init__(self, doc, elemento):
        self.elemento = elemento
        self.nome = elemento.Name
        self.type = doc.GetElement(elemento.GetTypeId())
        #self.caudal_acumulado = elemento.get_Parameter(RvtParameterName.FIXTURE_UNITS).AsDouble()
        self.system_type = elemento.LookupParameter("System Type").AsValueString()
        self.comprimento = round(elemento.LookupParameter("Length").AsDouble()/3.281,2)
        #self.tubo_queda = elemento.LookupParameter("Tubo de Queda")
        #self.colector = elemento.LookupParameter("Colector").AsInteger()
        #self.rni = elemento.LookupParameter("RNI").AsInteger()
        self.bbox = elemento.get_BoundingBox(None)
        self.troco = elemento.LookupParameter("Troço").AsString()
        self.slope = round(elemento.get_Parameter(BuiltInParameter.RBS_PIPE_SLOPE).AsDouble(),4)
        lvl = doc.GetElement(self.elemento.LookupParameter("Reference Level").AsElementId())
        self.lvl_name = lvl.Name
        self.lvl_elevation = round(lvl.Elevation/3.281, 2)

    def set_diameter(self, diameter):
        self.elemento.LookupParameter("Diameter").Set(diameter)
    
    def set_qcal(self, qcal):
        self.elemento.LookupParameter("Qcal").Set(qcal)

    def set_dcal(self, dcal):
        self.elemento.LookupParameter("Dcal").Set(dcal)

    def set_d_interno(self, d_interno):
        self.elemento.LookupParameter("D_interno").Set(d_interno)

    def set_velocity(self, velocity):
        self.elemento.LookupParameter("Velocidade").Set(velocity)

    def set_perda_carga(self, perda_carga):
        self.elemento.LookupParameter("J (m/m)").Set(perda_carga)

    def set_jl(self, jl):
        self.elemento.LookupParameter("JxL (m.c.a)").Set(jl)

    def set_jacumulado(self, j_acumulado):
        self.elemento.LookupParameter("Jacumulado (m.c.a)").Set(j_acumulado)

    def get_qcal(self):
        return self.elemento.LookupParameter("Qcal").AsDouble()

    def get_dcal(self):
        return self.elemento.LookupParameter("Dcal").AsDouble()

    def get_velocidade(self):
        return self.elemento.LookupParameter("Velocidade").AsDouble()

    def get_perda_carga(self):
        return self.elemento.LookupParameter("J (m/m)").AsDouble()

    def get_jl(self):
        return self.elemento.LookupParameter("JxL (m.c.a)").AsDouble()

    def get_jacumulado(self):
        return self.elemento.LookupParameter("Jacumulado (m.c.a)").AsDouble()
    
    @classmethod
    def filter_by_system(cls, pipes, system):
        return [pipe for pipe in pipes if pipe.system_type == system]


class WaterPipes(Pipes):
    
    def __init__(self, doc, elemento):
        Pipes.__init__(self, doc, elemento)
        self.caudal_acumulado = round(elemento.LookupParameter("Flow").AsDouble()*28.317,2)
        self.inside_diameter = elemento.get_Parameter(RvtParameterName.PIPE_INSIDE_DIAMETER).AsDouble()
        self.contador = elemento.LookupParameter("Contador").AsInteger()
        self.troco = elemento.LookupParameter("Troço").AsString()
        self.troco_auto = self.troco
        self.zona = elemento.LookupParameter("Zona").AsString()
        self.dispositivos = 1
        
    def set_dispositivos(self, valor):
            v = self.elemento.LookupParameter("Nr Dispositivos").Set(valor)
            return v
    
    def d_nominal(self, valor):
        if valor < 12:
            d = 16
        elif valor < 16:
            d = 20
        elif valor < 20:
            d = 26
        elif valor < 26:
            d = 32
        elif valor < 32:
            d = 40
        elif valor < 42:
            d = 50
        elif valor < 54:
            d = 63
        elif valor < 67:
            d = 75
        elif valor < 82:
            d = 90
        else:
            d = 110
        
        return d

    def d_interno(self, valor):
        if valor == 16:
            d_int = 12
        elif valor == 20:
            d_int = 16
        elif valor == 26:
            d_int = 20
        elif valor == 32:
            d_int = 26
        elif valor == 40:
            d_int = 32
        elif valor == 50:
            d_int = 42
        elif valor == 63:
            d_int = 56
        elif valor == 75:   
            d_int = 66
        elif valor == 90:
            d_int = 73
        elif valor == 110:
            d_int = 90
        else:
            d_int = "error"

        return float(d_int)

    @classmethod    
    def processar_trocos(cls, lista_trocos):
        """
        Processa uma lista de troços removendo duplicados e calculando o número de dispositivos.
        
        Regras:
        1. Remover duplicados
        2. Por defeito, troços com prefixo numérico têm 1 dispositivo
        3. Quando vários sufixos iguais existem em troços diferentes, 
        o troço com prefixo igual ao sufixo deve somar os números de dispositivos
        4. Considera todos os valores da lista, mesmo os que aparecem depois
        """
        
        # Remover duplicados mantendo a ordem
        trocos_unicos = []
        for item in lista_trocos:
            if item.troco not in trocos_unicos:
                trocos_unicos.append(item.troco)
        
        # Separar prefixos e sufixos
        trocos_info = []
        prefixos_validos = {"CH", "MLL", "MLR", "LV", "LL", "BR", "BA", "BD","BRE","LV1","LV2","TA", "MQ", "MQ1", "MQ2", "BDR1", "BDR2", "BDR3","BDR4", "BDR5", "BDR6"}
        for troco in trocos_unicos:
            partes = troco.split('-')
            if len(partes) == 2:
                prefixo, sufixo, = partes
                trocos_info.append({
                    'original': troco,
                    'prefixo': prefixo,
                    'sufixo': sufixo,
                    'dispositivos': 1 if prefixo in prefixos_validos else 0
                })
        
        # Criar mapeamentos para análise completa
        # Mapa de sufixos para troços que terminam nesse sufixo
        sufixos_para_trocos = {}
        # Mapa de prefixos para troços que começam com esse prefixo
        prefixos_para_trocos = {}
        
        for info in trocos_info:
            sufixo = info['sufixo']
            prefixo = info['prefixo']
            
            if sufixo not in sufixos_para_trocos:
                sufixos_para_trocos[sufixo] = []
            sufixos_para_trocos[sufixo].append(info)
            
            if prefixo not in prefixos_para_trocos:
                prefixos_para_trocos[prefixo] = []
            prefixos_para_trocos[prefixo].append(info)
        
        # Fazer múltiplas passagens até não haver mais mudanças
        # Isso garante que consideramos todos os valores, mesmo os que aparecem depois
        mudancas = True
        iteracao = 0
        max_iteracoes = len(trocos_info) + 1  # Evitar loop infinito
        
        while mudancas and iteracao < max_iteracoes:
            mudancas = False
            iteracao += 1
            
            for info in trocos_info:
                prefixo = info['prefixo']
                dispositivos_anteriores = info['dispositivos']
                
                # Se este prefixo aparece como sufixo noutros troços
                if prefixo in sufixos_para_trocos:
                    # Somar dispositivos dos troços que terminam neste prefixo
                    dispositivos_a_somar = 0
                    trocos_contribuintes = []
                    
                    for troco_com_sufixo in sufixos_para_trocos[prefixo]:
                        # Só contar troços que têm dispositivos (evitar loops infinitos)
                        if troco_com_sufixo['dispositivos'] > 0:
                            dispositivos_a_somar += troco_com_sufixo['dispositivos']
                            trocos_contribuintes.append(troco_com_sufixo['original'])
                    
                    # Atualizar o número de dispositivos se houver contribuições
                    if dispositivos_a_somar > 0 and not info['prefixo'].isdigit():
                        novo_valor = dispositivos_a_somar
                        if info['dispositivos'] != novo_valor:
                            info['dispositivos'] = novo_valor
                            mudancas = True
    
        # 2. Criar mapa final troco -> dispositivos
        troco_para_dispositivos = {info['original']: info['dispositivos'] for info in trocos_info}
            
        # 3. Atualizar todos os elementos originais (mesmo duplicados)
        for elem in lista_trocos:
            if elem.troco in troco_para_dispositivos:
                elem.dispositivos = troco_para_dispositivos[elem.troco]
            else:
                elem.dispositivos = 1  # fallback
        
        return lista_trocos

    @classmethod
    def aninhar_por_zona_troco(cls, lista_elementos):
        """
        Retorna lista ordenada de elementos, priorizando:
        1) lvl_elevation (mais baixo → mais alto)
        2) zona (alfabético)
        3) troço
        """
        from operator import attrgetter

        # Ordenação múltipla usando tupla: elevation → zona → troço
        lista_ordenada = sorted(
            lista_elementos,
            key=lambda e: (e.lvl_elevation, e.zona, e.troco)
        )
        
        return lista_ordenada

class SewagePipes(Pipes):
    
    def __init__(self, doc, elemento):
        Pipes.__init__(self, doc, elemento)
        self.caudal_acumulado = elemento.get_Parameter(RvtParameterName.FIXTURE_UNITS).AsDouble()
        self.tubo_queda = elemento.LookupParameter("Tubo de Queda")
        self.colector = elemento.LookupParameter("Colector").AsInteger()
        self.rni = elemento.LookupParameter("RNI").AsInteger()

    def set_tau(self, tau):
        self.elemento.LookupParameter("Tensao Arrastamento").Set(tau)

    def set_h_over_d(self, h_over_d):
        self.elemento.LookupParameter("h/d").Set(h_over_d)

class PlumbingFixture(Element):

    def __init__(self, doc, elemento):
        Element.__init__(self, doc, elemento)
        self.system_type = elemento.LookupParameter("System Type").AsValueString()
        #self.caudal_acumulado = elemento.get_Parameter(RvtParameterName.FIXTURE_UNITS).AsDouble()

    @classmethod
    def filter_by_system(cls, fixtures, system):
        return [fixture for fixture in fixtures if fixture.system_type == system]

class PipeFitting:
    """Wrapper mínimo para fittings — só para construir o grafo"""
    def __init__(self, doc, elemento):
        self.elemento = elemento
        self.nome = elemento.Name
        self.troco_auto = None
        self.contador = 0
        try:
            self.system_type = elemento.LookupParameter("System Type").AsValueString()
        except:
            self.system_type = None

    def get_nome_sistema(self):
        try:
            from Autodesk.Revit.DB import BuiltInParameter
            return self.elemento.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM).AsString()
        except:
            return None

    @staticmethod
    def filter_by_system(lista, prefixo):
        return [f for f in lista if f.get_nome_sistema() and 
                f.get_nome_sistema().startswith(prefixo)]

