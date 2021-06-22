from Player import Player

import time
import random
import numpy as np
import os
import pandas as pd

class MCTSPlayer(Player):
    
    # Player 1 selects the optimal UCT move 
    # Player 2 selects the worst move from Player 1's position
    
    def __init__(self, iterations = 1000, timeLimit = 3, isTimeLimited = True, c_param = 9):
        super().__init__()
        self.iterations = iterations
        self.timeLimit = timeLimit
        self.isTimeLimited = isTimeLimited
        self.c_param = c_param
        self.name = 'MCTS'
        self.fullName = f'MCTS (Time Limit = {self.timeLimit})' if self.isTimeLimited else  f'MCTS (Iterations = {self.iterations})'
        self.family = "MCTS"
        self.cols = ['Name','TimeLimit','Turn','Iter']
        self.file = self.CreateFile()
        
        
    def ClonePlayer(self):
        Clone = MCTSPlayer(self.iterations, self.timeLimit, self.isTimeLimited)
        return Clone
    
    
    def chooseAction(self, state):
        """
        Choose actions using UCT function
        """
        return self.MCTS_Search(state, self.iterations, self.timeLimit, self.isTimeLimited)
    
    
    def MCTS_Search(self, root_state, iterations, timeLimit, isTimeLimited):
        """
        Conduct a UCT search for itermax iterations starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with games results in the range [0, 1]
        """
        # Player 1 = 1, Player 2 = 2 (Player 2 wants to the game to be a loss)
        playerSymbol = root_state.playerSymbol
        
        # state the Root Node
        root_node = Node(state = root_state)
        #startTime = time.time()
        
        if self.isTimeLimited:
            self.MCTS_TimeLimit(root_node, root_state)
        else:
            self.MCTS_IterationLimit(root_node, root_state)
                
        # return the node with the highest number of wins from the view of the current player
        #for i in root_node.child: print(i)
        #for i in sorted(root_node.child, key = lambda c: c.Q): print(i)
        if playerSymbol == 1:
            bestMove = sorted(root_node.child, key = lambda c: c.Q)[-1].Move
        else:
            bestMove = sorted(root_node.child, key = lambda c: c.Q)[0].Move
        
        #print(bestMove.move)
        #print()
        
        return bestMove.move
    
    
    
    def MCTS_IterationLimit(self, root_node, root_state):
        
        for i in range(self.iterations):
            #if i % 100 == 0:
            #    print(i)
    
            node = root_node
            state = root_state.CloneState()
    
            # Select
            while node.untried_moves == [] and node.child != []:  # node is fully expanded
                node = node.UCTSearch(self.c_param)
                state.move(node.Move.move)
                
            # Expand
            if node.untried_moves != [] and (not state.isGameOver):  # if we can expand, i.e. state/node is non-terminal
                move_random = random.choice(node.untried_moves)
                state.move(move_random.move)
                node = node.AddChild(move = move_random, state = state, isGameOver = state.isGameOver)
                
            # Rollout
            # play random moves until the game reaches a terminal state
            # shuffle deck
            state.shuffle()
            while not state.isGameOver:
                m = state.getRandomMove()
                state.move(m.move)
             
            # Backpropogate
            result = state.checkWinner()
            while node != None:  # backpropogate from the expected node and work back until reaches root_node
                node.UpdateNode(result, self.c_param)
                node = node.parent
    
    
    
    def MCTS_TimeLimit(self, root_node, root_state):
        
        startTime = endTime = time.time()
        numberOfIterations = 0
        
        while ((endTime - startTime) < self.timeLimit):
            
            node = root_node
            state = root_state.CloneState()
            numberOfIterations += 1
    
            # Select
            while node.untried_moves == [] and node.child != []:  # node is fully expanded
                node = node.UCTSearch(self.c_param)
                state.move(node.Move.move)
                
            # Expand
            if node.untried_moves != [] and (not state.isGameOver):  # if we can expand, i.e. state/node is non-terminal
                move_random = random.choice(node.untried_moves)
                state.move(move_random.move)
                node = node.AddChild(move = move_random, state = state, isGameOver = state.isGameOver)
                
            # Rollout
            # play random moves until the game reaches a terminal state
            # shuffle deck
            state.shuffle()
            while not state.isGameOver:
                m = state.getRandomMove()
                state.move(m.move)
             
            # Backpropogate
            result = state.checkWinner()
            while node != None:  # backpropogate from the expected node and work back until reaches root_node
                node.UpdateNode(result, self.c_param)
                node = node.parent
            
            # latest time
            endTime = time.time()
            
        # append info to csv
        data = {'Name': self.name,'TimeLimit':self.timeLimit,'Turn':int((root_state.Turn+1)/2), 'Iter':numberOfIterations}
        self.UpdateFile(data)
            
            
