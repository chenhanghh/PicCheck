import requests
from PIL import Image
from io import BytesIO

# 定义基础URL
base_url = 'http://localhost/recognition/'


# 测试裂缝检测接口
def test_crack_detection(photo_id):
    url = f'{base_url}crack_detection/{photo_id}/'
    response = requests.get(url)

    if response.status_code == 200:
        print('裂缝检测接口测试成功')
        data = response.json()
        # 处理响应数据
        print(data)
    else:
        print(f'裂缝检测接口测试失败，HTTP状态码: {response.status_code}')


# 测试裂缝显示接口
def test_crack_show(row_id):
    url = f'{base_url}crack_show/{row_id}/'
    response = requests.get(url)

    if response.status_code == 200:
        print('裂缝显示接口测试成功')
    else:
        print(f'裂缝显示接口测试失败，HTTP状态码: {response.status_code}')


if __name__ == '__main__':
    # 测试裂缝检测接口
    test_crack_detection(3)  # 传递裂缝图片的ID

    # 测试裂缝显示接口
    test_crack_show(5)  # 传递裂缝识别的ID


api_url = 'http://localhost/recognition/crack_show/5/'

# 发送GET请求，获取图像数据
response = requests.get(api_url)

# 检查响应状态码
if response.status_code == 200:
    # 从响应中获取图像数据
    img_data = response.content

    # 将图像数据转换为PIL图像对象
    img = Image.open(BytesIO(img_data))

    # 显示图像
    img.show()
else:
    print("Error:", response.status_code)
