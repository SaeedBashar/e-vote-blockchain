

def mud_script(input:str, storage, balance, user_args, address,
               block_info, contract_address, gas, disable_logging = False):
               
        instructions = input.strip().replace('\t', "").split('\n')
        instructions = filter(lambda x: x != '', instructions)

        memory = {}
        user_args = map(lambda x : str(x), user_args)

        ins_ptr = 0

        while ins_ptr < len(instructions) and gas >= 0:
            line = instructions[ins_ptr].strip()
            command = filter(lambda x: x != '' , str(line).split(" "))[0]

            args = filter(lambda x: x != '' , line[len(command) + 1:].replace('\s', '').split(','))

            if command == 'set':
                memory[args[0]] = get_value(args[1], memory, user_args)

            elif command == 'balance':
                memory[args[0]] = str(balance)

            elif command == 'address':
                memory[args[0]] = address
            
            elif command == 'timestamp':
                memory[args[0]] = block_info['timestamp']
            
            elif command == 'difficulty':
                memory[args[0]] = block_info['difficulty']

            elif command == 'store':
                storage[get_value(args[0], memory, user_args)] = get_value(args[1], memory, user_args)
            
            elif command == 'pull':
                memory[args[0]] =storage[get_value(args[1], memory, user_args)] if storage[get_value(args[1], memory, user_args)] else "0"
            
            elif command == 'jump':
                if (get_value(args[0], memory, user_args) =="1"):
                    tmp = ''
                    for line in instructions:
                        if line.startswith("label " + get_value(args[1], memory, user_args)):
                            tmp = line
                            break
                    ptr = instructions.index(tmp)
            
            elif command == 'add':
                memory[args[0]] = str((int(memory[args[0]]) + int(get_value(args[1], memory, user_args))))

            elif command == 'sub':
                memory[args[0]] = str((int(memory[args[0]]) - int(get_value(args[1], memory, user_args))))

            elif command == 'div':
                memory[args[0]] = str((int(memory[args[0]]) / int(get_value(args[1], memory, user_args))))

            elif command == 'mul':
                memory[args[0]] = str((int(memory[args[0]]) * int(get_value(args[1], memory, user_args))))

            elif command == 'mod':
                memory[args[0]] = str((int(memory[args[0]]) % int(get_value(args[1], memory, user_args))))
    
            elif command == 'and':
                memory[args[0]] = str((int(memory[args[0]]) & int(get_value(args[1], memory, user_args))))

            elif command == 'or':
                memory[args[0]] = str((int(memory[args[0]]) | int(get_value(args[1], memory, user_args))))

            elif command == 'xor':
                memory[args[0]] = str((int(memory[args[0]]) ^ int(get_value(args[1], memory, user_args))))

            elif command == 'not':
                memory[args[0]] = str((~int(memory[args[0]])))

            elif command == 'gtr':
                memory[args[0]] = "1" if int(memory[args[0]]) >  int(get_value(args[1], memory, user_args)) else "0";
            
            elif command == 'lss':
                memory[args[0]] = "1" if int(memory[args[0]]) <  int(get_value(args[1], memory, user_args)) else "0";
            
            elif command == 'geq':
                memory[args[0]] = "1" if int(memory[args[0]]) >=  int(get_value(args[1], memory, user_args)) else "0";
            
            elif command == 'leq':
                memory[args[0]] = "1" if int(memory[args[0]]) <=  int(get_value(args[1], memory, user_args)) else "0";
            
            elif command == 'eq':
                memory[args[0]] = "1" if int(memory[args[0]]) ==  int(get_value(args[1], memory, user_args)) else "0";
            
            elif command == 'neq':
                memory[args[0]] = "1" if int(memory[args[0]]) !=  int(get_value(args[1], memory, user_args)) else "0";

            elif command == 'ls':
                memory[args[0]] = str((int(memory[args[0]]) << int(get_value(args[1], memory, user_args))))
            
            elif command == 'rs':
                memory[args[0]] = str((int(memory[args[0]]) >> int(get_value(args[1], memory, user_args))))
            
            elif command == 'log':
                if disable_logging == False:
                    print("LOG ::" + contract_address + ":" + get_value(args[0], memory, user_args))

            ptr += 1
            gas -= 1
        
        return [storage, balance]


def get_value(token : str, memory, user_args):
    if token.startswith('$'):
        token = token.replace("$", "")

        if type(memory[token]) == None:
            memory[token] = "0"
        return memory[token]
    
    elif (token.startswith('%')):
        token = token.replace("%", "")

        return "0" if type(user_args[int(token)]) == None else user_args[int(token)]
    
    else:
        return token