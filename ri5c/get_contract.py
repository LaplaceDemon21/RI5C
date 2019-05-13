# -*- coding: utf-8 -*-

import os
# BigQuery
from google.cloud import bigquery
from google.oauth2 import service_account
# Data Science and Networks
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg') # Important because no GUI in vagrant or server
import matplotlib.pyplot as plt
import community # Detecting communities
import pylab # Exporting figures
# For logarithmic stuff
from math import *
# Miscellaneous
import json # to build object that can be fed to sigma.js
from ri5c import settings

# Note to self: Interesting to consider using Gremlin for querying the databases
# M. Beck's rec
# https://pypi.org/project/gremlinpython/

def get_contract(contract_address, limit=1000):
    # This needs to be converted to Parametrized SQL
    # this https://cloud.google.com/bigquery/docs/parameterized-queries#bigquery-query-params-cli
    
    # TODO clean contract address to small caps
    contract_address = contract_address.lower()
    print ("Getting query...")
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

    # === Generate credentials and connect to BigQuery
    
    # Read env data and get JSON data from production level var
    set_googlebq_credentials()

    # Instantiate BigQuery
    bql = bigquery.Client()

    # Query
    query_job = bql.query(test_query)
    iterator = query_job.result(timeout=30)
    rows = list(iterator)

    print ("Finished getting data")
    # This returns a simple dataset that can be used and tested
    return rows

def set_googlebq_credentials():
    '''
    If you're doing this from production in Heroku, you might need something like this:
    $heroku config:set GOOGLE_APPLICATION_DATA="$(< ./config/big_query_creds.json)" -a HEROKU_APP
    '''
    production = settings.PRODUCTION
    if production == False:
        return False

    # Read env data and get JSON data from production level var
    credentials_raw = os.environ.get('GOOGLE_APPLICATION_DATA')
    # save to JSON
    data = json.loads(credentials_raw)
    # Write data to temporary json file
    with open('data.json', 'w') as outfile:
        json.dump(data, outfile)

    return True


def create_graph(contract):
    # Create graph
    print ("Creating a simple graph...")
    G = nx.Graph()
    # Pandas dataframe TODO: this method should be extracted
    sorted_list = [u'token_address', u'from_address',  u'to_address', u'value', u'transaction_hash', u'log_index' ,u'block_timestamp', u'block_number', u'block_hash']
    data=[list(x.values()) for x in contract]

    df = pd.DataFrame(data=data, columns=sorted_list)

    G = nx.from_pandas_edgelist(df, source='from_address', target='to_address', edge_attr=["value", "transaction_hash"])

    print ("Graph created.")
    print(nx.info(G))

    # Get Avg Degree for graph_data
    nnodes = G.number_of_nodes()
    s=sum(dict(G.degree()).values())
    avg_degree = (float(s)/float(nnodes))
    graph_data = {"density": nx.density(G), "degree": avg_degree, "nodes": nnodes, "edges": G.number_of_edges() }

    return G, graph_data

# I think this is a duplicate
# Created with F. Ramírez Alatriste – it's a weighted graph - 01.02.2019
def create_graph_new(contract):
    # TODO: This should be updated to stuff above, and probably DRY code.
    print ("Creating a simple graph...")
    G = nx.Graph()
    # Pandas dataframe

    df = pd.DataFrame(data=[list(x.values()) for x in contract], columns=list(contract[0].keys()))
    # Graph

    G = nx.from_pandas_edgelist(df, source='from_address', target='to_address', edge_attr="value")
    print ("Graph created.")
    print (nx.info(G))
    return G

def draw_graph(graph, filename='network.png', x=100, y=100):
    print ("Starting to draw...")
    G = graph
    #first compute the best partition
    partition = community.best_partition(G)
    plt.figure(figsize=(x,y))
    #drawing
    size = float(len(set(partition.values())))
    pos = nx.spring_layout(G)
    count = 0.0
    for com in set(partition.values()) :
        count = count + 1.
        list_nodes = [nodes for nodes in partition.keys()
                                    if partition[nodes] == com]
        nx.draw_networkx_nodes(G, pos, list_nodes, node_size = 20,
                                    node_color = str(count / size))

    # Draw
    nx.draw_networkx_edges(G, pos, alpha=0.5)

    print ("And now, let's save it in ", filename)
    pylab.savefig('network.png')

