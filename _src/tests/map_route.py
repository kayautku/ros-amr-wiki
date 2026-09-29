"""Haritalama için robotu sabit bir rotada sürer. Ortam değişkenleri: V (m/s), W (rad/s)."""
import os, rospy, math
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion

V = float(os.environ.get("V", "0.4"))
W = float(os.environ.get("W", "0.4"))
rospy.init_node("map_route")
pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
state = {}


def cb(m):
    p = m.pose.pose
    state["x"], state["y"] = p.position.x, p.position.y
    state["yaw"] = euler_from_quaternion([p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w])[2]


rospy.Subscriber("/odom", Odometry, cb)
rospy.sleep(2)
rate = rospy.Rate(20)


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def fwd(dist):
    x0, y0 = state["x"], state["y"]
    t = Twist(); t.linear.x = V
    while math.hypot(state["x"] - x0, state["y"] - y0) < dist and not rospy.is_shutdown():
        pub.publish(t); rate.sleep()
    pub.publish(Twist()); rospy.sleep(0.6)


def trn(angle):
    target = wrap(state["yaw"] + angle)
    t = Twist()
    while abs(wrap(target - state["yaw"])) > 0.02 and not rospy.is_shutdown():
        err = wrap(target - state["yaw"])
        t.angular.z = math.copysign(min(W, max(0.08, abs(err))), err)
        pub.publish(t); rate.sleep()
    pub.publish(Twist()); rospy.sleep(0.6)


def full():
    trn(math.pi * 0.99); trn(math.pi * 0.99)


full()                                   # oda 1: yerinde tam tur
fwd(4.0); full()                         # (4,0)
fwd(5.0); full()                         # kapidan gec -> (9,0)
trn(math.pi / 2); fwd(3.0); full()       # kuzey (9,3)
trn(math.pi); fwd(6.0); full()           # guney (9,-3)
trn(math.pi); fwd(3.0)                   # (9,0), kuzeye bakiyor
trn(math.pi / 2); fwd(9.0); full()       # bati'ya, kapidan geri -> (0,0)
print("rota bitti; son konum (odom): x=%.2f y=%.2f yaw=%.1f" % (state["x"], state["y"], math.degrees(state["yaw"])))
