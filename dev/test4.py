import pygame
import pygame_gui

def main():
    pygame.init()
    
    # Setup window
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Pygame GUI Textbox Fade Out Example")
    
    # Setup clock and manager
    clock = pygame.time.Clock()
    manager = pygame_gui.UIManager((screen_width, screen_height))
    
    # Create a UITextBox
    text_box_rect = pygame.Rect(200, 200, 400, 150)
    html_message = "<b>Hello!</b> Press the <font color='#ffff00'>SPACEBAR</font> to fade out this text box."
    test_text_box = pygame_gui.elements.UITextBox(
        html_text=html_message,
        relative_rect=text_box_rect,
        manager=manager
    )

    test_text_box.set_active_effect(pygame_gui.TEXT_EFFECT_FADE_OUT)
    
    running = True
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame_gui.UI_TEXT_EFFECT_FINISHED:
                pygame.quit()

        manager.update(time_delta)
        
        screen.fill((50, 50, 50))
        manager.draw_ui(screen)
        pygame.display.update()
        
    pygame.quit()

if __name__ == "__main__":
    main()
