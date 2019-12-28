# import arcade
#
# # Open up a window.
# # From the "arcade" library, use a function called "open_window"
# # Set the and dimensions (width and height)
# # Set the window title to "Drawing Example"
# arcade.open_window(800, 600, "Game")
import arcade
import socket
import os
import sys
import logging
import threading
import time
import struct
import subprocess
import sprite_modified

broadcast_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){2}[0-9]*' | grep -Eo '([0-9]*\.){2}[0-9]*' | grep -v '127.0.0'")
ip_address = subprocess.getoutput(
    " ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'")
server_ip = ""
player_listener_port = 10000
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_WIDTH = 96
PLAYER_HEIGHT = 128
announce = True
MOVEMENT_SPEED = 5
event = 0
level = 0
players = []
projectiles = []
obstacles = []
player_id=0
opponent_id=0
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
            return True
        else:
            return False

    def CollisionDetectionProjectile(self, target_x, target_y):
        if (target_x + (PLAYER_WIDTH // 5) >= (self.x - (self.width // 2)) and target_x - (PLAYER_WIDTH // 5) <= (
                self.x + (self.width // 2))) and (
                (self.y + (self.height // 2) >= target_y > self.y - (
                        self.height // 2))):
            return True
        else:
            return False


class Projectile:
    global projectiles
    global players
    global obstacles

    def __init__(self, id, x, y, speed, texture):
        self.id = id
        self.x = x
        self.y = y
        self.width = 75 if id == 1 else 20
        self.height = 15 if id == 1 else 10
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
                self.texture = arcade.load_texture("images/backgrounds/explosion.png")
                self.speed = 0
                self.collisionTime += 1
                if self.collisionTime == 20:
                    projectiles.remove(self)
        for i in range(z):
            if players[opponent_id].center_x + PLAYER_WIDTH // 2 > self.x > players[opponent_id].center_x - PLAYER_WIDTH // 2 and players[opponent_id].center_y + PLAYER_HEIGHT // 2 > self.y > players[opponent_id].center_y - PLAYER_HEIGHT // 2:
                self.texture = arcade.load_texture("images/backgrounds/explosion.png")
                self.speed = 0
                self.collisionTime += 1
                if self.collisionTime == 1:
                    players[opponent_id].health -= 20
                elif self.collisionTime == 10:
                    projectiles.remove(self)


class MyAppWindow(arcade.Window):
    """ Main application class. """

    def __init__(self, width, height):
        global players
        global obstacles
        global PLAYER_WIDTH
        global PLAYER_HEIGHT

        """
        Initializer
        :param width:
        :param height:
        """
        super().__init__(width, height)

        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.all_sprites_list = arcade.SpriteList()
        obstacles.clear()
        if level == 0:

            self.background = arcade.load_texture("images/backgrounds/backgroundColorForest.png")
            obstacles = [Obstacle(1, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH // 5, 100,
                                  arcade.load_texture(
                                      "images/backgrounds/cloud.png")),
                         Obstacle(2, SCREEN_WIDTH * 1 // 4, SCREEN_HEIGHT / 1.4, 100, 100,
                                  arcade.load_texture(
                                      "images/backgrounds/backgroundColorGrass.png")),
                         Obstacle(3, SCREEN_WIDTH * 2 // 4, SCREEN_HEIGHT / 1.4, 100, 100,
                                  arcade.load_texture(
                                      "images/backgrounds/backgroundColorFall.png")),
                         Obstacle(4, SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT / 1.4, 100, 100,
                                  arcade.load_texture(
                                      "images/backgrounds/backgroundColorDesert.png"))]
        else:
            PLAYER_WIDTH = 96
            PLAYER_HEIGHT = 128


            filenames = ["images/MalePerson/Tilesheet/character_malePerson_sheet.png",
                         "images/FemalePerson/Tilesheet/character_femalePerson_sheet.png"]
            for i in range(len(filenames)):
                image_location_list = [[0, 0, PLAYER_WIDTH, PLAYER_HEIGHT]]
                players[i].stand_right_textures = \
                    arcade.load_textures(filenames[i], image_location_list, False)
                players[i].stand_left_textures = \
                    arcade.load_textures(filenames[i], image_location_list, True)

                image_location_list = [[576, 256, PLAYER_WIDTH, PLAYER_HEIGHT],
                                       [672, 256, PLAYER_WIDTH, PLAYER_HEIGHT], [768, 256, PLAYER_WIDTH, PLAYER_HEIGHT]]
                players[i].walk_right_textures = \
                    arcade.load_textures(filenames[i], image_location_list, False)
                players[i].walk_left_textures = \
                    arcade.load_textures(filenames[i], image_location_list, True)
                image_location_list = [[96, 0, PLAYER_WIDTH, PLAYER_HEIGHT]]
                players[i].walk_up_textures = \
                    arcade.load_textures(filenames[i], image_location_list, False)
                players[i].walk_down_textures = \
                    arcade.load_textures(filenames[i], image_location_list, mirrored=True)

                players[i].texture_change_distance = 20

                players[i].center_x = (i * SCREEN_WIDTH) - (i * PLAYER_WIDTH)
                players[i].center_y = 50 + PLAYER_HEIGHT // 2
                players[i].scale = 1

                #time.sleep(10)
                self.all_sprites_list.append(players[i])

            if level == 1:
                self.background = arcade.load_texture("images/backgrounds/backgroundColorGrass.png")
                obstacles = [Obstacle(1, SCREEN_WIDTH // 2, 0, SCREEN_WIDTH, 100,
                                      arcade.load_texture(
                                          "images/backgrounds/big_platform.png")),
                             Obstacle(2, SCREEN_WIDTH // 3, SCREEN_HEIGHT // 4,
                                      75, 44,
                                      arcade.load_texture("images/backgrounds/small_platform.png")),
                             Obstacle(3, 5 * SCREEN_WIDTH // 50, SCREEN_HEIGHT // 2,
                                      75, 44,
                                      arcade.load_texture("images/backgrounds/small_platform.png")),
                             Obstacle(4, (SCREEN_WIDTH * 40) // 45, SCREEN_HEIGHT // 2.5,
                                      75, 44,
                                      arcade.load_texture("images/backgrounds/small_platform.png")),
                             Obstacle(5, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.5,
                                      SCREEN_WIDTH / 2, 30,
                                      arcade.load_texture("images/backgrounds/big_platform.png"))]
            elif level == 2:
                self.background = arcade.load_texture("images/backgrounds/backgroundColorFall.png")
                obstacles = [Obstacle(1, SCREEN_WIDTH // 2, 0, SCREEN_WIDTH, 100,
                                      arcade.load_texture(
                                          "images/backgrounds/big_platform.png")),
                             Obstacle(2, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4,
                                      75, 44,
                                      arcade.load_texture("images/backgrounds/small_platform.png")),
                             Obstacle(3, 5 * SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.5,
                                      75, 44,
                                      arcade.load_texture("images/backgrounds/small_platform.png")),
                             Obstacle(4, SCREEN_WIDTH // 3, SCREEN_HEIGHT // 1.4,
                                      75, 44,
                                      arcade.load_texture("images/backgrounds/small_platform.png")),
                             Obstacle(4, SCREEN_WIDTH * 2 / 3, SCREEN_HEIGHT // 1.4,
                                      75, 44,
                                      arcade.load_texture("images/backgrounds/small_platform.png")),
                             Obstacle(5, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                      SCREEN_WIDTH / 2, 30,
                                      arcade.load_texture("images/backgrounds/big_platform.png"))]
            elif level == 3:
                self.background = arcade.load_texture("images/backgrounds/backgroundColorDesert.png")
                obstacles = [Obstacle(1, SCREEN_WIDTH // 2, 0, SCREEN_WIDTH, 100,
                                      arcade.load_texture(
                                          "images/backgrounds/big_platform.png"))]
                for i in range(9):
                    obstacles.append(
                        Obstacle(i, ((i % 3) + 1) * SCREEN_WIDTH // 4, ((i / 3) + 1) * SCREEN_HEIGHT // 4.5, 75, 44,
                                 arcade.load_texture(
                                     "images/backgrounds/big_platform.png")))


    def on_draw(self):
        """
        Render the screen.
        """
        global players
        global projectiles
        global obstacles
        global player_id

        # This command has to happen before we start drawing
        arcade.start_render()
        arcade.draw_texture_rectangle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                      SCREEN_WIDTH, SCREEN_HEIGHT, self.background)
        if server_ip != "":
            arcade.draw_text("Server Connected:" + str(server_ip), SCREEN_WIDTH // 3, 30, arcade.color.BLACK, 15)

        for obstacle in obstacles:
            arcade.draw_texture_rectangle(obstacle.x, obstacle.y, obstacle.width, obstacle.height, obstacle.texture)
        for projectile in projectiles:
            arcade.draw_texture_rectangle(projectile.x, projectile.y, projectile.width, projectile.height,
                                          projectile.texture)
            if projectile.x - projectile.width // 2 > SCREEN_WIDTH:
                projectiles.remove(projectile)
            projectile.updatePosition()


        # Draw all the sprites.
        if level > 0:
            for i in range(len(players)):
                arcade.draw_rectangle_filled((((-1) ** i) * (SCREEN_WIDTH // 6)) + (i) * SCREEN_WIDTH,
                                             SCREEN_HEIGHT * 0.95,
                                             100 * 2, 15, arcade.color.BARN_RED)
                arcade.draw_rectangle_filled(
                    (((((-1) ** i) * (SCREEN_WIDTH // 6)) + i * SCREEN_WIDTH) - 100) + int(players[i].health),
                    SCREEN_HEIGHT * 0.95,
                    int(players[i].health) * 2, 15, arcade.color.RED)
            self.all_sprites_list.draw()
            data_ = str(ip_address)+",update_my_player,"+str(player_id)+","+str(players[player_id].center_x)+","+str(players[player_id].center_y)+","+str(players[player_id].health)+","+str(players[player_id].change_x)+","+str(players[player_id].change_y)
            server_socket.send(data_.encode("utf-8"))
            server_socket.recv(1024)

            print("asked to get opponent "+str(player_id))
            server_socket.send((str(ip_address) + ",get_opponent,"+str(player_id)).encode("utf-8"))
            data = server_socket.recv(1024)
            if data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "server_opponent_response":
                players[1 - int(player_id)].center_x = int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
                players[1 - int(player_id)].center_y = int(data.decode("utf-8").rstrip(os.linesep).split(",")[3])
                players[1 - int(player_id)].health = int(data.decode("utf-8").rstrip(os.linesep).split(",")[4])
                players[1 - int(player_id)].weapon_id = int(data.decode("utf-8").rstrip(os.linesep).split(",")[5])
                players[1 - int(player_id)].ammo = int(data.decode("utf-8").rstrip(os.linesep).split(",")[6])
                players[1 - int(player_id)].change_x = float(data.decode("utf-8").rstrip(os.linesep).split(",")[7])
                players[1 - int(player_id)].change_y = float(data.decode("utf-8").rstrip(os.linesep).split(",")[8])
    def on_key_press(self, key, modifiers):
        global event
        global level
        global projectiles
        global player
        """
        Called whenever the mouse moves.
        """
        if level > 0:
            if key == arcade.key.UP:
                if event == 0 and players[player_id].change_y == 0:
                    event = 30

            elif key == arcade.key.DOWN:
                players[player_id].change_y = -MOVEMENT_SPEED
            elif key == arcade.key.LEFT:
                players[player_id].change_x = -MOVEMENT_SPEED
            elif key == arcade.key.RIGHT:
                players[player_id].change_x = MOVEMENT_SPEED
            elif key == arcade.key.SPACE:
                projectiles.append(Projectile(0, players[player_id].center_x + PLAYER_WIDTH // 2, players[player_id].center_y,
                                              10 if players[player_id].change_x >= 0 else -10,
                                              arcade.load_texture("images/backgrounds/bazooka_missile.png",
                                                                  mirrored=False if players[player_id].change_x >= 0 else True)))

    def on_key_release(self, key, modifiers):
        global event
        global level
        """
        Called when the user presses a mouse button.
        """
        if level > 0:
            if key == arcade.key.UP or key == arcade.key.DOWN:

                players[player_id].change_y = 0
            elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
                players[player_id].change_x = 0

    def on_mouse_press(self, x, y, button, modifiers):
        global event
        global level
        global PLAYER_WIDTH
        global PLAYER_HEIGHT
        global obstacles
        global opponent

        """
        Called when the user presses a mouse button.
        """
        if level <= 0 and button == arcade.MOUSE_BUTTON_LEFT:

            for i in range(len(obstacles)):
                if level <= 0:
                    PLAYER_WIDTH = 0
                    PLAYER_HEIGHT = 0

                if obstacles[i].CollisionDetectionProjectile(x, y):
                    if int(obstacles[i].id) != 1:
                        level = -1 * (int(obstacles[i].id) - 1)

                        try:
                            server_socket.send( (   str(ip_address) + ",set_level," + str(level)  ).encode("utf-8") )
                            server_socket.recv(1024)
                        except :
                            print("no connection to the server")
                    else:
                        level = -1 * level if level != 0 else 1
                        PLAYER_WIDTH = 96
                        PLAYER_HEIGHT = 128

                        server_socket.send((str(ip_address) + ",is_ready").encode("utf-8"))
                        data = int(server_socket.recv(1024).decode("utf-8"))
                        while data==0:
                            print("waiting for opponent")
                            time.sleep(1)
                            server_socket.send((str(ip_address) + ",is_ready").encode("utf-8"))
                            data = int(server_socket.recv(1024).decode("utf-8"))
                        level = data

                        self.__init__(800, 600)

    def update(self, delta_time):
        global event
        global level
        global players
        global projectiles
        """ Movement and game logic """
        if level > 0:

            if 0 < event <= 30:
                players[player_id].change_y = MOVEMENT_SPEED
                event -= 1
            elif event == 0:
                players[player_id].change_y = -MOVEMENT_SPEED
                for obstacle in obstacles:
                    if players[player_id].change_y != 0 and obstacle.CollisionDetectionFall(players[player_id].center_x,
                                                                                     (players[player_id].center_y - PLAYER_HEIGHT // 2)):
                        players[player_id].change_y = 0
                        players[player_id].center_y = obstacle.y + PLAYER_HEIGHT // 2 + (obstacle.height // 2)

                        break
            else:
                players[player_id].change_y = 0
            for projectile in projectiles:
                projectile.CollisionDetection()
            self.all_sprites_list.update()
            self.all_sprites_list.update_animation()

def udp_listener():
    global server_ip
    global players
    global opponent
    global server_socket
    global player_id
    global opponent_id
    UDP_IP = ""
    UDP_PORT = 12347
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        if data:
            if data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "server_announce":
                server_ip = data.decode("utf-8").rstrip(os.linesep).split(",")[0]
                server_socket.connect((server_ip, int(data.decode("utf-8").rstrip(os.linesep).split(",")[2]) ))
                server_socket.send((str(ip_address) + ",character_assign").encode("utf-8"))
                data = int(server_socket.recv(1024).decode("utf-8"))
                player_id = int(data)
                opponent_id = 1-int(data)
                break

def main():
    global players
    MyAppWindow(SCREEN_WIDTH, SCREEN_HEIGHT)
    udp_listen = threading.Thread(target=udp_listener)
    udp_listen.start()
    players = [sprite_modified.AnimatedWalkingSprite(), sprite_modified.AnimatedWalkingSprite()]
    arcade.run()



if __name__ == "__main__":
    main()
