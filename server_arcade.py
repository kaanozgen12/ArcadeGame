import socket
import os
import sys
import arcade
import threading
import time
import struct
from random import randint, random
import subprocess
from threading import Semaphore, BoundedSemaphore

s1 = Semaphore(1)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_WIDTH = 96
PLAYER_HEIGHT = 128

MOVEMENT_SPEED = 5

broadcast_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){2}[0-9]*' | grep -Eo '([0-9]*\.){2}[0-9]*' | grep -v '127.0.0'")
ip_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'")

level = 1
players = []
projectiles = ["",""]
obstacles = []



class Player:
    def __init__(self, ip, p_id, x, y, health, weapon_id, ammo, x_speed, y_speed):
        self.ip = ip
        self.p_id= p_id
        self.x = x
        self.y = y
        self.health = health
        self.weapon_id = weapon_id
        self.ammo = ammo
        self.x_speed = x_speed
        self.y_speed = y_speed


def activate_listener(port_number):
    global level
    global bazooka
    global rifle
    global GAME_STATUS

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip_address, port_number))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    s.listen(5)
    print("socket established port:" + str(port_number))
    while True:
        conn, addr = s.accept()
        while True:
            data = conn.recv(15000)
            if not data: break
            if data:
                #print(data.decode("utf-8"))
                target_ip = data.decode("utf-8").rstrip(os.linesep).split(",")[0]

                if data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "get_opponent":
                    i = int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
                    data_string = str(ip_address) + ",server_opponent_response," + str(
                        players[1 - i].x) + "," + str(players[1 - i].y) + "," + str(players[1 - i].health) + "," + str(
                        players[1 - i].weapon_id) + "," + str(int(players[1 - i].ammo)) + "," + str(
                        players[1 - i].x_speed) + "," + str(
                        players[1 - i].y_speed)
                    conn.send(data_string.encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "set_level":
                    level = -1 * int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
                    conn.send("received already".encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "get_level":
                    data_string = str(ip_address) + ",server_get_level_response," + str(level)
                    conn.send(data_string.encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "update_hp":
                    players[int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])].health -= int(data.decode("utf-8").rstrip(os.linesep).split(",")[3])
                    conn.send("opponent damaged".encode("utf-8"))
                    print("opponent damaged")
                    print("player1 healt: "+str(players[0].health))
                    print("player2 healt: "+str(players[1].health))
                    if int(players[int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])].health)<=0:
                        GAME_STATUS = -1*(1-int(data.decode("utf-8").rstrip(os.linesep).split(",")[2]))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "update_my_player":
                    i = int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
                    players[i].x = data.decode("utf-8").rstrip(os.linesep).split(",")[3]
                    players[i].y = data.decode("utf-8").rstrip(os.linesep).split(",")[4]
                    players[i].x_speed = data.decode("utf-8").rstrip(os.linesep).split(",")[5]
                    players[i].y_speed = data.decode("utf-8").rstrip(os.linesep).split(",")[6]
                    players[i].ammo = data.decode("utf-8").rstrip(os.linesep).split(",")[7]
                    players[i].weapon_id = data.decode("utf-8").rstrip(os.linesep).split(",")[8]

                    conn.send("received already!!".encode("utf-8"))
                    if int(players[i].y)<-100:
                        players[i].health = 0
                        GAME_STATUS = -1 * (1-int(i))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "character_assign":
                    if players[0].ip == 0 and players[1].ip == 0:
                        conn.send(str(0).encode("utf-8"))
                    elif players[0].ip != 0 and players[1].ip == 0:
                        conn.send(str(1).encode("utf-8"))
                    if players[0].ip == 0:
                        players[0].ip = data.decode("utf-8").rstrip(os.linesep).split(",")[0]
                    else:
                        players[1].ip = data.decode("utf-8").rstrip(os.linesep).split(",")[0]
                        set_obstacles()
                        game_timing = threading.Thread(target=game_timer)
                        game_timing.start()
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "is_ready":
                    data = level if (players[0].ip != 0 and players[1].ip != 0) else 0
                    print("player1 ip: " + str(players[0].ip) + "  player2 ip:" + str(players[1].ip))
                    if data != "":
                        conn.send(str(data).encode("utf-8"))
                    else:
                        conn.send(str("0000000").encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "get_projectiles":
                    data_string = projectiles[1-int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])]
                    conn.send(data_string.encode("utf-8") if data_string!="" else "empty_projectiles".encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "get_my_status":
                    id_of_user = int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
                    data_string = str(players[id_of_user].health)
                    conn.send(data_string.encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "get_game_status":

                    data_string = str(GAME_STATUS)+";"+str(bazooka)+";"+str(rifle)+";"+str(bomb)
                    conn.send(data_string.encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "loot":
                    players[int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])].weapon_id = int(data.decode("utf-8").rstrip(os.linesep).split(",")[3])
                    players[int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])].ammo = 10
                    if int(data.decode("utf-8").rstrip(os.linesep).split(",")[3]) == 1 :
                        bazooka="-1000000,-1000000"
                    else:
                        rifle="-1000000,-1000000"
                    conn.send("loot activated".encode("utf-8"))
                    print("loot awarded")
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "set_projectiles":
                    try:
                        projectiles[int(data.decode("utf-8").rstrip(os.linesep).split(";")[0].split(",")[2])] = data.decode("utf-8").rstrip(os.linesep).split(";", 1)[1]
                    except IndexError:
                        pass
                    conn.send("projectiles_set".encode("utf-8"))

        # conn.close()

