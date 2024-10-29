import os
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.approximation import traveling_salesman_problem

# Función para convertir las distancias a valores numéricos
def convertir_distancia(pasillo_1, pasillo_2, nave_1, nave_2, distancia):
    unidad_mapeo = {
        'mc': 10,  # mili
        'c': 20,   # centi
        'i': 30,   # unidad base
        'l': 45,   # kilo
        'ml': 60,   # micro
        'xml': 70,
        'Xxml': 140
    }
    pasillo_1 = str(pasillo_1)
    pasillo_2 = str(pasillo_2)

    if pasillo_1 == 'club gourmet' or pasillo_2 == 'club gourmet':
        distancia = 'Xxml'

    if pasillo_2.isdigit():
        if pasillo_1 == 'carnicería' and int(pasillo_2) > 16:
            distancia = 'xml'

        if pasillo_1 == 'charcutería' and int(pasillo_2) > 16:
            distancia = 'xml'

        if pasillo_1 == 'pescadería' and int(pasillo_2) > 16:
            distancia = 'xml'

    if pasillo_1.isdigit():
        if pasillo_2 == 'carnicería' and int(pasillo_1) > 16:
            distancia = 'xml'

        if pasillo_2 == 'pescadería' and int(pasillo_1) > 16:
            distancia = 'xml'

        if pasillo_2 == 'charcutería' and int(pasillo_1) > 16:
            distancia = 'xml'
    # Convertir usando el mapeo
    return unidad_mapeo[distancia]

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, '../data/input')
    output_dir = os.path.join(base_dir, '../data/output')
    #Fichero que se genera de generate_distances.py y contiene la información de distancias entre todos los productos de cada pedido
    file_name = "distancias_por_pedidos_relleno_completed.xlsx"
    file_path = os.path.join(input_dir, file_name)
    file_name_complete = "df_complete.xlsx"
    file_path_complete = os.path.join(input_dir, file_name_complete)
    df_complete = pd.read_excel(file_path_complete)
    # Leer todas las hojas en un diccionario
    pedidos_rellenos = pd.ExcelFile(file_path)

    lista_dfs = []
    dict_tsp = {
        'pedido': [],  # dict to store results
        'ruta': [],
        'distancia': [],
        'distancia_by_order': [],
        'tam_pedido': []
    }

    columns_to_int = ['Depto_a', 'Depto_b', 'Familia_a', 'Familia_b', 'Barra_a', 'Barra_b']
    columns_to_str = ['Nave_a', 'Nave_b', 'pasillo_a', 'pasillo_b', 'gondola_a', 'gondola_b']

    for pedido in pedidos_rellenos.sheet_names:

        df_order = df_complete[df_complete['Codigo de Pedido'] == int(pedido)]
        df_order = df_order.drop_duplicates(subset=['Codigo de Pedido', 'Descripcion'])

        df_pedido = pd.read_excel(file_path, sheet_name=pedido)
        df_pedido[columns_to_int] = df_pedido[columns_to_int].astype(float).astype(int)
        df_pedido[columns_to_str] = df_pedido[columns_to_str].astype(str)

        dict_tsp['pedido'].append(pedido)
        G = nx.Graph()
        # Add edges to the graph with filtered distances
        for _, row in df_pedido.iterrows():
            nodo_a = (row['Nave_a'], row['pasillo_a'], row['gondola_a'], row['Depto_a'], row['Descripcion_a'])
            nodo_b = (row['Nave_b'], row['pasillo_b'], row['gondola_b'], row['Depto_b'], row['Descripcion_b'])
            distancia = convertir_distancia(row['pasillo_a'], row['pasillo_b'], row['Nave_a'], row['Nave_b'], row['Distancia'])
            G.add_node(nodo_a)
            G.add_node(nodo_b)
            G.add_edge(nodo_a, nodo_b, weight=distancia)  # add edge to graph

        ciclo_tsp = traveling_salesman_problem(G, cycle=False)  # solve TSP
        dict_tsp['ruta'].append(ciclo_tsp)  # store TSP route
        distancia_total_tsp = 0
        for i in range(len(ciclo_tsp) - 1):
            u = ciclo_tsp[i]
            v = ciclo_tsp[i + 1]
            try:
                distancia_total_tsp += G[u][v]['weight']  # accumulate total distance
            except KeyError as e:
                print(f"Error: No edge found between {u} and {v} in the graph.")
                continue
        dict_tsp['distancia'].append(distancia_total_tsp)  # store total distance


        comb_order = []
        filas_pedido = list(df_order.iterrows())
        # Iterar sobre las filas del pedido actual
        for i in range(len(filas_pedido) - 1):
            # Obtener la fila actual (a) y la siguiente (a+1)
            _, fila_a = filas_pedido[i]
            _, fila_b = filas_pedido[i + 1]

            # Crear un diccionario para almacenar la combinación de las filas
            combinacion = {'Codigo de Pedido': pedido}

            # Añadir las columnas para la combinación a y b
            for col in df_order.columns:
                if col != 'Codigo de Pedido':  # Evitar duplicar la columna 'Codigo de Pedido'
                    combinacion[f'{col}_a'] = fila_a[col]
                    combinacion[f'{col}_b'] = fila_b[col]

            # Añadir la combinación a la lista
            comb_order.append(combinacion)  # Añadir el diccionario creado en esta iteración

        # Convertir la lista de combinaciones en un DataFrame
        df_combinado_final = pd.DataFrame(comb_order)
        df_combinado_final = df_combinado_final.drop(['CO_ARTICULO_a', 'CO_ARTICULO_b', 'Empresa_a', 'Empresa_b', 'Cluster pedidos_b'], axis=1)
        df_pedido_to_join = df_pedido[['Descripcion_a', 'Descripcion_b', 'Distancia']]
        df_combinado_final = pd.merge(df_combinado_final, df_pedido_to_join, how='left', on=['Descripcion_a', 'Descripcion_b'])
        # Verificar el resultado
        df_combinado_final = df_combinado_final.sort_values(by=['Nave_a', 'Nave_b', 'pasillo_a', 'pasillo_b', 'Depto_a', 'Depto_b'])
        df_combinado_final['distancia_convertida'] = df_combinado_final.apply(lambda row: convertir_distancia(row['pasillo_a'], row['pasillo_b'], row['Nave_a'], row['Nave_b'], row['Distancia']), axis=1)
        # Sumar la columna de distancias convertidas
        suma_distancias = df_combinado_final['distancia_convertida'].sum()
        dict_tsp['distancia_by_order'].append(suma_distancias)
        dict_tsp['tam_pedido'].append(df_combinado_final['Cluster pedidos_a'].iat[0])


    # Crear dataframe para comparar distancias originales y distancias con best route
    df_comparativo = pd.DataFrame(dict_tsp)
    df_comparativo['diferencia'] = df_comparativo['distancia_by_order'] - df_comparativo['distancia']
    df_comparativo['diferencia_pcr'] = (df_comparativo['diferencia'] / df_comparativo['distancia_by_order']) * 100
    lista_dfs.append([pedido,df_comparativo])
    df_agrupado = df_comparativo.groupby('tam_pedido')[['diferencia', 'diferencia_pcr']].mean().reset_index()
    print(df_agrupado)

    for df in lista_dfs:

        print(df)

if __name__ == "__main__":
    main()
