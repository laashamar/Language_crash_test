

---



**Objective:**
Create a robust Python script to automate sending messages in the Microsoft Copilot for Windows app. The script's purpose is to stress-test the application's performance and stability by simulating a long, bilingual conversation.

**Key Requirements:**
1.  **Language and Libraries:** The script must be written in **Python 3**. It must use the **`pywinauto`** library for all Windows UI automation tasks. No other third-party UI automation libraries should be used.
2.  **Prerequisites:** Include a comment at the top of the script stating that the user must first install the required library via `pip install pywinauto`.
3.  **Configuration Block:** The script must begin with a clear, well-commented configuration section where a user can easily edit parameters. This section must include:
    * A variable for the total number of messages to send (e.g., `NUMBER_OF_MESSAGES`).
    * A variable for the wait time in seconds between messages (e.g., `WAIT_TIME_SECONDS`).
    * A list of predefined sample messages, which must include a mix of both **English** and **Norwegian** sentences. The Norwegian strings must include the special characters **æ, ø, and å**.Strings in both Languages must include emojis and combined emojis.
4.  **UI Element Identification (Crucial):**
    * The script needs to identify UI elements like the main window, the text input field, and the send button.
    * Use clear **placeholder variables** for these identifiers (e.g., `COPILOT_WINDOW_TITLE`, `TEXT_BOX_AUTO_ID`).
    * Add a prominent comment block explaining that these are placeholder values. Instruct the user that they **must find the correct identifiers** for their system using a tool like Microsoft's `Inspect.exe` or by using `pywinauto`'s own inspection capabilities.
5.  **Debugging Helper:** Immediately after connecting to the application window, include a **commented-out call to `window.print_control_identifiers()`**. Add a comment explaining to the user that they can uncomment this line to print a tree of all available UI elements to the console, which is the easiest way to find the correct identifiers for the text box and button.
6.  **Functionality:**
    * The script should connect to an already running Copilot application window using `Application(backend="uia").connect(...)`. It should not be responsible for starting the application.
    * The core logic should be a `for` loop that iterates for the configured number of messages.
    * Inside the loop, the script must find the text box and send button controls, select a random message, type it into the text box using `.type_keys()`, and click the button using `.click()`.
7.  **Robustness and Logging:**
    * Use `try...except` blocks (specifically catching `ElementNotFoundError`) to gracefully handle cases where the Copilot window or its child controls cannot be found.
    * Use `print()` statements to provide clear, step-by-step feedback in the console as the script executes (e.g., "Connecting to window...", "Sending message X of Y...", "Waiting...").

**Logical Script Flow:**
1.  Import necessary libraries (`pywinauto`, `time`, `random`).
2.  Define all user-configurable variables in a section at the top.
3.  Define a `main()` function containing the core logic.
4.  Use a standard `if __name__ == "__main__":` block to call the `main()` function.
5.  Inside `main()`, attempt to connect to the Copilot window. If it fails, print an informative error and exit.
6.  Include the commented-out `print_control_identifiers()` call for debugging.
7.  Execute the main `for` loop to find elements, type text, click the send button, and wait.
8.  Print a final message when the script has completed all its iterations.

**Code Quality and Comments:**
The code should be clean, well-commented, and easy for a non-expert to understand and modify. Pay special attention to the comments in the configuration and UI identifier sections. Use descriptive variable names.