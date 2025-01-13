import tkinter as tk

# Create the main window
window = tk.Tk()
window.title("Hello World GUI")

# Create a label with the text "hello world"
label = tk.Label(window, text="hello world", padx=20, pady=20)
label.pack()


# Run the main loop to display the window
window.mainloop()