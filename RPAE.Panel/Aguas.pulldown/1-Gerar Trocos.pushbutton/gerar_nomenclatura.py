# -*- coding: utf-8 -*-

__title__ = "1-Geral Nomenclatura"
__doc__ = "Gera a nomenclatura automática de troços e nós para redes de águas e o respetivo numero de dispositivos"
__author__ = "Joao Ferreira, OE nº 86233"

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

from collections import defaultdict
from collections import deque

import os.path
import sys
import math


# ============================================================
# IMPORTAR CLASSES
# ============================================================

grandparent_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)

sys.path.insert(0, grandparent_dir)

from classes import WaterPipes, PipeFitting
from classes import RvtApi as rvt
from classes import RvtClasses as cls
from classes import RvtApiCategory as cat


# ============================================================
# DOCUMENTO
# ============================================================

doc = __revit__.ActiveUIDocument.Document


# ============================================================
# CONNECTORS
# ============================================================

def get_connector_manager(elemento):
    """
    Obtém ConnectorManager independentemente
    do tipo de elemento.
    """

    try:
        # Pipes e outros MEP elements
        return elemento.ConnectorManager

    except AttributeError:
        pass

    try:
        # FamilyInstance:
        # fittings, válvulas, acessórios, fixtures, etc.
        return elemento.MEPModel.ConnectorManager

    except:
        return None


# ============================================================
# DETETAR FITTING T
# ============================================================

def e_fitting_T(elemento):
    """
    True se o elemento tiver 3 ou mais conectores.
    """

    try:

        cm = get_connector_manager(elemento)

        if cm is None:
            return False

        it = cm.Connectors.ForwardIterator()

        count = 0

        while it.MoveNext():
            count += 1

        return count >= 3

    except:
        return False


# ============================================================
# GERAR GRAFO DA REDE
# ============================================================

def gerar_trocos_automatico(elementos):

    id_to_elem = {}
    ligacoes = {}

    # --------------------------------------------------------
    # Criar dicionário ID -> elemento
    # --------------------------------------------------------

    for elem in elementos:

        elem_id = elem.elemento.Id.Value

        id_to_elem[elem_id] = elem
        ligacoes[elem_id] = []


    # --------------------------------------------------------
    # Construir grafo através dos connectors
    # --------------------------------------------------------

    for elem in elementos:

        elem_id = elem.elemento.Id.Value

        try:

            cm = get_connector_manager(elem.elemento)

            if cm is None:
                continue

            it = cm.Connectors.ForwardIterator()

            while it.MoveNext():

                c = it.Current

                refs_it = c.AllRefs.ForwardIterator()

                while refs_it.MoveNext():

                    ref = refs_it.Current
                    owner = ref.Owner

                    if owner:

                        other_id = owner.Id.Value

                        # Só interessa se o elemento
                        # pertence à rede
                        if (
                            other_id in id_to_elem
                            and other_id != elem_id
                        ):

                            if other_id not in ligacoes[elem_id]:

                                ligacoes[elem_id].append(
                                    other_id
                                )

        except Exception as ex:

            print(
                "Erro grafo ID {0}: {1}".format(
                    elem_id,
                    ex
                )
            )

            continue


    # ========================================================
    # ENCONTRAR ORIGEM DA REDE
    # ========================================================

    contador_id = None


    # --------------------------------------------------------
    # 1. Procurar Contador = 1
    #
    # IMPORTANTE:
    # Não usamos isinstance(elem, Element)
    # porque agora os pipes são WaterPipes.
    # --------------------------------------------------------

    for elem in elementos:

        if hasattr(elem, "contador"):

            try:

                if elem.contador == 1:

                    contador_id = elem.elemento.Id.Value

                    print(
                        "Contador encontrado: ID {0}".format(
                            contador_id
                        )
                    )

                    break

            except:
                pass


    # --------------------------------------------------------
    # 2. Se não encontrou contador,
    #    procurar Termoacumulador
    # --------------------------------------------------------

    if contador_id is None:

        for elem_id, vizinhos in ligacoes.items():

            elem = id_to_elem[elem_id]

            try:

                cat_id = elem.elemento.Category.Id.Value

                if cat_id != int(
                    BuiltInCategory.OST_PlumbingFixtures
                ):

                    continue


                nome_lower = elem.elemento.Name.lower()


                if "termoacumulador" in nome_lower:

                    if vizinhos:

                        contador_id = vizinhos[0]

                        print(
                            "Termoacumulador encontrado — origem: ID {0}".format(
                                contador_id
                            )
                        )

                        break

            except:
                continue


    # --------------------------------------------------------
    # 3. Fallback
    # --------------------------------------------------------

    if contador_id is None:

        print(
            "⚠️ Origem não encontrada — usando primeiro elemento"
        )

        for elem in elementos:

            if hasattr(elem, "elemento"):

                contador_id = elem.elemento.Id.Value

                break


    # ========================================================
    # DEBUG — FIXTURES NO GRAFO
    # ========================================================

    for elem_id, elem in id_to_elem.items():

        try:

            cat_id = elem.elemento.Category.Id.Value

            if cat_id == int(
                BuiltInCategory.OST_PlumbingFixtures
            ):

                print(
                    "Fixture {0} | vizinhos: {1}".format(
                        elem.elemento.Name,
                        ligacoes.get(elem_id, [])
                    )
                )

        except:
            continue


    # --------------------------------------------------------
    # Devolver informação do grafo
    # --------------------------------------------------------

    return (
        elementos,
        ligacoes,
        id_to_elem,
        contador_id
    )


