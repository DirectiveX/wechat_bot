# -*- coding: utf-8 -*-
import json
import logging
import os
import time
from datetime import datetime
from queue import Empty
from threading import Thread

from wcferry import Wcf, WxMsg

__version__ = "39.2.4.0"

from job_mgmt import Job
import sqlite3


class Robot(Job):
    """个性化自己的机器人
    """

    def __init__(self, wcf: Wcf) -> None:
        super().__init__()
        self.wcf = wcf
        self.LOG = logging.getLogger("Robot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()
        self.__init_db__()

    def __init_db__(self):
        self.conn = sqlite3.connect("wechat.db", check_same_thread=False)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS wechat_pyq(
        id bigint primary key,
        content text,
        publish_time varchar(31),
        username varchar(511)
        );
        """)
        self.conn.execute(f"CREATE INDEX IF NOT EXISTS username_publish_time_idx ON wechat_pyq(username,publish_time);")

    @staticmethod
    def value_check(args: dict) -> bool:
        if args:
            return all(value is not None for key, value in args.items() if key != 'proxy')
        return False

    def processMsg(self, msg: WxMsg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        此处可进行自定义发送的内容,如通过 msg.content 关键字自动获取当前天气信息，并发送到对应的群组@发送者
        群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
        content = "xx天气信息为："
        receivers = msg.roomid
        self.sendTextMsg(content, receivers, msg.sender)
        """
        # 处理朋友圈消息
        if msg.type == 0:
            print("from pyq " + msg.content)
            self.conn.execute(
                f"insert or ignore into wechat_pyq(id,content,publish_time,username) values({msg.id},'{msg.content}','{datetime.fromtimestamp(msg.ts)}','{msg.sender}')")
        else:
            print("from other " + msg.content)

    def onMsg(self, msg: WxMsg) -> int:
        try:
            self.LOG.info(msg)  # 打印信息
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)

        return 0

    def enableRecvMsg(self) -> None:
        self.wcf.enable_recv_msg(self.onMsg)

    def enableReceivingMsg(self) -> None:
        def innerProcessMsg(wcf: Wcf):
            while wcf.is_receiving_msg():
                try:
                    msg = wcf.get_msg()
                    self.LOG.info(msg)
                    self.processMsg(msg)
                except Empty:
                    continue  # Empty message
                except Exception as e:
                    self.LOG.error(f"Receiving message error: {e}")

        self.wcf.enable_receiving_msg(pyq=True)
        Thread(target=innerProcessMsg, name="GetMessage", args=(self.wcf,), daemon=True).start()

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            if at_list == "notify@all":  # @所有人
                ats = " @所有人"
            else:
                wxids = at_list.split(",")
                for wxid in wxids:
                    # 根据 wxid 查找群昵称
                    ats += f" @{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
        if ats == "":
            self.LOG.info(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
        else:
            self.LOG.info(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats}\n\n{msg}", receiver, at_list)

    def find_all_msg_between_date(self, username, from_date_time, to_date_time):
        """
        找到时间范围内的所有朋友圈
        :param from_date_time:
        :param to_date_time:
        :param username: 需要查询的用户
        :param robot:
        :return:
        """
        cursor = self.conn.cursor()
        cursor.execute(
            f"select id,content,publish_time,username from wechat_pyq where username = '{username}' and publish_time >= '{from_date_time}' and publish_time < '{to_date_time}' order by publish_time")
        results = cursor.fetchall()
        return [{"content":row[1],"datetime":row[2]} for row in results]

    def getAllContacts(self) -> dict:
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)
