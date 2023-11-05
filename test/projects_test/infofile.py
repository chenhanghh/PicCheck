import requests

url = 'http://192.168.106.89:8000/projects/api/file/1/'

jwt_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk3NzA0MjA5LCJpYXQiOjE2OTc2MTc4MDksImp0aSI6IjIyODM2ZmUyM2E2MDQ3M2Q4Y2E4ODAxZjE2ODUwNWVjIiwidXNlcl9pZCI6MzJ9.3uDAngwdKtNfawo4fRqplpi0RINg7T4fxrnc2bGuBPo'

# 请求头
headers = {
    'Authorization': f'Bearer {jwt_token}',  # Bearer 访问令牌
}

# 发送GET请求
response = requests.get(url, headers=headers)

# 检查响应的状态码
if response.status_code == 200:
    try:
        # 尝试解析JSON响应
        json_data = response.json()
        print(json_data)
    except ValueError:
        print("服务器返回的响应不是有效的JSON格式")
else:
    print(f"请求失败，状态码：{response.status_code}")
