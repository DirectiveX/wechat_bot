#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import os
import json
import config
from ai.chat_ai import BaseGenerateAi
from entity.moment_info import MomentInfo
from wcferry import Wcf
from robot import Robot, __version__
import time
import datetime
from ai.chat_ai import BaseGenerateAi
from entity.moment_info import MomentInfo


def moment_msg_conclusion(robot: Robot, ai: BaseGenerateAi):
    subscribe_list, subscribe_sends = get_moment_subscribe_info()
    yesterday_time = datetime.datetime.now() + datetime.timedelta(days=-1)
    from_time = yesterday_time.strftime('%Y-%m-%d %H:%M:%S')
    to_time = time.strftime('%Y-%m-%d %H:%M:%S')
    for username in subscribe_list:
        contents = robot.find_all_msg_between_date(username, from_time, to_time)
        if contents is not None and len(contents) > 0:
            request_info = [MomentInfo(record.get("content"), record.get("datetime")) for record in contents]
            if subscribe_sends.get(username):
                response = ai.generate_moment_conclusion(request_info)
                report = generate_report(response)
                send_users = subscribe_sends.get(username)
                for user in send_users:
                    robot.sendTextMsg(report, user)


def generate_report(response):
    return f'今日心情：{response["心情"]}\n\n今日重点：\n{response["重点"]}\n\n今日总结：\n{response["总结"]}\n\n作诗：\n{response["赋诗"]}'


def get_moment_subscribe_info():
    """
    获取朋友圈订阅以及发送报告给对应的人
    :return:
    """
    subscribe = os.getenv("MOMENT_SUBSCRIBE")
    subscribe_send = os.getenv("MOMENT_CONCLUSION_SEND")
    if subscribe and subscribe_send:
        return subscribe.split(","), json.loads(subscribe_send)


if __name__ == '__main__':
    wcf = Wcf(debug=True)
    robot = Robot(wcf)
    robot.LOG.info(f"WeChatRobot【{__version__}】成功启动···")
    # 机器人启动发送测试消息
    # robot.sendTextMsg("bibo启动成功！", "filehelper")

    robot.onEveryTime("00:00", moment_msg_conclusion, robot)

    robot.enableReceivingMsg()  # 加队列
    # 让机器人一直跑
    # test
    ai = BaseGenerateAi()
    robot.keepRunningAndBlockProcess()