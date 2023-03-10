import pygame
from controller import Controller
from model import World
from view import View
import threading


def train_thread(world):
    clock = pygame.time.Clock()

    while True:
        world.update()
        clock.tick(1)


def draw_thread(view, controller, screen):
    clock = pygame.time.Clock()

    while True:
        controller.handle_events()

        # Draw
        screen.fill((43, 42, 41))
        view.draw()
        pygame.display.update()

        # Limit FPS
        clock.tick(200)


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("train-sim 2.0")

    world = World()
    view = View(world, screen)
    controller = Controller(world, view)

    # Start train thread
    t_thread = threading.Thread(target=train_thread, args=(world,))
    t_thread.start()

    # Draw loop
    d_thread = threading.Thread(
        target=draw_thread, args=(view, controller, screen, ))
    d_thread.start()


if __name__ == "__main__":
    main()
