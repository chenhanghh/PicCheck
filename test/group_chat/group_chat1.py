import websocket
import json

VALID_JWT_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk4OTE0MjIyLCJpYXQiOjE2OTg4Mjc4MjIsImp0aSI6IjM2ZmZkNjI3MTU3YTQ2NmFiMTQxOTU3MTM3MDhjMzdmIiwidXNlcl9pZCI6MzJ9._aN2HoVUK_2OHchCbMeW0a3ES6PyPxfuSjhad8Xqbi0'


def on_message(ws, message):  # 在接收到WebSocket消息时被调用，打印消息内容
    print(message)


def on_error(ws, error):  # 在发生WebSocket连接错误时被调用，打印错误信息
    print(error)


def on_close(ws, close_status_code, close_msg):  # 在WebSocket连接关闭时被调用，打印连接关闭的状态码和关闭消息
    print("### closed ###")


def on_open(ws):  # 在WebSocket连接成功打开时被调用，发送一条文本消息并打印 "Opened connection"
    # 发送文本消息
    text_message = {
        'message_type': 'text',
        'message_data': 'Hello, group chat!',
    }
    ws.send(json.dumps(text_message))
    print("Opened connection")


if __name__ == "__main__":
    websocket.enableTrace(True)  # 启用WebSocket库的跟踪功能，用于打印WebSocket连接的详细信息
    # 指定WebSocket服务器的URL和回调函数
    ws = websocket.WebSocketApp("ws://192.168.137.135:80/ws/chat/21/?token=" + VALID_JWT_TOKEN,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever()  # 启动WebSocket连接并保持它处于运行状态，该连接将持续接收和发送消息
