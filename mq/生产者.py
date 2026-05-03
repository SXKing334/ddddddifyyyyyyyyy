# 导入 pika 库，这是 Python 操作 RabbitMQ 的标准客户端
import pika

credentials = pika.PlainCredentials('guest', 'guest')

# ==================== 建立连接 ====================
# 创建一个阻塞式连接（BlockingConnection）
# ConnectionParameters 封装了连接参数，'localhost' 表示连接本机的 RabbitMQ 服务
# 如果 RabbitMQ 在其他服务器，可以写成 pika.ConnectionParameters('192.168.1.100', 5672)
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost',credentials=credentials))
channel = connection.channel()

# 从连接中创建一个通道（channel）
# 通道是进行消息通信的虚拟连接，大多数 RabbitMQ 操作（声明队列、发送消息等）都是在通道上完成的
# 一个 connection 可以创建多个 channel，用于隔离不同的业务
channel = connection.channel()

# ==================== 声明队列 ====================
# 声明/创建一个队列，如果队列不存在则创建，如果已存在则使用现有配置
# 参数说明：
#   queue='novel_1'  : 队列名称，后续发送和接收都通过这个名字找到它
#   durable=True     : 队列持久化。True 表示即使 RabbitMQ 服务重启，这个队列也不会丢失
#                      注意：durable 只保证队列本身不丢失，消息的持久化需要另外设置
channel.queue_declare(queue='novel_1')

# ==================== 发送消息 ====================
# 发布消息到指定队列
# 参数说明：
#   exchange=''      : 交换器名称。空字符串表示使用默认的交换器（direct 类型）
#                      默认交换器的路由规则是：routing_key 必须等于队列名，消息才会被路由到该队列
#   routing_key='novel_1' : 路由键。与默认交换器配合时，这个值就是目标队列的名称
#   body='Hello World!'   : 消息内容（二进制格式）。实际可以是任何字符串或序列化后的数据（如 JSON）
channel.basic_publish(exchange='',
                      routing_key='novel_1',
                      body='Hello World')

# ==================== 关闭连接 ====================
# 关闭连接，释放资源
# 这会自动关闭连接下所有的通道，并且通知 RabbitMQ 服务端断开
connection.close()