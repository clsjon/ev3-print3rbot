#!/usr/bin/env python3
# coding: utf-8

import math, os, time, sys, getopt

#rpyc
import rpyc

        #RPYC stuff
conn = rpyc.classic.connect('192.168.3.2')
ev3 = conn.modules['ev3dev.ev3']
   
#from ev3dev.ev3 import *

from svg.parser import parse_path
from svg.path import Line

class mymotor(Motor):
    def stop(self, stop_command='coast'):
        self.stop_action = stop_command
        self.command = "stop"
    
    def reset_position(self, value = 0):
        self.stop()
        iter = 1
        while (self.position != 0 and iter < 10):
            iter += 1
            try:
                self.position = value
            except:
                print ("impossible to fix position, attempt",iter-1,"on 10.")
            time.sleep(0.05)
    
    def rotate_forever(self, speed=480, regulate='on', stop_command='brake'):
        self.stop_action = stop_command
        self.speed_regulation = regulate
        if regulate=='on':
            self.speed_sp = int(speed)
            self.command = 'run-forever'
        else:
            self.duty_cycle_sp = int(speed)
            self.command = 'run-direct'
    
    def goto_position(self, position, speed=480, up=0, down=0, regulate='on', stop_command='brake', wait=0):
        self.stop_action = stop_command
        self.speed_regulation = regulate
        self.ramp_up_sp,self.ramp_down_sp = up,down
        if regulate=='on':
            self.speed_sp = speed
        else:
            self.duty_cycle_sp = speed
        self.position_sp = position
        sign = math.copysign(1, self.position - position)
        self.command = 'run-to-abs-pos'
        
        if (wait):
            new_pos = self.position
            nb_same = 0
            while (sign * (new_pos - position) > 5):
                time.sleep(0.05)
                old_pos = new_pos
                new_pos = self.position
                if old_pos == new_pos:
                    nb_same += 1
                else:
                    nb_same = 0
                if nb_same > 10:
                    break
            time.sleep(0.05)
            if (not stop_command == "hold"):
                self.stop()


