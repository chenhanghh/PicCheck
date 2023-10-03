import requests

# 您的API端点URL
url = 'http://localhost/projects/api/file/68/'  # 替换成您要获取文件信息的文件ID

# 请求头，如果需要身份验证，请添加适当的标头
headers = {
    'Authorization': "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjozMiwidXNlcm5hbWUiOiJVbHltYURIeSIsImV4cCI6MTY5NjA1MzA2OCwiZW1haWwiOiIiLCJvcmlnX2lhdCI6MTY5NTQ0ODI2OH0.to3ZIAzaUVJTgDSvCJP28tPr1Foy96w6pBDYBk1zLz0",  # 替换为您的身份验证令牌（如果有）
}

# 发送GET请求
response = requests.get(url, headers=headers)

# 检查响应的状态码
if response.status_code == 200:  # 200表示成功
    try:
        # 尝试解析JSON响应
        json_data = response.json()
        print(json_data)
    except ValueError:
        print("服务器返回的响应不是有效的JSON格式")
else:
    print(f"请求失败，状态码：{response.status_code}")
