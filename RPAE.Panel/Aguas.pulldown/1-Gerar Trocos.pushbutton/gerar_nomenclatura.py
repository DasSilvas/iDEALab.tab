# -*- coding: utf-8 -*-

__title__ = "1-Geral Nomenclatura"
__doc__ = "Gera a nomenclatura automática de troços e nós para redes de águas e o respetivo numero de dispositivos"
__author__ = "Joao Ferreira, OE nº 86233"


# ============================================================
# IMPORTS
# ============================================================

import clr
import os
import sys

from collections import deque


clr.AddReference("RevitAPI")

from Autodesk.Revit.DB import *


# ============================================================
# IMPORTAR CLASSES
# ============================================================

grandparent_dir = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        ".."
    )
)

if grandparent_dir not in sys.path:
    sys.path.insert(
        0,
        grandparent_dir
    )


from classes import WaterPipes, PipeFitting
from classes import RvtApi as rvt
from classes import RvtClasses as cls
from classes import RvtApiCategory as cat


# ============================================================
# DOCUMENTO
# ============================================================

doc = __revit__.ActiveUIDocument.Document


# ============================================================
# CONSTANTES DE CATEGORIA
# ============================================================

PIPE_CATEGORY_ID = int(
    BuiltInCategory.OST_PipeCurves
)

FITTING_CATEGORY_ID = int(
    BuiltInCategory.OST_PipeFitting
)

FIXTURE_CATEGORY_ID = int(
    BuiltInCategory.OST_PlumbingFixtures
)


# ============================================================
# CONNECTORS
# ============================================================

def get_connector_manager(elemento):

    try:
        return elemento.ConnectorManager

    except AttributeError:
        pass

    try:
        return elemento.MEPModel.ConnectorManager

    except:
        return None


# ============================================================
# ID DO ELEMENTO
# ============================================================

def get_element_id(elemento):

    try:
        return int(elemento.Id.Value)

    except:
        return str(elemento.Id)


# ============================================================
# FITTING T
# ============================================================

def e_fitting_T(elemento):

    try:

        cm = get_connector_manager(elemento)

        if cm is None:
            return False

        # Na maioria dos casos conseguimos obter
        # diretamente o número de connectors.
        try:
            return cm.Connectors.Size >= 3

        except:
            pass

        # Fallback
        it = cm.Connectors.ForwardIterator()

        count = 0

        while it.MoveNext():

            count += 1

            if count >= 3:
                return True

        return False

    except:

        return False


# ============================================================
# GERAR GRAFO DA REDE
# ============================================================

