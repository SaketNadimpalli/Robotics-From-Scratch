# A3: Custom interfaces, services, actions and QoS

## What it does

- `a3_interfaces`: a CMake package defining `srv/GetStats.srv` and `action/RampAmplitude.action`.
- `average_subscriber` serves `get_stats`: mean, min and max of the last N values.
- `stats_client` calls `get_stats` once, prints the result and exits.
- `sine_publisher` serves the `ramp_amplitude` action: it changes the wave's amplitude to a target over a set duration, sends progress feedback, and can be cancelled.

## Key ideas

**Three ways for nodes to talk.**

| Pattern | Shape | Use for |
| --- | --- | --- |
| Topic | Continuous one-way stream | Sensor data, odometry, `/cmd_vel`, anything that keeps changing |
| Service | One request, one quick response | Computing or doing something on demand: stats, save a map, reset |
| Action | Long task with feedback, result and cancel | Navigate to a pose, take off, explore, ramp a value |

"What's the battery right now?" is still a topic: the value already exists and keeps changing, so read the latest message. Use a service when the answer has to be computed or done on demand. My uni project sent drone goals on a topic, so it had no acceptance, progress or failure information and needed a timeout workaround. An action provides all three.

**Interfaces.** A `.msg`, `.srv` or `.action` file defines fields and types, like a struct. `std_msgs/Float64` is just `float64 data`. At build time `rosidl` generates Python and C++ classes from the file, which needs an `ament_cmake` package:

```cmake
find_package(rosidl_default_generators REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/GetStats.srv"
  "action/RampAmplitude.action"
)
```

`package.xml` needs `rosidl_default_generators` (build), `rosidl_default_runtime` (exec), `<member_of_group>rosidl_interface_packages</member_of_group>`, and `action_msgs` for actions. A `.srv` splits at `---` into `GetStats_Request` and `GetStats_Response`; an `.action` has goal, result and feedback.

**Service server and client.** `create_service(type, name, callback)`; the callback fills in and returns the response. The client uses `create_client`, `wait_for_service(timeout_sec=...)`, `call_async(request)` (returns a future) and `spin_until_future_complete`. Never use the blocking `client.call()` inside a callback: the reply needs the same spin loop that is stuck waiting, so the node deadlocks.

**Executors.** `rclpy.spin()` uses a single-threaded executor: one worker runs one callback at a time. A `time.sleep(5)` in the service handler stopped `signal_avg` for 5 s; about 100 messages arrived, and with a QoS depth of 10 only the last 10 were processed and 90 were dropped. `/robot2` was unaffected because it's a separate process. Rules: keep callbacks short; for long work, use a `MultiThreadedExecutor` and put the long callbacks in a `ReentrantCallbackGroup`. More workers alone isn't enough, because callbacks in the default group still run one at a time.

**Action server.** `goal_callback` accepts or rejects (reject duration <= 0). `execute_callback` does the work, calls `publish_feedback`, checks `is_cancel_requested` in its loop, then calls `succeed()` or `canceled()` and returns the result. `cancel_callback` must return `CancelResponse.ACCEPT`, because rclpy rejects cancels by default.

**Node state persists.** The amplitude stays wherever the last goal left it. A second goal to 3.0 looked like nothing happened because it ramped 3.0 to 3.0. In robotics, holding the last value can be unsafe: a motor controller that keeps the last `/cmd_vel` keeps driving if the planner dies, which is why command topics use timeouts (the `twist_mux` `timeout: 0.5` in the uni project).

**QoS.** Two separate questions:

- Reliability: resend lost messages? `reliable` (like a phone call: nothing lost, can arrive late) vs `best_effort` (like live TV: a lost message is gone, the next is coming).
- Durability: give late joiners the last message? `volatile` (live radio) vs `transient_local` (a notice board).

A subscriber can't demand more than the publisher offers: a best-effort publisher with a reliable subscriber, or a volatile publisher with a transient-local subscriber, never connect, and there's no error beyond an easily missed warning. Check with `ros2 topic info <topic> -v`.

| Data | QoS | Why |
| --- | --- | --- |
| Lidar at 20 Hz | Best effort + volatile | A fresh scan comes in 50 ms; an old one is useless (`qos_profile_sensor_data`) |
| Map | Reliable + transient local | Large, rare, must be complete; late joiners need it now |
| `/cmd_vel` | Reliable + volatile | Never replay an old movement command to a late joiner |
| `robot_description` | Reliable + transient local | Published once at startup; RViz and Gazebo start later |

## How to run

```bash
cd ~/Robotics-From-Scratch
colcon build --symlink-install
source install/setup.bash
ros2 launch a1_pubsub pubsub_pairs.launch.py
```

In another sourced terminal:

```bash
ros2 interface show a3_interfaces/srv/GetStats
ros2 service call /robot1/get_stats a3_interfaces/srv/GetStats "{last_n: 10}"
ros2 run a1_pubsub stats_client --ros-args -r __ns:=/robot1 -p last_n:=10
ros2 action send_goal /robot1/ramp_amplitude a3_interfaces/action/RampAmplitude "{target_amplitude: 3.0, duration: 5.0}" --feedback
```

Ctrl+C on `send_goal` cancels the goal.

## What broke and how I found it

| Problem | Cause | Lesson |
| --- | --- | --- |
| `NameError: self` / method not found | `self.srv = ...` at class level and `handle_get_stats` at module level | Statements using `self` go inside a method; methods sit at the same indent as `__init__` |
| `a3_interfaces` underlined in VS Code | Not built yet, and VS Code started without the workspace sourced | Build, source, then reopen VS Code from that terminal; the real test is running it |
| Build failed: "failed to create symbolic link ... Is a directory" | Built once without `--symlink-install`, then with it | Always use `--symlink-install`; fix by deleting that package's `build/` and `install/` folders |
| `1 package not processed` | `a1_pubsub` depends on the failed `a3_interfaces` | colcon builds in dependency order from `package.xml` |
| `ros2 service call`: "The passed service type is invalid" | Terminal not sourced, so the CLI couldn't import the generated type | Listing only needs discovery; calling needs the generated code |
| `rqt_plot` command not found | Not on PATH in Humble | `ros2 run rqt_plot rqt_plot` |
| Ramp to 3.0 showed no change | Amplitude was already 3.0 from the previous goal | Node state persists between goals |

## What I'd do differently

- Decide the communication pattern for each link before writing code: topic, service or action.
- Use a multi-threaded executor and callback groups from the start in any node with a long-running callback.
- Choose QoS on purpose for every publisher instead of relying on defaults.
