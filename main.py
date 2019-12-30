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

GAME_STATUS = 1
GAME_STARTED = False
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
projectiles_opponent = ""
obstacles = []
player_id = 0
opponent_id = 0
ammo = 0
weapon_damages = [0, 20, 10]
weapon_heights = [50, 25, 10]
weapon_widths = [50, 65, 20]

damage_opponent = False
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
loot_number = 0


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
        global loot_number
        if (target_x + (PLAYER_WIDTH // 5) >= (float(self.x) - (float(self.width) // 2)) and target_x - (
                PLAYER_WIDTH // 5) <= (
                    float(self.x) + (float(self.width) // 2))) and (
                (float(self.y) + (float(self.height) // 2) >= target_y > float(self.y) - (
                        float(self.height) // 2))):
            return True
        else:
            return False


class Projectile:
    global projectiles
    global players
    global obstacles

    def __init__(self, id_number, x, y, speed):
        self.id_number = id_number
        self.x = x
        self.y = y
        self.speed = speed
        if abs(self.id_number) == 1:
            self.width = weapon_widths[1]
        elif abs(self.id_number) == 2:
            self.width = weapon_widths[2]
        else:
            self.width = 60
        if abs(self.id_number) == 1:
            self.height = weapon_heights[1]
        elif abs(self.id_number) == 2:
            self.height = weapon_heights[2]
        else:
            self.height = 60

        self.collisionTime = 0
        self.texture = arcade.load_texture("images/backgrounds/explosion.png")
        if id_number == 0:
            self.texture = arcade.load_texture("images/backgrounds/explosion.png")
        elif abs(id_number) == 1:
            self.texture = arcade.load_texture("images/backgrounds/bazooka_missile.png",
                                               mirrored=False if id_number > 0 else True)
        elif abs(id_number) == 2:
            self.texture = arcade.load_texture("images/backgrounds/bullet.png",
                                               mirrored=False if id_number > 0 else True)
        elif id_number == -4:
            self.texture = arcade.load_texture("images/backgrounds/bazooka.png")
        elif id_number == -3:
            self.texture = arcade.load_texture("images/backgrounds/rifle.png")

    def updatePosition(self):
        self.x += self.speed

    def LootDetection(self):
        global loot_number
        if players[player_id].center_x + PLAYER_WIDTH // 2 > self.x > players[
            player_id].center_x - PLAYER_WIDTH // 2 and players[
                 player_id].center_y + PLAYER_HEIGHT // 2 > self.y > players[
                 player_id].center_y - PLAYER_HEIGHT // 2:
            print("collision with loot")
            loot_number =  int(self.id_number) + 5
            self.x = -1000000
            self.y = -1000000
            players[player_id].weapon = int(self.id_number) + 5
            players[player_id].ammo = 10

    def CollisionDetection(self):
        global damage_opponent
        y = (len(obstacles))
        z = (len(players))

        if self.x > SCREEN_WIDTH or self.x < 0:
            try:
                projectiles.remove(self)
            except ValueError:
                print("already removed")

        else:
            for i in range(y):
                if obstacles[i].x + obstacles[i].width // 2 > self.x > obstacles[i].x - \
                        obstacles[i].width // 2 and \
                        obstacles[i].y + obstacles[i].height // 2 > self.y > obstacles[i].y - obstacles[i].height // 2:
                    self.texture = arcade.load_texture("images/backgrounds/explosion.png")
                    self.id_number = 0
                    self.speed = 0
                    self.collisionTime += 1
                    if self.collisionTime == 40:
                        try:
                            projectiles.remove(self)
                        except ValueError:
                            print("already removed")
            for i in range(z):
                if players[opponent_id].center_x + PLAYER_WIDTH // 2 > self.x > players[
                    opponent_id].center_x - PLAYER_WIDTH // 2 and players[
                    opponent_id].center_y + PLAYER_HEIGHT // 2 > self.y > players[
                    opponent_id].center_y - PLAYER_HEIGHT // 2:
                    self.texture = arcade.load_texture("images/backgrounds/explosion.png")
                    self.speed = 0
                    self.id_number = 0
                    self.collisionTime += 1
                    if self.collisionTime == 1:
                        damage_opponent = True
                    elif self.collisionTime == 40:
                        try:
                            projectiles.remove(self)
                        except ValueError:
                            print("already removed")




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

                # time.sleep(10)
                self.all_sprites_list.append(players[i])

            if level == 1:
                self.background = arcade.load_texture("images/backgrounds/backgroundColorGrass.png")
                obstacles = [Obstacle(1, SCREEN_WIDTH // 2, 0, SCREEN_WIDTH * 2, 100,
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
                obstacles = [Obstacle(1, SCREEN_WIDTH // 2, 0, SCREEN_WIDTH * 2, 100,
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
        global game_environment
        global player_id

        # This command has to happen before we start drawing
        arcade.start_render()
        arcade.draw_texture_rectangle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                      SCREEN_WIDTH, SCREEN_HEIGHT, self.background)
        if GAME_STATUS == 1:
            if server_ip != "":
                arcade.draw_text("Server Connected:" + str(server_ip), SCREEN_WIDTH // 3, 30, arcade.color.BLACK, 15)

            for obstacle in obstacles:
                arcade.draw_texture_rectangle(obstacle.x, obstacle.y, obstacle.width, obstacle.height, obstacle.texture)

            for weapon in game_environment:
                if weapon.x != -1000000:
                    arcade.draw_texture_rectangle(weapon.x, weapon.y, weapon.width, weapon.height, weapon.texture)

            for projectile in projectiles:
                arcade.draw_texture_rectangle(projectile.x, projectile.y, projectile.width, projectile.height,
                                              projectile.texture)
                if projectile.x - projectile.width // 2 > SCREEN_WIDTH:
                    projectiles.remove(projectile)
                projectile.updatePosition()

            # Draw all the sprites.
            if level > 0:
                for i in range(0,2):
                    arcade.draw_rectangle_filled((((-1) ** i) * (SCREEN_WIDTH // 6)) + (i) * SCREEN_WIDTH,
                                                 SCREEN_HEIGHT * 0.95,
                                                 100 * 2, 15, arcade.color.BARN_RED)
                    weapon_of_user = int(players[i].weapon)
                    if weapon_of_user == 0:
                        texture = arcade.load_texture("images/backgrounds/no_weapon.png")
                    elif weapon_of_user == 1:
                        texture = arcade.load_texture("images/backgrounds/bazooka.png")
                    else:
                        texture = arcade.load_texture("images/backgrounds/rifle.png")

                    arcade.draw_texture_rectangle(SCREEN_WIDTH // 2 - ((-1) ** i) * 100,
                                                  SCREEN_HEIGHT * 0.95,
                                                  40, 40, texture)
                    arcade.draw_text(str(players[i].ammo), SCREEN_WIDTH // 2 - ((-1) ** i) * 100,
                                     SCREEN_HEIGHT * 0.90, arcade.color.BLACK, 12)

                    arcade.draw_rectangle_filled(
                        (((((-1) ** i) * (SCREEN_WIDTH // 6)) + i * SCREEN_WIDTH) - 100) + int(players[i].health),
                        SCREEN_HEIGHT * 0.95,
                        int(players[i].health) * 2, 15, arcade.color.RED)

                try:
                    for i in range(len(projectiles_opponent.rstrip(os.linesep).split(";"))):
                        id_projectile = int(projectiles_opponent.rstrip(os.linesep).split(";")[i].split(",")[0])
                        if abs(id_projectile) == 0:
                            texture = arcade.load_texture("images/backgrounds/explosion.png")
                        elif abs(id_projectile) == 1:
                            texture = arcade.load_texture("images/backgrounds/bazooka_missile.png",
                                                          mirrored=False if id_projectile > 0 else True)
                        else:
                            texture = arcade.load_texture("images/backgrounds/bullet.png",
                                                          mirrored=False if id_projectile > 0 else True)
                        if projectiles_opponent.rstrip(os.linesep).split(";")[i] != "":
                            center_x = float(projectiles_opponent.rstrip(os.linesep).split(";")[i].split(",")[1])
                            center_y = float(projectiles_opponent.rstrip(os.linesep).split(";")[i].split(",")[2])
                            arcade.draw_texture_rectangle(center_x, center_y, weapon_widths[abs(id_projectile)],
                                                          weapon_heights[abs(id_projectile)],texture)
                except IndexError:
                    pass
                except ValueError:
                    pass

                self.all_sprites_list.draw()
        elif GAME_STATUS == 0 or GAME_STATUS == -1 :
            arcade.draw_text("PLAYER "+str(int(GAME_STATUS)*-1)+" WON", SCREEN_WIDTH // 2.5 ,
                             SCREEN_HEIGHT //2 , arcade.color.BLACK, 20)

    def on_key_press(self, key, modifiers):
        global event
        global level
        global projectiles
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
                if len(projectiles) < 1 and players[player_id].ammo > 0:
                    players[player_id].ammo -= 1
                    projectiles.append(
                        Projectile(
                            -1 * int(players[player_id].weapon) if players[player_id].change_x < 0 else int(
                                players[player_id].weapon),
                            (players[player_id].center_x + PLAYER_WIDTH // 2),
                            players[player_id].center_y,
                            10 if players[player_id].change_x >= 0 else -10))
                    if players[player_id].ammo == 0:
                        players[player_id].weapon = 0

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
        global  GAME_STATUS
        global GAME_STARTED

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
                            server_socket.send((str(ip_address) + ",set_level," + str(level)).encode("utf-8"))
                            server_socket.recv(1024)
                        except:
                            print("no connection to the server")
                    else:
                        try:
                            #level = -1 * level if level != 0 else 1
                            PLAYER_WIDTH = 96
                            PLAYER_HEIGHT = 128
                            server_socket.send((str(ip_address) + ",is_ready").encode("utf-8"))
                            data = int(server_socket.recv(1024).decode("utf-8"))
                            while data == 0:
                                print("waiting for opponent")
                                time.sleep(1)
                                server_socket.send((str(ip_address) + ",is_ready").encode("utf-8"))
                                data = int(server_socket.recv(1024).decode("utf-8"))
                            level = data

                            self.__init__(800, 600)
                            GAME_STATUS = 1
                            GAME_STARTED= True
                            #server_update = threading.Thread(target=updates_from_server)
                            #server_update.start()
                        except OSError:
                            print("connection not ready")

    def update(self, delta_time):
        global event
        global level
        global players
        global projectiles
        global GAME_STARTED
        """ Movement and game logic """
        if GAME_STARTED and level > 0:

            if 0 < event <= 30:
                players[player_id].change_y = MOVEMENT_SPEED
                event -= 1
            elif event == 0:
                players[player_id].change_y = -MOVEMENT_SPEED
                for obstacle in obstacles:
                    if players[player_id].change_y != 0 and obstacle.CollisionDetectionFall(players[player_id].center_x,
                                                                                            (players[
                                                                                                 player_id].center_y - PLAYER_HEIGHT // 2)):
                        players[player_id].change_y = 0
                        players[player_id].center_y = obstacle.y + PLAYER_HEIGHT // 2 + (obstacle.height // 2)

                        break
            else:
                players[player_id].change_y = 0
            for projectile in projectiles:
                projectile.CollisionDetection()
            for weapon in game_environment:
                weapon.LootDetection()
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
                server_socket.connect((server_ip, int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])))
                server_socket.send((str(ip_address) + ",character_assign").encode("utf-8"))
                data = int(server_socket.recv(1024).decode("utf-8"))
                player_id = int(data)
                opponent_id = 1 - int(data)
                break


def updates_from_server():
    global players
    global projectiles_opponent
    global damage_opponent
    global GAME_STATUS
    global game_environment
    global GAME_STARTED
    global loot_number
    while  GAME_STATUS == 1:
        if GAME_STARTED:
            try:
                data_string = str(ip_address) + ",get_my_status," + str(player_id)
                server_socket.send(data_string.encode("utf-8"))
                data_string = server_socket.recv(1024)
                #print(data_string.decode("utf-8"))
                players[player_id].health = float(data_string.decode("utf-8").rstrip(os.linesep))

                data_ = str(ip_address) + ",set_projectiles," + str(player_id) + ";"
                for i in range(len(projectiles)):
                    data_ += str(projectiles[i].id_number) + "," + str(projectiles[i].x) + "," + str(projectiles[i].y) + ";"
                server_socket.send(data_.encode("utf-8"))
                server_socket.recv(1024)

                # print("asked to get opponent " + str(player_id))
                server_socket.send((str(ip_address) + ",get_opponent," + str(player_id)).encode("utf-8"))
                data = server_socket.recv(1024)
                if data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "server_opponent_response":
                    players[opponent_id].center_x = float(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
                    players[opponent_id].center_y = float(data.decode("utf-8").rstrip(os.linesep).split(",")[3])
                    players[opponent_id].health = float(data.decode("utf-8").rstrip(os.linesep).split(",")[4])
                    players[opponent_id].weapon = int(data.decode("utf-8").rstrip(os.linesep).split(",")[5])
                    players[opponent_id].ammo = int(data.decode("utf-8").rstrip(os.linesep).split(",")[6])
                    players[opponent_id].change_x = float(data.decode("utf-8").rstrip(os.linesep).split(",")[7])
                    players[opponent_id].change_y = float(data.decode("utf-8").rstrip(os.linesep).split(",")[8])

                data_string = str(ip_address) + ",get_projectiles," + str(player_id)
                server_socket.send(data_string.encode("utf-8"))
                data_string = server_socket.recv(1024)
                if data_string.decode("utf-8") != "empty_projectiles":
                    projectiles_opponent = data_string.decode("utf-8")

                else:
                    projectiles_opponent = ""



                data_ = str(ip_address) + ",update_my_player," + str(player_id) + "," + str(
                    players[player_id].center_x) + "," + str(players[player_id].center_y) + "," + str(
                    players[player_id].change_x) + "," + str(players[player_id].change_y) + "," + str(players[player_id].ammo) +"," +str(players[player_id].weapon)
                server_socket.send(data_.encode("utf-8"))
                server_socket.recv(1024)


                data_ = str(ip_address) + ",get_game_status"
                server_socket.send(data_.encode("utf-8"))
                data = server_socket.recv(1024)
                datas = data.decode("utf-8").rstrip(os.linesep).split(";")
                # print(datas)
                GAME_STATUS = int(datas[0])
                game_environment[0].x = float(datas[1].split(",")[0])
                game_environment[0].y = float(datas[1].split(",")[1])
                game_environment[1].x = float(datas[2].split(",")[0])
                game_environment[1].y = float(datas[2].split(",")[1])


                if loot_number > 0:
                    data_ = str(ip_address) + ",loot," + str(player_id) + "," + str(loot_number)
                    loot_number = 0
                    server_socket.send(data_.encode("utf-8"))
                    server_socket.recv(1024)
                time.sleep(0.05)

                if damage_opponent:
                    server_socket.send((str(ip_address) + ",update_hp," + str(opponent_id) + "," + str(
                        weapon_damages[players[player_id].weapon])).encode("utf-8"))
                    server_socket.recv(1024)
                    damage_opponent = False
            except OSError:
                print("Server not connected yet")



game_environment = [Projectile(-4, -1000000, -1000000, 0),
                    Projectile(-3, -1000000, -1000000, 0)]


def main():
    global players
    MyAppWindow(SCREEN_WIDTH, SCREEN_HEIGHT)
    udp_listen = threading.Thread(target=udp_listener)
    udp_listen.start()
    server_update = threading.Thread(target=updates_from_server)
    server_update.start()
    players = [sprite_modified.AnimatedWalkingSprite(), sprite_modified.AnimatedWalkingSprite()]
    arcade.run()


if __name__ == "__main__":
    main()
