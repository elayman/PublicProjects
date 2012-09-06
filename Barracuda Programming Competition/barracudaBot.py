'''
Created on Oct 14, 2011

@author: Ahmed, Travis, Evan
'''
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import random

class RequestHandler(SimpleXMLRPCRequestHandler):
	rpc_paths = ('/RPC2',)
	
# Create server
server = SimpleXMLRPCServer(("172.16.118.181", 8080), requestHandler=RequestHandler)
server.register_introspection_functions()

def ping_function(inputString):
	return 'pong'

server.register_function(ping_function, 'ping')

#Global Variables
moveNum = 0
seriesIndices = []

	
def start_game (struct):
	global moveNum
	global seriesIndices
	moveNum = 0
	seriesIndices = []
#takes XMLRPC struct
	#An integer representing the game you are currently playing. This is purely advisory, but may be useful in your debugging and logging. This integer may also be used to lookup the game on the website.
	#game_id = struct['game_id'] 
	# A zero-based index indicating which player you are this round. Player 0 goes first, player 1 goes second.
	#player_id = struct['player_id'] 
	#A number indicating what the initial discard is.
	#initial_discard = struct['initial_discard']
	#The team ID of the other player, which can be used to go to the team page by feeding it in the obvious manner to the /team/ URI.
	#other_player_id = struct['other_player_id']
	
	#return null
	return ""

server.register_function(start_game, 'start_game')

#takes XMLRPC struct
#decides whether to take card from discard pile or deck
#depending on current series in hand
def get_move(struct):
	print("timeremaining: ",struct['remaining_microseconds'])
	global moveNum
	#call heuristic
	moveTuple = calculate(struct)
	print("moveTuple: ",moveTuple)
	moveNum += 1
	print("moveNumber: ",moveNum)
	#moveTuple = ('request_deck',)
	move = moveTuple[0]
	#if (move)
	#print("move = ", move)
	if (move == 'request_discard'):
		answerStruct = {'move':move, 'idx':moveTuple[1]}#CHANGE 0 TO INDEX FROM MOVETUPLE
	else:
	    #print("we are trying request the deck")	    
	    answerStruct = {'move':'request_deck'}
	#move: A string indicating which move you wish to make, which must be one of the strings request_discard or request_deck.
	#If you choose to request_discard, your struct must have an idx field with is a number that
	#corresponds to the zero-based index of which card in your rack you wish to replace.
	#This field must not be present if you choose request_deck.
	return answerStruct

server.register_function(get_move, 'get_move')

#If you return a move of type request_deck for a get_move call, the server will make this call to you. 
def get_deck_exchange(struct):
    #index is where in our rack we want to place the new card
    rack = struct['rack']
    card = struct['card']
    
    #check if it makes a series
    #print("get deck exchange")
    seriesReturn = seriesCheck(rack, card)
    if seriesReturn:
        return seriesReturn
    else:
        index = getIndex(rack, card)
        return index

server.register_function(get_deck_exchange, 'get_deck_exchange')

def move_result(struct):
	# An integer matching the one sent with the corresponding start_game call.
	#game_id = struct['game_id'] 
	#This is a string, which will contain one of the following strings, and possibly additional members of this struct:
	#move = struct['move'] 
	#The move has been processed successfully and the game is continuing on normally.
	#next_player_move = struct['next_player_move'] 
	#That move cause the game to end. A human-readable string reason will be given in an additional reason member of the struct.
	#move_ended_game = struct['move_ended_game']
	#The move was illegal, and the game has proceded onwards with no change to your rack. A human-readable string reason will be given in an additional reason member of the struct.
	#illegal = struct['illegal'] 

	return ""

server.register_function(move_result, 'move_result')

def game_result(struct):
	# A number corresponding to the game_ids received previously.
	#game_id = struct['game_id'] 
	# Your score for this game, as an integer.
	#your_score = struct['your_score']
	# The score of your opponent, as an integer.
	#other_socre = struct['other_score']
	# A human-readable string explaining why the game is over.
	#reason = struct['reason'] 

	return ""

server.register_function(game_result, 'game_result')

def getIndex(rack, discard):
	global moveNum
	print("movenum at getIndex is", moveNum)
	return beginnerFunction(rack, discard)

def calculate(struct):
	#game_id = struct['game_id'] # An integer matching the one sent with the corresponding start_game call.
	rack = struct['rack'] # This is an array of ints, corresponding to the current 20 cards in your rack.
	discard = struct['discard'] # This is a single int, corresponding to the top card on the discard pile.
	#remaining_microseconds = struct['remaining_microseconds'] #An integer which is the approximate count of the remaining microseconds available to your bot in this game.
	#other_player_moves = struct['other_player_moves'] #might be empty if you are first player
	
	#index = getIndex(rack, discard)
	answer = isGoodPick(rack,discard)
	#print ("isGoodPick is :", answer)
	if answer == 1:
	    return ('request_discard', getIndex(rack, discard))
	if answer == 0:
	    return ('request_deck')
	else:
		return ('request_discard', answer[1])	
	



