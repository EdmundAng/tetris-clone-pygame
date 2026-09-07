import pygame
import pygame_gui
import os

pygame.init()

pygame.display.set_caption('Quick Start')
window_surface = pygame.display.set_mode((800, 600))
background = pygame.Surface((800, 600))
background.fill(pygame.Color('#000000'))

manager = pygame_gui.UIManager((800, 600))
manager.preload_fonts(
    [
        {'name': 'noto_sans', 'point_size': 14, 'style': 'bold', 'antialiased': '1'},       # For <b>Welcome...</b>
        {'name': 'noto_sans', 'point_size': 14, 'style': 'italic', 'antialiased': '1'},     # For <i>UITextBox</i>
    ]
)
html_text = (
    "<b>Welcome to Pygame GUI!</b><br><br>"
    "This is a <i>UITextBox</i> element. It automatically handles text wrapping "
    "and will generate a vertical scroll bar if the text overflows the height limit.<br><br>"
    "You can style specific parts of the text using standard HTML tags like:<br>"
    "• <font color='#ff5555'>Color tags</font><br>"
    "• <u>Underline tags</u><br>"
    "• <a href='https://pygame-gui.readthedocs.io/'>Links</a>"
)
text_box = pygame_gui.elements.UITextBox(
    html_text=html_text,
    relative_rect=pygame.Rect((0, 0), (400, 250)),
    manager=manager,
    anchors={'center': 'center'}
)

clock = pygame.time.Clock()
is_running = True
isPaused = False

while is_running:
    time_delta = clock.tick(60)/1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            isPaused = not(isPaused)
        manager.process_events(event)

    manager.update(time_delta)
    window_surface.blit(background, (0, 0))
    if isPaused: manager.draw_ui(window_surface)
    pygame.display.update()