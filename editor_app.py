from flask import Flask
from Editor_texto import TextEditorApp
import threading
import tkinter as tk

app = Flask(__name__)

@app.route('/editor')
def run_editor():
    def start_editor():
        root = tk.Tk()
        app_editor = TextEditorApp(root)
        root.mainloop()
    
    threading.Thread(target=start_editor).start()
    return "Editor regional en ejecución..."

if __name__ == '__main__':
    app.run(port=5001)