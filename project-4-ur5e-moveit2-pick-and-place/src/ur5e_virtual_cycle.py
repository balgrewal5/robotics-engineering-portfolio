#!/usr/bin/env python3
"""RR1 Project 4: Webots UR5e teach/replay with simulation-assisted grasp.

Commands:
  python3 ur5e_virtual_cycle.py reset-cube
  python3 ur5e_virtual_cycle.py teach
  python3 ur5e_virtual_cycle.py run

Requires an already running Webots Ros2Supervisor with the RR1 virtual-grasp
extension and the Jazzy MoveIt demo. This is NOT a physics-validated grasp.
"""
import json
import sys
import time
from pathlib import Path

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MoveItErrorCodes
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectoryPoint
from webots_ros2_msgs.srv import SpawnNodeFromString

JOINTS = [
    'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
    'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint',
]
FINGERS = ['finger_1_joint_1', 'finger_2_joint_1']
POSES = ['approach', 'grasp', 'lift', 'place', 'retreat']
POSE_FILE = Path.home() / 'rr1_project4_poses.json'

TABLE = '''Solid {
  translation 0.45 0.35 0.50
  name "pickup_table"
  children [
    Shape {
      appearance PBRAppearance { baseColor 0.5 0.55 0.6 roughness 1 }
      geometry Box { size 0.45 0.35 0.04 }
    }
    Transform { translation -0.19 -0.14 -0.25 children [Shape { geometry Box { size 0.04 0.04 0.46 } }] }
    Transform { translation 0.19 -0.14 -0.25 children [Shape { geometry Box { size 0.04 0.04 0.46 } }] }
    Transform { translation -0.19 0.14 -0.25 children [Shape { geometry Box { size 0.04 0.04 0.46 } }] }
    Transform { translation 0.19 0.14 -0.25 children [Shape { geometry Box { size 0.04 0.04 0.46 } }] }
  ]
  boundingObject Box { size 0.45 0.35 0.04 }
}'''

CUBE = '''Solid {
  translation 0.45 0.35 0.551
  name "pick_cube"
  children [
    Shape {
      appearance PBRAppearance { baseColor 1 0 0 roughness 1 }
      geometry Box { size 0.06 0.06 0.06 }
    }
  ]
  boundingObject Box { size 0.06 0.06 0.06 }
}'''