# ============================================================
# GERAR NOMENCLATURA
# ============================================================

def gerar_nomenclatura(
    elementos,
    ligacoes,
    id_to_elem,
    contador_id,
    nome_rede=""
):

    # --------------------------------------------------------
    # Converter índice em letra
    # 0 -> A
    # 1 -> B
    # 2 -> C
    # ...
    # --------------------------------------------------------

    def letra_de_indice(n):

        resultado = ""

        n += 1

        while n > 0:

            n, r = divmod(
                n - 1,
                26
            )

            resultado = chr(
                65 + r
            ) + resultado

        return resultado


    # --------------------------------------------------------
    # Verificar No Principal
    # --------------------------------------------------------

    def e_no_principal(elemento):

        try:

            p = elemento.LookupParameter(
                "No Principal"
            )

            return (
                p is not None
                and p.AsInteger() == 1
            )

        except:

            return False


    # --------------------------------------------------------
    # Verificar Fixture
    # --------------------------------------------------------

    def e_fixture(
        elemento,
        rede=""
    ):

        try:

            cat_id = elemento.Category.Id.Value

            if cat_id != int(
                BuiltInCategory.OST_PlumbingFixtures
            ):

                return False


            # Em AQ o TA não é considerado
            # fixture terminal

            if rede.startswith("AQ"):

                nome_lower = elemento.Name.lower()

                if "termoacumulador" in nome_lower:

                    return False


            return True

        except:

            return False


    # --------------------------------------------------------
    # Prefixo dos aparelhos
    # --------------------------------------------------------

    def prefixo_fixture(nome):

        nome_lower = nome.lower()


        if (
            "lava-louça" in nome_lower
            or "lava louça" in nome_lower
        ):

            return "LL"


        elif (
            "lavatório" in nome_lower
            or "lavatorio" in nome_lower
        ):

            return "LV"


        elif "banheira" in nome_lower:

            return "BA"


        elif "chuveiro" in nome_lower:

            return "CH"


        elif (
            "sanita" in nome_lower
            or "autoclismo" in nome_lower
        ):

            return "BR"


        elif (
            "bidé" in nome_lower
            or "bide" in nome_lower
        ):

            return "BD"


        elif (
            "máquina" in nome_lower
            or "maquina" in nome_lower
        ):

            return "MQ"


        elif (
            "boca" in nome_lower
            or "rega" in nome_lower
        ):

            return "BDR"


        elif "piscina" in nome_lower:

            return "P"


        elif "termoacumulador" in nome_lower:

            return "TA"


        else:

            return "XX"


    # ========================================================
    # MAPAS
    # ========================================================

    no_map = {}

    troco_map = {}

    indice_no_principal = [0]

    contadores_derivacoes = {}


    # --------------------------------------------------------
    # Criar novo nó principal
    # --------------------------------------------------------

    def novo_no_principal():

        nome = letra_de_indice(
            indice_no_principal[0]
        )

        indice_no_principal[0] += 1

        return nome


    # --------------------------------------------------------
    # Criar derivação
    # --------------------------------------------------------

    def nova_derivacao(nome_pai):

        if nome_pai not in contadores_derivacoes:

            contadores_derivacoes[nome_pai] = 1

        else:

            contadores_derivacoes[nome_pai] += 1


        return "{0}.{1}".format(
            nome_pai,
            contadores_derivacoes[nome_pai]
        )


    # ========================================================
    # ORIGEM
    # ========================================================

    if nome_rede.startswith("AQ"):

        no_origem = "TA"

    else:

        no_origem = "CONTADOR"


    # ========================================================
    # COLOCAR ORIGEM NO MAPA
    # ========================================================

    no_map[contador_id] = no_origem

    # Aqui fica inicialmente CONTADOR-?
    # ou TA-?

    troco_map[contador_id] = (
        "{0}-?".format(
            no_origem
        )
    )


    fila = deque(
        [
            (
                contador_id,
                no_origem
            )
        ]
    )


    # ========================================================
    # BFS
    # ========================================================

    visitados = set()


    while fila:

        atual, no_atual = fila.popleft()


        if atual in visitados:

            continue


        visitados.add(atual)


        vizinhos = [
            v
            for v in ligacoes.get(
                atual,
                []
            )
            if v not in visitados
        ]


        for vizinho_id in vizinhos:

            elem_vizinho = (
                id_to_elem[
                    vizinho_id
                ].elemento
            )


            # =================================================
            # FIXTURE TERMINAL
            # =================================================

            if e_fixture(
                elem_vizinho,
                nome_rede
            ):

                nome_lower = (
                    elem_vizinho.Name.lower()
                )


                # ---------------------------------------------
                # Termoacumulador
                # ---------------------------------------------

                if "termoacumulador" in nome_lower:

                    troco_map[
                        vizinho_id
                    ] = "TA"

                    no_map[
                        vizinho_id
                    ] = "TA"


                # ---------------------------------------------
                # Fixture normal
                # ---------------------------------------------

                else:

                    prefixo = prefixo_fixture(
                        elem_vizinho.Name
                    )

                    troco = "{0}.{1}".format(
                        prefixo,
                        no_atual
                    )

                    troco_map[
                        vizinho_id
                    ] = troco

                    no_map[
                        vizinho_id
                    ] = troco


                visitados.add(
                    vizinho_id
                )

                continue


            # =================================================
            # FITTING T
            # =================================================

            if e_fitting_T(
                elem_vizinho
            ):

                if e_no_principal(
                    elem_vizinho
                ):

                    novo_no = novo_no_principal()

                else:

                    novo_no = nova_derivacao(
                        no_atual
                    )


                no_map[
                    vizinho_id
                ] = novo_no


                troco_map[
                    vizinho_id
                ] = "{0}-{1}".format(
                    no_atual,
                    novo_no
                )


                fila.append(
                    (
                        vizinho_id,
                        novo_no
                    )
                )


            # =================================================
            # PIPE / VÁLVULA / OUTRO
            # =================================================

            else:

                troco_map[
                    vizinho_id
                ] = "{0}-?".format(
                    no_atual
                )


                fila.append(
                    (
                        vizinho_id,
                        no_atual
                    )
                )


    # ========================================================
    # SEGUNDA PASSAGEM
    # RESOLVER "-?"
    # ========================================================

    for elem_id in list(
        troco_map.keys()
    ):

        troco = troco_map[
            elem_id
        ]


        if not troco.endswith("-?"):

            continue


        no_origem_troco = (
            troco.split("-?")[0]
        )


        no_destino = None


        fila_busca = list(
            ligacoes.get(
                elem_id,
                []
            )
        )


        visitados_busca = set(
            [elem_id]
        )


        while (
            fila_busca
            and no_destino is None
        ):

            vizinho_id = (
                fila_busca.pop(0)
            )


            if (
                vizinho_id
                in visitados_busca
            ):

                continue


            visitados_busca.add(
                vizinho_id
            )


            # -----------------------------------------------
            # Já tem um nó identificado
            # -----------------------------------------------

            if vizinho_id in no_map:

                no_candidato = no_map[
                    vizinho_id
                ]


                if (
                    no_candidato
                    != no_origem_troco
                ):

                    elem_candidato = (
                        id_to_elem[
                            vizinho_id
                        ].elemento
                    )


                    nome_lower = (
                        elem_candidato.Name.lower()
                    )


                    # ---------------------------------------
                    # Termoacumulador
                    # ---------------------------------------

                    if (
                        "termoacumulador"
                        in nome_lower
                    ):

                        no_destino = (
                            no_candidato
                        )


                    # ---------------------------------------
                    # Nó normal
                    # ---------------------------------------

                    elif not e_fixture(
                        elem_candidato,
                        nome_rede
                    ):

                        no_destino = (
                            no_candidato
                        )


                    # ---------------------------------------
                    # Fixture
                    # ---------------------------------------

                    else:

                        no_destino = (
                            prefixo_fixture(
                                elem_candidato.Name
                            )
                        )


            # -----------------------------------------------
            # Ainda não encontrou nó
            # -----------------------------------------------

            else:

                fila_busca.extend(
                    ligacoes.get(
                        vizinho_id,
                        []
                    )
                )


        # ====================================================
        # DEFINIR TROÇO
        # ====================================================

        if no_destino:

            troco_map[
                elem_id
            ] = "{0}-{1}".format(
                no_destino,
                no_origem_troco
            )

        else:

            troco_map[
                elem_id
            ] = no_origem_troco


    # ========================================================
    # APLICAR AO REVIT
    # ========================================================

    for elem in elementos:

        elem_id = (
            elem.elemento.Id.Value
        )


        troco = troco_map.get(
            elem_id,
            "?"
        )


        elem.troco_auto = troco


        p = elem.elemento.LookupParameter(
            "Troço"
        )


        if (
            p
            and not p.IsReadOnly
        ):

            p.Set(troco)


    return (
        elementos,
        troco_map,
        no_map
    )


