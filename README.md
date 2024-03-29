# pokerstars-v2

## Client Installation Instructions

- Install Python 3.9.18 (any Python 3.9.x should work though)
    - Python 3.10.6 worked on Windows
    - Python 3.12 didn't work on Windows
- Install the Python dependencies needed:
    - Find the file path to the client/requirements.txt file (e.g. `C:\Users\username\Downloads\pokerstars-v2\client\requirements_windows.txt`)
    - In your terminal, run the command `pip install -r C:\Users\username\Downloads\pokerstars-v2\client\requirements_windows.txt`
        - You may need to use pip3 instead of pip
        - If not on Windows, you should use `requirements_linux.txt` instead.
    - If you can't find the requirements.txt file, you can directly install the dependencies with `pip install art==6.1` then `pip install npyscreen==4.10.5` then `pip install python-socketio==5.11.1`
        - You can also try without the version numbers if it can't install any of those three.
- Run the client!
    - Find the file path to the `client.py` file (e.g. `C:\Users\username\Downloads\pokerstars-v2\client\client.py`)
    - Find the server IP Address that you want to connect to (e.g. `something.a.b.c`)
    - In your terminal, run the command `python3 client.py something.a.b.c`

### Notes

- Using `python client.py IP --no-auto-update` will disable the auto-update feature, which keeps your client up to date with the latest version on GitHub.

## Server Installation Instructions

- Relatively straightforward, use Python 3.9.18, install the dependencies in `server/requirements.txt`, and run the server with `python3 server.py`.
