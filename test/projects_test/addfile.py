import requests

# 定义上传文件的 URL
upload_url = 'http://localhost/projects/api/upload/'  # 替换成你的实际服务器 URL

jwt_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk2NDA1MDQ5LCJpYXQiOjE2OTYzMTg2NDksImp0aSI6IjY5ODE2NDQ2MTY3YTQzYTViYzAwZDcyOWM1YWY4Y2JiIiwidXNlcl9pZCI6MzJ9.CrGZpOGSoFEm00sL5Fq0rlNSKG91s7HklaB0n0eiF6o'

# 请求头，如果需要身份验证，请添加适当的标头
headers = {
    'Authorization': f'Bearer {jwt_token}',  # Bearer 访问令牌
}

# 要上传的文件
files = {'file': open('C:/Users/chenh/Desktop/接口文档/图片/接口描述：图片上传.txt', 'rb')}  # 替换成您要上传的文件路径

# 请求数据（其他字段）
data = {
    'user': 32,      # 用户ID
    'folder': 45,    # 文件夹ID
    'project': 36,   # 项目ID
}

# 发送POST请求
response = requests.post(upload_url, data=data, files=files, headers=headers)

# 打印响应
print(response.status_code)
print(response.json())  # 如果服务器返回JSON响应