class RR1(Node):
    def __init__(self):
        super().__init__('rr1_ur5e_virtual_cycle')
        self.last_state = None
        self.status = None
        self.create_subscription(JointState, '/ur5e/joint_states', self._on_state, 10)
        self.create_subscription(String, '/Ros2Supervisor/virtual_grasp_status', self._on_status, 10)
        self.virtual_pub = self.create_publisher(String, '/Ros2Supervisor/virtual_grasp', 10)
        self.remove_pub = self.create_publisher(String, '/Ros2Supervisor/remove_node', 10)
        self.spawn_client = self.create_client(
            SpawnNodeFromString, '/Ros2Supervisor/spawn_node_from_string')
        self.moveit = ActionClient(self, MoveGroup, '/move_action')
        self.controller = ActionClient(
            self, FollowJointTrajectory,
            '/ur5e/ur_joint_trajectory_controller/follow_joint_trajectory')

    def _on_state(self, msg):
        if all(j in msg.name for j in JOINTS):
            self.last_state = dict(zip(msg.name, msg.position))

    def _on_status(self, msg):
        self.status = msg.data

    def spin_until(self, future, timeout=90):
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout)
        if not future.done() or future.result() is None:
            raise RuntimeError('ROS action/service timed out')
        return future.result()

    def positions(self):
        # Discard any stale readings: only accept a fresh message.
        self.last_state = None
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
            if self.last_state is not None:
                return {j: float(self.last_state[j]) for j in JOINTS}
        raise RuntimeError('No fresh UR5e joint states. Check Webots Play and controller.')

    def reset_cube(self):
        if not self.spawn_client.wait_for_service(timeout_sec=8):
            raise RuntimeError('Webots spawn service unavailable')
        # The original cube must be removed; it may have physics enabled.
        deadline = time.monotonic() + 4
        while self.remove_pub.get_subscription_count() == 0 and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        if self.remove_pub.get_subscription_count() == 0:
            raise RuntimeError('No Ros2Supervisor/remove_node subscriber')
        self.remove_pub.publish(String(data='pick_cube'))
        self.remove_pub.publish(String(data='pickup_table'))
        time.sleep(1.0)
        for name, text in [('pickup_table', TABLE), ('pick_cube', CUBE)]:
            request = SpawnNodeFromString.Request()
            request.data = text
            result = self.spin_until(self.spawn_client.call_async(request), 15)
            if not result.success:
                raise RuntimeError(f'Webots could not spawn {name}; inspect supervisor log')
        print('WORKCELL READY: table and stationary red cube at (0.45, 0.35, 0.551)')

    def teach(self):
        print('\n=== NEW WAYPOINT RECORDING ===')
        print('These are positions of the ACTUAL arm, not the orange RViz preview.')
        print('For each: RViz Plan & Execute, check Webots, then press Enter here.')
        print('approach = above cube; grasp = fingers around cube; lift = raised')
        print('place = over free tabletop area; retreat = raised again')
        poses = {}
        for name in POSES:
            while True:
                input(f'\nMove to {name.upper()} using RViz, then press Enter... ')
                new_pose = self.positions()
                if poses:
                    old_pose = poses[list(poses)[-1]]
                    delta = max(abs(new_pose[j] - old_pose[j]) for j in JOINTS)
                    if delta < 0.04:
                        print(f'NOT SAVED: arm moved only {delta:.4f} rad. Move ACTUAL arm further.')
                        continue
                    print(f'Confirmed joint displacement: {delta:.3f} rad')
                poses[name] = new_pose
                POSE_FILE.write_text(json.dumps(poses, indent=2))
                print(f'Saved {name}')
                break
        print('\nALL FIVE DISTINCT WAYPOINTS SAVED:', POSE_FILE)
        print('Next run: python3 ~/rr1-project4/ur5e_virtual_cycle.py run')

    def move_arm(self, name, target):
        if not self.moveit.wait_for_server(timeout_sec=8):
            raise RuntimeError('MoveIt /move_action unavailable')
        before = self.positions()
        goal = MoveGroup.Goal()
        req = goal.request
        req.group_name = 'ur5e_arm'
        req.pipeline_id = 'ompl'
        req.allowed_planning_time = 10.0
        req.num_planning_attempts = 10
        req.max_velocity_scaling_factor = 0.15
        req.max_acceleration_scaling_factor = 0.15
        constraint = Constraints()
        for joint in JOINTS:
            jc = JointConstraint()
            jc.joint_name = joint
            jc.position = float(target[joint])
            jc.tolerance_above = 0.025
            jc.tolerance_below = 0.025
            jc.weight = 1.0
            constraint.joint_constraints.append(jc)
        req.goal_constraints = [constraint]
        goal.planning_options.plan_only = False
        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.planning_scene_diff.robot_state.is_diff = True
        print('MoveIt:', name, flush=True)
        handle = self.spin_until(self.moveit.send_goal_async(goal), 15)
        if not handle.accepted:
            raise RuntimeError(f'MoveIt rejected {name}')
        result = self.spin_until(handle.get_result_async(), 120).result
        if result.error_code.val != MoveItErrorCodes.SUCCESS:
            raise RuntimeError(f'MoveIt failed {name}: {result.error_code.val}')
        after = self.positions()
        requested = max(abs(target[j] - before[j]) for j in JOINTS)
        actual = max(abs(after[j] - before[j]) for j in JOINTS)
        error = max(abs(target[j] - after[j]) for j in JOINTS)
        if requested > 0.06 and actual < 0.025:
            raise RuntimeError(f'{name}: MoveIt reported success but arm did not move')
        if error > 0.13:
            raise RuntimeError(f'{name}: actual joint error too large ({error:.3f} rad)')
        print(f'  Reached {name}: moved {actual:.3f} rad, worst joint error {error:.3f} rad')

    def grip(self, value, label):
        if not self.controller.wait_for_server(timeout_sec=8):
            raise RuntimeError('Joint trajectory action unavailable')
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = FINGERS
        pt = JointTrajectoryPoint()
        pt.positions = [float(value), float(value)]
        pt.time_from_start = Duration(sec=3)
        goal.trajectory.points = [pt]
        print('Gripper:', label, flush=True)
        handle = self.spin_until(self.controller.send_goal_async(goal), 15)
        if not handle.accepted:
            raise RuntimeError('Gripper rejected ' + label)
        result = self.spin_until(handle.get_result_async(), 30).result
        if result.error_code != 0:
            raise RuntimeError('Gripper failed ' + label)

    def virtual(self, command):
        deadline = time.monotonic() + 8.0
        while self.virtual_pub.get_subscription_count() == 0 and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        if self.virtual_pub.get_subscription_count() == 0:
            raise RuntimeError('Virtual grasp supervisor extension not running; restart Webots world')
        self.status = None
        # Repeat command only until an acknowledgement is received.
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            self.virtual_pub.publish(String(data=command))
            wait = time.monotonic() + 0.7
            while time.monotonic() < wait:
                rclpy.spin_once(self, timeout_sec=0.1)
                if self.status:
                    print('Webots:', self.status, flush=True)
                    if self.status.startswith('ERROR'):
                        raise RuntimeError(self.status)
                    expected = 'ATTACHED' if command == 'attach' else 'RELEASED'
                    if self.status == expected:
                        return
                    raise RuntimeError('Unexpected Webots status: ' + self.status)
        raise RuntimeError('No virtual grasp response from Webots')

    def run(self):
        if not POSE_FILE.exists():
            raise RuntimeError('No waypoints. Run teach first.')
        data = json.loads(POSE_FILE.read_text())
        if any(name not in data for name in POSES):
            raise RuntimeError('Waypoint list incomplete. Run teach first.')
        for a, b in zip(POSES, POSES[1:]):
            delta = max(abs(data[b][j] - data[a][j]) for j in JOINTS)
            if delta < 0.04:
                raise RuntimeError(f'Duplicate waypoints {a} / {b}; re-teach actual arm motion')
        print('\nAUTONOMOUS SIMULATION-ASSISTED PICK AND PLACE')
        print('Prerequisite: stationary cube on table, not already attached')
        start = time.monotonic()
        self.grip(0.10, 'OPEN')
        self.move_arm('APPROACH', data['approach'])
        self.move_arm('GRASP', data['grasp'])
        # RR1_SCENE_TRANSFER_SAFE: remove immovable cube BEFORE closing fingers.
        if self.remove_pub.get_subscription_count() < 1:
            raise RuntimeError('Webots scene removal subscriber unavailable')
        print('Webots: simulated PICK — remove stationary cube', flush=True)
        self.remove_pub.publish(String(data='pick_cube'))
        time.sleep(1.5)  # allow Webots Supervisor to remove the obstacle
        self.grip(0.63, 'CLOSE (scene-assisted; cube removed)')
        #         self.virtual('attach')  # Attach only if physically near cube
        self.move_arm('LIFT', data['lift'])
        self.move_arm('PLACE', data['place'])
        #         self.virtual('release')  # Stationary cube settles to known tabletop height
        self.grip(0.10, 'OPEN')
        # Recreate the cube on the same table at a new (left-side) position.
        if not self.spawn_client.wait_for_service(timeout_sec=8):
            raise RuntimeError('Webots spawn service unavailable')
        req = SpawnNodeFromString.Request()
        req.data = CUBE.replace('translation 0.45 0.35 0.551',
                                'translation 0.57 0.35 0.551', 1)
        result = self.spin_until(self.spawn_client.call_async(req), 15)
        if not result.success:
            raise RuntimeError('Webots could not create cube at PLACE')
        print('Webots: simulated PLACE — cube reappeared at (0.57, 0.35, 0.551)', flush=True)
        self.move_arm('RETREAT', data['retreat'])
        print('\nCYCLE COMPLETE — DISCRETE scene-assisted object transfer')
        print('Elapsed wall time: %.1f s' % (time.monotonic() - start))
        print('Check in Webots: cube should be at the placement location.')
        print('Scene transfer uses remove/recreate, NOT physical or continuous carried grasp.')


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'help'
    if mode not in ('reset-cube', 'teach', 'run'):
        print('Usage: python3 ur5e_virtual_cycle.py reset-cube | teach | run')
        return
    rclpy.init()
    node = RR1()
    try:
        if mode == 'reset-cube':
            node.reset_cube()
        elif mode == 'teach':
            node.teach()
        else:
            node.run()
    except (RuntimeError, KeyboardInterrupt) as e:
        print('STOPPED:', e)
        sys.exit(1)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
