import redis


def test_sync_redis():
    print("=== 开始同步测试 ===")
    try:
        # 1. 建立连接
        # decode_responses=True 表示自动把字节解码成字符串，不然拿到的会是 b'hello'
        client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_timeout=3  # 设置3秒超时，防止卡死
        )

        # 2. 测试连接 (Ping)
        if client.ping():
            print("✅ 连接成功！Redis 正在响应。")

        # 3. 写入数据
        client.set("test_key", "Hello Sync Redis!")
        print("📝 写入数据: test_key = 'Hello Sync Redis!'")

        # 4. 读取数据
        value = client.get("test_key")
        print(f"📖 读取数据: {value}")
        client.save()

    except redis.ConnectionError as e:
        print("❌ 连接失败！请检查 Redis 服务是否启动。")
        print(f"错误详情: {e}")
    except Exception as e:
        print(f"❌ 发生其他错误: {e}")


if __name__ == "__main__":
    test_sync_redis()