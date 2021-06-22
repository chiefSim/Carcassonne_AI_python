from Player import RandomPlayer
from MCTS_Player import MCTSPlayer
from MCTS_RAVE_Player import MCTS_RAVEPlayer
from Star1_Player import Star1
from Star2_5_Player import Star2_5
from Carcassonne import CarcassonneState

import os
import time
import pandas as pd
import sys
from datetime import date

PLAYER_LIST = [
    RandomPlayer(),
    Star1(),
    Star2_5(),
    MCTSPlayer(),
    MCTS_RAVEPlayer()
    ]

PLAYER_LIST1 = 20*[RandomPlayer()]

timeLimit = 0.01
PLAYER_LIST2 = [
    MCTSPlayer(timeLimit=timeLimit),
    MCTS_RAVEPlayer(timeLimit=timeLimit),
    RandomPlayer(),
    Star1(),
    Star2_5()
    ]


timeLimit = 10
PLAYER_LIST3 = [
    MCTSPlayer(timeLimit=timeLimit),
    #MCTS_RAVEPlayer(timeLimit=timeLimit),
    RandomPlayer(),
    #Star1(),
    #Star2_5()
    ]


# create log file
class Logger(object):
    
    def __init__(self, filename="Default.log"):
        if os.path.exists(filename):
            os.remove(filename)
        self.log = open(filename, "w")
        self.terminal = sys.stdout
        sys.stdout = self

    def __del__(self):
        sys.stdout = self.stdout
        self.log.close()
        
    def close(self):
        self.log.close()

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        
    def flush(self):
        self.terminal.flush()
        self.log.flush()
        

###################################################

###################################################


def RunLeague(players = PLAYER_LIST, gamesPerMatch=5):
    
    # recreate the csv's for MCTS and Expectimax players
    #mctsCols = ['Name','TimeLimit','Turn','Iter']
    #expCols = ['Name','MaxDepth','ProbingFactor','Turn','Time','NodesVisited']
    
    # create tables
    #dfMCTS = pd.DataFrame(columns = mctsCols)
    #dfMCTS_Rave = pd.DataFrame(columns = mctsCols)
    #dfStar1 = pd.DataFrame(columns = expCols)
    #dfStar2_5 = pd.DataFrame(columns = expCols)
    
    
    # export to logs file
    #dfMCTS.to_csv('logs/0_MCTS_Stats.csv', index=False)
    #dfMCTS_Rave.to_csv(r'logs\MCTS_Rave_Stats.csv', index=False)
    #dfStar1.to_csv(r'logs\Star1Stats.csv', index=False)
    #dfStar2_5.to_csv(r'logs\Star2_5Stats.csv', index=False)
    
    # number of players
    n = len(players)
    
    # initial statement
    print(f'Welcome to the start of a new League \nDate: {date.today().strftime(("%d %B, %Y"))} \n')
    
    # print each competitor
    print('Here are the competitors: \n')
    i = 1
    for player in players:
        print(f'{i}. {player}')
        i += 1
        
    # create league table
    data = {
        "Pos": list(range(1,n+1)),
        "Player": [player for player in players], 
        "MatchesPlayed": n*[0], 
        "Points": n*0, 
        "BWP": n*0, 
        "BLP": n*0, 
        "W": n*0, 
        "L": n*0, 
        "D": n*0, 
        "PD": n*0
        }
    # create pandas league table
    df_league = pd.DataFrame(data)
    
    # create a table of stats for all players
    columnNames = ["FixtureSet", "Game", "Player", "Opponent", "Result", "Win", "Loss", "Draw", 
                   "PlayerScore", "OpponentScore", "CompleteCityScore", "CompleteRoadScore", 
                   "CompleteMonasteryScore", "IncompleteCityScore", "IncompleteRoadScore", 
                   "IncompleteMonasteryScore", "FarmScore","MeeplesPlayed", "MeepleTurns", 
                   "MeepleFeatures", "Turns", "AvgTurnTime"]
    dfStats = pd.DataFrame(columns = columnNames)
    
    # get full fixture list
    fixtures = Fixtures(players)
    
    numberOfFixturesSet = len(fixtures)
    fixtureSetNumber = 1
    # each set of fixtures
    for fixtureSet in fixtures:
        print("\n###############################################\n\n###############################################")
        print(f'\nFixture Set {fixtureSetNumber} (Out of {numberOfFixturesSet})')
        j = 1
        for pairing in fixtureSet:
            
            player1 = pairing[0]
            player2 = pairing[1]
            
            print(f'\nMatch {j}: {player1} vs. {player2}')
            j += 1
            
            if 'Idle' in pairing: # skip match if there is an 'Idle' player
                print("No Matches Played")
                continue
            
            winners, results, timePerMatch, dfStats = PlayFullMatch(player1, player2, gamesPerMatch, fixtureSetNumber, dfStats)
            df_league = UpdateLeagueTable(df_league, player1, player2, gamesPerMatch, winners, results)
        
        # sort league table by points, then PD, then wins
        df_league = df_league.sort_values(by=['Points', 'PD', 'W'], ascending=False)
        df_league['Pos'] = df_league['Pos'].sort_values().values
        
        # print table at the end of each fixture set
        print(f'\nLeague Table after Fixture Set {fixtureSetNumber}:\n')
        print(df_league)
        fixtureSetNumber += 1
        
    # export final table as csv
    df_league.to_csv(r'logs\FinalLeagueTable.csv', index=False)
    dfStats.to_csv(r'logs\PlayerStats.csv', index=False)
   

    
