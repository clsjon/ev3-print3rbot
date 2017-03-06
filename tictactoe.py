#!/usr/bin/env python3
# coding: utf-8

import random, sys


class TicTacToe():
    # Tic Tac Toe
    
    def __init__(self,playerLetter):
        self.theBoard = [' '] * 10
        self.playerLetter = playerLetter
        self.computerLetter = 'X' if playerLetter == 'O' else 'O'
 
    def drawBoard(self):
        # This function prints out the board that it was passed.
    
        # "board" is a list of 10 strings representing the board (ignore index 0)
        print('   |   |')
        print(' ' + self.theBoard[7] + ' | ' + self.theBoard[8] + ' | ' + self.theBoard[9])
        print('   |   |')
        print('-----------')
        print('   |   |')
        print(' ' + self.theBoard[4] + ' | ' + self.theBoard[5] + ' | ' + self.theBoard[6])
        print('   |   |')
        print('-----------')
        print('   |   |')
        print(' ' + self.theBoard[1] + ' | ' + self.theBoard[2] + ' | ' + self.theBoard[3])
        print('   |   |')


    def whoGoesFirst(self):
        # Randomly choose the player who goes first.
        if random.randint(0, 1) == 0:
            return 'computer'
        else:
            return 'player'

    def playAgain(self):
        # This function returns True if the player wants to play again, otherwise it returns False.
        print('Do you want to play again? (yes or no)')
        return input().lower().startswith('y')

    def makeMove(self, board, letter, move):
        board[move] = letter
        
    def isWinner(self, board, letter):
        # Given a board and a player's letter, this function returns True if that player has won.
        # We use bo instead of board and le instead of letter so we don't have to type as much.
        
        return ((board[7] == letter and board[8] == letter and board[9] == letter) or # across the top
        (board[4] == letter and board[5] == letter and board[6] == letter) or # across the middletter
        (board[1] == letter and board[2] == letter and board[3] == letter) or # across the boardttom
        (board[7] == letter and board[4] == letter and board[1] == letter) or # down the letterft side
        (board[8] == letter and board[5] == letter and board[2] == letter) or # down the middletter
        (board[9] == letter and board[6] == letter and board[3] == letter) or # down the right side
        (board[7] == letter and board[5] == letter and board[3] == letter) or # diagonal
        (board[9] == letter and board[5] == letter and board[1] == letter)) # diagonal

    def getBoardCopy(self):
        # Make a duplicate of the board list and return it the duplicate.
        return self.theBoard[:]
        
    def isSpaceFree(self, board, move):
        # Return true if the passed move is free on the passed board.
        return board[move] == ' '

    def getPlayerMove(self):
        # Let the player type in their move.
        move = ' '
        while move not in '1 2 3 4 5 6 7 8 9'.split() or not self.isSpaceFree(self.theBoard, int(move)):
            print('What is your next move? (1-9)')
            move = input()
        return int(move)

    def chooseRandomMoveFromList(self, movesList):
        # Returns a valid move from the passed list on the passed board.
        # Returns None if there is no valid move.
        possibleMoves = []
        for i in movesList:
            if self.isSpaceFree(self.theBoard,i):
                possibleMoves.append(i)
    
        if len(possibleMoves) != 0:
            return random.choice(possibleMoves)
        else:
            return None

    def getComputerMove(self):
        # Given a board and the computer's letter, determine where to move and return that move.
        # Here is our algorithm for our Tic Tac Toe AI:
        # First, check if we can win in the next move
        for i in range(1, 10):
            copy = self.getBoardCopy()
            if self.isSpaceFree(copy, i):
                self.makeMove(copy, self.computerLetter, i)
                if self.isWinner(copy, self.computerLetter):
                    return i
    
        # Check if the player could win on their next move, and block them.
        for i in range(1, 10):
            copy = self.getBoardCopy()
            if self.isSpaceFree(copy, i):
                self.makeMove(copy, self.playerLetter, i)
                if self.isWinner(copy, self.playerLetter):
                    return i
    
        # Try to take one of the corners, if they are free.
        move = self.chooseRandomMoveFromList([1, 3, 7, 9])
        if move != None:
            return move
    
        # Try to take the center, if it is free.
        if isSpaceFree(board, 5):
            return 5
    
        # Move on one of the sides.
        return chooseRandomMoveFromList([2, 4, 6, 8])

    def isBoardFull(self):
        # Return True if every space on the board has been taken. Otherwise return False.
        for i in range(1, 10):
            if self.isSpaceFree(self.theBoard, i):
                return False
        return True


def inputPlayerLetter():
    # Lets the player type which letter they want to be.
# Returns a list with the player's letter as the first item, and the computer's letter as the second.
    letter = ''
    while not (letter == 'X' or letter == 'O'):
        print('Do you want to be X or O?')
        letter = input().upper()

    # the first element in the list is the player's letter, the second is the computer's letter.
    return letter
    
def main(argv):
    
    
    print('Welcome to Tic Tac Toe!')
    ttt = TicTacToe(inputPlayerLetter())
    
    while True:
        # Reset the board
        turn = ttt.whoGoesFirst()
        print('The ' + turn + ' will go first.')
        gameIsPlaying = True
    
        while gameIsPlaying:
            if turn == 'player':
                # Player's turn.
                ttt.drawBoard()
                move = ttt.getPlayerMove()
                ttt.makeMove(ttt.theBoard, ttt.playerLetter, move)
            
                if ttt.isWinner(ttt.theBoard, ttt.playerLetter):
                    ttt.drawBoard(ttt.theBoard)
                    print('Hooray! You have won the game you silly banana!')
                    gameIsPlaying = False
                else:
                    if ttt.isBoardFull():
                        ttt.drawBoard()
                        print('The game is a tie!')
                        break
                    else:
                        turn = 'computer'
        
            else:
                # Computer's turn.
                move = ttt.getComputerMove()
                ttt.makeMove(ttt.theBoard, ttt.computerLetter, move)
            
                if ttt.isWinner(ttt.theBoard, ttt.computerLetter):
                    ttt.drawBoard()
                    print('The computer has beaten you! You lose.')
                    gameIsPlaying = False
                else:
                    if ttt.isBoardFull():
                        ttt.drawBoard()
                        print('The game is a tie!')
                        break
                    else:
                        turn = 'player'
    
        if ttt.playAgain():
            ttt = TicTacToe(inputPlayerLetter())
        else:
            break


if __name__ == '__main__':
    main(sys.argv[1:])
