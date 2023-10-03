import requests

# 您的API端点URL
api_url = 'http://localhost/recognition/api/crack_detection/'  # 请替换成您的API端点URL

# 要发送的数据
data = {
    'file_id': 3,  # 替换为您要检测的文件的FileinUser ID
    'user_id': 32    # 替换为用户的ID
}

# 发送POST请求
try:
    response = requests.post(api_url, data=data)

    # 检查响应状态码
    if response.status_code == 200:
        # 请求成功，处理响应数据
        result = response.json()
        print("Crack detection result:", result)
    elif response.status_code == 404:
        print("FileinUser not found.")
    elif response.status_code == 500:
        print("An error occurred during crack detection.")
    else:
        print("Unexpected error with status code:", response.status_code)

except requests.exceptions.RequestException as e:
    print("Request error:", str(e))
