# A1: Workspace, publishers and subscribers

## What it does

A ROS2 Python package (`a1_pubsub`) with four nodes:

- `talker` / `listener`: my own versions of the demo talker and listener on `/chatter`.
- `sine_publisher`: publishes a sine wave (`std_msgs/Float64`) on `signal` at 20 Hz.
- `average_subscriber`: subscribes to `signal`, keeps a moving average of the last 20 values, and republishes it on `signal_avg`.

Two independent pairs run side by side in the `/robot1` and `/robot2` namespaces.

## Key ideas

**Workspace and overlay.** The repo is the workspace. `colcon build` (run from the root, not `src/`) creates:

| Folder | What it is |
| --- | --- |
| `build/` | Intermediate build files |
| `install/` | The finished result. `ros2 run` runs from here, not from `src/` |
| `log/` | Build logs, useful when a build fails |

All three are regenerated from `src/`, so they are git-ignored and safe to delete for a clean rebuild. `/opt/ros/humble` is the base layer (sourced in `~/.bashrc`); my workspace is an **overlay** on top, so every new terminal needs `source install/setup.bash`.

**Package files.**

- `package.xml`: name, licence and dependencies. `rosdep` reads it to install missing dependencies, and colcon reads it for build order.
- `setup.py`: `entry_points` maps a command name to a Python function (`talker = a1_pubsub.talker:main`). `data_files` installs launch and config files.
- `--symlink-install`: edits to existing `.py` files apply without rebuilding. Changes to `setup.py`, `package.xml` or new files need a rebuild.

**Node anatomy.** `super().__init__('name')` names the node; `create_publisher(type, topic, qos_depth)` and `create_subscription(type, topic, callback, qos_depth)` create the endpoints; `create_timer(period, callback)` schedules work. `rclpy.spin()` is the loop that runs callbacks: without it, no timer fires and no message is received.

**How nodes connect.** DDS discovery matches a publisher and subscriber only when the **topic name**, **message type** and **QoS** all match. A mismatch fails silently: the topic exists but no data flows. `ros2 topic info <topic> -v` shows each endpoint's type and QoS.

**Names and namespaces.** Names work like file paths. A relative name (`chatter`) gets the node's namespace prepended (`/robot1/chatter`); an absolute name (`/chatter`) never changes. Use relative names in code so the same node can run in any namespace. `--ros-args -r __ns:=/robot1` sets a namespace, `-r __node:=name2` renames a node, and `-r chatter:=/other` remaps a topic.

**Durability.** Default QoS is *volatile*: a subscriber that starts late misses earlier messages. *Transient local* keeps the last few for late joiners (used for maps).

**Moving average as a filter.** A 20-sample window at 20 Hz spans 1 s. The output lags by about half the window (19/2 x 0.05 s = 0.475 s) because all 20 samples are weighted equally. On a 0.5 Hz wave the average shrinks to about 64% of the input height. On a 1 Hz wave the 1 s window covers exactly one period, so the positive and negative halves cancel and the average sits near 0. Shorter window: less lag, less smoothing.

**Event-driven output.** `average_subscriber` publishes once per incoming message, so `signal_avg` runs at whatever rate `signal` arrives. If the input rate changes, a window of N samples covers a different length of time.

## How to run

```bash
cd ~/Robotics-From-Scratch
colcon build --symlink-install
source install/setup.bash

ros2 run a1_pubsub sine_publisher --ros-args -r __ns:=/robot1
ros2 run a1_pubsub average_subscriber --ros-args -r __ns:=/robot1
```

Useful tools: `ros2 node list`, `ros2 topic list`, `ros2 topic echo /robot1/signal`, `ros2 topic hz /robot1/signal`, `ros2 pkg executables a1_pubsub`, `rqt_graph` (who talks to whom, click refresh) and `ros2 run rqt_plot rqt_plot` (values over time, e.g. `/robot1/signal/data`).

## What broke and how I found it

| Problem | Cause | Lesson |
| --- | --- | --- |
| `ros2 pkg create` said `package_name` is required | `--dependencies` takes any number of names, so it swallowed the package name | Put the package name before `--dependencies`; read the `usage:` block |
| `AttributeError: can't set attribute 'subscriptions'` | `Node` already has a read-only `subscriptions` property | My attributes share a namespace with the parent class |
| `msg = Float64` then publish failed | Assigned the class, not an instance | `Float64()` creates a message |
| Float64 talker + String listener: nothing printed, no error | Type mismatch, so DDS never connected them | Check `ros2 topic info -v` when data isn't flowing |
| `git push` rejected: 927 MB file | VS Code's C/C++ index (`.vscode/browse.vc.db`) was committed | Ignore `.vscode/`; amend the unpushed commit; run `git status` before every commit |
| "No executable found" | Missing comma in `setup.py`, so Python joined two strings into one entry | Use `ros2 pkg executables`; always keep trailing commas |
| Broken executables still listed after the fix | colcon never deletes old files in `install/` | Clean rebuild: `rm -rf build install log` |

## What I'd do differently

- Run `git status` before every commit, and set up `.gitignore` before opening the repo in an editor.
- Define the moving-average window by time instead of sample count, so it doesn't change when the input rate changes.
- Use `get_logger().debug()` for per-message logging in high-rate nodes.
