"""
Application Entry Point
Run this file to start the Flask development server
This is the main file you execute to run the application
"""

from app import create_app
import os

# Create the Flask application using the factory function
app = create_app()

if __name__ == '__main__':
    """
    This code only runs if you execute this file directly
    (not if you import it in another file)
    """
    
    # Get configuration from environment or use defaults
    host = os.getenv('FLASK_HOST', '0.0.0.0')  # Listen on all network interfaces
    port = int(os.getenv('FLASK_PORT', 5000))  # Port 5000 by default
    debug = os.getenv('FLASK_ENV', 'development') == 'development'  # Enable auto-reload
    
    #print("""
    #╔═══════════════════════════════════════════════════════╗
    #║                                                       ║
    #║   🏨 HOTEL BOOKING SYSTEM                            ║
    #║                                                       ║
    #║   ✅ Server is starting...                           ║
    #║                                                       ║
    #║   🌐 Open your browser and go to:                    ║
    #║      http://localhost:5000                           ║
    #║                                                       ║
    #║   📚 API Documentation:                              ║
    #║      http://localhost:5000/health                    ║
    #║                                                       ║
    #║   ⏹️  Press CTRL+C to stop the server                ║
    #║                                                       ║
    #╚═══════════════════════════════════════════════════════╝
    #""")
    
    print("Server is starting ")

    # Start the development server
    app.run(host=host, port=port, debug=debug)