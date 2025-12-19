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
        
        # マージン（コーンに近づきすぎないようにする）
        margin = 0.3 # 50cm -> 30cm に戻す

        if robot_width <= 0:
            self.get_logger().error('robot_width must be greater than 0')
            return

        points = msg.polygon.points
        if len(points) < 3:
            self.get_logger().warn('Polygon has less than 3 points.')
            return

        # 1. 多角形の範囲 (Min/Max) を計算 (AABB)
        # マージンを適用して範囲を縮小
        min_x = min(p.x for p in points) + margin
        max_x = max(p.x for p in points) - margin
        min_y = min(p.y for p in points) + margin
        max_y = max(p.y for p in points) - margin
        
        # 範囲が逆転した場合は中心点のみにするなどの処理が必要だが、
        # ここでは単純にスキップ（または中心1点）
        if min_x > max_x or min_y > max_y:
             self.get_logger().warn('Polygon is too small for the given margin.')
             # 中心点を計算してそこをゴールにするなどのフォールバックも考えられるが、
             # 一旦は何もしない（パス生成失敗 -> BT側でハンドリングされるべき）
             return

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