def getImposCards(rack):
	index = 0 
	if not impossibleCards:
		for cardVal in rack:
			if ((cardVal < (index + 1)) or (cardVal > (19 - index))):
			#impossible card 
				val = index
				impossibleCards.append(val)
				index = index + 1		
	

#returns number of cards out of order
def numOutOrder(rack):
	n = 0
	i = 0
	while i < 19 :
		if rack[i] > rack[i + 1]:
			n = n + 1
		i = i + 1
	if rack[19] < rack[18]:
		n = n + 1
	return n
	

#returns 1 if the discarded card is good
#returns 0 if it is not
#returns tuple ('s', seriesIndex) if good pick and forms a series, so we know
#have the index to place the card when we pick it
def isGoodPick(rack, discard):
    
    seriesIndex = seriesCheck(rack,discard)
    #print ("seriesIndex is :", seriesIndex)
    if seriesIndex:
        return ('s', seriesIndex)        
    
    bestSpot = beginnerFunction(rack, discard)
    #print("bestSpot is: ",bestSpot)
    bestValue = betterOrWorse(rack,discard,bestSpot)
    #print("bestValue is: ",bestValue)
    if (bestValue > 0):
        return 1
    else:
        return 0
    

#Returns index of best place to put a card in current rack
currentIndex = 0
def beginnerFunction(rack, cardVal):
	#indices correspond to valus 0-76 increments of 4
	#if I place card in corresponding slot, will it make it better orworse? then increment / decrement slot
	print("called beginner")
	print("beginner rack = ", rack)
	print("beginner card = ", cardVal)
	global currentIndex
	global seriesIndices
	if cardVal < 5:
		highIndex = 0
		currentIndex = 0
	else:
		highIndex = cardVal / 4 - 1
		highIndex = int(round(highIndex,0))
		currentIndex = highIndex
	lowIndex = highIndex
	useHigh = 1
	bestIndex = (random.randint(0,19),-2)
	while (((highIndex < 20) or (lowIndex > 0)) and ((highIndex < (currentIndex+3)) or (lowIndex > (currentIndex-3)))):
		#print("looping:",highIndex," ",lowIndex," ",cardVal)
		#switch back and forth, until all options are used
		#set default index
		index = highIndex
		if (highIndex >= 20):
			index = lowIndex
		else:
			if (lowIndex <= 0):
				index = highIndex
			else:
				if useHigh:
					index = highIndex
				else:
					index = lowIndex
		betteroWorse = betterOrWorse(rack,cardVal,index)
		#print("Better or Worse?:", betteroWorse)
		if (betteroWorse > 0):
			return index
		else:
			if betteroWorse > bestIndex[1]:
				bestIndex = (index, betteroWorse)
			if useHigh:
				lowIndex = lowIndex - 1
				useHigh = 0
			else:
				highIndex = highIndex + 1
				useHigh = 1
	return bestIndex[0]

#returns -2, -1, 0, 1, or 2 depending on if it makes the rack worse by 2,1, 0, or better by 1, or 2
def betterOrWorse(rack, cardVal, index):
    
	#print("betterOrWorse")
	#find current value
	currentVal = 0
	#print("rack: ",rack,"cardVal: ",cardVal,"index: ",index)
	if (index != 19):
		if (rack[index + 1] > rack[index]):
			currentVal = currentVal + 1
	#base case (end cases)
	if (index != 0):
		if rack[index - 1] < rack[index]:
			currentVal = currentVal + 1
	#find new val
	newVal = 0
	if (index != 19):
		if (rack[index + 1] > cardVal):
			newVal = newVal + 1
	if (index != 0):
		if (rack[index - 1] < cardVal):
			newVal = newVal + 1
	#print("newVal: ", newVal, " currentVal: ", currentVal)
	return (newVal - currentVal)
	
	
def validSeries(card, index):
    print("got to validSeries")
    cardIndex = card / 4 - 1
    cardIndex = int(round(cardIndex,0))
    if abs(index-cardIndex) < 5:
        print("found a valid series")
        return 1
    else:
        print("series is invalid")
        return 0

#returns index of card that makes a sequential series with the given card
def seriesCheck(rack, card):
    global seriesIndices
    print("we are successfully in SeriesCheck")
    series = False
    i = -1
    ireturn = 0
    seriesIndex = 0
    print("series rack = ", rack)
    print("series card = ", card)
    for num in rack:
        i = i+1
        #front base case
        if i == 0:
            if card == num+1:
                ireturn = 1
                seriesIndex = 0
                x = validSeries(card, ireturn)
                if x:
                    series = True
                    break
        #back end base case
        elif i == 19:
            if (num == (card + 1)):
                ireturn = 18
                seriesIndex = 19
                if validSeries(card, ireturn):
                    series = True
                    break
        else:
            #regular case
            if (num == (card + 1)):
                ireturn = i - 1
                seriesIndex = i
                if validSeries(card, ireturn):
                    series = True
                    break
            elif card == num+1:
                ireturn = i + 1
                seriesIndex = i
                if validSeries(card, ireturn):
                    series = True
                    break
    if series:
        print("we found a series at ", ireturn)
        seriesIndices.append(ireturn)
        seriesIndices.append(seriesIndex)
        return ireturn
    else:
        print("no series")
        return None

	

server.serve_forever()