class Writer():
    
    def __init__(self, calibrate=True):
        
        #RPYC stuff
        conn = rpyc.classic.connect('192.168.3.2')
        ev3 = conn.modules['ev3dev.ev3']
        
        self.mot_A    = mymotor(ev3.OUTPUT_C)
        self.mot_B    = mymotor(ev3.OUTPUT_A)
        
        self.mot_lift = mymotor(ev3.OUTPUT_B)
        
        self.touch_A  = ev3.TouchSensor(ev3.INPUT_3)
        self.touch_B  = ev3.TouchSensor(ev3.INPUT_2)
        
        if (calibrate):
            self.calibrate()
        self.pen_up()
    
    def pen_up (self):
        self.mot_lift.goto_position(40, 30, regulate = 'off', stop_command='brake', wait = 1)
        time.sleep(0.1)
    
    def pen_down(self):
        self.mot_lift.goto_position(0, 30, regulate = 'off', stop_command='brake', wait = 1)
        time.sleep(0.1)
    
    def calibrate (self):
        self.mot_lift.rotate_forever(speed=-50, regulate='off')
        time.sleep(0.5)
        while(abs(self.mot_lift.speed) > 5):
            time.sleep(0.001)
        self.mot_lift.stop()
        time.sleep(0.1)
        self.mot_lift.reset_position()
        time.sleep(0.1)
        self.mot_lift.goto_position(40, speed=400, regulate='on', stop_command='brake', wait=1)
        time.sleep(0.1)
        self.mot_lift.reset_position()
        time.sleep(1)
        
        self.pen_up()
        
        self.mot_A.reset_position()
        self.mot_B.reset_position()
        
        if (self.touch_A.value()):
            self.mot_A.goto_position(-200, speed=400, regulate='on', stop_command='coast', wait=1)
        if (self.touch_B.value()):
            self.mot_B.goto_position(200, speed=400, regulate='on', stop_command='coast', wait=1)
        self.mot_B.rotate_forever(speed=-25, regulate='off')
        self.mot_A.rotate_forever(speed=25, regulate='off')
        stop_A = stop_B = False
        start = time.time()
        while True:
            touch_A, touch_B = self.touch_A.value(), self.touch_B.value()
            if (not stop_A and touch_A):
                pos = self.mot_A.position
                self.mot_A.stop()
                self.mot_A.goto_position(pos, speed=-400, regulate='on', stop_command='hold')
                stop_A = True
            if (not stop_B and touch_B):
                pos = self.mot_B.position
                self.mot_B.goto_position(pos, speed=400, regulate='on', stop_command='hold')
                stop_B = True
            if (stop_B and stop_A):
                break
            if (time.time() - start > 30):
                self.mot_A.stop()
                self.mot_B.stop()
                break
            time.sleep(0.05)
        time.sleep(1)
        self.mot_A.reset_position()
        self.mot_B.reset_position()
        self.mot_A.goto_position(-200, speed=400, regulate='on', stop_command='hold', wait=0)
        self.mot_B.goto_position(200, speed=400, regulate='on', stop_command='hold', wait=1)
        time.sleep(1)
        self.mot_A.stop()
        self.mot_B.stop()
        self.mot_A.reset_position()
        self.mot_B.reset_position()
    
    # All coordinates are in Lego distance (1 = distance between two holes center)
    # Coordinates of gear centre A
    xA, yA = 0.,0.
    # Coordinates of gear centre B
    xB, yB = 6.,0.
    # Length between articulation and pen
    r1 = 16.+1.3125
    # Length between gear centre and articulation
    r2 = 11.
    
    #      .E   (pen is in coordinates E = (xE,yE))
    #     / \
    #    /   \
    #   /     \
    # C.       .D
    #   \     /
    #    \   /
    #    A. .B
    #   -------
    #   [robot]
    #   -------
    
    ## Computes the intersection of 2 circles of centres x0,y0 and x1,y1 and radius resp. R0 and R1.
    @staticmethod
    def get_coord_intersec (x0, y0, x1, y1, R0, R1):
        if y0 == y1:
            y0+=0.1
        N = R1*R1 - R0*R0 - x1*x1 + x0*x0 - y1*y1 + y0*y0
        N /= 2.*(y0-y1)
        A = ((x0-x1)/(y0-y1))*((x0-x1)/(y0-y1)) + 1.
        B = 2.*y0 * (x0-x1)/(y0-y1) - 2.*N*(x0-x1)/(y0-y1) - 2.*x0
        C = x0*x0 + y0*y0 + N*N -  R0*R0 - 2.*y0*N
        delta = math.sqrt(B*B - 4.*A*C)
        xA_ = (-B + delta) / (2.*A)
        xB_ = (-B - delta) / (2.*A)
        yA_ = N - xA_ * (x0-x1)/(y0-y1)
        yB_ = N - xB_ * (x0-x1)/(y0-y1)
        return (xA_,yA_),(xB_,yB_)
    
    ## Converts coordinates xE, yE to angles of robot arms.
    @staticmethod
    def coordinates_to_angles (xE, yE):
        try:
            ((xIA, yIA), (xIA2, yIA2)) = Writer.get_coord_intersec (xE, yE, Writer.xA, Writer.yA, Writer.r1, Writer.r2)
            if xIA > xIA2:
                xIA = xIA2
                yIA = yIA2
            ((xIB, yIB), (xIB2, yIA2)) = Writer.get_coord_intersec (xE, yE, Writer.xB, Writer.yB, Writer.r1, Writer.r2)
            if xIB < xIB2:
                xIB = xIB2
                yIB = yIB2
        except:
            return None
        alpha = 180. - 360 * math.acos((xIA-Writer.xA)/Writer.r2) / (2.*math.pi)
        beta =  360. * math.acos((xIB-Writer.xB)/Writer.r2) / (2.*math.pi)
        return (alpha, beta)
    
    ## converts coordinates x,y into motor position
    @staticmethod
    def coordinates_to_motorpos (x, y):
        def angle_to_pos (angle):
            #0     = 14
            #-2970 = 90
            return ((angle-14.) * 2970. / (90.-14.))
        (alpha, beta) = Writer.coordinates_to_angles (x, y)
        return angle_to_pos (alpha), -angle_to_pos (beta)
    
    ## Converts angles of arms to coordinates.
    @staticmethod
    def angles_to_coordinates (alpha, beta):
        xC = Writer.xA - Writer.r2 * math.cos((2.*math.pi) * alpha/360.)
        yC = Writer.yA + Writer.r2 * math.sin((2.*math.pi) * alpha/360.)
        xD = Writer.xB + Writer.r2 * math.cos((2.*math.pi) * beta/360.)
        yD = Writer.yB + Writer.r2 * math.sin((2.*math.pi) * beta/360.)
        ((xE, yE), (xE2, yE2)) = Writer.get_coord_intersec (xC, yC, xD, yD, Writer.r1, Writer.r1)
        if yE2 > yE:
            xE = xE2
            yE = yE2
        return xE, yE
    
    ## Converts motor position to coordinates
    @staticmethod
    def motorpos_to_coordinates (pos1, pos2):
        def pos_to_angle (pos):
            #0     = 14
            #-2970 = 90
            return 14. + pos * (90.-14) / 2970.
        
        (alpha, beta) = (pos_to_angle(pos1), pos_to_angle(-pos2))
        return Writer.angles_to_coordinates (alpha, beta)
    
    @staticmethod
    def get_angle (xA, yA, xB, yB, xC, yC):
        ab2 = (xB-xA)*(xB-xA) + (yB-yA)*(yB-yA)
        bc2 = (xC-xB)*(xC-xB) + (yC-yB)*(yC-yB)
        ac2 = (xC-xA)*(xC-xA) + (yC-yA)*(yC-yA)
        try:
            cos_abc = (ab2 + bc2 - ac2) / (2*math.sqrt(ab2) * math.sqrt(bc2))
            return 180 - (360. * math.acos(cos_abc) / (2 * math.pi))
        except:
            return 180
    
    def set_speed_to_coordinates (self,x,y,max_speed,initx=None,inity=None,brake=0.):
        posB, posA = self.mot_B.position, self.mot_A.position
        myx, myy = Writer.motorpos_to_coordinates (posB, posA)
        dist = math.sqrt((myx-x)*(myx-x) + (myy-y)*(myy-y))
        if (initx or inity):
            too_far = (180-Writer.get_angle(initx, inity, x, y, myx, myy) >= 90)
        else:
            too_far = False
        if too_far or (dist < 0.1 and brake < 1.) or dist < 0.05:
            return 0
        
        nextx = myx + (x - myx) / (dist * 100.)
        nexty = myy + (y - myy) / (dist * 100.)
        
        next_posB, next_posA = Writer.coordinates_to_motorpos (nextx, nexty)
        
        speed = max_speed
        slow_down_dist = (max_speed / 50.)
        if (dist < slow_down_dist):
            speed -= (slow_down_dist-dist)/slow_down_dist * (brake * (max_speed-20))/1.
        
        distB = (next_posB - posB)
        distA = (next_posA - posA)
        if abs(distB) > abs(distA):
            speedB = speed
            speedA = abs(speedB / distB * distA)
        else:
            speedA = speed
            speedB = abs(speedA / distA * distB)
        
        self.mot_B.rotate_forever((math.copysign(speedB, distB)), regulate='off')
        self.mot_A.rotate_forever((math.copysign(speedA, distA)), regulate='off')
        return 1
    
    def goto_point (self, x,y, brake=1., last_x=None, last_y=None, max_speed=70.):
        if (last_x == None or last_y == None):
            initposB, initposA = self.mot_B.position, self.mot_A.position
            initx, inity = Writer.motorpos_to_coordinates (initposB, initposA)
        else:
            initx, inity = last_x, last_y
        max_speed_ = 20
        while (self.set_speed_to_coordinates (x,y,max_speed_,initx,inity,brake)):
            max_speed_ += 5
            if max_speed_>max_speed:max_speed_=max_speed
            time.sleep(0.0001)
        if brake == 1:
            self.mot_B.stop(stop_command='brake')
            self.mot_A.stop(stop_command='brake')
    
    def follow_path (self, list_points, max_speed=70):
        pen_change = False
        lastx = lasty = None
        while (len(list_points)>0):
            if type(list_points[0]) is int:
                pen_change = True
                pen = int(list_points.pop(0))
                time.sleep(0.1)
                if pen:
                    self.pen_down()
                else:
                    self.pen_up()
                return self.follow_path (list_points, max_speed)
            (x,y) = list_points.pop(0)
            posB, posA = self.mot_B.position, self.mot_A.position
            myx, myy = Writer.motorpos_to_coordinates (posB, posA)
            try:
                (x2,y2) = list_points[0]
                angle = Writer.get_angle (myx, myy, x, y, x2, y2)
                brake = 1.
                if angle < 45:
                    brake -= (45-angle)/45.
            except:
                brake = 1.
            if pen_change:
                pen_change = False
                brake = 1.
            self.goto_point (x,y,brake,lastx, lasty, max_speed=max_speed)
            lastx, lasty = x, y
        self.mot_A.stop()
        self.mot_B.stop()
    
    def read_svg (self, image_file):
        # Open simple svg created from template.svg with only paths and no transform.
        # To remove transformations from svg and convert objects to path, use:
        # inkscape --verb=EditSelectAll --verb=ObjectToPath --verb=SelectionUnGroup --verb=FileSave --verb=FileClose --verb=FileQuit my_image.svg
        
        from xml.dom import minidom
        
        def svg_point_to_coord (svg_point):
            scale = 10.
            targetx = svg_point.real/scale
            targety = (272.74-svg_point.imag)/scale
            return (targetx, targety)
        def feq(a,b):
            if abs(a-b)<0.0001:
                return 1
            else:
                return 0
        
        xmldoc = minidom.parse(image_file)
        
        itemlist = xmldoc.getElementsByTagName('path')
        try:
            itemlist = filter(lambda x: x.attributes['id'].value != "borders", itemlist)
        except:
            pass
        path = [s.attributes['d'].value for s in itemlist]
        
        list_points = []
        actual = (0+0j)
        for p_ in path:
            p__ = parse_path(p_)
            for p in p__:
                start = p.point(0.)
                if not feq(actual,start):
                    list_points.append(0)
                    list_points.append(svg_point_to_coord(start))
                    list_points.append(1)
                if ( isinstance(p, Line)):
                    interv = 15
                else:
                    interv = 3
                length = p.length(error=1e-2)
                for i in range(interv,int(math.floor(length)),interv):
                    list_points.append(svg_point_to_coord(p.point(i/length)))
                end = p.point(1.)
                list_points.append(svg_point_to_coord(end))
                actual = end
        list_points.append(0)
        return list_points

    
    def fit_path (self, points):
        def get_bounding_box (points):
            min_x,max_x = min([pix[0] for pix in points if type(pix) is not int]),max([pix[0] for pix in points if type(pix) is not int])
            min_y,max_y = min([pix[1] for pix in points if type(pix) is not int]),max([pix[1] for pix in points if type(pix) is not int])
            return (min_x,min_y,max_x-min_x,max_y-min_y)
        def quad_solve (a,b,c):
            d = b**2-4*a*c
            if d < 0:
                return None
            elif d == 0:
                return (-b+math.sqrt(d))/(2*a)
            else:
                return max((-b+math.sqrt(d))/(2*a), (-b-math.sqrt(d))/(2*a))
        def get_y_circle (circle, x):
            xC, yC, rC = circle
            a = 1
            b = -2 * yC
            c = -2*xC*x + yC**2 - rC**2 + x**2 + xC**2
            return quad_solve (a,b,c)
        def point_pos(x0, y0, d, theta):
            theta_rad = math.radians(theta)
            return x0 + d*math.cos(theta_rad), y0 + d*math.sin(theta_rad)
        def get_circles (r1, r2, xA, yA, xB, yB):
            angle_min = 16
            left_top     = (xB,yB,r1+r2)
            x,y = point_pos(xA, yA, r2, 180-angle_min)
            left_bottom  = (x,y,r1)
            return (left_top, left_bottom)
        def drange(start, stop, step):
            r = start
            while r < stop:
                yield r
                r += step
        
        (bbox_x, bbox_y, bbox_w, bbox_h) = get_bounding_box (points)
        (left_top, left_bottom) = get_circles (Writer.r1 - 1, Writer.r2, Writer.xA, Writer.yA, Writer.xB, Writer.yB)
        min_x = max(left_top[0] - left_top[2] , left_bottom[0] - left_bottom[2] )
        best_fit, best_fit_x, best_fit_y, best_scale = 10000, 0,0,0
        mx = (Writer.xB + Writer.xA)/2.
        for x in drange(min_x, mx, 0.5):
            y1,y2 = get_y_circle(left_top,x)-1, get_y_circle(left_bottom,x)+1
            if (y1!=None and y2 != None):
                if (y1> y2):
                    if abs(((mx-x)*2)/(y1-y2) - (bbox_w/bbox_h)) < best_fit:
                        best_fit, best_fit_x, best_fit_y, best_scale = abs((mx-x)*2)/(y1-y2) - (bbox_w/bbox_h), x, y2, (mx-x)*2 / bbox_w
        
        new_points = []
        for point in points:
            if type(point) is int:
                new_points.append (point)
            else:
                new_points.append(((point[0]-bbox_x)*best_scale + best_fit_x,(point[1]-bbox_y)*best_scale + best_fit_y))
        return new_points

    
    def draw_image (self, image_file = 'images/drawing.svg', max_speed=70.):
        list_points = self.fit_path (self.read_svg (image_file))
        f = open ('pointsfile', w)
        
        f.write (list_points)
        
        f.close ()
        #self.follow_path(list_points, max_speed=max_speed)
    
    def follow_mouse (self, path="/dev/input/by-id/usb-0461_USB_Optical_Mouse-event-mouse"):
        if not os.path.exists(path):
            return
        posB, posA = self.mot_B.position, self.mot_A.position
        startx, starty = Writer.motorpos_to_coordinates (posB, posA)
        self.pen_up()
        pen_up = True
        import evdev
        dev = evdev.Device(path)
        while 1:
            dev.poll()
            time.sleep(0.005)
            if ("BTN_RIGHT" in dev.buttons.keys()):
                #self.pen_up()
                if (dev.buttons["BTN_RIGHT"]):
                    x,y = dev.axes["REL_X"]/100., dev.axes["REL_Y"]/100.
                    targetx = startx-x
                    targety = starty+y
                    print ((targetx, targety))
            if ("BTN_LEFT" in dev.buttons.keys()):
                if (pen_up and dev.buttons["BTN_LEFT"]):
                    pen_up = False
                    self.pen_down()
                elif (not pen_up and not dev.buttons["BTN_LEFT"]):
                    pen_up = True
                    self.pen_up()
            if ("REL_X" in dev.axes.keys()) and ("REL_Y" in dev.axes.keys()):
                x,y = dev.axes["REL_X"]/100., dev.axes["REL_Y"]/100.
                targetx = startx-x
                targety = starty+y
                if (not self.set_speed_to_coordinates (targetx,targety,brake=1.,max_speed = 100)):
                    self.mot_A.stop()
                    self.mot_B.stop()

