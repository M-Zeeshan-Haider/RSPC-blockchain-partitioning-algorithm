import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import random 
import sqlite3
import requests
from flask import Flask, jsonify, request

repValue = 0.0
conn = sqlite3.connect('rscp.db')
c = conn.cursor()

def create_table():
    c.execute('CREATE TABLE IF NOT EXISTS nodes(id INTEGER PRIMARY KEY, host TEXT, rep FLOAT, consType INT, partType INT)')

def create_rep():
    c.execute('CREATE TABLE IF NOT EXISTS node_reputation(id INTEGER PRIMARY KEY, host TEXT, rep FLOAT, repGrowth FLOAT)')

def create_part():
    c.execute('CREATE TABLE IF NOT EXISTS partitions(id INTEGER PRIMARY KEY, node_id INT, rep FLOAT, repGrowth FLOAT)')

def create_localchain():
    c.execute('CREATE TABLE IF NOT EXISTS da_st(id INTEGER PRIMARY KEY, part_id INT, node_id INT, block TEXT)')

def data_entry():
    c.execute("INSERT INTO nodes(host, rep, consType, partType) VALUES('5001', 0.5, 0, 0)")
    conn.commit()
    c.close()

create_table()
create_rep()
create_part()
create_localchain()
data_entry()

class Blockchain:
    def __init__(self):
        global repValue
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        repValue = 0.5
        respons = 0.0
        mf = 0.1*2.5
        ir = 0.3*3.5
        er = 0.3*1
        ar = 0.1*1.4



        repGr = 50

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address of node. Eg. 'http://192.168.0.5:5001'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5001'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')
        
    def exit_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address of node. Eg. 'http://192.168.0.5:5001'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.remove(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def insert_partition(self):
      

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.remove(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')        

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        

        return self.last_block['index'] + 1

    def get_reputation(self):
        respons = requests.get("http://localhost:5001/nodes/reputation")
        return respons
    
#         """
#         This is our consensus algorithm, it resolves reputation values
#         by replacing our chain with the longest one in the network.
#         :return: True if our chain was replaced and display reputation value, False if not
#         """

#         neighbours = self.nodes
#         new_chain = None

#         # We're only looking for chains longer than ours
#         max_length = len(self.chain)

#         # Grab and verify the chains from all the nodes in our network
#         for node in neighbours:
#             response = requests.get(f'http://{node}/chain')

#             if response.status_code == 200:
#                 length = response.json()['length']
#                 chain = response.json()['chain']

#                 # Check if the length is longer and the chain is valid
#                 if length > max_length and self.valid_chain(chain):
#                     max_length = length
#                     new_chain = chain

#         # Replace our chain if we discovered a new, valid chain longer than ours
#         if new_chain:
#             self.chain = new_chain
#             return True

#         return False





    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    global repValue
    repValue = repValue + 1
    
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)
    
    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )
    
    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    global repValue
    repValue = repValue + 1
    # c = conn.cursor()
    # def data_entry():
    #     c.execute("UPDATE nodes SET rep=? WHERE host=? ",(repValue,'5001'))
    #     conn.commit()
    #     c.close()
    # data_entry()
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    c = conn.cursor()
    def data_entry():
        c.execute("INSERT INTO dag_st(node_id, part_id, block) VALUES(1, 5001, '3')")
        conn.commit()
        c.close()     
    data_entry()

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/vrfnode', methods=['GET'])
def vrf_node():

    prnm = random.choice(list(blockchain.nodes))

    response = {
        'message': 'This is the selected VRF consensus node',
        'VRF_nodes': prnm , 
    }
    return jsonify(response), 201

@app.route('/nodes/list', methods=['GET'])
def list_nodes():

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    global repValue
    repValue = repValue + 1
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/reputationupdate', methods=['GET'])
def rep_chain():
    values = request.get_json()

    rep = values.get('rep')
    # mf+ir+er+ar
    repGrowth = values.get('repGrowth')
    # ((rep/0.5)-1)*1
    c = conn.cursor()
    def data_entry():
        c.execute("INSERT INTO node_reputation(host, rep, repGrowth) VALUES(?, ?, ?)",('5001',rep,repGrowth))
        conn.commit()
        c.close()     
    data_entry()
    
    
    c = conn.cursor()
    def data_entry():
        c.execute("UPDATE nodes SET consTYPE=? WHERE host=? ",(1,'5001'))
        conn.commit()
        c.close()
    data_entry()


    response = {
        'reputation': rep,
        'growth': repGrowth
    }
    return jsonify(response), 200