def Fixtures(players):
    """
    Returns a round robin fixture with "home-and-away" results
    """
    # need an even amount of players
    if len(players) % 2:
        players.append("Idle")
    
    n = len(players)
    
    matchs = []  # individual matches (P1 vs P2)
    fixtures = []  # set of matches containing each player [(P1 vs. P2), (P3 vs. P4)]
    return_matches = []
    for fixture in range(1, n):
        for i in range(n//2):
            matchs.append((players[i], players[n - 1 - i]))
            return_matches.append((players[n - 1 - i], players[i]))
        players.insert(1, players.pop())
        fixtures.insert(len(fixtures)//2, matchs)
        fixtures.append(return_matches)
        matchs = []
        return_matches = []
    
    return fixtures
  

def PlayOneGame(player1, player2, gameNumber, fixtureSetNumber, dfStats, showLogs=False):
    """
    Plays a single game between two players
    """
    times = [[],[]] # record each player's play time
    numberMeeples = [0,0] # record number of meeples each player places
    meepleTurn = [[],[]] # record when each player plays a meeple
    meepleFeature = [[],[]]  # record what feature they place meeple on
    
    # record time of game
    startTime = time.time()
    
    # begin the game state
    state = CarcassonneState(player1, player2)
    
    # record the turn number
    turns = [1,1]
    
    # game loop
    while (not state.isGameOver):
        
        if state.playerSymbol == 1:
            # calculate move time
            initialMoveTime = time.time()
            m = player1.chooseAction(state) # make move
            endMoveTime = time.time()
            times[0].append(endMoveTime - initialMoveTime)
            # record meeple info
            #print(m)
            if (m != 0) and (m[4] is not None):
                numberMeeples[0] += 1  # meeple has been played
                meepleTurn[0].append(turns[0])  # record turn
                meepleFeature[0].append(m[4][0])  # record feature type
            turns[0] += 1
            
        else:
            # calculate move time
            initialMoveTime = time.time()
            m = player2.chooseAction(state) # make move
            endMoveTime = time.time()
            times[1].append(endMoveTime - initialMoveTime)
            # record meeple info
            #print(m)
            if (m != 0) and (m[4] is not None):
                numberMeeples[1] += 1  # meeple has been played
                meepleTurn[1].append(turns[1])  # record turn
                meepleFeature[1].append(m[4][0])  # record feature type
            turns[1] += 1
        
        # make the move on the board
        state.move(m)
    
    # final scores
    finalScore = state.Scores
    # winner (1 = P1 wins, 2 = P2 wins, 0 = Draw)
    winner = state.winner
    # result = P1 score - P2 Score
    result = state.result
    
    # game time 
    endTime = time.time()
    timeTaken = endTime-startTime
    
    gameResult = 'Draw' if winner == 0 else f'Player{winner} Wins'
    
    # update players stats table
    dfStats = UpdateStatsTable(player1, player2, gameNumber, fixtureSetNumber, dfStats, finalScore, winner, state.FeatureScores, times, numberMeeples, meepleTurn, meepleFeature, turns)
    
    if showLogs:
        print(f'    Game {gameNumber}, Player1: {finalScore[0]} - Player2: {finalScore[1]}      {gameResult}     (Time: {int(timeTaken//60)} Mins {int(timeTaken%60)} Secs)')
    
    # return results of game
    return winner, result, timeTaken, dfStats



def UpdateStatsTable(player1, player2, gameNumber, fixtureSetNumber, dfStats, finalScore, winner, FeatureScores, times, numberMeeples, meepleTurn, meepleFeature, turns):
    """
    Update a players stats after each game
    """
    # new data to be added
    data = {"FixtureSet": fixtureSetNumber, "Game": gameNumber, "Player": player1, "Opponent": player2, "Result": winner,
            "Win":int(winner==1), "Loss":int(winner==2), "Draw":int(winner==0), 
            "PlayerScore": finalScore[0], "OpponentScore": finalScore[1], "CompleteCityScore": FeatureScores[0][0], 
            "CompleteRoadScore": FeatureScores[0][1], "CompleteMonasteryScore": FeatureScores[0][2], 
            "IncompleteCityScore": FeatureScores[0][3], "IncompleteRoadScore": FeatureScores[0][4], 
            "IncompleteMonasteryScore": FeatureScores[0][5], "FarmScore": FeatureScores[0][6],
            "MeeplesPlayed": numberMeeples[0], "MeepleTurns": [meepleTurn[0]], "MeepleFeatures": [meepleFeature[0]], 
            "Turns": turns[0], "AvgTurnTime": (sum(times[0]))/turns[0]}
    p1_data = pd.DataFrame(data)
    dfStats = dfStats.append(p1_data)  # add new data to table
    
    # new data to be added
    data = {"FixtureSet": fixtureSetNumber, "Game": gameNumber, "Player": player2, "Opponent": player1, "Result": (3-winner)%3,
            "Win":int(winner==2), "Loss":int(winner==1), "Draw":int(winner==0), 
            "PlayerScore": finalScore[1], "OpponentScore": finalScore[0], "CompleteCityScore": FeatureScores[1][0], 
            "CompleteRoadScore": FeatureScores[1][1], "CompleteMonasteryScore": FeatureScores[1][2], 
            "IncompleteCityScore": FeatureScores[1][3], "IncompleteRoadScore": FeatureScores[1][4], 
            "IncompleteMonasteryScore": FeatureScores[1][5], "FarmScore": FeatureScores[1][6],
            "MeeplesPlayed": numberMeeples[1], "MeepleTurns": [meepleTurn[1]], "MeepleFeatures": [meepleFeature[1]], 
            "Turns": turns[1], "AvgTurnTime": (sum(times[1]))/turns[1]}
    p2_data = pd.DataFrame(data)
    dfStats = dfStats.append(p2_data)  # add new data to table
    
    return dfStats




def PlayFullMatch(player1, player2, gamesPerMatch, fixtureSetNumber, dfStats, showLogs=False):
    """
    Play a full set of games between two players
    """
    winners = [0,0,0]  # [P1 wins, P2 wins, Draws]
    results = []  # points difference of each games
    timePerMatch = []
    
    for game in range(gamesPerMatch):
        winner, result, timeTaken, dfStats = PlayOneGame(player1, player2, game+1, fixtureSetNumber, dfStats)
        # record the results
        winners[(winner-1)%3] += 1
        results.append(result)
        timePerMatch.append(timeTaken)
    
    if showLogs:
        print(f'Games:{gamesPerMatch} - Player1 Wins:{winners[0]}    Player2 Wins:{winners[1]}    Draws:{winners[2]}')
        
    # return full set of results and scores
    return winners, results, timePerMatch, dfStats



def UpdateLeagueTable(df, player1, player2, gamesPerMatch, winners, results):
    """
    Update table with the results after a full match
    """
    p1Wins, p2Wins = winners[0], winners[1]
    isP1Winner = isP1Loser = isP2Winner = isP2Loser = isDraw = False  
    isP1BW = isP2BW = isP1BL = isP2BL = False
    p1Score = p2Score = 0  # initialize scores
    
    if p1Wins > p2Wins:  # player 1 wins
        p1Score += 4
        isP1Winner = True
        isP2Loser = True
        if (p1Wins/gamesPerMatch >= 0.7):  # dominant winner
            p1Score += 1
            isP1BW = True
        elif (p1Wins/gamesPerMatch <= 0.55): # bonus losing point for other player
            p2Score += 1
            isP2BL = True
            
    elif p2Wins > p1Wins:  # player 2 wins
        p2Score += 4
        isP2Winner = True
        isP1Loser = True
        if (p2Wins/gamesPerMatch >= 0.7):  # dominant winner
            p2Score += 1
            isP2BW = True
        elif (p2Wins/gamesPerMatch <= 0.55): # bonus losing point for other player
            p1Score += 1
            isP1BL = True
            
    else: # draw
        p1Score += 2
        p2Score += 2
        isDraw = True
    
    avgScoreDifference = round(sum(results)/len(results), 3)
    
    # update table with these values
    p1Update = [player1, 1, p1Score, int(isP1BW), int(isP1BL), int(isP1Winner), int(isP1Loser), int(isDraw), round(avgScoreDifference,2)]
    p2Update = [player2, 1, p2Score, int(isP2BW), int(isP2BL), int(isP2Winner), int(isP2Loser), int(isDraw), -round(avgScoreDifference,2)]
    
    print(f'Points Earned - Player 1: {p1Score}    Player 2: {p2Score}')
    
    # update values for each player 
    for update in (p1Update, p2Update):
        updateValue = 1
        for column in df.columns:
            player = update[0]
            if column != "Pos" and column != "Player":
                df.loc[df['Player'] == player, column] += update[updateValue]
                updateValue += 1
    # return the updated tables                
    return df

#########################

if __name__ == "__main__":
    
    #temp = sys.stdout
    #sys.stdout = log = Logger("Logs/League.txt")
    
    # run league
    RunLeague(PLAYER_LIST3, gamesPerMatch=2)
    
    #sys.stdout = temp
    #log.close()

