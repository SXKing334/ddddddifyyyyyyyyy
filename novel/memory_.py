import os
import json
from contextlib import ExitStack
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Sequence

import aiomysql
from dotenv import load_dotenv
from langgraph.checkpoint.base import (
    BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple,
    SerializerProtocol,ChannelVersions, get_checkpoint_metadata, WRITES_IDX_MAP,
)
from langchain_core.runnables import RunnableConfig
from novel.exception.exceptions import MySQLLoadError
load_dotenv()

# 数据库配置加载
mysql_setting = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'db': os.getenv('MYSQL_DBNAME'),
    'autocommit': True if os.getenv('AUTOCOMMIT') == 'True' else False,
    'minsize': int(os.getenv('MYSQL_MINSIZE', 1)),
    'maxsize': int(os.getenv('MYSQL_MAXSIZE', 10))
}
async def mysql_pool():
    """创建异步数据库连接池"""
    return await aiomysql.create_pool(**mysql_setting)





class MySQLMemorySaver(BaseCheckpointSaver):
    def __init__(
            self,
            *,
            conn_pool: aiomysql.Pool,
            serde: SerializerProtocol | None = None,
    ) -> None:
        super().__init__(serde=serde)
        self.pool = conn_pool
        self.stack = ExitStack()

    # --- 上下文管理 ---
    def __enter__(self) -> MySQLMemorySaver:
        return self
    def __exit__(self, *args) -> None:
        pass
    async def __aenter__(self) -> MySQLMemorySaver:
        return self
    async def __aexit__(self, *args) -> None:
        pass

    async def _load_blobs(self, thread_id: str, checkpoint_ns: str, versions: ChannelVersions) -> dict[str, Any]:
        """根据版本清单从 blobs 表还原数据零件"""
        channel_values: dict[str, Any] = {}
        if not versions:
            return channel_values

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                for k, v in versions.items():
                    sql = """
                          SELECT blob_type, blob_bin FROM checkpoint_blobs
                          WHERE thread_id = %s AND checkpoint_ns = %s AND channel = %s AND version = %s 
                          """
                    await cur.execute(sql, (thread_id, checkpoint_ns, k, v))
                    row = await cur.fetchone()
                    if row and row["blob_type"] != "empty":
                        channel_values[k] = self.serde.loads_typed(
                            (row["blob_type"], row["blob_bin"])
                        )
        return channel_values

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """从数据库读取并组装 CheckpointTuple"""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id", None)

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if checkpoint_id:
                    sql = "SELECT * FROM checkpoints WHERE thread_id=%s AND checkpoint_ns=%s AND checkpoint_id=%s"
                    await cur.execute(sql, (thread_id, checkpoint_ns, checkpoint_id))
                else:
                    # 按照创建时间倒序取最新一个
                    sql = "SELECT * FROM checkpoints WHERE thread_id=%s AND checkpoint_ns=%s ORDER BY created_at DESC LIMIT 1"
                    await cur.execute(sql, (thread_id, checkpoint_ns))

                row = await cur.fetchone()
                if not row:
                    return None

                # 还原骨架和元数据
                checkpoint_data = self.serde.loads_typed((row["checkpoint_type"], row["checkpoint_bin"]))
                metadata = self.serde.loads_typed((row["metadata_type"], row["metadata_bin"]))
                channel_versions = json.loads(row["channel_versions"])

                # 合并具体业务数据 (Blobs)
                final_values = await self._load_blobs(thread_id, checkpoint_ns, channel_versions)
                checkpoint_data["channel_values"] = final_values

                # 加载中间状态 (Pending Writes)
                write_sql = """
                            SELECT task_id, channel, blob_type, value_bin FROM checkpoint_writes
                            WHERE thread_id = %s AND checkpoint_ns = %s AND checkpoint_id = %s
                            """
                await cur.execute(write_sql, (thread_id, checkpoint_ns, row["checkpoint_id"]))
                writes_rows = await cur.fetchall()
                pending_writes = [
                    (r["task_id"], r["channel"], self.serde.loads_typed((r["blob_type"], r["value_bin"])))
                    for r in writes_rows
                ]

                return CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": row["checkpoint_id"]
                        }
                    },
                    checkpoint=checkpoint_data,
                    metadata=metadata,
                    pending_writes=pending_writes,
                    parent_config=({
                                       "configurable": {
                                           "thread_id": thread_id,
                                           "checkpoint_ns": checkpoint_ns,
                                           "checkpoint_id": row["parent_id"]
                                       }
                                   } if row["parent_id"] else None),
                )

    async def aput(
            self, config: RunnableConfig,
            checkpoint: Checkpoint,
            metadata: CheckpointMetadata,
            new_versions: ChannelVersions
    ) -> RunnableConfig:
        """增量存储当前状态"""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = checkpoint["id"]

        print(f"检查点数据： {checkpoint}")
        print(f"检查点元数据：{metadata}")
        print(f"要更新的版本：{new_versions}")

        c = checkpoint.copy()
        values: dict[str, Any] = c.pop("channel_values")

        async with self.pool.acquire() as conn:
            try:
                async with conn.cursor() as cur:
                    # 1. 存入变动的数据零件 (Blobs)
                    for k, v in new_versions.items():
                        blob_type, blob_bin = self.serde.dumps_typed(values[k]) if k in values else ("empty", b"")
                        sql = """
                              INSERT INTO checkpoint_blobs (thread_id, checkpoint_ns, channel, version, blob_type, blob_bin)
                              VALUES (%s, %s, %s, %s, %s, %s) AS new
                              ON DUPLICATE KEY UPDATE blob_bin = new.blob_bin, blob_type = new.blob_type
                              """
                        await cur.execute(sql, (thread_id, checkpoint_ns, k, v, blob_type, blob_bin))

                    # 2. 存入检查点骨架 (Index)
                    c_type, c_bin = self.serde.dumps_typed(c)
                    meta = get_checkpoint_metadata(config, metadata)
                    m_type, m_bin = self.serde.dumps_typed(meta)
                    channel_versions_json = json.dumps(checkpoint["channel_versions"])
                    # 上一轮的 id 即为本轮的 parent_id
                    parent_id = config["configurable"].get("checkpoint_id")

                    sql = """
                          INSERT INTO checkpoints (
                              thread_id, checkpoint_ns, checkpoint_id, parent_id, 
                              checkpoint_type, checkpoint_bin, metadata_type, metadata_bin, 
                              channel_versions, created_at
                          )
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS new
                          ON DUPLICATE KEY UPDATE checkpoint_bin = new.checkpoint_bin
                          """
                    await cur.execute(sql, (
                        thread_id, checkpoint_ns, checkpoint_id, parent_id,
                        c_type, c_bin, m_type, m_bin,
                        channel_versions_json, datetime.now(timezone.utc)
                    ))
                    await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise MySQLLoadError(e)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    async def aput_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:
        """保存节点运行中的中间产物"""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        async with self.pool.acquire() as conn:
            try:
                async with conn.cursor() as cur:
                    for idx, (channel, value) in enumerate(writes):
                        write_idx = WRITES_IDX_MAP.get(channel, idx)
                        blob_type, value_bin = self.serde.dumps_typed(value)
                        sql = """
                              INSERT INTO checkpoint_writes (
                                  thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, blob_type, value_bin, task_path
                              )
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) AS new
                              ON DUPLICATE KEY UPDATE value_bin = new.value_bin, blob_type = new.blob_type 
                              """
                        await cur.execute(sql, (
                            thread_id, checkpoint_ns, checkpoint_id, task_id,
                            write_idx, channel, blob_type, value_bin, task_path
                        ))
                    await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise MySQLLoadError(e)

    async def alist(
            self,
            config: RunnableConfig | None,
            *,
            filter: dict[str, Any] | None = None,
            before: RunnableConfig | None = None,
            limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """按条件列出历史记录"""
        thread_id = config["configurable"]["thread_id"] if config else None
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "") if config else ""

        sql = "SELECT thread_id, checkpoint_ns, checkpoint_id FROM checkpoints WHERE 1=1"
        params = []
        if thread_id:
            sql += " AND thread_id = %s"
            params.append(thread_id)
        if checkpoint_ns:
            sql += " AND checkpoint_ns = %s"
            params.append(checkpoint_ns)

        if before and (before_id := before["configurable"].get("checkpoint_id")):
            # 基于 ID 过滤更早的版本
            sql += " AND checkpoint_id < %s"
            params.append(before_id)

        sql += " ORDER BY created_at DESC"
        if limit:
            sql += f" LIMIT {limit}"

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, tuple(params))
                rows = await cur.fetchall()

        for row in rows:
            res = await self.aget_tuple({
                "configurable": {
                    "thread_id": row["thread_id"],
                    "checkpoint_ns": row["checkpoint_ns"],
                    "checkpoint_id": row["checkpoint_id"]
                }
            })
            if res:
                # 应用 metadata 过滤器
                if filter and not all(res.metadata.get(k) == v for k, v in filter.items()):
                    continue
                yield res

if __name__ == "__main__":
    pass