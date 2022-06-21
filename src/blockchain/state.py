from src.blockchain.mudscript.mudscript import mud_script

def change_state(new_block, state):
    for tx in new_block.data:
        if (state[tx.to_addr] == None):
            state[tx.to_addr] = {
                'balance': 0,
                'body': "",
                'timestamps': [],
                'storage': {}
            }
        
        if (state[tx.from_addr] == None):
            state[tx.from_addr] = {
                'balance': 0,
                'body': "",
                'timestamps': [],
                'storage': {}
            }

            if (tx.to.startsWith("SC")):
                state[tx.from_addr]['body'] = tx.to_addr
            
        elif (tx.to.startsWith("SC") and state[tx.to].body == None):
            state[tx.from_addr]['body'] = tx.to_addr
        

        state[tx.to_addr]['balance'] += tx.value
        state[tx.from_addr]['balance'] -= tx.amount + tx.gas

        state[tx.from_addr]['timestamps'].append(tx.timestamp)

def trigger_contract(new_block, state, chain, log):
    for tx in new_block.data:
        if state[tx.to]['body'] != "":
            try:
                [state[tx.to_addr]['storage'], state[tx.to_addr]['balance']] = mud_script(
                    state[tx.to_addr]['body'].replace("SC", ""),
                    state[tx.to_addr].storage, 
                    state[tx.to_addr].balance - tx.value,
                    tx.args,
                    tx.from_addr,
                    { 'difficulty': chain.difficulty, 'timestamp': chain[-1].timestamp },
                    tx.to_addr,
                    tx.value,
                    not log
                )
            except Exception as err:
                print(("LOG :: Error at contract " + tx.to_addr + err))