# ============================================================
# OBTER ELEMENTOS DO MODELO
# ============================================================

piping_system = rvt.get_element_byclass(
    doc,
    cls.PIPING_SYSTEM,
    element_type=False
)


pipe_fittings = rvt.get_elements_bycategory(
    doc,
    cat.PIPE_FITTINGS
)


pipe_accessories = rvt.get_elements_bycategory(
    doc,
    cat.PIPE_ACCESSORIES
)


plumbing_fixtures = rvt.get_elements_bycategory(
    doc,
    cat.PLUMBING_FIXTURES
)


# ============================================================
# WRAPPERS
# ============================================================

fittings_wrapped = [
    PipeFitting(doc, f)
    for f in pipe_fittings
]


accessories_wrapped = [
    PipeFitting(doc, a)
    for a in pipe_accessories
]


fixtures_wrapped = [
    PipeFitting(doc, pf)
    for pf in plumbing_fixtures
]


# ============================================================
# LEVELS
# ============================================================

levels = rvt.get_element_byclass(
    doc,
    cls.LEVEL
)


# ============================================================
# PIPES
# ============================================================

elements = rvt.get_elements_bycategory(
    doc,
    cat.PIPES
)


# ============================================================
# PRESSÃO
# ============================================================

pressao_rede = 30


