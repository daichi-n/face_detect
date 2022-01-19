"""
オウム返し Line Bot
"""

# from email import message
from email import message
import os
from unittest import result
# from tkinter import Image
# from urllib import response
# from aiohttp import client

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage,
)

import boto3

handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

boto3_client = boto3.client('rekognition')

def all_happy(result):
    for detail in result["FaceDetails"]:
        if most_confident_emotion(detail["Emotions"]) != "HAPPY":
            return False
    return True

def most_confident_emotion(emotions):
    max_conf = 0
    result = ""

    for e in emotions:
        if max_conf < e["Confidence"]:
            max_conf = e["Confidence"]
            result = e["Type"]

    return result

def convert_text_for_emotions(emotions):
    if emotions == "SAD":
        return "悲しい"
    if emotions == "CALM":
        return "落ち着き"
    if emotions == "FEAR":
        return "恐れ"
    if emotions == "HAPPY":
        return "ハッピー"
    if emotions == "CONFUSED":
        return "混乱"
    if emotions == "DISGUSTED":
        return "嫌悪感"
    if emotions == "ANGRY":
        return "怒り"
    if emotions == "SURPRISED":
        return "驚いた"

def get_personal_info(target):
    ret_text = ""

    # 性別を取得する
    if target["Gender"]["Value"] == "Female":
        ret_text += "性別：女性\n"
    else:
        ret_text += "性別：男性\n"

    ret_text += ("年代：" + str(target["AgeRange"]["Low"]) + "歳～" + str(target["AgeRange"]["High"]) + "歳\n")

    ret_text += "感情："
    emotions = most_confident_emotion(target["Emotions"])
    ret_text += convert_text_for_emotions(emotions) + "\n"

    return ret_text


def lambda_handler(event, context):
    headers = event["headers"]
    body = event["body"]

    # get X-Line-Signature header value
    signature = headers['x-line-signature']

    # handle webhook body
    handler.handle(body, signature)

    return {"statusCode": 200, "body": "OK"}


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """ TextMessage handler """
    input_text = event.message.text + "きたよ"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=input_text))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """ ImageMessage handler """
    # ユーザーから送られてきた画像を一時ファイルとして保存
    message_content = line_bot_api.get_message_content(event.message.id)
    file_path = "/tmp/sent-image.jpg"
    with open(file_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

    # Recongnitionで感情分析する
    with open(file_path, 'rb') as fd:
        sent_image_binary = fd.read()
        response = boto3_client.detect_faces(Image={"Bytes": sent_image_binary},
                                            Attributes=["ALL"])

    print(response)

    # LINEで返す文字列を定義
    res_text = "撮影人数：" + str(len(response["FaceDetails"])) + "人\n\n"

    # 一人づつ情報を取得する
    count = 1
    for detail in response["FaceDetails"]:
        res_text += "------" + str(count) + "人目------\n"

        res_text += get_personal_info(detail)

        count += 1

    print(res_text)


    # 返答を送信する
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=res_text))
#        TextSendMessage(text=str(response)[:1000]))

    # file_pathの画像を削除
    os.remove(file_path)