# -*- coding: utf-8 -*-

from google.cloud import bigquery
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg') # Important because no GUI in vagrant or server
import matplotlib.pyplot as plt
import community # Detecting communities
import pylab # Exporting figures

def get_contract(contract_address, limit=1000):
    # Instantiate Big Query
    bigquery_client = bigquery.Client()
    
    # This needs to be converted to Parametrized SQL
    # this https://cloud.google.com/bigquery/docs/parameterized-queries#bigquery-query-params-cli
    
    # TODO clean contract address to small caps
    contract_address = contract_address.lower()
    print "Getting query..."
    test_query = """
        #standardSQL
        SELECT
          *
        FROM
          `bigquery-public-data.ethereum_blockchain.token_transfers`
        WHERE
          token_address='%s'
        LIMIT
          %s
    """ % (contract_address, limit)

    # Connect
    bql = bigquery.Client()
    # Query
    query_job = bql.query(test_query)
    iterator = query_job.result(timeout=30)
    rows = list(iterator)

    print "Finished getting data"
    # This returns a simple dataset that can be used and tested
    return rows

def create_graph(contract):
    # Create graph
    print "Creating a simple graph..."
    G = nx.Graph()
    # Pandas dataframe
    df = pd.DataFrame(data=[list(x.values()) for x in contract], columns=list(contract[0].keys()))
    # Create Nodes
    nodes = df['to_address'].unique()
    G.add_nodes_from(nodes)
    # Create edges
    for index, row in df.iterrows():
        G.add_edge(row['to_address'], row['from_address'])

    print "Graph created."
    print(nx.info(G))
    return G

def draw_graph(graph, filename='network.png', x=100, y=100):
    print "Starting to draw..."
    G = graph
    #first compute the best partition
    partition = community.best_partition(G)
    plt.figure(figsize=(x,y))
    #drawing
    size = float(len(set(partition.values())))
    pos = nx.spring_layout(G)
    count = 0.
    for com in set(partition.values()) :
        count = count + 1.
        list_nodes = [nodes for nodes in partition.keys()
                                    if partition[nodes] == com]
        nx.draw_networkx_nodes(G, pos, list_nodes, node_size = 20,
                                    node_color = str(count / size))

    # Draw
    nx.draw_networkx_edges(G, pos, alpha=0.5)

    print "And now, let's save it in "+filename
    pylab.savefig('network.png')


def network_this(contract, limit=1000):
    contract = get_contract(contract, limit)
    graph = create_graph(contract)
    draw_graph(graph)
    print "Success"
    pass

from ri5c.get_contract import network_this, get_contract, create_graph, draw_graph
# g = nx.from_pandas_edgelist(df, source='from_address', target='to_address',edge_attr="value")
# Weighted example 
# weights = [0.1*math.log(i['value']) for i in dict(g.edges).values()]
# #print(weights)
# #nx.draw(g,**options)
# fig, ax = plt.subplots(figsize=(18,18))
# pos = nx.spring_layout(g)
# nx.draw_networkx_nodes(g, pos, ax = ax,node_size=node_degree_size, labels=True)
# nx.draw_networkx_edges(g, pos, width=weights, ax=ax)
