
class JoystickHandler {
    constructor() {
        this.currentHover = null;
        this.processingSelection = false;
        this.socket = null;
        this.clientId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.connectionActive = false;
        this.isStartScreen = false;
        
        this.init();
    }

    init() {
        console.log("Initializing joystick handler...");
        this.setupWebSocket();
        this.addStyles();
        this.setupKeyboardControls();
        this.detectStartScreen();
    }

    detectStartScreen() {
        // Check if we're on the start screen by looking for specific elements
        const startButton = document.querySelector('button[data-gpio="left"]');
        const finishButton = document.querySelector('button[data-gpio="right"]');
        
        this.isStartScreen = !!(startButton && finishButton);
        
        if (this.isStartScreen) {
            console.log("Start screen detected");
            this.addStartScreenStyles();
        }
    }

    addStartScreenStyles() {
        if (!document.getElementById('start-screen-styles')) {
            const style = document.createElement('style');
            style.id = 'start-screen-styles';
            style.textContent = `
                .start-button, .finish-button {
                    transition: all 0.3s ease;
                }
                .hover {
                    transform: scale(1.2) !important;
                    filter: brightness(1.2);
                }
                .active {
                    transform: scale(1.1) !important;
                    filter: brightness(1.5);
                }
            `;
            document.head.appendChild(style);
        }
    }

    setupWebSocket() {
        if (this.connectionActive) {
            console.log("WebSocket connection already active");
            return;
        }

        console.log("Setting up WebSocket connection...");
        
        try {
            this.socket = io();

            this.socket.on('connect', () => {
                console.log("WebSocket connected");
                this.connectionActive = true;
                this.reconnectAttempts = 0;
            });

            this.socket.on('connection_established', (data) => {
                this.clientId = data.client_id;
                console.log(`Client ID assigned: ${this.clientId}`);
            });

            this.socket.on('gpio_event', (data) => {
                console.log("Received GPIO event:", data);
                
                if (data.type === 'joystick' && data.direction) {
                    this.handleJoystickMove(data.direction.toLowerCase());
                } 
                else if (data.type === 'select') {
                    this.handleSelect(data.choice);
                }
            });

            this.socket.on('error', (error) => {
                console.error("WebSocket error:", error);
            });

            this.socket.on('disconnect', () => {
                console.log("WebSocket disconnected");
                this.connectionActive = false;
                
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Reconnection attempt ${this.reconnectAttempts}`);
                    setTimeout(() => this.setupWebSocket(), 2000);
                } else {
                    console.error("Max reconnection attempts reached");
                    this.cleanup();
                }
            });

        } catch (error) {
            console.error("Failed to create WebSocket:", error);
            this.connectionActive = false;
        }
    }

    handleJoystickMove(direction) {
        if (!['left', 'right'].includes(direction)) {
            console.error("Invalid direction:", direction);
            return;
        }

        console.log(`Joystick moved: ${direction}`);
        
        // Clear previous hover
        if (this.currentHover) {
            const prevButton = this.isStartScreen ? 
                document.querySelector(`button[data-gpio="${this.currentHover}"]`) :
                document.getElementById(`${this.currentHover}-button`);
            
            if (prevButton) {
                prevButton.classList.remove('hover', 'active');
                if (!this.isStartScreen) {
                    prevButton.style.transform = 'scale(1)';
                }
            }
        }
        
        // Set new hover
        this.currentHover = direction;
        const button = this.isStartScreen ?
            document.querySelector(`button[data-gpio="${direction}"]`) :
            document.getElementById(`${direction}-button`);
        
        if (button) {
            button.classList.add('hover');
            if (!this.isStartScreen) {
                button.style.transform = 'scale(1.6)';
            }
            console.log(`Button ${direction} hovered`);
        }
    }

    handleSelect(choice) {
        if (this.processingSelection || !this.currentHover) {
            console.log("Selection blocked");
            return;
        }

        this.processingSelection = true;
        const direction = choice || this.currentHover;

        const button = this.isStartScreen ?
            document.querySelector(`button[data-gpio="${direction}"]`) :
            document.getElementById(`${direction}-button`);

        if (button) {
            button.classList.add('active');
            if (!this.isStartScreen) {
                button.style.transform = 'scale(1.8)';
            }
            
            // Trigger click
            button.click();
            
            // Reset after animation
            setTimeout(() => {
                button.classList.remove('hover', 'active');
                if (!this.isStartScreen) {
                    button.style.transform = 'scale(1)';
                }
                this.processingSelection = false;
            }, 200);
        } else {
            this.processingSelection = false;
        }
    }

    sendEvent(eventData) {
        if (!this.connectionActive) {
            console.error("Cannot send event: WebSocket not connected");
            return;
        }

        try {
            this.socket.emit('joystick_event', eventData);
            console.log("Event sent:", eventData);
        } catch (error) {
            console.error("Failed to send event:", error);
        }
    }

    setupKeyboardControls() {
        document.removeEventListener('keydown', this.handleKeydown);
        
        this.handleKeydown = (event) => {
            if (this.processingSelection) return;

            switch (event.key) {
                case 'ArrowLeft':
                    this.sendEvent({
                        type: 'joystick',
                        direction: 'left'
                    });
                    break;
                case 'ArrowRight':
                    this.sendEvent({
                        type: 'joystick',
                        direction: 'right'
                    });
                    break;
                case 'Enter':
                    if (this.currentHover) {
                        this.sendEvent({
                            type: 'select',
                            choice: this.currentHover
                        });
                    }
                    break;
            }
        };
        
        document.addEventListener('keydown', this.handleKeydown);
    }

    cleanup() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.connectionActive = false;
        this.currentHover = null;
        this.processingSelection = false;
        this.clientId = null;
    }
}

// Single instance management
let joystickHandlerInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    const gpioEnabled = document.body.getAttribute('data-gpio-enabled') === 'true';
    
    if (gpioEnabled && !joystickHandlerInstance) {
        joystickHandlerInstance = new JoystickHandler();
        window.joystickHandler = joystickHandlerInstance;
        console.log("Joystick handler initialized");
    }
});

window.addEventListener('unload', () => {
    if (joystickHandlerInstance) {
        joystickHandlerInstance.cleanup();
        joystickHandlerInstance = null;
    }
});