GAME_STATUS = 1
obstacles = []
bazooka = "-1000000,-1000000"
rifle = "-1000000,-1000000"
bomb = "-1000000,-1000000"


def game_timer():
    global obstacles
    global bazooka
    global rifle
    global bomb
    #print("timer started")
    while GAME_STATUS == 1:
        #print("loop")
        if bazooka == "-1000000,-1000000":

            distancer =  1 if random() < 0.5 else -1
            i = randint(0, len(obstacles)-1)
            margin = round(random(), 2)*obstacles[i].width
            center_x = obstacles[i].x + distancer*margin
            center_y= obstacles[i].y + (obstacles[i].height/2) +20
            bazooka=str(center_x)+","+str(center_y)
            print("bazooka generated: "+bazooka)
        if rifle == "-1000000,-1000000":

            distancer =  1 if random() < 0.5 else -1
            ix = randint(0, len(obstacles)-1)
            margin = round(random(), 2)*obstacles[ix].width
            center_x = obstacles[ix].x + distancer*margin
            center_y= obstacles[ix].y + (obstacles[ix].height/2) +20
            rifle=str(center_x)+","+str(center_y)
            print("rifle generated: "+rifle)
        time.sleep(120)



class Obstacle:
    def __init__(self, obstacle_id, x, y, width, height):
        self.id = obstacle_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height


def set_obstacles():
    global obstacles
    if level == 1:
        obstacles = [Obstacle(2, SCREEN_WIDTH // 3, SCREEN_HEIGHT // 4,
                              75, 44),
                     Obstacle(3, 5 * SCREEN_WIDTH // 50, SCREEN_HEIGHT // 2,
                              75, 44),
                     Obstacle(4, (SCREEN_WIDTH * 40) // 45, SCREEN_HEIGHT // 2.5,
                              75, 44),
                     Obstacle(5, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.5,
                              SCREEN_WIDTH / 2, 30)]
    elif level == 2:
        obstacles = [Obstacle(2, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4,
                              75, 44),
                     Obstacle(3, 5 * SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.5,
                              75, 44),
                     Obstacle(4, SCREEN_WIDTH // 3, SCREEN_HEIGHT // 1.4,
                              75, 44),
                     Obstacle(4, SCREEN_WIDTH * 2 / 3, SCREEN_HEIGHT // 1.4,
                              75, 44),
                     Obstacle(5, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                              SCREEN_WIDTH / 2, 30)]
    elif level == 3:
        for i in range(9):
            obstacles.append(
                Obstacle(i, ((i % 3) + 1) * SCREEN_WIDTH // 4, ((i / 3) + 1) * SCREEN_HEIGHT // 4.5, 75, 44))


def activate_announcer():
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        host = '<broadcast>'
        data_string = str(ip_address) + ",server_announce," + (str(12345) if players[0].ip == 0 else str(12346))
        s.sendto(data_string.encode("utf-8"), (host, 12345))
        s.sendto(data_string.encode("utf-8"), (host, 12346))
        s.sendto(data_string.encode("utf-8"), (host, 12347))
        time.sleep(2)
        #print("announced")


players.append(Player(0, 0, 0, 50 + PLAYER_HEIGHT // 2, 100, 0, 0, 0, 0))
players.append(Player(0, 0, SCREEN_WIDTH - PLAYER_WIDTH, 50 + PLAYER_HEIGHT // 2, 100, 0, 0, 0, 0))
announcer = threading.Thread(target=activate_announcer)
announcer.start()
listener1 = threading.Thread(target=activate_listener, args=(12345,))
listener2 = threading.Thread(target=activate_listener, args=(12346,))
listener1.start()
listener2.start()
