import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PolygonStamped, PoseStamped
from nav_msgs.msg import Path
import math

class ZigzagGenerator(Node):
    def __init__(self):
        super().__init__('zigzag_generator')
        
        # パラメータの宣言 (ロボットの幅 = ジグザグの間隔)
        self.declare_parameter('robot_width', 0.5)  # デフォルト 50cm
        
        # /cone_area トピックをサブスクライブ
        self.subscription = self.create_subscription(
            PolygonStamped,
            '/cone_area',
            self.area_callback,
            10)
        
        # /coverage_path トピックに Path をパブリッシュ
        self.path_publisher_ = self.create_publisher(Path, '/coverage_path', 10)
        
        self.get_logger().info('Zigzag Generator started. Waiting for /cone_area...')

    def area_callback(self, msg: PolygonStamped):
        """
        多角形エリアを受信し、ジグザグ経路を生成するコールバック関数
        """
        self.get_logger().info('Received polygon area. Generating path...')
        
        # パラメータ（ロボット幅）を取得
        robot_width = self.get_parameter('robot_width').get_parameter_value().double_value
        if robot_width <= 0:
            self.get_logger().error('robot_width must be greater than 0')
            return

        points = msg.polygon.points
        if len(points) < 3:
            self.get_logger().warn('Polygon has less than 3 points.')
            return

        # 1. 多角形の範囲 (Min/Max) を計算 (AABB)
        # (ダミーノードは四角形なので、これで十分)
        min_x = min(p.x for p in points)
        max_x = max(p.x for p in points)
        min_y = min(p.y for p in points)
        max_y = max(p.y for p in points)

        # 2. ジグザグ経路 (Path) のウェイポイントを生成
        path_msg = Path()
        path_msg.header = msg.header # 'map' フレームを引き継ぐ

        current_x = min_x
        direction = 1  # 1: min_y -> max_y, -1: max_y -> min_y

        while current_x <= max_x:
            if direction == 1:
                # Y軸プラス方向 (min_y -> max_y) のウェイポイント
                start_pose = self.create_pose(current_x, min_y, msg.header)
                end_pose = self.create_pose(current_x, max_y, msg.header)
            else:
                # Y軸マイナス方向 (max_y -> min_y) のウェイポイント
                start_pose = self.create_pose(current_x, max_y, msg.header)
                end_pose = self.create_pose(current_x, min_y, msg.header)

            path_msg.poses.append(start_pose)
            path_msg.poses.append(end_pose)

            # X軸方向にロボット幅だけ前進
            current_x += robot_width
            # 方向転換
            direction *= -1

        # 3. 生成した経路をパブリッシュ
        self.path_publisher_.publish(path_msg)
        self.get_logger().info(f'Published path with {len(path_msg.poses)} waypoints.')

    def create_pose(self, x, y, header):
        """
        (x, y) 座標から PoseStamped メッセージを作成するヘルパー関数
        """
        pose = PoseStamped()
        pose.header = header
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        # (向きはNav2が処理するので、ここでは単純に 0 を設定)
        pose.pose.orientation.w = 1.0 
        return pose

def main(args=None):
    rclpy.init(args=args)
    node = ZigzagGenerator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
