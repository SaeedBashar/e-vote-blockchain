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

                    'secretary': {

                        2 : 0,

                        3 : 0

                    },

                    'treasurer': {

                        4 : 0,

                        5 : 0

                    }

                }



        election_stop_timer(60)



    def election_vote():



        res = verify_transaction()

        if res['status'] == True:

            nonlocal election_in_progress

            if election_in_progress:

                for k in list(args[1].keys()):

                    for k1 in state['storage']['candidates'].keys():

                        if k == k1:

                            state['storage']['candidates'][k][args[1][k]] += 1

                            break

                state['storage']['total_votes'] += 1

     



    def election_stop_timer(stop_time):



        def stop_election():

            nonlocal election_in_progress

            election_in_progress = False



        timer = Timer(stop_time, stop_election)

        timer.start()



    def verify_transaction():

        data = args[0]['sign_data']

        tmp = ""

        for x in data:

            tmp += x

        

        h = SHA256.new(tmp.encode())

        try:

            pub_key = RSA.importKey(verification_pub_key.encode())

            verifier = PKCS1_v1_5.new(pub_key)



            verifier.verify(h, args[0]['signature'].encode())

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

    else:

        pass



    return state

