from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, StickerSendMessage, ImageSendMessage, LocationSendMessage
import requests, json, time, statistics
import os

# 地震資訊函式
def earth_quake():
    msg = ['找不到地震資訊','https://example.com/demo.jpg']            # 預設回傳的訊息
    try:
        code = 'CWA-C7DED748-AB01-46ED-B03D-3730BA31B6B0'
        url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={code}'
        e_data = requests.get(url)                                   # 爬取地震資訊網址
        e_data_json = e_data.json()                                  # json 格式化訊息內容
        eq = e_data_json['records']['Earthquake']                    # 取出地震資訊
        for i in eq:
            loc = i['EarthquakeInfo']['Epicenter']['Location']       # 地震地點
            val = i['EarthquakeInfo']['EarthquakeMagnitude']['MagnitudeValue'] # 地震規模
            dep = i['EarthquakeInfo']['FocalDepth']              # 地震深度
            eq_time = i['EarthquakeInfo']['OriginTime']              # 地震時間
            img = i['ReportImageURI']                                # 地震圖
            msg = [f'{loc}，芮氏規模 {val} 級，深度 {dep} 公里，發生時間 {eq_time}。', img]
            break     # 取出第一筆資料後就 break
        return msg    # 回傳 msg
    except:
        return msg    # 如果取資料有發生錯誤，直接回傳 msg

