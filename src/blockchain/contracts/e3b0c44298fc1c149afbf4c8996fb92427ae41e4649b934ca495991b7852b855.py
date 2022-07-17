from threading import Timer
import time

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
        nonlocal election_in_progress
        if election_in_progress:
            for k in list(args[0].keys()):
                for k1 in state['storage']['candidates'].keys():
                    if k == k1:
                        state['storage']['candidates'][k][args[0][k]] += 1
                        break
            state['storage']['total_votes'] += 1

    def election_stop_timer(stop_time):

        def stop_election():
            nonlocal election_in_progress
            election_in_progress = False

        timer = Timer(stop_time, stop_election)
        timer.start()

    if action == 'init':
        election_main()
    elif action == 'vote_cast':
        election_vote()
    else:
        pass

    return state
