# A2: Parameters and launch files

## What it does

The A1 nodes now take their settings from parameters instead of hard-coded values, and one command starts both namespaced pairs:

```bash
ros2 launch a1_pubsub pubsub_pairs.launch.py
```

`config/params.yaml` gives `/robot1` a 0.5 Hz wave and `/robot2` a 1.0 Hz wave. The sine publisher's frequency can also be changed live with `ros2 param set`, and invalid values are rejected.

## Key ideas

**Parameters.** A node declares each setting with a default, then reads it:

```python
self.declare_parameter('frequency', 0.5)
self.frequency = self.get_parameter('frequency').value
```

The default's type becomes the parameter's type. Precedence, strongest first: **`-p` on the command line > YAML file / launch file > default in code**.

**YAML config.** Each top-level key is a node's full name (namespace + node name), so one file can configure several copies of the same node differently. `ros__parameters` has two underscores; misspelling it fails silently.

**Launch files.** Ordinary Python that returns a `LaunchDescription`. Each `Node(...)` replaces one `ros2 run` with `--ros-args`: `namespace=` replaces `-r __ns:=`, and `parameters=` replaces `-p` / `--params-file`. A `for` loop starts the same nodes in several namespaces.

**Installing files.** Nodes and launch files read from `install/`, not `src/`. `setup.py`'s `data_files` copies launch and config files into `install/<pkg>/share/<pkg>/`, and `get_package_share_directory()` finds them there. `glob('config/*.yaml')` runs from the package folder, so `config/` must sit next to `setup.py`.

**Reacting to changes.** Reading a parameter once in `__init__` means later `ros2 param set` calls change ROS's copy but not my variable. Two fixes:

- Polling: re-read it in the timer callback every tick. Simple but wasteful.
- Event-driven (used): `add_on_set_parameters_callback(self.on_params)`. ROS calls `on_params` only when someone sets a parameter, and it can reject bad values by returning `SetParametersResult(successful=False, reason=...)`.

## How to run

```bash
cd ~/Robotics-From-Scratch
colcon build --symlink-install
source install/setup.bash
ros2 launch a1_pubsub pubsub_pairs.launch.py
```

In another terminal:

```bash
ros2 param list
ros2 param get /robot2/sine_publisher frequency
ros2 param set /robot1/sine_publisher frequency 2.0
ros2 param set /robot1/sine_publisher frequency -1.0   # rejected
```

## What broke and how I found it

| Problem | Cause | Lesson |
| --- | --- | --- |
| robot2 frequency stayed at the 0.5 default | `config/` was at `src/config/`, so `glob` found nothing and an empty `config/` folder was installed | Check `ls install/<pkg>/share/<pkg>/config`; trust the terminal over editor indentation |
| `ros2 param get` said "Node not found" | The launch had been stopped | `ros2 param` talks to live nodes |
| rqt_graph showed only the subscribers | Stale view | Click refresh |
| `AttributeError: no attribute 'on_params'` | `on_params` was indented inside `__init__`, making it a local function, not a method | Methods sit at the same indent as `__init__` and take `self` first |
| `ros2 param set` "succeeded" but the wave didn't change | The value was only read in `__init__` | Use a parameter callback |

## Open to-dos

- `average_subscriber` doesn't declare `window_size` yet, so the `window_size: 20` lines in `params.yaml` have no effect. Declare it and use it for `deque(maxlen=...)`.
- Changing frequency mid-run makes the wave jump, because `sin(2*pi*f*t)` uses total elapsed time. Fix with a phase accumulator: `self.phase += 2*pi*f*dt` each tick.
- Check whether the installed `params.yaml` is a symlink (`ls -l install/a1_pubsub/share/a1_pubsub/config/params.yaml`) to know whether YAML edits need a rebuild.

## What I'd do differently

- Make every tunable value a parameter from the start, instead of hard-coding and then hacking around it (the `if namespace == '/robot2'` version).
- Validate parameters in the callback from the beginning.