# ============================================================
# CRIAR REDES
# ============================================================

redes = {}


for ele in elements:

    nome_sistema = ele.get_Parameter(
        BuiltInParameter.RBS_SYSTEM_NAME_PARAM
    ).AsString()


    if nome_sistema.startswith(
        ("AF", "AQ")
    ):

        if nome_sistema not in redes:

            redes[nome_sistema] = []


        redes[
            nome_sistema
        ].append(
            WaterPipes(
                doc,
                ele
            )
        )


# ============================================================
# FITTINGS + ACESSÓRIOS
# ============================================================

for elem in (
    fittings_wrapped
    + accessories_wrapped
):

    try:

        nome_sistema = (
            elem.elemento.get_Parameter(
                BuiltInParameter.RBS_SYSTEM_NAME_PARAM
            ).AsString()
        )

    except:

        continue


    if (
        nome_sistema
        and nome_sistema in redes
    ):

        redes[
            nome_sistema
        ].append(
            elem
        )


# ============================================================
# FIXTURES
# ============================================================

for fixture in fixtures_wrapped:

    try:

        nome_sistema = (
            fixture.elemento.get_Parameter(
                BuiltInParameter.RBS_SYSTEM_NAME_PARAM
            ).AsString()
        )

    except:

        continue


    if not nome_sistema:

        continue


    # Exemplo:
    # "AF_EDI,AQ_EDI"

    sistemas = [
        s.strip()
        for s in nome_sistema.split(",")
    ]


    for sistema in sistemas:

        if sistema in redes:

            if fixture not in redes[
                sistema
            ]:

                redes[
                    sistema
                ].append(
                    fixture
                )


