from src.blockchain.mudscript.mudscript import mud_script

def change_state(new_block, state):
    for tx in new_block.data:
        if (not tx.to_addr in state):
            state[tx.to_addr] = {
                'balance': 0,
                'body': "",
                'timestamps': [],
                'storage': {}
            }
        
        if (not tx.from_addr in state):
            state[tx.from_addr] = {
                'balance': 0,
                'body': "",
                'timestamps': [],
                'storage': {}
            }

            if (tx.to_addr.startswith("SC")):
                state[tx.from_addr]['body'] = tx.to_addr
            
        elif (tx.to_addr.startswith("SC") and state[tx.to_addr]['body'] == ""):
            state[tx.from_addr]['body'] = tx.to_addr
        

        state[tx.to_addr]['balance'] += tx.value
        state[tx.from_addr]['balance'] -= (int(tx.value) + int(tx.gas))

        state[tx.from_addr]['timestamps'].append(tx.timestamp)
    return state

def trigger_contract(new_block, state, blk_chain, log):
    for tx in new_block.data:
        if state[tx.to_addr]['body'] != "":
            try:
                [state[tx.to_addr]['storage'], state[tx.to_addr]['balance']] = mud_script(
                    state[tx.to_addr]['body'].replace("SC", ""),
                    state[tx.to_addr]['storage'], 
                    state[tx.to_addr]['balance'] - tx.value,
                    tx.args,
                    tx.from_addr,
                    { 'difficulty': blk_chain.difficulty, 'timestamp': blk_chain.chain[-1].timestamp },
                    tx.to_addr,
                    tx.value,
                    not log
                )
            except Exception as err:
                print(("LOG :: Error at contract " + tx.to_addr + err))