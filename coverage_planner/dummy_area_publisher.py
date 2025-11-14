import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PolygonStamped, Point32

class DummyAreaPublisher(Node):
    def __init__(self):
        super().__init__('dummy_area_publisher')
        
        # /cone_area トピックに PolygonStamped を発行する
        self.publisher_ = self.create_publisher(PolygonStamped, '/cone_area', 10)
        
        # 2秒ごとに publish_dummy_area 関数を呼び出すタイマー
        self.timer = self.create_timer(2.0, self.publish_dummy_area)
        
        self.get_logger().info('Dummy Area Publisher started.')
        self.get_logger().info('Publishing a test square (2x1) to /cone_area...')

    def publish_dummy_area(self):
        # ダミーの多角形メッセージを作成
        msg = PolygonStamped()
        
        # ヘッダー情報を設定 (TFが動いていれば 'map' や 'odom' が望ましい)
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"  # Nav2と連携するなら map フレームが基準

        # ダミーの四角形の頂点を定義 (例: 2m x 1m の四角形)
        points = [
            Point32(x=0.0, y=0.0, z=0.0),
            Point32(x=2.0, y=0.0, z=0.0),
            Point32(x=2.0, y=1.0, z=0.0),
            Point32(x=0.0, y=1.0, z=0.0),
        ]
        
        msg.polygon.points = points
        
        # メッセージを発行
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = DummyAreaPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