# LINE push 訊息函式
def push_message(msg, uid, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {'to':uid,'messages':[{"type": "text","text": msg}]}
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/push', headers=headers,data=json.dumps(body).encode('utf-8'))
    print(req.text)

# LINE 回傳訊息函式
def reply_message(msg, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {'replyToken':rk,'messages':[{"type": "text","text": msg}]}
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    print(req.text)


# LINE 回傳圖片函式
def reply_image(msg, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {'replyToken':rk,'messages':[{'type': 'image','originalContentUrl': msg,'previewImageUrl': msg}]}
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    print(req.text)

# 目前天氣函式
def current_weather(address):
    city_list, area_list, area_list2 = {}, {}, {} # 定義好待會要用的變數
    msg = '找不到氣象資訊。'                         # 預設回傳訊息

  # 定義取得資料的函式
    def get_data(url):
        w_data = requests.get(url)   # 爬取目前天氣網址的資料
        w_data_json = w_data.json()  # json 格式化訊息內容
        location = w_data_json["records"]["Station"]  # 取出對應地點的內容
        for i in location:
            name = i["StationName"]                       # 測站地點
            city = i["GeoInfo"]["CountyName"]     # 縣市名稱
            area = i["GeoInfo"]["TownName"]     # 鄉鎮行政區
            temp = check_data(i["WeatherElement"]["AirTemperature"])                       # 氣溫
            humd = check_data(round(float(i["WeatherElement"]["RelativeHumidity"] ) ,1)) # 相對濕度
            if area not in area_list:
                area_list[area] = {'temp':temp, 'humd':humd}  # 以鄉鎮區域為 key，儲存需要的資訊
            if city not in city_list:
                city_list[city] = {'temp':[], 'humd':[]}       # 以主要縣市名稱為 key，準備紀錄裡面所有鄉鎮的數值
            city_list[city]['temp'].append(temp)   # 記錄主要縣市裡鄉鎮區域的溫度 ( 串列格式 )
            city_list[city]['humd'].append(humd)   # 記錄主要縣市裡鄉鎮區域的濕度 ( 串列格式 )

  # 定義如果數值小於 0，回傳 False 的函式
    def check_data(e):
        return False if float(e)<0 else float(e)

  # 定義產生回傳訊息的函式
    def msg_content(loc, msg):
        a = msg
        for i in loc:
            if i in address:  # 如果地址裡存在 key 的名稱
                temp = f"氣溫 {loc[i]['temp']} 度，" if loc[i]['temp'] != False else ''
                humd = f"相對濕度 {loc[i]['humd']}%，" if loc[i]['humd'] != False else ''
                description = f'{temp}{humd}'.strip('，')
                a = f'{description}。' # 取出 key 的內容作為回傳訊息使用
                break
        return a

    try:
        # 因為目前天氣有兩組網址，兩組都爬取
        code = 'CWA-C7DED748-AB01-46ED-B03D-3730BA31B6B0'
        get_data(f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={code}&format=JSON')
        get_data(f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={code}&format=JSON')

        for i in city_list:
            if i not in area_list2: # 將主要縣市裡的數值平均後，以主要縣市名稱為 key，再度儲存一次，如果找不到鄉鎮區域，就使用平均數值
                area_list2[i] = {'temp':round(statistics.mean(city_list[i]['temp']),1),'humd':round(statistics.mean(city_list[i]['humd']),1)}
        msg = msg_content(area_list2, msg)  # 將訊息改為「大縣市」
        msg = msg_content(area_list, msg)   # 將訊息改為「鄉鎮區域」
        return msg    # 回傳 msg
    except:
        return msg    # 如果取資料有發生錯誤，直接回傳 msg

def forecast(address):
    area_list = {}
    # 將主要縣市個別的 JSON 代碼列出
    json_api = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013","彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029","屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045","基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061","高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077","連江縣":"F-D0047-081","金門縣":"F-D0047-085"}
    msg = '找不到天氣預報資訊。'    # 預設回傳訊息
    try:
        code = 'CWA-C7DED748-AB01-46ED-B03D-3730BA31B6B0'
        url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={code}&format=JSON'
        f_data = requests.get(url)   # 取得主要縣市預報資料
        f_data_json = f_data.json()  # json 格式化訊息內容
        location = f_data_json["records"]['location']  # 取得縣市的預報內容
        for i in location:
            city = i['locationName']    # 縣市名稱
            wx8 = i['weatherElement'][0]['time'][0]['parameter']['parameterName']    # 天氣現象
            mint8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']  # 最低溫
            maxt8 = i['weatherElement'][4]['time'][0]['parameter']['parameterName']  # 最高溫
            ci8 = i['weatherElement'][3]['time'][0]['parameter']['parameterName']    # 舒適度
            pop8 = i['weatherElement'][1]['time'][0]['parameter']['parameterName']   # 降雨機率
            area_list[city] = f'未來 8 小時{wx8}，最高溫 {maxt8} 度，最低溫 {mint8} 度，降雨機率 {pop8} %'  # 組合成回傳的訊息，存在以縣市名稱為 key 的字典檔裡
        for i in area_list:
            if i in address:        # 如果使用者的地址包含縣市名稱
                msg = area_list[i]  # 將 msg 換成對應的預報資訊
                 # 將進一步的預報網址換成對應的預報網址
                url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{json_api[i]}?Authorization={code}&elementName=WeatherDescription'
                f_data = requests.get(url)  # 取得主要縣市裡各個區域鄉鎮的氣象預報
                f_data_json = f_data.json() # json 格式化訊息內容
                location = f_data_json['records']['locations'][0]['location']    # 取得預報內容
                break
        for i in location:
            city = i['locationName']   # 取得縣市名稱
            wd = i['weatherElement'][0]['time'][1]['elementValue'][0]['value']  # 綜合描述
            if city in address:           # 如果使用者的地址包含鄉鎮區域名稱
                msg = f'未來八小時天氣{wd}' # 將 msg 換成對應的預報資訊
                break
        return msg  # 回傳 msg
    except:
        return msg  # 如果取資料有發生錯誤，直接回傳 msg


app = Flask(__name__)

access_token = 'Nkju9l/a0p1IXBDaeUpUABJhA3DY4ek/zS2pW3AMUYoagBuTXvHMEdrheBOuL3q5Ty/k6+11UFTihIzd5+SqciLoKNYI/gG0XM6cpW+jB0OlcbvqgSvWF1aD2GbWl96FW9tPNdeK0+TZobRLmeciOQdB04t89/1O/w1cDnyilFU='

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)    # 取得收到的訊息內容
    try:
        line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
        handler = WebhookHandler(os.environ['CHANNEL_SECRET'])
        signature = request.headers['X-Line-Signature']       # 加入回傳的 headers
        handler.handle(body, signature)                       # 綁定訊息回傳的相關資訊
        json_data = json.loads(body)                          # 轉換內容為 json 格式
        if 'events' in json_data and json_data['events']:
            reply_token = json_data['events'][0]['replyToken']    # 取得回傳訊息的 Token ( reply message 使用 )
            user_id = json_data['events'][0]['source']['userId']  # 取得使用者 ID ( push message 使用 )
            print(json_data)                         # 印出內容
            if 'message' in json_data['events'][0]:           # 如果傳送的是 message
                if json_data['events'][0]['message']['type'] == 'location':                    # 如果 message 的類型是地圖 location
                    address = json_data['events'][0]['message']['address'].replace('台','臺')   # 取出地址資訊，並將「台」換成「臺」
                    reply_message(f'{address}\n\n{current_weather(address)}\n\n{forecast(address)}', reply_token, access_token)
                    print(address)
            if json_data['events'][0]['message']['type'] == 'text':   # 如果 message 的類型是文字 text
                text = json_data['events'][0]['message']['text']      # 取出文字
                if text == '雷達回波圖' or text == '雷達回波': 
                    reply_image(f'https://cwaopendata.s3.ap-northeast-1.amazonaws.com/Observation/O-A0058-001.png?{time.time_ns()}', reply_token, access_token)
                elif text == '地震資訊' or text == '地震':        # 如果是地震相關的文字
                    msg = earth_quake()   # 爬取地震資訊
                    push_message(msg[0], user_id, access_token)       # 傳送地震資訊 ( 用 push 方法，因為 reply 只能用一次 )
                    reply_image(msg[1], reply_token, access_token)    # 傳送地震圖片 ( 用 reply 方法 )
                else:
                    reply_message(f'請點選左下方☰圖示，開啟選單功能', reply_token, access_token)        # 如果是一般文字，直接回覆同樣的文字
    except InvalidSignatureError:
        abort(400)                
    return 'OK'                              # 驗證 Webhook 使用，不能省略


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

    
    

