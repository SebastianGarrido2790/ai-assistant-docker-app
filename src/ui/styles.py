"""
Centralized CSS design system for the AI Assistant.
"""

STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Base Typography */
html, body, [class*="css"]  {
    font-family: 'Outfit', sans-serif !important;
}

/* Gradient Header */
.stApp header {
    background: transparent !important;
}

.stTitle {
    background: linear-gradient(135deg, #4f46e5, #9333ea);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    text-align: center;
    padding-bottom: 2rem;
    animation: glow 3s ease-in-out infinite alternate;
}

@keyframes glow {
    from {
        text-shadow: 0 0 10px rgba(79, 70, 229, 0.2);
    }
    to {
        text-shadow: 0 0 20px rgba(147, 51, 234, 0.4);
    }
}

/* Chat Messages with Glassmorphism and Micro-animations */
.stChatMessage {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    animation: slideIn 0.3s ease-out forwards;
    opacity: 0;
    transform: translateY(10px);
}

@keyframes slideIn {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* User Message specific styling */
[data-testid="chatAvatarIcon-user"] {
    background-color: #4f46e5 !important;
}

/* Assistant Message specific styling */
[data-testid="chatAvatarIcon-assistant"] {
    background-color: #9333ea !important;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(147, 51, 234, 0.5);
}

/* Button Styling */
.stButton button {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    transition: all 0.2s ease-in-out;
}

.stButton button:hover {
    background: rgba(147, 51, 234, 0.2);
    border-color: rgba(147, 51, 234, 0.5);
    transform: translateY(-2px);
}

/* Chat Input Styling */
.stChatInputContainer {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px);
}
</style>
"""
