import rg

HEALTH_LIMIT = 20  # min hp for healthy bot
SUICIDE_HP   = 10  # when to consider a self-destruct
RATING_DEPTH = 0   # how far ahead to check a move's rating
BUDDY_RATING = 0.5 # buddy rating
BOGY_RATING  = 2.0 # bogy rating

turns = []
moves = []
moved = []
state = None

def get_all_around( loc ):
    locs = []

    x = loc[0] - 1
    y = loc[1] - 1

    for x_count in range( x, x + 3 ):
        for y_count in range( y, y + 3 ):
            if ( ( x_count, y_count ) != loc ):
                locs.append( ( x_count, y_count ) )

    return locs

class Robot:

    def act(self, game):

        global moves, moved, state

        actions = []

        # Get Game State
        state  = self._get_game_state( game )

        # If on spawn move
        if ( 'spawn' in rg.loc_types(self.location) ):
            actions = self._move( game )

        # SUICIDE !!!
        if ( actions == [] and self.hp <= SUICIDE_HP ):
            actions = self._suicide( game )

        # If healthy then attack
        if ( actions == [] and self.hp >= HEALTH_LIMIT ):
            actions = self._attack( game )

        # If sick then run
        if ( actions == [] ):
            actions = self._move( game )

        # Else just chill
        if ( actions == [] ):
            actions = ['guard']

        if ( actions[0] == 'move' ):
            moves.append( actions[1] )
            moved.append( self.robot_id )

        # SUICIDE !!!
        elif ( actions[0] == 'guard' and self.hp <= SUICIDE_HP ):
            test = self._suicide( game, 0 )

            if ( test != [] ):
                actions = test

        #self.count += 1
        return actions

    def _get_game_state( self, game ):

        global moves, moved, turns

        state = {}
        state['BUDDY'] = []
        state['BOGY']  = []

        keys = game.get('robots').keys()

        for loc in keys:
            robot = game.get('robots')[loc]

            if ( self.player_id == robot.player_id ):
                state['BUDDY'].append( loc )
            else:
                state['BOGY'].append( loc )

        if ( game.turn not in turns ):
            turns.append( game.turn )
            moves = []
            moved = []

        return state

    def _move( self, game ):

        global moves

        # Always move when in spawn
        move = rg.toward(self.location, rg.CENTER_POINT)
        if ( 'spawn' not in rg.loc_types(self.location) or not self._check_move_valid( game, move ) ):

            around   = rg.locs_around(self.location, filter_out=('invalid', 'obstacle') )

            new_move    = ()
            best_rating = 9999.0

            # Check if staying is better
            around.append( self.location )

            for loc in around:
                if ( 'spawn' not in rg.loc_types(loc) and loc not in moves ):
                    rating = self._get_move_rating( loc, game )

                    if ( rating < best_rating ):
                        best_rating = rating
                        new_move = loc

            if ( new_move != () ):
                move = new_move

        if ( not self._check_move_valid( game, move ) ):
            return ['guard']

        return ['move', move]

    def _attack( self, game ):

        global state

        # Look for weakest bogu around and attack him.
        around   = rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))

        health = 9999
        attack = ()

        # find weakest bogy around me
        for loc in around:
            if ( loc in state['BOGY'] and game.get('robots')[loc].hp < health ):

                health = game.get('robots')[loc].hp

                attack = loc

        if ( attack != () ):
            return ['attack', attack]

        # Check diagonal and attack incase bogy moves into that location
        all_around = get_all_around( self.location )

        for loc in all_around:
            if ( loc in around ):
                continue

            if ( loc in state['BOGY'] ):
                check_locs = [(-1,-1),(1,-1),(-1,1),(1,1)]

                for check in check_locs:
                    if ( loc[0] == self.location[0]+check[0] and loc[1] == self.location[1]+check[1] ):

                        move = ( self.location[0]+check[0],self.location[1] )

                        if ( self._check_move_valid( game, move ) ):
                            return ['attack', move]

                        move = ( self.location[0],self.location[1]+check[1] )

                        if ( self._check_move_valid( game, move ) ):
                            return ['attack', move]

        # Move to closest bogy
        closest_dist = 9999
        closest_loc  = ()

        for loc in state['BOGY']:
            dist = rg.wdist(self.location, loc)

            if ( dist < closest_dist ):
                closest_dist = dist
                closest_loc  = loc

        if ( closest_loc != () ):
            move = rg.toward(self.location, closest_loc)

            if ( self._check_move_valid( game, move ) ):

                # If the distance is close enough then attack, bogy might move there
                if closest_dist == 2:
                    return ['attack', move]

                return ['move', move]

        return []

    def _suicide( self, game, limit=1 ):

        global state

        around   = rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))

        count = 0

        for loc in around:
            if ( loc in state['BOGY'] ):
                count += 1

        if ( count > limit ):
            return ['suicide']

        return []

    def _check_move_valid( self, game, loc ):

        global moves, moved, state

        # If another robot already booked this move its not valid
        if ( loc in moves ):
            return False

        # Dont move back into spawn
        if ( 'spawn' in rg.loc_types(loc) and 'spawn' not in rg.loc_types(self.location) ):
            return False

        # If planned move is location of buddy, check if he is moving
        if ( loc in state['BUDDY'] ):
            if ( game.get('robots')[loc].robot_id not in moved ):
                return False

        # Dont move over enemy
        if ( loc in state['BOGY'] ):
            return False

        # One more check
        if ( self.location == loc ):
            return False

        return True

    def _get_move_rating( self, loc, game, index=0 ):

        global state

        rating = 0.0

        all_around = get_all_around( loc )

        for loc in all_around:
            if ( loc == self.location ):
                continue

            if ( loc in state['BUDDY'] ):
                rating += BUDDY_RATING
            if ( loc in state['BOGY'] ):
                rating += BOGY_RATING * game.get('robots')[loc].hp
            #elif ( index <= RATING_DEPTH ):
            #    rating += self._get_move_rating( loc, state, game, index+1 )

        return rating
