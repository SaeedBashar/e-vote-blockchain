# A Simple Blockchain-based Voting System

This is system is in two parts, the blockchain Network part and the decentralize application part. We begin with how to go about with the blockchain network part first and then how the decentralize application (In this case decentralize electronic voting system) is being integrated in the blockchain.

## Decentralized Peer-To-Peer Blockchain Network
This system provides a basic and simple decentralized peer-to-peer framework to start a p2p network. Basic functionality of the nodes and the connection to and from these nodes has been implemented.

As with any p2p network, you would have to start your own server in order to join the network.

### Prerequisites
This project was run and tested on windows 10 machine

1. Make sure [Python 3.9.6](https://www.python.org/downloads/) is installed. 
2. Make sure you install Sqlite database

```
pip install -r requirements.txt
```

### Setting Up A Node
1. To begin, you first need to import `queries.sql` file in the `database` folder at the root folder from `sqlite browser` and create the database needed to keep track of ledger and other resources needed by every node on the network.

2. While you are in the root folder, run the flask application by executing
```
py app.py
```
from the command line.

3. The default port for the flask application is `4000`, you can specify a different one when runnng the app `--port NEW_PORT`.

4. Access the Graphic User Interface, and create a wallet by signing up to create a profile and get a private and public key to be used for your transactions on the netowrk.


### How It Looks

![alt tag](https://raw.githubusercontent.com/SaeedBashar/e-vote-blockchain/master/docs/signup.jpg)
