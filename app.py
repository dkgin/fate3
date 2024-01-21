from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['Nkju9l/a0p1IXBDaeUpUABJhA3DY4ek/zS2pW3AMUYoagBuTXvHMEdrheBOuL3q5Ty/k6+11UFTihIzd5+SqciLoKNYI/gG0XM6cpW+jB0OlcbvqgSvWF1aD2GbWl96FW9tPNdeK0+TZobRLmeciOQdB04t89/1O/w1cDnyilFU='])
handler = WebhookHandler(os.environ['fd20299c1f5e9dfc7a89330b458ce6b2'])


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

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
