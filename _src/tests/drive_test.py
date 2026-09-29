import rospy, math
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from gazebo_msgs.srv import GetModelState
from tf.transformations import euler_from_quaternion

rospy.init_node("drive_test")
pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
rospy.wait_for_service("/gazebo/get_model_state")
gms = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)


def truth():
    r = gms("amr", "world").pose
    return r.position.x, r.position.y, euler_from_quaternion([r.orientation.x, r.orientation.y, r.orientation.z, r.orientation.w])[2]


def odom():
    o = rospy.wait_for_message("/odom", Odometry, timeout=3).pose.pose
    return o.position.x, o.position.y, euler_from_quaternion([o.orientation.x, o.orientation.y, o.orientation.z, o.orientation.w])[2]


def run(v, w, secs):
    t = Twist(); t.linear.x = v; t.angular.z = w
    end = rospy.Time.now() + rospy.Duration(secs); r = rospy.Rate(20)
    while rospy.Time.now() < end and not rospy.is_shutdown():
        pub.publish(t); r.sleep()
    pub.publish(Twist()); rospy.sleep(1.5)


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


rospy.sleep(2)
g0 = truth(); o0 = odom(); run(0.3, 0.0, 5.5); g1 = truth(); o1 = odom()
dg = math.hypot(g1[0] - g0[0], g1[1] - g0[1]); do = math.hypot(o1[0] - o0[0], o1[1] - o0[1])
print(f"ILERI 0.3 m/s x 5.5 s -> gercek={dg:.3f} m | odom={do:.3f} m | fark={abs(dg - do):.3f} m")
run(0.0, 0.5, 6.28); g2 = truth(); o2 = odom()
print(f"DONUS 0.5 rad/s x 6.28 s -> gercek={math.degrees(wrap(g2[2] - g1[2])):.1f} | odom={math.degrees(wrap(o2[2] - o1[2])):.1f} (beklenen ~ +-180)")
r = gms("amr", "world").pose
print(f"z={r.position.z:.3f} egim qx={r.orientation.x:.3f} qy={r.orientation.y:.3f}")
