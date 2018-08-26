
# RI5C Risk Index Coefficient
## Python - NetworkX – Postgres implementation of an easy to use, interoperable framework to measure the risk coefficient of ERC20 contracts.  First implementation will use NetworkX: https://github.com/networkx/networkx

### Motivation
Due to the public nature of transaction data on blockchain based financial systems, it is possible to model these systems as a network and analyze its structure to provide and define whether the different variables that emerge in the transaction history of ERC20 tokens can be used to correlate the health of the system and therefore propose a risk coefficient that quantifies how active the token is, how distributed it is and inferr how likely it is to respond to contagion and how stable the price is.

### Quick start
```
vagrant up
get server running and start creating stuff
vagrant ssh

$ cd /vagrant/
$ python ?
```
### Load data
Here a contract address should be specified ```0x...```

Database created is called "mydb", to load psql console type:
```
psql -d mydb
```

### Evaluate
Where the magic will happen – we extract transactions, model the network and provide an analysis.
