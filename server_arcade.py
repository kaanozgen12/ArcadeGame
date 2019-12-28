import socket
import os
import sys
import logging
import threading
import time
import struct
import subprocess

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
projectiles = []


class Player:
    def __init__(self, ip, p_id, x, y, health, weapon_id, ammo, x_speed, y_speed):
        self.ip = ip
        self.x = x
        self.y = y
        self.health = health
        self.weapon_id = weapon_id
        self.ammo = ammo
        self.x_speed = x_speed
        self.y_speed = y_speed


class Projectile:
    global projectiles
    global players
    global obstacles

    def __init__(self, id, x, y, texture):
        self.id = id
        self.x = x
        self.y = y
        self.texture = texture


def activate_listener(port_number):
    global level
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip_address, port_number))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    s.listen(5)
    print("socket established port:"+str(port_number))
    while True:
        conn, addr = s.accept()
        while True:
            data = conn.recv(15000)
            if not data: break
            if data:
                print(data.decode("utf-8"))
                target_ip = data.decode("utf-8").rstrip(os.linesep).split(",")[0]

                if data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "get_opponent":
                    i = int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
                    data_string = str(ip_address) + ",server_opponent_response,"  + str(
                        players[1-i].x) + "," + str(players[1-i].y) + "," + str(players[1-i].health) + "," + str(
                        players[1-i].weapon_id) + "," + str(players[1-i].ammo) + "," + str(players[1-i].x_speed) + "," + str(
                        players[1-i].y_speed)
                    conn.send(data_string.encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "set_level":
                    level = -1 * int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
                    conn.send("received already".encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "get_level":
                    data_string = str(ip_address) + ",server_get_level_response," + str(level)
                    conn.send(data_string.encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "update_my_player":
                    i = int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
                    players[i].x = data.decode("utf-8").rstrip(os.linesep).split(",")[3]
                    players[i].y = data.decode("utf-8").rstrip(os.linesep).split(",")[4]
                    players[i].health = data.decode("utf-8").rstrip(os.linesep).split(",")[5]
                    players[i].x_speed = data.decode("utf-8").rstrip(os.linesep).split(",")[6]
                    players[i].y_speed = data.decode("utf-8").rstrip(os.linesep).split(",")[7]
                    conn.send("received already!!".encode("utf-8"))
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "character_assign":
                    if players[0].ip == 0 and players[1].ip == 0:
                        conn.send(str(0).encode("utf-8"))
                    elif players[0].ip != 0 and players[1].ip == 0:
                        conn.send(str(1).encode("utf-8"))
                    if players[0].ip == 0 :
                        players[0].ip = data.decode("utf-8").rstrip(os.linesep).split(",")[0]
                    else:
                        players[1].ip = data.decode("utf-8").rstrip(os.linesep).split(",")[0]
                elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "is_ready":
                    data = level if (players[0].ip != 0 and players[1].ip != 0) else 0
                    print("player1 ip: "+str(players[0].ip) + "  player2 ip:"+ str(players[1].ip))
                    conn.send(str(data).encode("utf-8"))
        #conn.close()


def activate_announcer():
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        host = '<broadcast>'
        data_string = str(ip_address) + ",server_announce,"+(str(12345) if players[0].ip==0 else str(12346))
        s.sendto(data_string.encode("utf-8"), (host, 12345))
        s.sendto(data_string.encode("utf-8"), (host, 12346))
        s.sendto(data_string.encode("utf-8"), (host, 12347))
        time.sleep(5)
        print("announced")


players.append(Player(0, 0, 0, 50 + PLAYER_HEIGHT // 2, 100, 0, 0, 0, 0))
players.append(Player(0, 0, SCREEN_WIDTH - PLAYER_WIDTH, 50 + PLAYER_HEIGHT // 2, 100, 0, 0, 0, 0))
announcer = threading.Thread(target=activate_announcer)
announcer.start()
listener1 = threading.Thread(target=activate_listener, args=(12345,))
listener2 = threading.Thread(target=activate_listener, args=(12346,))
listener1.start()
listener2.start()
