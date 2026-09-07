import pygame
import pygame_gui

# 1. Initialize Pygame
pygame.init()

# 2. Set up the window display
window_size = (800, 600)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Pygame GUI UILabel Example")

# 3. Initialize the UI Manager
ui_manager = pygame_gui.UIManager(window_size)

# 4. Create the UILabel
ui_label = pygame_gui.elements.UILabel(
    relative_rect=pygame.Rect((300, 250), (200, 50)), # Position (x, y) and size (width, height)
    text="Hello, Pygame GUI!",                        # Text content
    manager=ui_manager                                # Associated UI manager
)

# 5. Application loop clock
clock = pygame.time.Clock()
is_running = True

while is_running:
    # Calculate time delta per frame (required by pygame_gui)
    time_delta = clock.tick(60) / 1000.0

    # Handle window events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        
        # Pass events to the UI Manager
        ui_manager.process_events(event)

    # Update UI components
    ui_manager.update(time_delta)

    # Draw everything
    screen.fill((40, 40, 40))         # Clean background
    ui_manager.draw_ui(screen)        # Draw the labels and UI elements onto the screen
    pygame.display.update()           # Flip display buffers

pygame.quit()
