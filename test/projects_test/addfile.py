import requests

# 定义上传文件的 URL
upload_url = 'http://localhost/projects/api/upload/'

jwt_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk3MjU5NTIwLCJpYXQiOjE2OTcxNzMxMjAsImp0aSI6IjRlMTYwOTlmMjg4NjQ1OTBhNmY1MjJlYjMxMDFjNTliIiwidXNlcl9pZCI6MzJ9.Et4ZVadJaOIJSneTQNvSeK5jlcLSSlzjqHD0Jb65goE'

# 请求头
headers = {
    'Authorization': f'Bearer {jwt_token}',  # Bearer 访问令牌
}

# 要上传的文件
# files = {'file': open('C:/Users/chenh/Desktop/接口文档/图片/接口描述：图片上传.txt', 'rb')}

files = {
    'file': ('接口描述：图片上传.txt', open('C:/Users/chenh/Desktop/接口文档/图片/接口描述：图片上传.txt', 'rb')),
    # 'file': ('接口描述：图片识别.txt', open('C:/Users/chenh/Desktop/接口文档/图片/接口描述：图片识别.txt', 'rb')),
}

# 请求数据（其他字段）
data = {
    'user': 32,      # 用户ID
    'folder': 46,    # 文件夹ID
    'project': 36,   # 项目ID
}

# 发送POST请求
response = requests.post(upload_url, data=data, files=files, headers=headers)

# 打印响应
print(response.status_code)
print(response.json())  # 如果服务器返回JSON响应