# WEIGHTED VERSION
# This graph weights the vertexes, not the nodes. I need to find a way to weigh the nodes, vertexes can remain thin or change with colour, or length
def draw_weighted_graph(graph, filename='network_weighted.png', x=500, y=500):
    print ("Starting to draw a weighted graph...")
    G = graph

    node_degree_size=[G.degree(n) for n in G.nodes()] # This is what makes nodes larger

    options = { 
        'node_color': 'blue', 
        'node_size': node_degree_size, 
        'width': 1, # What does this do?
        'arrowstyle': '-|>', 
        'arrowsize': 12, # What does this do?
    }

    # LOG INDEX IS A TEMP MEASURE, needs to be changed
    weights = [0.1*log(float(i['log_index'])) for i in dict(G.edges).values()]
    #print (weights)
    #nx.draw(g,**options)
    fig, ax = plt.subplots(figsize=(x,y))
    pos = nx.spring_layout(G)
    nx.draw_networkx_nodes(G, pos, ax = ax, node_size=node_degree_size, labels=True)
    nx.draw_networkx_edges(G, pos, width=weights, ax=ax)

    print ("And now, let's save it in "+filename)
    pylab.savefig('network_weighted.png')

def generate_sigma_network(graph):
    '''
    NOTE: G should include edge_attr="value" ie: G2 = nx.from_pandas_edgelist(df, source='from_address', target='to_address', edge_attr="value")
    This method should generate a JSON with sigmajs readable format
    It should integrate Nodes, Edges and positions
    '''
    print ("Starting to generate sigma.js compatible graph...")
    
    G = graph
    # POSITION: First compute the best partition and get positions
    partition = community.best_partition(G)
    pos = nx.spring_layout(G) # should try other layouts
    
    # COLOR - using louvain, should work on this more, colors are unnappealing and weird
    colors = {}
    for node in G.nodes():
        colors[node] = '{0:06X}'.format(partition.get(node)*70000)

    # NODE SIZE - Calculate node size
    node_size = {}
    for node in G.nodes():
        ne = G.edges(node, data=True)
        value = 0
        for v in ne:
            value += int(v[2]["value"])
        node_size[node] = value # Should add a log or something

    # Weights
    weights = []
    for e in dict(G.edges).values():
        if float(e['value']) != 0.0:
            weights.append(float(e['value']))
        else:
            weights.append(0.0)

    # txids
    txids = []
    for e in dict(G.edges).values():
        txids.append(e['transaction_hash'])
        
    # Init JSON
    data ={ 'nodes': [], 'edges': [] }

    # Nodes
    for n in G.nodes:
        data['nodes'].append({
                "id": n,
                "label": n+", total volume: "+ str(node_size[n]),
                "x": pos[n][0],
                "y": pos[n][1],
                "size": node_size[n],
                "color": "#"+colors[n]
            })

    # Edges
    for i, e in enumerate(G.edges):
        data['edges'].append({
                "id": "e" + str(i),
                "label": txids[i],
                "source": e[0],
                "target": e[1],
                "color": "rgba(190,190,190,0.4)", # Last digit is transparency
                "type": 'arrow',
                "size": weights[i]
            })
    
    print ("Finally, let's return data :)")

    return json.dumps(data)

def network_this(contract, limit=1000):
    contract = get_contract(contract, limit)
    graph = create_graph(contract)
    draw_graph(graph)
    print ("Success")
    pass

def network_this_w(contract, limit=1000):
    contract = get_contract(contract, limit)
    graph = create_graph_new(contract)
    draw_weighted_graph(graph)
    print ("Success")
    pass

