#!/usr/bin/env python3
# Based on https://python101.readthedocs.io/pl/latest/pygame/pong/#
import pygame
from typing import Type
import skfuzzy as fuzz
import skfuzzy.control as fuzzcontrol

FPS = 30


class Board:
    def __init__(self, width: int, height: int):
        self.surface = pygame.display.set_mode((width, height), 0, 32)
        pygame.display.set_caption("AIFundamentals - PongGame")

    def draw(self, *args):
        background = (0, 0, 0)
        self.surface.fill(background)
        for drawable in args:
            drawable.draw_on(self.surface)

        pygame.display.update()


class Drawable:
    def __init__(self, x: int, y: int, width: int, height: int, color=(255, 255, 255)):
        self.width = width
        self.height = height
        self.color = color
        self.surface = pygame.Surface(
            [width, height], pygame.SRCALPHA, 32
        ).convert_alpha()
        self.rect = self.surface.get_rect(x=x, y=y)

    def draw_on(self, surface):
        surface.blit(self.surface, self.rect)


class Ball(Drawable):
    def __init__(
        self,
        x: int,
        y: int,
        radius: int = 20,
        color=(255, 10, 0),
        speed: int = 3,
    ):
        super(Ball, self).__init__(x, y, radius, radius, color)
        pygame.draw.ellipse(self.surface, self.color, [0, 0, self.width, self.height])
        self.x_speed = speed
        self.y_speed = speed
        self.start_speed = speed
        self.start_x = x
        self.start_y = y
        self.start_color = color
        self.last_collision = 0

    def bounce_y(self):
        self.y_speed *= -1

    def bounce_x(self):
        self.x_speed *= -1

    def bounce_y_power(self):
        self.color = (
            self.color[0],
            self.color[1] + 10 if self.color[1] < 255 else self.color[1],
            self.color[2],
        )
        pygame.draw.ellipse(self.surface, self.color, [0, 0, self.width, self.height])
        self.x_speed *= 1.1
        self.y_speed *= 1.1
        self.bounce_y()

    def reset(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.x_speed = self.start_speed
        self.y_speed = self.start_speed
        self.color = self.start_color
        self.bounce_y()

    def move(self, board: Board, *args):
        self.rect.x += round(self.x_speed)
        self.rect.y += round(self.y_speed)

        if self.rect.x < 0 or self.rect.x > (
            board.surface.get_width() - self.rect.width
        ):
            self.bounce_x()

        if self.rect.y < 0 or self.rect.y > (
            board.surface.get_height() - self.rect.height
        ):
            self.reset()

        timestamp = pygame.time.get_ticks()
        if timestamp - self.last_collision < FPS * 4:
            return

        for racket in args:
            if self.rect.colliderect(racket.rect):
                self.last_collision = pygame.time.get_ticks()
                if (self.rect.right < racket.rect.left + racket.rect.width // 4) or (
                    self.rect.left > racket.rect.right - racket.rect.width // 4
                ):
                    self.bounce_y_power()
                else:
                    self.bounce_y()


class Racket(Drawable):
    def __init__(
        self,
        x: int,
        y: int,
        width: int = 80,
        height: int = 20,
        color=(255, 255, 255),
        max_speed: int = 10,
    ):
        super(Racket, self).__init__(x, y, width, height, color)
        self.max_speed = max_speed
        self.surface.fill(color)

    def move(self, x: int, board: Board):
        delta = x - self.rect.x
        delta = self.max_speed if delta > self.max_speed else delta
        delta = -self.max_speed if delta < -self.max_speed else delta
        delta = 0 if (self.rect.x + delta) < 0 else delta
        delta = (
            0
            if (self.rect.x + self.width + delta) > board.surface.get_width()
            else delta
        )
        self.rect.x += delta


class Player:
    def __init__(self, racket: Racket, ball: Ball, board: Board) -> None:
        self.ball = ball
        self.racket = racket
        self.board = board

    def move(self, x: int):
        self.racket.move(x, self.board)

    def move_manual(self, x: int):
        """
        Do nothing, control is defined in derived classes
        """
        pass

    def act(self, x_diff: int, y_diff: int):
        """
        Do nothing, control is defined in derived classes
        """
        pass


class PongGame:
    def __init__(
        self, width: int, height: int, player1: Type[Player], player2: Type[Player]
    ):
        pygame.init()
        self.board = Board(width, height)
        self.fps_clock = pygame.time.Clock()
        self.ball = Ball(width // 2, height // 2)

        self.opponent_paddle = Racket(x=width // 2, y=0)
        self.oponent = player1(self.opponent_paddle, self.ball, self.board)

        self.player_paddle = Racket(x=width // 2, y=height - 20)
        self.player = player2(self.player_paddle, self.ball, self.board)

    def run(self):
        while not self.handle_events():
            self.ball.move(self.board, self.player_paddle, self.opponent_paddle)
            self.board.draw(
                self.ball,
                self.player_paddle,
                self.opponent_paddle,
            )
            self.oponent.act(
                self.oponent.racket.rect.centerx - self.ball.rect.centerx,
                self.oponent.racket.rect.centery - self.ball.rect.centery,
            )
            self.player.act(
                self.player.racket.rect.centerx - self.ball.rect.centerx,
                self.player.racket.rect.centery - self.ball.rect.centery,
            )
            self.fps_clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if (event.type == pygame.QUIT) or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                pygame.quit()
                return True
        keys = pygame.key.get_pressed()
        if keys[pygame.constants.K_LEFT]:
            self.player.move_manual(0)
        elif keys[pygame.constants.K_RIGHT]:
            self.player.move_manual(self.board.surface.get_width())
        return False


class NaiveOponent(Player):
    def __init__(self, racket: Racket, ball: Ball, board: Board):
        super(NaiveOponent, self).__init__(racket, ball, board)

    def act(self, x_diff: int, y_diff: int):
        x_cent = self.ball.rect.centerx
        self.move(x_cent)


class HumanPlayer(Player):
    def __init__(self, racket: Racket, ball: Ball, board: Board):
        super(HumanPlayer, self).__init__(racket, ball, board)

    def move_manual(self, x: int):
        self.move(x)


# ----------------------------------
# DO NOT MODIFY CODE ABOVE THIS LINE
# ----------------------------------

#import numpy as np
#import matplotlib.pyplot as plt


class FuzzyPlayer(Player):
    def __init__(self, racket: Racket, ball: Ball, board: Board):
        super(FuzzyPlayer, self).__init__(racket, ball, board)
        # for Mamdami:
        self.x_diff = fuzz.control.Antecedent(range(-400, 401), 'x_dist')
        self.y_diff = fuzz.control.Antecedent(range(-200, 201), 'y_dist')
        self.velocity = fuzz.control.Consequent(range(-10, 11), 'velocity')

        #self.racket_controller = fuzz.control.ControlSystem...


        #prędkość
        self.velocity['fast_left'] = fuzz.trimf(self.velocity.universe, [-10, -10, -10])
        self.velocity['slow_left'] = fuzz.trimf(self.velocity.universe, [-9, -9, -3])
        self.velocity['stop'] = fuzz.trimf(self.velocity.universe, [-3, 0, 3])
        self.velocity['slow_right'] = fuzz.trimf(self.velocity.universe, [3, 9, 9])
        self.velocity['fast_right'] = fuzz.trimf(self.velocity.universe, [10, 10, 10])

        #dla x (800)
        #punkty
        #-edge    -middle_edge     -middle_edge/2      center(0)        middle_edge/2       middle_edge      edge
        edge = 400
        middle_edge = 30
        self.x_diff['far_left'] = fuzz.trimf(self.x_diff.universe, [-edge, -edge, -middle_edge+10])
        self.x_diff['left'] = fuzz.trimf(self.x_diff.universe, [-middle_edge, -middle_edge/2, 0])
        self.x_diff['center'] = fuzz.trimf(self.x_diff.universe, [-middle_edge/2, 0, middle_edge/2])
        self.x_diff['right'] = fuzz.trimf(self.x_diff.universe, [0, middle_edge/2, middle_edge])
        self.x_diff['far_right'] = fuzz.trimf(self.x_diff.universe, [middle_edge-10, edge, edge])

        #dla y (400)
        self.y_diff['above'] = fuzz.trimf(self.y_diff.universe, [-200, -100, 0])
        self.y_diff['center'] = fuzz.trimf(self.y_diff.universe, [-100, 0, 100])
        self.y_diff['below'] = fuzz.trimf(self.y_diff.universe, [0, 100, 200])


        rules = [
            fuzzcontrol.Rule(self.x_diff['left'] & (self.y_diff['above'] | self.y_diff['center']), self.velocity['fast_right']),
            fuzzcontrol.Rule(self.x_diff['right'] & (self.y_diff['above'] | self.y_diff['center']), self.velocity['fast_left']),

            fuzzcontrol.Rule(self.x_diff['far_left'], self.velocity['fast_right']),
            fuzzcontrol.Rule(self.x_diff['left'], self.velocity['slow_right']),
            fuzzcontrol.Rule(self.x_diff['center'], self.velocity['stop']),
            fuzzcontrol.Rule(self.x_diff['right'], self.velocity['slow_left']),
            fuzzcontrol.Rule(self.x_diff['far_right'], self.velocity['fast_left']),
        ]


        self.racket_controller = fuzzcontrol.ControlSystem(rules)
        self.racket_simulation = fuzzcontrol.ControlSystemSimulation(self.racket_controller)

    def act(self, x_diff: int, y_diff: int):
        velocity = self.make_decision(x_diff, y_diff)
        self.move(self.racket.rect.x + velocity)

    def make_decision(self, x_diff: int, y_diff: int):
        # for Mamdami:
        self.racket_simulation.input['x_dist'] = x_diff
        self.racket_simulation.input['y_dist'] = y_diff
        self.racket_simulation.compute()
        
        try:
            velocity = self.racket_simulation.output['velocity']
            return velocity
        except:
            return 0


if __name__ == "__main__":
    #game = PongGame(800, 400, NaiveOponent, HumanPlayer)
    game = PongGame(800, 400, NaiveOponent, FuzzyPlayer)
    game.run()