def gerar_trocos_automatico(elementos):

    id_to_elem = {}
    ligacoes = {}
    ligacoes_set = {}

    # --------------------------------------------------------
    # Criar dicionários
    # --------------------------------------------------------

    for elem in elementos:

        elem_id = get_element_id(
            elem.elemento
        )

        id_to_elem[elem_id] = elem

        ligacoes[elem_id] = []

        ligacoes_set[elem_id] = set()


    # --------------------------------------------------------
    # Construir grafo
    # --------------------------------------------------------

    for elem in elementos:

        elem_id = get_element_id(
            elem.elemento
        )

        try:

            cm = get_connector_manager(
                elem.elemento
            )

            if cm is None:
                continue

            it = cm.Connectors.ForwardIterator()

            while it.MoveNext():

                connector = it.Current

                if not connector.IsConnected:
                    continue

                refs_it = (
                    connector.AllRefs.ForwardIterator()
                )

                while refs_it.MoveNext():

                    ref = refs_it.Current
                    owner = ref.Owner

                    if owner is None:
                        continue

                    other_id = get_element_id(
                        owner
                    )

                    if (
                        other_id in id_to_elem
                        and other_id != elem_id
                    ):

                        if (
                            other_id
                            not in ligacoes_set[elem_id]
                        ):

                            ligacoes_set[
                                elem_id
                            ].add(
                                other_id
                            )

                            ligacoes[
                                elem_id
                            ].append(
                                other_id
                            )

        except:

            continue


    # ========================================================
    # ENCONTRAR ORIGEM
    # ========================================================

    contador_id = None


    # --------------------------------------------------------
    # 1. Contador = 1
    # --------------------------------------------------------

    for elem in elementos:

        if not hasattr(
            elem,
            "contador"
        ):
            continue

        try:

            if elem.contador == 1:

                contador_id = get_element_id(
                    elem.elemento
                )

                break

        except:

            pass


    # --------------------------------------------------------
    # 2. Termoacumulador
    # --------------------------------------------------------

    if contador_id is None:

        for elem_id, vizinhos in ligacoes.items():

            elem = id_to_elem[elem_id]

            try:

                elemento = elem.elemento

                category = elemento.Category

                if category is None:
                    continue

                if (
                    int(category.Id.Value)
                    != FIXTURE_CATEGORY_ID
                ):
                    continue

                nome_lower = (
                    elemento.Name.lower()
                )

                if (
                    "termoacumulador"
                    in nome_lower
                ):

                    if vizinhos:

                        contador_id = vizinhos[0]

                        break

            except:

                continue


    # --------------------------------------------------------
    # 3. Fallback
    # --------------------------------------------------------

    if contador_id is None:

        for elem in elementos:

            if hasattr(
                elem,
                "elemento"
            ):

                contador_id = get_element_id(
                    elem.elemento
                )

                break


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
    # LETRA
    # --------------------------------------------------------

    def letra_de_indice(n):

        resultado = ""

        n += 1

        while n > 0:

            n, r = divmod(
                n - 1,
                26
            )

            resultado = (
                chr(65 + r)
                + resultado
            )

        return resultado


    # --------------------------------------------------------
    # CACHE DE ELEMENTOS
    # --------------------------------------------------------

    elemento_cache = {}

    nome_cache = {}
    categoria_cache = {}

    for elem_id, wrapper in id_to_elem.items():

        elemento = wrapper.elemento

        elemento_cache[elem_id] = elemento

        try:
            nome_cache[elem_id] = (
                elemento.Name
            )

        except:
            nome_cache[elem_id] = ""


        try:
            categoria_cache[elem_id] = (
                int(
                    elemento.Category.Id.Value
                )
            )

        except:
            categoria_cache[elem_id] = None


    # --------------------------------------------------------
    # NO PRINCIPAL
    # --------------------------------------------------------

    no_principal_cache = {}

    def e_no_principal(elemento):

        elem_id = get_element_id(
            elemento
        )

        if elem_id in no_principal_cache:

            return no_principal_cache[
                elem_id
            ]

        try:

            p = elemento.LookupParameter(
                "No Principal"
            )

            resultado = (
                p is not None
                and p.AsInteger() == 1
            )

        except:

            resultado = False

        no_principal_cache[
            elem_id
        ] = resultado

        return resultado


    # --------------------------------------------------------
    # FIXTURE
    # --------------------------------------------------------

    fixture_cache = {}

    def e_fixture(
        elemento,
        rede=""
    ):

        elem_id = get_element_id(
            elemento
        )

        chave = (
            elem_id,
            rede.startswith("AQ")
        )

        if chave in fixture_cache:

            return fixture_cache[chave]

        try:

            if elemento.Category is None:

                fixture_cache[
                    chave
                ] = False

                return False


            cat_id = int(
                elemento.Category.Id.Value
            )

            if cat_id != FIXTURE_CATEGORY_ID:

                fixture_cache[
                    chave
                ] = False

                return False


            if rede.startswith("AQ"):

                nome_lower = (
                    elemento.Name.lower()
                )

                if (
                    "termoacumulador"
                    in nome_lower
                ):

                    fixture_cache[
                        chave
                    ] = False

                    return False


            fixture_cache[
                chave
            ] = True

            return True

        except:

            fixture_cache[
                chave
            ] = False

            return False


    # --------------------------------------------------------
    # PREFIXO FIXTURE
    # --------------------------------------------------------

    prefixo_cache = {}

    def prefixo_fixture(nome):

        nome_lower = nome.lower()

        if nome_lower in prefixo_cache:

            return prefixo_cache[
                nome_lower
            ]


        if (
            "lava-louça" in nome_lower
            or "lava louça" in nome_lower
        ):

            resultado = "LL"


        elif (
            "lavatório" in nome_lower
            or "lavatorio" in nome_lower
        ):

            resultado = "LV"


        elif "banheira" in nome_lower:

            resultado = "BA"


        elif "chuveiro" in nome_lower:

            resultado = "CH"


        elif (
            "sanita" in nome_lower
            or "autoclismo" in nome_lower
        ):

            resultado = "BR"


        elif (
            "bidé" in nome_lower
            or "bide" in nome_lower
        ):

            resultado = "BD"


        elif (
            "máquina" in nome_lower
            or "maquina" in nome_lower
        ):

            resultado = "MQ"


        elif (
            "boca" in nome_lower
            or "rega" in nome_lower
        ):

            resultado = "BDR"


        elif "piscina" in nome_lower:

            resultado = "P"


        elif "termoacumulador" in nome_lower:

            resultado = "TA"


        else:

            resultado = "XX"


        prefixo_cache[
            nome_lower
        ] = resultado

        return resultado


    # ========================================================
    # MAPAS
    # ========================================================

    no_map = {}
    troco_map = {}

    indice_no_principal = [0]

    contadores_derivacoes = {}


    # --------------------------------------------------------
    # NOVO NÓ PRINCIPAL
    # --------------------------------------------------------

    def novo_no_principal():

        nome = letra_de_indice(
            indice_no_principal[0]
        )

        indice_no_principal[0] += 1

        return nome


    # --------------------------------------------------------
    # NOVA DERIVAÇÃO
    # --------------------------------------------------------

    def nova_derivacao(nome_pai):

        if nome_pai not in (
            contadores_derivacoes
        ):

            contadores_derivacoes[
                nome_pai
            ] = 1

        else:

            contadores_derivacoes[
                nome_pai
            ] += 1


        return "{0}.{1}".format(
            nome_pai,
            contadores_derivacoes[
                nome_pai
            ]
        )


    # ========================================================
    # ORIGEM
    # ========================================================

    if nome_rede.startswith("AQ"):

        no_origem = "TA"

    else:

        no_origem = "CONTADOR"


    no_map[
        contador_id
    ] = no_origem


    troco_map[
        contador_id
    ] = "{0}-?".format(
        no_origem
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


        for vizinho_id in ligacoes.get(
            atual,
            []
        ):

            if vizinho_id in visitados:
                continue


            elem_vizinho = elemento_cache[
                vizinho_id
            ]


            # =================================================
            # FIXTURE
            # =================================================

            if e_fixture(
                elem_vizinho,
                nome_rede
            ):

                nome_lower = (
                    nome_cache[
                        vizinho_id
                    ].lower()
                )


                if "termoacumulador" in nome_lower:

                    troco_map[
                        vizinho_id
                    ] = "TA"

                    no_map[
                        vizinho_id
                    ] = "TA"


                else:

                    prefixo = prefixo_fixture(
                        nome_cache[
                            vizinho_id
                        ]
                    )

                    troco_map[
                        vizinho_id
                    ] = "{0}.{1}".format(
                        prefixo,
                        no_atual
                    )

                    no_map[
                        vizinho_id
                    ] = troco_map[
                        vizinho_id
                    ]


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

                    novo_no = (
                        novo_no_principal()
                    )

                else:

                    novo_no = (
                        nova_derivacao(
                            no_atual
                        )
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
            troco[:-2]
        )


        no_destino = None


        # IMPORTANTE:
        # deque em vez de list.pop(0)
        fila_busca = deque(
            ligacoes.get(
                elem_id,
                []
            )
        )


        visitados_busca = {
            elem_id
        }


        while (
            fila_busca
            and no_destino is None
        ):

            vizinho_id = (
                fila_busca.popleft()
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
            # Já tem nó
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
                        elemento_cache[
                            vizinho_id
                        ]
                    )


                    nome_lower = (
                        nome_cache[
                            vizinho_id
                        ].lower()
                    )


                    # ---------------------------------------
                    # TA
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
                                nome_cache[
                                    vizinho_id
                                ]
                            )
                        )


            # -----------------------------------------------
            # Continuar procura
            # -----------------------------------------------

            else:

                for proximo_id in ligacoes.get(
                    vizinho_id,
                    []
                ):

                    if (
                        proximo_id
                        not in visitados_busca
                    ):

                        fila_busca.append(
                            proximo_id
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

        elem_id = get_element_id(
            elem.elemento
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
            p is not None
            and not p.IsReadOnly
        ):

            p.Set(troco)


    return (
        elementos,
        troco_map,
        no_map
    )


# ============================================================
# ATRIBUIR NÓS AOS FITTINGS
# ============================================================

def atribuir_nos_a_fittings(doc):

    fittings = (
        FilteredElementCollector(doc)
        .OfCategory(
            BuiltInCategory.OST_PipeFitting
        )
        .WhereElementIsNotElementType()
        .ToElements()
    )


    atribuidos = 0
    sem_trocos = 0
    sem_no = 0
    ambiguos = 0
    sem_parametro = 0
    erros = 0


    # ========================================================
    # MAPAS DOS FITTINGS
    # ========================================================

    fitting_por_id = {}
    fitting_neighbors = {}

    # Troços diretamente ligados a cada fitting
    fitting_trocos_diretos = {}


    # --------------------------------------------------------
    # Primeira passagem pelos fittings
    # --------------------------------------------------------

    for fitting in fittings:

        fitting_id = get_element_id(
            fitting
        )

        fitting_por_id[
            fitting_id
        ] = fitting

        fitting_neighbors[
            fitting_id
        ] = []

        fitting_trocos_diretos[
            fitting_id
        ] = []


    # ========================================================
    # CONSTRUIR GRAFO DOS FITTINGS
    #
    # Fazemos isto UMA VEZ.
    #
    # Antes:
    # cada fitting voltava a percorrer os mesmos
    # redutores/fittings.
    #
    # Agora:
    # construímos o grafo uma única vez.
    # ========================================================

    for fitting in fittings:

        fitting_id = get_element_id(
            fitting
        )

        try:

            cm = get_connector_manager(
                fitting
            )

            if cm is None:
                continue


            it = cm.Connectors.ForwardIterator()


            while it.MoveNext():

                connector = it.Current

                if not connector.IsConnected:
                    continue


                refs_it = (
                    connector.AllRefs.ForwardIterator()
                )


                while refs_it.MoveNext():

                    owner = (
                        refs_it.Current.Owner
                    )


                    if owner is None:
                        continue


                    owner_id = get_element_id(
                        owner
                    )


                    if owner_id == fitting_id:
                        continue


                    if owner.Category is None:
                        continue


                    owner_category_id = int(
                        owner.Category.Id.Value
                    )


                    # ----------------------------------------
                    # PIPE
                    # ----------------------------------------

                    if (
                        owner_category_id
                        == PIPE_CATEGORY_ID
                    ):

                        p_troco = (
                            owner.LookupParameter(
                                "Troço"
                            )
                        )


                        if p_troco is None:
                            continue


                        troco = p_troco.AsString()


                        if not troco:
                            continue


                        troco = troco.strip()


                        if (
                            troco
                            not in fitting_trocos_diretos[
                                fitting_id
                            ]
                        ):

                            fitting_trocos_diretos[
                                fitting_id
                            ].append(
                                troco
                            )


                    # ----------------------------------------
                    # OUTRO FITTING
                    #
                    # Inclui REDUTORES
                    # ----------------------------------------

                    elif (
                        owner_category_id
                        == FITTING_CATEGORY_ID
                    ):

                        if (
                            owner_id
                            in fitting_por_id
                        ):

                            if (
                                owner_id
                                not in fitting_neighbors[
                                    fitting_id
                                ]
                            ):

                                fitting_neighbors[
                                    fitting_id
                                ].append(
                                    owner_id
                                )


        except:

            continue


    # ========================================================
    # ENCONTRAR COMPONENTES DE FITTINGS
    #
    # Todos os fittings ligados por redutores/outros fittings
    # pertencem ao mesmo componente.
    #
    # Os Troços desse componente são calculados UMA VEZ.
    # ========================================================

    fitting_component_trocos = {}

    componentes_visitados = set()


    for inicio_id in fitting_por_id:

        if inicio_id in componentes_visitados:
            continue


        componente = []
        componente_set = set()

        fila = deque(
            [inicio_id]
        )


        while fila:

            atual_id = fila.popleft()


            if atual_id in componente_set:
                continue


            componente_set.add(
                atual_id
            )

            componente.append(
                atual_id
            )


            for vizinho_id in fitting_neighbors.get(
                atual_id,
                []
            ):

                if (
                    vizinho_id
                    not in componente_set
                ):

                    fila.append(
                        vizinho_id
                    )


        componentes_visitados.update(
            componente_set
        )


        # ----------------------------------------------------
        # Recolher todos os Troços do componente
        # ----------------------------------------------------

        trocos_componente = []
        trocos_set = set()


        for fitting_id in componente:

            for troco in fitting_trocos_diretos.get(
                fitting_id,
                []
            ):

                if troco not in trocos_set:

                    trocos_set.add(
                        troco
                    )

                    trocos_componente.append(
                        troco
                    )


        # ----------------------------------------------------
        # Associar o mesmo resultado a todos os fittings
        # do componente.
        # ----------------------------------------------------

        for fitting_id in componente:

            fitting_component_trocos[
                fitting_id
            ] = trocos_componente


    # ========================================================
    # PROCESSAR FITTINGS
    # ========================================================

    for fitting in fittings:

        try:

            fitting_id = get_element_id(
                fitting
            )


            # ------------------------------------------------
            # PARAMETRO NÓ
            # ------------------------------------------------

            p_no = fitting.LookupParameter(
                "Nó"
            )


            if p_no is None:

                sem_parametro += 1

                continue


            # ------------------------------------------------
            # TROÇOS
            # ------------------------------------------------

            trocos = fitting_component_trocos.get(
                fitting_id,
                []
            )


            # ------------------------------------------------
            # PELO MENOS 2 TROÇOS
            # ------------------------------------------------

            if len(trocos) < 2:

                sem_trocos += 1

                continue


            # ------------------------------------------------
            # PREFIXOS / SUFIXOS
            # ------------------------------------------------

            prefixos = set()
            sufixos = set()


            for troco in trocos:

                if "-" not in troco:
                    continue


                prefixo, sufixo = (
                    troco.split(
                        "-",
                        1
                    )
                )


                prefixo = prefixo.strip()
                sufixo = sufixo.strip()


                if prefixo:
                    prefixos.add(
                        prefixo
                    )


                if sufixo:
                    sufixos.add(
                        sufixo
                    )


            # ------------------------------------------------
            # NÓ
            # ------------------------------------------------

            candidatos = [
                sufixo
                for sufixo in sufixos
                if sufixo in prefixos
            ]


            # ------------------------------------------------
            # SEM NÓ
            # ------------------------------------------------

            if not candidatos:

                sem_no += 1

                continue


            # ------------------------------------------------
            # AMBIGUO
            # ------------------------------------------------

            if len(candidatos) > 1:

                ambiguos += 1

                continue


            # ------------------------------------------------
            # NÓ
            # ------------------------------------------------

            no = candidatos[0]


            # ------------------------------------------------
            # READ ONLY
            # ------------------------------------------------

            if p_no.IsReadOnly:

                sem_parametro += 1

                continue


            # ------------------------------------------------
            # ESCREVER
            # ------------------------------------------------

            p_no.Set(no)


            # ------------------------------------------------
            # CONFIRMAR
            # ------------------------------------------------

            if p_no.AsString() == no:

                atribuidos += 1

            else:

                erros += 1


        except:

            erros += 1


    # ========================================================
    # RESUMO
    # ========================================================

    print("")
    print("==========================================")
    print("ATRIBUIR NÓS AOS FITTINGS")
    print("==========================================")
    print(
        "Fittings encontrados: {}".format(
            fittings.Count
        )
    )
    print(
        "NÓS ATRIBUIDOS: {}".format(
            atribuidos
        )
    )
    print(
        "SEM TROÇOS SUFICIENTES: {}".format(
            sem_trocos
        )
    )
    print(
        "SEM NÓ: {}".format(
            sem_no
        )
    )
    print(
        "AMBIGUOS: {}".format(
            ambiguos
        )
    )
    print(
        "SEM PARAMETRO / READ ONLY: {}".format(
            sem_parametro
        )
    )
    print(
        "ERROS: {}".format(
            erros
        )
    )
    print("==========================================")


# ============================================================
# ELEMENTOS DO MODELO
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
# CRIAR REDES
# ============================================================

redes = {}


for ele in elements:

    try:

        parametro_sistema = ele.get_Parameter(
            BuiltInParameter.RBS_SYSTEM_NAME_PARAM
        )

        if parametro_sistema is None:
            continue

        nome_sistema = (
            parametro_sistema.AsString()
        )

        if not nome_sistema:
            continue


        if not nome_sistema.startswith(
            ("AF", "AQ")
        ):

            continue


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

    except:

        continue


# ============================================================
# FITTINGS + ACESSÓRIOS
# ============================================================

for elem in (
    fittings_wrapped
    + accessories_wrapped
):

    try:

        parametro_sistema = (
            elem.elemento.get_Parameter(
                BuiltInParameter.RBS_SYSTEM_NAME_PARAM
            )
        )

        if parametro_sistema is None:
            continue

        nome_sistema = (
            parametro_sistema.AsString()
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

        parametro_sistema = (
            fixture.elemento.get_Parameter(
                BuiltInParameter.RBS_SYSTEM_NAME_PARAM
            )
        )

        if parametro_sistema is None:
            continue

        nome_sistema = (
            parametro_sistema.AsString()
        )

    except:

        continue


    if not nome_sistema:
        continue


    sistemas = [
        s.strip()
        for s in nome_sistema.split(",")
        if s.strip()
    ]


    for sistema in sistemas:

        if sistema not in redes:
            continue


        if fixture not in redes[
            sistema
        ]:

            redes[
                sistema
            ].append(
                fixture
            )


# ============================================================
# TRANSACTION
# ============================================================

t = Transaction(
    doc,
    "Relatorio Aguas"
)

t.Start()


try:

    # ========================================================
    # PROCESSAR REDES
    # ========================================================

    output_por_rede_temp = {}


    for nome_rede, elementos_rede in redes.items():

        print("")
        print(
            "======================================"
        )
        print(
            "REDE: {0}".format(
                nome_rede
            )
        )
        print(
            "======================================"
        )


        # ----------------------------------------------------
        # 1. GRAFO
        # ----------------------------------------------------

        (
            elementos_rede,
            ligacoes,
            id_to_elem,
            contador_id
        ) = gerar_trocos_automatico(
            elementos_rede
        )


        # ----------------------------------------------------
        # 2. NOMENCLATURA
        # ----------------------------------------------------

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


    # ========================================================
    # NÓS DOS FITTINGS
    # ========================================================

    atribuir_nos_a_fittings(
        doc
    )


    # ========================================================
    # COMMIT
    # ========================================================

    t.Commit()


except Exception as ex:

    print("")
    print(
        "ERRO GERAL: {}".format(
            ex
        )
    )

    try:
        t.RollBack()

    except:
        pass