class TicTacToe():
    # Tic Tac Toe

    import random

    def drawBoard(board):
        # This function prints out the board that it was passed.
    
        # "board" is a list of 10 strings representing the board (ignore index 0)
        print('   |   |')
        print(' ' + board[7] + ' | ' + board[8] + ' | ' + board[9])
        print('   |   |')
        print('-----------')
        print('   |   |')
        print(' ' + board[4] + ' | ' + board[5] + ' | ' + board[6])
        print('   |   |')
        print('-----------')
        print('   |   |')
        print(' ' + board[1] + ' | ' + board[2] + ' | ' + board[3])
        print('   |   |')

    def inputPlayerLetter():
        # Lets the player type which letter they want to be.
    # Returns a list with the player's letter as the first item, and the computer's letter as the second.
        letter = ''
        while not (letter == 'X' or letter == 'O'):
            print('Do you want to be X or O?')
            letter = input().upper()
    
        # the first element in the list is the player's letter, the second is the computer's letter.
        if letter == 'X':
            return ['X', 'O']
        else:
            return ['O', 'X']

    def whoGoesFirst():
        # Randomly choose the player who goes first.
        if random.randint(0, 1) == 0:
            return 'computer'
        else:
            return 'player'

    def playAgain():
        # This function returns True if the player wants to play again, otherwise it returns False.
        print('Do you want to play again? (yes or no)')
        return input().lower().startswith('y')

    def makeMove(board, letter, move):
        board[move] = letter

    def isWinner(bo, le):
        # Given a board and a player's letter, this function returns True if that player has won.
        # We use bo instead of board and le instead of letter so we don't have to type as much.
        return ((bo[7] == le and bo[8] == le and bo[9] == le) or # across the top
        (bo[4] == le and bo[5] == le and bo[6] == le) or # across the middle
        (bo[1] == le and bo[2] == le and bo[3] == le) or # across the bottom
        (bo[7] == le and bo[4] == le and bo[1] == le) or # down the left side
        (bo[8] == le and bo[5] == le and bo[2] == le) or # down the middle
        (bo[9] == le and bo[6] == le and bo[3] == le) or # down the right side
        (bo[7] == le and bo[5] == le and bo[3] == le) or # diagonal
        (bo[9] == le and bo[5] == le and bo[1] == le)) # diagonal

    def getBoardCopy(board):
        # Make a duplicate of the board list and return it the duplicate.
        dupeBoard = []
    
        for i in board:
            dupeBoard.append(i)
    
        return dupeBoard

    def isSpaceFree(board, move):
        # Return true if the passed move is free on the passed board.
        return board[move] == ' '

    def getPlayerMove(board):
        # Let the player type in their move.
        move = ' '
        while move not in '1 2 3 4 5 6 7 8 9'.split() or not isSpaceFree(board, int(move)):
            print('What is your next move? (1-9)')
            move = input()
        return int(move)

    def chooseRandomMoveFromList(board, movesList):
        # Returns a valid move from the passed list on the passed board.
        # Returns None if there is no valid move.
        possibleMoves = []
        for i in movesList:
            if isSpaceFree(board, i):
                possibleMoves.append(i)
    
        if len(possibleMoves) != 0:
            return random.choice(possibleMoves)
        else:
            return None

    def getComputerMove(board, computerLetter):
        # Given a board and the computer's letter, determine where to move and return that move.
        if computerLetter == 'X':
            playerLetter = 'O'
        else:
            playerLetter = 'X'
    
        # Here is our algorithm for our Tic Tac Toe AI:
        # First, check if we can win in the next move
        for i in range(1, 10):
            copy = getBoardCopy(board)
            if isSpaceFree(copy, i):
                makeMove(copy, computerLetter, i)
                if isWinner(copy, computerLetter):
                    return i
    
        # Check if the player could win on their next move, and block them.
        for i in range(1, 10):
            copy = getBoardCopy(board)
            if isSpaceFree(copy, i):
                makeMove(copy, playerLetter, i)
                if isWinner(copy, playerLetter):
                    return i
    
        # Try to take one of the corners, if they are free.
        move = chooseRandomMoveFromList(board, [1, 3, 7, 9])
        if move != None:
            return move
    
        # Try to take the center, if it is free.
        if isSpaceFree(board, 5):
            return 5
    
        # Move on one of the sides.
        return chooseRandomMoveFromList(board, [2, 4, 6, 8])

    def isBoardFull(board):
        # Return True if every space on the board has been taken. Otherwise return False.
        for i in range(1, 10):
            if isSpaceFree(board, i):
                return False
        return True


    print('Welcome to Tic Tac Toe!')

    while True:
        # Reset the board
        theBoard = [' '] * 10
        playerLetter, computerLetter = inputPlayerLetter()
        turn = whoGoesFirst()
        print('The ' + turn + ' will go first.')
        gameIsPlaying = True
    
        while gameIsPlaying:
            if turn == 'player':
                # Player's turn.
                drawBoard(theBoard)
                move = getPlayerMove(theBoard)
                makeMove(theBoard, playerLetter, move)
            
                if isWinner(theBoard, playerLetter):
                    drawBoard(theBoard)
                    print('Hooray! You have won the game you silly banana!')
                    gameIsPlaying = False
                else:
                    if isBoardFull(theBoard):
                        drawBoard(theBoard)
                        print('The game is a tie!')
                        break
                    else:
                        turn = 'computer'
        
            else:
                # Computer's turn.
                move = getComputerMove(theBoard, computerLetter)
                makeMove(theBoard, computerLetter, move)
            
                if isWinner(theBoard, computerLetter):
                    drawBoard(theBoard)
                    print('The computer has beaten you! You lose.')
                    gameIsPlaying = False
                else:
                    if isBoardFull(theBoard):
                        drawBoard(theBoard)
                        print('The game is a tie!')
                        break
                    else:
                        turn = 'player'
    
        if not playAgain():
            break


def main(argv):
    wri = Writer(calibrate = True)
    wri.pen_up()
    path = [0,(-4,18),1,(-4,23),0,(0,18),1,(0,23),0,(2,18),1,(2,23)]
    wri.follow_path (path, max_speed=35)
    #wri.draw_image(image_file = 'images/test.svg',max_speed=35)
    #wri.follow_mouse()
    wri.pen_up()



if __name__ == '__main__':
    main(sys.argv[1:])