# ============================================================
# LEVEL RUA
# ============================================================

for l in levels:

    if l.Name == "RUA":

        lvl_abastecimento = round(
            l.Elevation / 3.281
        )


# ============================================================
# TRANSACTION
# ============================================================

t = Transaction(
    doc,
    "Relatorio Aguas"
)

t.Start()


# ============================================================
# PROCESSAR REDES
# ============================================================

output_por_rede_temp = {}


for nome_rede, elementos_rede in redes.items():

    print("")
    print("======================================")
    print("REDE: {0}".format(nome_rede))
    print("======================================")


    # --------------------------------------------------------
    # 1. GERAR GRAFO
    # --------------------------------------------------------

    (
        elementos_rede,
        ligacoes,
        id_to_elem,
        contador_id
    ) = gerar_trocos_automatico(
        elementos_rede
    )


    print(
        "ID origem: {0}".format(
            contador_id
        )
    )


    # --------------------------------------------------------
    # 2. GERAR NOMENCLATURA
    # --------------------------------------------------------

    (
        elementos_com_troco,
        troco_map,
        no_map
    ) = gerar_nomenclatura(
        elementos_rede,
        ligacoes,
        id_to_elem,
        contador_id,
        nome_rede
    )


    # --------------------------------------------------------
    # 3. DEBUG — TODOS OS ELEMENTOS
    # --------------------------------------------------------

    print("")
    print("---- TROÇOS GERADOS ----")


    for elem_id, troco in troco_map.items():

        elem = id_to_elem[
            elem_id
        ]

        print(
            "{0} | ID {1} -> {2}".format(
                elem.nome,
                elem_id,
                troco
            )
        )


    print("")
    print("---- FIXTURES ----")


    for elem_id, elem in id_to_elem.items():

        try:

            cat_id = (
                elem.elemento.Category.Id.Value
            )


            if cat_id == int(
                BuiltInCategory.OST_PlumbingFixtures
            ):

                print(
                    "Fixture: {0} | ID: {1} | Troço: {2}".format(
                        elem.nome,
                        elem_id,
                        troco_map.get(
                            elem_id,
                            "N/A"
                        )
                    )
                )

        except:

            continue


# ============================================================
# DEBUG FINAL
# ============================================================

print("")
print("======================================")
print(
    "Fixtures recolhidos: {0}".format(
        len(fixtures_wrapped)
    )
)
print("======================================")


for f in fixtures_wrapped[:3]:

    try:

        cat_id = (
            f.elemento.Category.Id.Value
        )


        nome_sistema = (
            f.elemento.get_Parameter(
                BuiltInParameter.RBS_SYSTEM_NAME_PARAM
            ).AsString()
        )


        print(
            "Nome: {0} | Cat ID: {1} | Sistema: {2}".format(
                f.nome,
                cat_id,
                nome_sistema
            )
        )


    except Exception as ex:

        print(
            "Erro: {0}".format(
                ex
            )
        )


print(
    "OST_PlumbingFixtures ID: {0}".format(
        int(
            BuiltInCategory.OST_PlumbingFixtures
        )
    )
)


# ============================================================
# COMMIT
# ============================================================

t.Commit()