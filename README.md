# A Simple Blockchain-based Voting System

This is system is in two parts, the blockchain Network part and the decentralize application part. We begin with how to go about with the blockchain network part first and then how the decentralize application (In this case decentralize electronic voting system) is being integrated in the blockchain.

## Decentralized Peer-To-Peer Blockchain Network
This system provides a basic and simple decentralized peer-to-peer framework to start a p2p network. Basic functionality of the nodes and the connection to and from these nodes has been implemented.

As with any p2p network, you would have to start your own server in order to join the network.

### Prerequisites
This project was run and tested on windows 10 machine

1. Make sure [Python 3.9.6](https://www.python.org/downloads/) is installed. 
2. Make sure [Sqlite browser](https://www.sqlite.org/download.html) is installed.

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

5. You can set up a new node by making a copy of the code and repeating the steps above.

6. Note that the nodes on the network use `SOCKET` connection to connect to themselves. The port used by each node for this, is always `1000` more than the one used by the flask app. So to connect to a different node, you would need the ip address and the port(the one used for the socket connection) of the node.

7. Once a network of two or more nodes is set up successfully, basic funcitionality like mining, transacting, verifications of transctions, etc of any node on any peer to peer blockchain network could be achieved.


## Integrating A DApp On The Blockchain(E-VOTE APPLICATION)

Besides being used as a `Crypto Currency` system, this blockchain protocol also serves a platform for decentralize applications. It uses the concept of `smart Contract` to achieve this. This blockchain uses the stateful protocol. State is like a result created by the blockchain where you can get accounts’ information like balance or used timestamps.
This blockchain protocol follows an account-based model, which is better for smart contracts and is also used by Ethereum, while Bitcoin and many other networks use the UTxO (unspent transactions’ output) model. This model works like a key-value database, with
the key being an address, and the value is its information. Every time a new transaction is submitted, the state will be changed according to the information in the transactions.

This Blockchain protocol provides APIs where transactions from such decentralize applications could submit transactions to the network and get some information about those contracts.
```
Any Decentralize application used in this project can be found in the `Applications folder` in the root directory.
```
### Electronic Voting System Used In this Project

Per the decentralize application being integrated with the blockchain, you can add other nodes to the network besides the actual `Miner Nodes' who are helping to establish the network.
In this our application of voting, we introduced two other different type of nodes, `Registration Authority` and `Board Member` nodes.

#### Registration Authority(RA)
This entity is like an Election Commissioner. This entity is responsible for starting the whole election process. He creates and initialize some information like the election id, election addresss, etc at the start of the whole process.

#### Board Member
There is always more than one board member, each indicating a reprensentative from the various political parties involved in the election. This entity is responsible for submitting information about his/ her party the registration authority.

```
Of course, besides the stated nodes in this application, there are also voters who are engaged in this whole election process.
```

### STEP BY STEP ACTIVITIES IN THE VOTING PROCESS
Access the `Application folder` and initiliaze the databases of the RA and board using the 
`queries.sql` of each of them by imorting file using sqlite browser. After initializing the database for the RA and each of the board you want to be involded, you run the flask application for each of them and create the profile and get public and private key for each entity. You then run the application to be used by the voters.

#### STEPS
1. The RA initiate the election from the graphic interface, to get the address which you would be used as the public key for the election smart contract when deployed to the blockchain network.

2. Each board member reprensenting various political parties acquire information for each candidates for the various portfolio and submit that information together with the public key of that board to the RA.

3. After all board members have submitted thier candidates information to the RA. The RA creates the election smart contract with the informatin provided by each of the board.
```
In this application, there are only two portfolio, 'President and Parliament(for each constituency). We assumed only two constituencies for demonstration purposes. In our case, the smart contract was prewritten using the python programming language. It can be found in the RA directory.
```

4. The RA configure the election information, like the start and end date of the election including the time.

5. The RA then deploys(sends it as a transaction to any miner node) it to the network.

6. No Ballot paper(transaction from a voter to the smart contract) would be accepted by the smart contract unless the Board Members approve(transation from BM to SC indicating approval) the smart contract.

7. After all the board members have approved, the election has officially begun.

8. To vote, a user has to login to be verified since only elible voters are required to take part of the election. The RA maintains a list of voters who are elible to vote.

9. A voter logs in, gets verified and the RA generates a signed ballot paper(contains information about the candidates) for the voter. Each voter has a unique ballot signed by the RA which would be verify by the smart contract on submitted to prevent the forgery of ballot papers by the unlawful entities.

10. Voters are supposed to vote within the allocated time, since the system does not accept any transaction to a smart contract that has expired.

11. Once the election is over, the RA, the board members and the voters can view the election results



