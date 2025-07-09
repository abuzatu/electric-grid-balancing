# Intro

Here are various tips that are needed when developing.

# To use tee windows on the MVPS server

To see all `tmux` seesions
```
tmux ls
```
I get answer
```
session_name_solar: 1 windows (created Sat Oct  7 19:49:01 2023)
```
To go into one of them 
```
tmux attach -t session_name_solar
```
or shorter version
```
tmux a -t session_name_solar
```
Once you're in a session, you can:
* Use `Ctrl+b d` to detach from the session (it will keep running in the background)
* Use `Ctrl+b c` to create a new window
* Use `Ctrl+b n` to go to the next window
* Use `Ctrl+b p` to go to the previous window
* Use `Ctrl+b &` to kill the current window
* Use `Ctrl+b [` to enter scroll mode (use arrow keys to scroll, press q to exit)

To create a new session called `session_name_electric_grid_balancing`:
```
tmux new -s session_name_electric_grid_balancing
```
Then go to the folder and start streamlit
```
cd electric_grid_balancing
make streamlit
```
Then detach to let it run
* Use `Ctrl+b d` to detach from the session (it will keep running in the background)

Later to attach to the existing session
```
tmux a -t session_name_electric_grid_balancing
```