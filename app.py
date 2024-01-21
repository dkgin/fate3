from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import pandas as pd

app = Flask(__name__)

access_token = '0VwSNMKzkkxvqbBG0QJHjOro/LAbii4Fmn47oG3Dnjnj3ZVDUu+o8a0ZqMIDHNI0ZdZsVKthhCDJhsDN+hEUEeE0pT6qyhQmDoeoYwhI8Vwy3/vZdpKUEYE7YvF5Yf2niVZ+6xT9hTvoTT5PcXHm8QdB04t89/1O/w1cDnyilFU='
secret = '95a60f29fc8c4db5c373b53ea55f25cf'
line_bot_api = LineBotApi(access_token)              
handler = WebhookHandler(secret) 


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = TextSendMessage(text=event.message.text)
    line_bot_api.reply_message(event.reply_token, message)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
