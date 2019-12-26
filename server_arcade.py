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
PORT = 12345
broadcast_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){2}[0-9]*' | grep -Eo '([0-9]*\.){2}[0-9]*' | grep -v '127.0.0'")
ip_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'")

players = []
projectiles = []


class Player:
    def __init__(self, id, x, y, health, weapon_id, ammo, x_speed, y_speed):
        self.id = id
        self.x = x
        self.y = y
        self.health = health
        self.weapon_id = weapon_id
        self.ammo = ammo
        self.x_speed = x_speed
        self.y_speed = y_speed


class Obstacle:
    def __init__(self, id, x, y, width, height, texture):
        self.id = id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.texture = texture

    def CollisionDetectionFall(self, target_x, target_y):
        if (target_x + (PLAYER_WIDTH // 5) >= (self.x - (self.width // 2)) and target_x - (PLAYER_WIDTH // 5) <= (
                self.x + (self.width // 2))) and (
                (self.y + (self.height // 2) - MOVEMENT_SPEED * 0.5 <= target_y < self.y + (
                        self.height // 2) + MOVEMENT_SPEED)):
            # print(str(self.x) + "..." + str(self.y) + "???id:::" + str(self.id) + "..." + str(target_x) + "::" + str(target_y))
            return True
        else:
            return False

    def CollisionDetectionProjetile(self, target_x, target_y):
        if (target_x + (PLAYER_WIDTH // 5) >= (self.x - (self.width // 2)) and target_x - (PLAYER_WIDTH // 5) <= (
                self.x + (self.width // 2))) and (
                (self.y + (self.height // 2) - MOVEMENT_SPEED * 0.5 <= target_y < self.y + (
                        self.height // 2) + MOVEMENT_SPEED)):
            return True
        else:
            return False


class Projectile:
    global projectiles
    global players
    global obstacles

    def __init__(self, id, x, y, width, height, speed, texture):
        self.id = id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.texture = texture
        self.speed = speed
        self.collisionTime = 0

    def updatePosition(self):
        self.x += self.speed

    def CollisionDetection(self):
        y = (len(obstacles))
        z = (len(players))
        for i in range(y):
            if obstacles[i].x + obstacles[i].width // 2 > self.x > obstacles[i].x - obstacles[i].width // 2 and \
                    obstacles[i].y + obstacles[i].height // 2 > self.y > obstacles[i].y - obstacles[i].height // 2:
                # self.texture = arcade.load_texture("images/backgrounds/explosion.png")
                self.speed = 0
                self.collisionTime += 1
                if self.collisionTime == 20:
                    projectiles.remove(self)
        for i in range(z):
            if players[i].center_x + PLAYER_WIDTH // 2 > self.x > players[i].center_x - PLAYER_WIDTH // 2 and players[
                i].center_y + PLAYER_HEIGHT // 2 > self.y > players[i].center_y - PLAYER_HEIGHT // 2:
                # self.texture = arcade.load_texture("images/backgrounds/explosion.png")
                self.speed = 0
                self.collisionTime += 1
                if self.collisionTime == 1:
                    players[i].health -= 20
                elif self.collisionTime == 10:
                    projectiles.remove(self)


def handle_message(conn, addr):
    # data received from client
    data = conn.recv(1024)
    if data:
        print(data.decode("utf-8"))

        if data.decode("utf-8").rstrip(os.linesep).split(",")[2] == "server_probe":
            print("hello")

    conn.close()


def udp_listener():
    UDP_IP = ""
    UDP_PORT = 12345
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        data, addr = sock.recvfrom(1500)  # buffer size is 1500 bytes
        if data:
            print(data.decode("utf-8"))
            if data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "server_probe":
                target_ip = data.decode("utf-8").rstrip(os.linesep).split(",")[0]
                x = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                x.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
                x.connect((str(target_ip), 10000))
                if 0 <= len(players) < 2:
                    data_string = str(ip_address) + ",server_response," + str(10000 + len(players))
                    x.sendto(data_string.encode("utf-8"), (str(target_ip), 10000))
                else:
                    data_string = str(ip_address) + ",server_reject"
                    x.sendto(data_string.encode("utf-8"), (str(target_ip), 10000))
                x.shutdown(2)
                x.close()


def activate_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip_address, 12345))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    s.listen(5)
    while True:
        conn, addr = s.accept()
        if conn:
            l = threading.Thread(target=handle_message, args=(conn, addr,))
            l.start()
            l.join()


udp_listen = threading.Thread(target=udp_listener)
udp_listen.start()
activate_listener()