# c.execute("UPDATE nodes SET rep=? WHERE host=? ",(repValue,'5001'))
@app.route('/nodes/exit', methods=['POST'])
def exit_nodes():
    global repValue
    repValue = repValue + 1
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.exit_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201
# @app.route('/nodes/resolve', methods=['GET'])
# def consensus():
#     replaced = blockchain.resolve_conflicts()

#     if replaced:
#         response = {
#             'message': 'Our chain was replaced',
#             'new_chain': blockchain.chain
#         }
#     else:
#         response = {
#             'message': 'Our chain is authoritative',
#             'chain': blockchain.chain
#         }

#     return jsonify(response), 200


@app.route('/nodes/getreputations', methods=['GET'])
def get_reputation():
    #r = blockchain.get_reputation()
    reps = []
    
    #response = requests.get("http://localhost:5002/nodes/reputation")
    #data = response.json()
    #reps.append(data)

    for val in blockchain.nodes: 
        response = requests.get("http://" + val + "/nodes/reputation")
        data = response.json()
        reps.append(data)
    #r = requests.get("http://localhost:5001/nodes/reputation", headers={
    #'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"
    #})

    #for i in blockchain.nodes:
        #response = requests.get(blockchain.nodes[i]+"/reputation")
        #data = response.json()
        #reps.append(data)

    #print(nodes) 
    #esponse = {
    #    'reputation' : respons
    #}
       # print(json.load(reps[0]).host5001)
        
    return jsonify(reps)

@app.route('/nodes/reputation', methods=['GET'])
def reputation():
    #global repValue
    #repValue = repValue + 1
    response = {
        'reputation' : repValue
    }
    # c = conn.cursor()
    # def data_entry():
    #     c.execute("UPDATE nodes SET rep=? WHERE host=? ",(repValue,'5001'))
    #     conn.commit()
    #     c.close()
    # data_entry()
    return jsonify(response)


@app.route('/nodes/partitioning', methods=['POST'])
def partitioning():

    global repValue

    values = request.get_json()

    repGrowth = values.get('rg')

    length = len(blockchain.nodes)
    if length < 10 :
        p = length/2
        # blockchain.insert_partition(p)
        c = conn.cursor()
        def data_entry():
            c.execute("INSERT INTO node_partition(node_id, rep, repGrowth) VALUES(?, ?, ?)",('5001',repValue,repGrowth))
            conn.commit()
            c.close()     
        data_entry()
    else :
        p = length/3
        def data_entry():
            c.execute("INSERT INTO node_partition(node_id, rep, repGrowth) VALUES(?, ?, ?)",('5001',rep,repGrowth))
            conn.commit()
            c.close()     
        data_entry()    
    response = {
        'partition status' : 'updated to new consensus'
    }
    
    return jsonify(response)
    
@app.route('/nodes/latency', methods=['POST'])
def latency():
    values = request.get_json()
    nodes = values.get('nodes')
    st = values.get('stime')
    nt = values.get('ntime')
    lat = nt-st

    response = {
        'latency is': lat
    }
    return jsonify(response), 201

@app.route('/nodes/throughput', methods=['POST'])
def throughput():
    values = request.get_json()
    blockTime = values.get('btime')
    
    th = blockTime/100

    response = {
        'throughput is': th
    }
    return jsonify(response), 201

@app.route('/nodes/byThroughput', methods=['POST'])
def bythroughput():
    values = request.get_json()
    blockTime = values.get('btime')
    byNode = values.get('bnodes')
    
    th = blockTime/100

    response = {
        'throughput is': th
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    global repValue
    repValue = repValue + 1
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


@app.route('/globalChain', methods=['GET'])
def global_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/updateDag', methods=['GET'])
def dag_st():
    values = request.get_json()
    nodeid = values['node_id']
    partid = values['part_id']
    block = values['blockkid']

    c = conn.cursor()
    dag_level = 1
    def data_entry():
        dagchain = c.execute("INSERT INTO dag_st(node_id, part_id, block) VALUES(?, ?, ?)",(nodeid, partid, block))
        dchain = dagchain.fetchall()
        conn.commit()
        c.close()     
    data_entry()

    dag_level = dag_level+1
    response = {
        'chain': lchain,
        'length': len(lchain),
    }
    return jsonify(response), 200



if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)