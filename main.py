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
announce=True
MOVEMENT_SPEED = 5
event = 0
level = 0
players = []
player = 0
opponent = 0
projectiles = []
obstacles = []


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
            print(str(self.x) + "..." + str(self.y) + "???id:::" + str(self.id) + "..." + str(target_x) + "::" + str(
                target_y))
            print(str(PLAYER_HEIGHT))
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
    global opponent

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
                self.texture = arcade.load_texture("images/backgrounds/explosion.png")
                self.speed = 0
                self.collisionTime += 1
                if self.collisionTime == 20:
                    projectiles.remove(self)
        for i in range(z):
            if opponent.center_x + PLAYER_WIDTH // 2 > self.x > opponent.center_x - PLAYER_WIDTH // 2 and opponent.center_y + PLAYER_HEIGHT // 2 > self.y > opponent.center_y - PLAYER_HEIGHT // 2:
                self.texture = arcade.load_texture("images/backgrounds/explosion.png")
                self.speed = 0
                self.collisionTime += 1
                if self.collisionTime == 1:
                    opponent.health -= 20
                elif self.collisionTime == 10:
                    projectiles.remove(self)


class MyAppWindow(arcade.Window):
    """ Main application class. """

    def __init__(self, width, height):
        global players
        global opponent
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

        # Set up the player
        players.clear()
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

            players = [sprite_modified.AnimatedWalkingSprite(), sprite_modified.AnimatedWalkingSprite()]
            self.player = players[0]
            opponent = players[1]

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

        # This command has to happen before we start drawing
        arcade.start_render()


        arcade.draw_texture_rectangle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                      SCREEN_WIDTH, SCREEN_HEIGHT, self.background)
        if server_ip != "":
            arcade.draw_point( SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.9, arcade.color.BLUE, 5)
            arcade.draw_text("Server Connected:"+str(server_ip), SCREEN_WIDTH // 3, 30, arcade.color.BLACK, 15)

        for obstacle in obstacles:
            arcade.draw_texture_rectangle(obstacle.x, obstacle.y, obstacle.width, obstacle.height, obstacle.texture)
        for projectile in projectiles:
            arcade.draw_texture_rectangle(projectile.x, projectile.y, projectile.width, projectile.height,
                                          projectile.texture)
            if projectile.x - projectile.width // 2 > SCREEN_WIDTH:
                projectiles.remove(projectile)
            projectile.updatePosition()

        for i in range(len(players)):
            arcade.draw_rectangle_filled((((-1) ** i) * (SCREEN_WIDTH // 6)) + (i) * SCREEN_WIDTH, SCREEN_HEIGHT * 0.95,
                                         100 * 2, 15, arcade.color.BARN_RED)
            arcade.draw_rectangle_filled(
                (((((-1) ** i) * (SCREEN_WIDTH // 6)) + (i) * SCREEN_WIDTH) - 100) + players[i].health,
                SCREEN_HEIGHT * 0.95,
                players[i].health * 2, 15, arcade.color.RED)
        # Draw all the sprites.
        self.all_sprites_list.draw()

        # # Put the text on the screen.
        # output = "Score: {}".format(self.score)
        # arcade.draw_text(output, 10, 20, arcade.color.WHITE, 14)

    def on_key_press(self, key, modifiers):
        global event
        global level
        global projectiles
        """
        Called whenever the mouse moves.
        """
        if level > 0:
            if key == arcade.key.UP:
                if event == 0 and self.player.change_y == 0:
                    event = 30

            elif key == arcade.key.DOWN:
                self.player.change_y = -MOVEMENT_SPEED
            elif key == arcade.key.LEFT:
                self.player.change_x = -MOVEMENT_SPEED
            elif key == arcade.key.RIGHT:
                self.player.change_x = MOVEMENT_SPEED
            elif key == arcade.key.SPACE:
                projectiles.append(Projectile(0, self.player.center_x + PLAYER_WIDTH // 2, self.player.center_y, 75, 15,
                                              10 if self.player.change_x >= 0 else -10,
                                              arcade.load_texture("images/backgrounds/bazooka_missile.png",
                                                                  mirrored=False if self.player.change_x >= 0 else True)))

    def on_key_release(self, key, modifiers):
        global event
        global level
        """
        Called when the user presses a mouse button.
        """
        if level > 0:
            if key == arcade.key.UP or key == arcade.key.DOWN:
                # self.player.change_y = 0
                self.player.change_y = 0
            elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
                self.player.change_x = 0

    def on_mouse_press(self, x, y, button, modifiers):
        global event
        global level
        global PLAYER_WIDTH
        global PLAYER_HEIGHT
        global obstacles

        """
        Called when the user presses a mouse button.
        """
        if level <= 0 and button == arcade.MOUSE_BUTTON_LEFT:
            print("click" + str(x) + ".." + str(y))

            for i in range(len(obstacles)):
                if level <= 0:
                    PLAYER_WIDTH = 0
                    PLAYER_HEIGHT = 0

                if obstacles[i].CollisionDetectionProjectile(x, y):
                    if int(obstacles[i].id) != 1:
                        level = -1 * (int(obstacles[i].id) - 1)
                        print(level)
                    else:
                        level = -1 * level if level != 0 else 1
                        PLAYER_WIDTH = 96
                        PLAYER_HEIGHT = 128
                        print(".." + str(level) + ".." + str(PLAYER_HEIGHT) + ".." + str(PLAYER_WIDTH))
                        self.__init__(800, 600)

    def update(self, delta_time):
        global event
        global level
        global players
        global projectiles
        """ Movement and game logic """
        if level > 0:

            if 0 < event <= 30:
                self.player.change_y = MOVEMENT_SPEED
                event -= 1
            elif event == 0:
                self.player.change_y = -MOVEMENT_SPEED
                for obstacle in obstacles:
                    if self.player.change_y != 0 and obstacle.CollisionDetectionFall(self.player.center_x,
                                                                                     (
                                                                                             self.player.center_y - PLAYER_HEIGHT // 2)):
                        self.player.change_y = 0
                        self.player.center_y = obstacle.y + PLAYER_HEIGHT // 2 + (obstacle.height // 2)

                        break
            else:
                self.player.change_y = 0
            for projectile in projectiles:
                projectile.CollisionDetection()
            self.all_sprites_list.update()
            self.all_sprites_list.update_animation()


def handle_message(conn, addr):
    global server_ip
    global announce
    global player_listener_port
    # data received from client
    data = conn.recv(1024)
    if data:
        print(data.decode("utf-8"))

        if data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "server_probe":

            data_string = str(ip_address) + ",server_response"
            x = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            x.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            x.connect((str(server_ip), player_listener_port))
            x.sendto(data_string.encode("utf-8"), (str(server_ip), player_listener_port))
            x.shutdown(2)
            x.close()
        elif data.decode("utf-8").rstrip(os.linesep).split(",")[1] == "server_response":
            server_ip = data.decode("utf-8").rstrip(os.linesep).split(",")[0]
            player_listener_port = int(data.decode("utf-8").rstrip(os.linesep).split(",")[2])
            print(data.decode("utf-8").rstrip(os.linesep).split(",")[0]+" "+str(player_listener_port))
            announce = False

    conn.close()


def activate_announcer():
    global announce
    while announce:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        host = '<broadcast>'
        port = 12345
        data_string = str(ip_address) + ",server_probe"
        s.sendto(data_string.encode("utf-8"), (host, port))
        s.sendto(data_string.encode("utf-8"), (host, port))
        s.sendto(data_string.encode("utf-8"), (host, port))
        time.sleep(5)
        print("announced")


def send_message_to_server(message):
    data_string = str(ip_address) + "," + message
    x = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    x.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    x.connect((server_ip, player_listener_port))
    x.sendto(data_string.encode("utf-8"), (server_ip, player_listener_port))
    x.shutdown(2)
    x.close()


def activate_listener():
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((ip_address, player_listener_port))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        s.listen(1)
        conn, addr = s.accept()
        if conn and player_listener_port==10000:
            handle_message(conn, addr)
        elif conn and player_listener_port!=10000:
            print("I will listen on"+str(player_listener_port))
            l = threading.Thread(target=handle_message, args=(conn, addr,))
            l.start()
            l.join()






def main():
    port_listener = threading.Thread(target=activate_listener)
    announcer = threading.Thread(target=activate_announcer)
    port_listener.start()

    announcer.start()
    MyAppWindow(SCREEN_WIDTH, SCREEN_HEIGHT)
    arcade.run()
    send_message_to_server(ip_address + ",server_probe")


if __name__ == "__main__":
    main()
