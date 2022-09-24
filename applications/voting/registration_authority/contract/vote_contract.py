from threading import Timer
import time
import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


verification_pub_key = "-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5njk02H9XaeB7ixlGAx6hktZ0\nUU/CeS+bo1ENbwIYFM3vhVuuzE7JufTVssfKpk/2A0qQ7pTftM6kS9Gp8LispuVt\naL813v9E/DTrgU13YTFyCDMPZLLGhVi4DCCLjl0v6auT4KTDoAacv6exXb7h6As5\nvEhJBH1dFxYomHkYvQIDAQAB\n-----END PUBLIC KEY-----"

def contract(action='init', args=[], state={}):

    election_in_progress = True

    def election_main():
        nonlocal election_in_progress
        if election_in_progress:
            if len(state['storage']) == 0:
                state['storage']['total_votes'] = 0
                state['storage']['candidates'] = {
                    'president': {
                        0 : 0,
                        1 : 0
                    },
                    'parliament': {
                        'cons1': {
                            0 : 0,
                            1 : 0
                        },
                        'cons2': {
                            0 : 0,
                            1 : 0
                        }
                    }
                }
                state['storage']['board'] = [
                    {
                        'party_id': 545,
                        'party_name': 'party1',
                        'public_key': """-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCofnA63FjJ2bOznmRAyRYFPjzZ\ngaoJ9Gx8Jg4jBScucEMO+LvsckrDsvwpgKMnmuxhIyIwfmgX4y4Tnc+Py+TkgkpZ\n0qMXdzhnqTttB44Ku+pxNll0/fZrR/DVJtZwuc9jrPQyzGdRE59x24Ux8EhNFMNB\naeO8p+qhe1sp4IU9dwIDAQAB\n-----END PUBLIC KEY-----""",
                        'approved': False
                    }
                ]

    def election_vote():

        res = verify_transaction(verification_pub_key, args[1]['ballot_info']['sign_data'], args[1]['ballot_info']['signature'])
        if res['status'] == True:
            
            for b in state['storage']['board']:
                if b['approved'] == False:
                    return

            nonlocal election_in_progress
            if election_in_progress:
                for k in list(args[1]['candidates'].keys()):
                    for k1 in state['storage']['candidates'].keys():
                        if k == k1:
                            if k != 'parliament':
                                state['storage']['candidates'][k][args[1]['candidates'][k]] += 1
                                break
                            else:
                                state['storage']['candidates'][k][args[1]['ballot_info']['constituency']][args[1]['candidates'][k]] += 1
                                break

                state['storage']['total_votes'] += 1
    
    def board_consent():
        for b in state['storage']['board']:
            if args[1]['public_key'] == b['public_key']:
                res = verify_transaction(
                    args[1]['public_key'], 
                    args[1]['sign_data'], 
                    args[1]['signature']
                )

                if res['status'] == True:
                    b['approved'] = True
                break

    def verify_transaction(pk, data, sig):
        tmp = ""
        for x in data:
            tmp += x
        
        h = SHA256.new(tmp.encode())
        try:
            pub_key = RSA.importKey(pk.encode())
            verifier = PKCS1_v1_5.new(pub_key)

            verifier.verify(h, sig.encode())
            return {
                'status': True,
                'msg': 'Verification Success'
            }
        except ValueError as e:
            print("Verification Failed")
            return {
                'status': False,
                'msg': 'Verification Failed'
            }
        except Exception as e:
            print("Unexpected Error occured!!")
            return  {
                'status': False,
                'msg': 'Unexpected Error occured!!'
            }

    if action == 'init':
        election_main()
    elif action == 'vote_cast':
        election_vote()
    elif action == 'consent':
        board_consent()
    else:
        pass

    return state