##############################################################################
##############################################################################
##############################################################################


#C_PARAM = 2

class Node:
    """
    The Search Tree is built of Nodes
    A node in the search tree
    """
    
    def __init__(self, Move = None, parent = None, state = None, isGameOver = False):
        self.Move = Move  # the move that got us to this node - "None" for the root
        self.parent = parent  # parent node of this node - "None" for the root node
        self.child = []  # list of child nodes
        self.state = state
        self.untried_moves = state.availableMoves()
        self.playerSymbol = state.playerSymbol
        # keep track of visits/wins/losses
        self.visits = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.Q = 0
        # UCT score
        self.UCT_high = 0
        self.UCT_low = 0
        
    
    def __repr__(self):
        visits = 1 if self.visits == 0 else self.visits
        String = "["
        String += f'Move:{str(self.Move.move)}, Wins:{round(self.wins,1)},'
        String += f' Losses:{self.losses}, Draws:{self.draws}, Q:{round(self.Q,3)},'
        String += f' Wins/Visits:{round(self.wins,1)}/{self.visits} ({round(self.wins/visits,3)}),'
        String += f' UCT_high:{round(self.UCT_high, 3)}, UCT_low:{round(self.UCT_low, 3)},'
        String += f' Remaining Moves:{len(self.untried_moves)}'
        String += "]"
        
        return String
    
    def AddChild(self, move, state, isGameOver):
        """
        Add new child node for this move remove m from list of untried_moves.
        Return the added child node.
        """
        node = Node(Move = move, state = state, isGameOver = isGameOver, parent = self)
        self.untried_moves.remove(move)  # this move is now not available
        self.child.append(node)
        return node
    
    
    def UpdateNode(self, result, c_param):
        """
        Update result and number of visits of node
        """
        self.visits += 1
        self.wins += (result > 0)
        self.losses += (result < 0)
        self.draws += (result == 0)
        self.Q = self.Q + (result - self.Q)/self.visits
        
        for c in self.child:
            c.UCT_high = c.Q + np.sqrt(c_param * np.log(self.visits) / c.visits)
            c.UCT_low = c.Q - np.sqrt(c_param * np.log(self.visits) / c.visits)
        
    
    def SwitchNode(self, move, state):
        """
        Switch node to new state
        """
        # if node has children
        for i in self.child:
            if i.Move == move:
                return i
        
        # if node has no children
        return self.AddChild(move, state)
    
    
    def UCTSearch(self, c_param):
        """
        Use the UCB1 formula to select the best child node from the children array.
        C_PARAM is an exploration-explotation factor
        """
        if self.playerSymbol == 1:
            #  look for maximum output
            choice_weights = [c.Q + np.sqrt(c_param * np.log(self.visits) / c.visits) for c in self.child]
            return self.child[np.argmax(choice_weights)]
        else: 
            #  look for minimum output
            choice_weights = [c.Q - np.sqrt(c_param * np.log(self.visits) / c.visits) for c in self.child]
            return self.child[np.argmin(choice_weights)]