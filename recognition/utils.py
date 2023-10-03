import os
import abc
import random
from io import BytesIO
from copy import deepcopy
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any, BinaryIO

import cv2
import numpy as np
from django.conf import settings
from django.http.response import HttpResponse
from PIL import Image, ImageFont, ImageDraw, ImageOps


@dataclass
class TextArgument:
    """
    图片绘制文字时,应该传递的参数
    """
    text: str
    color: Tuple
    place: Tuple
    size: int = 5


def put_text_to_img(img: Image, text_arg: TextArgument,
                    font_path: Optional[str] = None) -> Image:
    """
    对图片[Image] 添加文字
    Args:
        font_path:
        text_arg:
        img:

    Returns:
    """
    if font_path is None:
        font_path = getattr(settings, "DEFAULT_FONT_PATH_IN_IMAGE", None)
    if font_path is None:
        font_path = os.path.join("fonts", "simsun.ttc")
    # 不调整外部img原本色彩空间
    img = deepcopy(img)
    font = ImageFont.truetype(font_path, text_arg.size)
    draw = ImageDraw.Draw(img)
    draw.text(text_arg.place, text_arg.text, font=font, fill=text_arg.color)
    return img


def put_text_to_ndarray(img: np.ndarray, text_arg: TextArgument,
                        font_path: Optional[str] = None) -> np.ndarray:
    """
    处理矩阵像素点形式的图片;绘制文字信息
    Args:
        img:
        text_arg:
        font_path:

    Returns:

    """
    image = Image.fromarray(img)
    image_new = put_text_to_img(image, text_arg, font_path)
    img_new = np.array(image_new)
    return img_new


def draw_circle(image: np.ndarray, bboxes, color=None):
    if color is None:
        color = (0, 0, 255)
    for box in bboxes:
        center_x = int(box[0] + box[2] / 2)
        center_y = int(box[1] + box[3] / 2)
        center = (center_x, center_y)
        radius = int(0.15 * box[2])
        # cv2 有该用法. pylint:disable=no-member
        cv2.circle(image, center, radius, color=color, thickness=-1)
    return image


class IImageDispose(abc.ABC):
    def __init__(self, img: Image, data: Any):
        self._img = img
        self._data = data  # 不限制数据类型
        super().__init__()

    @abc.abstractmethod
    def draw(self) -> Image:
        ...


def convert_opened_file_to_image(binary_io: BinaryIO):
    img: Image.Image = Image.open(binary_io)
    img = ImageOps.exif_transpose(img)
    if img.mode == "RGBA":
        color_r, color_g, color_b, _ = img.split()
        img = Image.merge("RGB", (color_r, color_g, color_b))

    return img


def make_image_response(image: Image) -> HttpResponse:
    result_content: BytesIO = BytesIO()
    image.save(result_content, "png")
    result_content.seek(0)
    response = HttpResponse(result_content.read(),
                            content_type="image/png")
    return response


class CrackDetectionDispose(IImageDispose):
    def draw(self) -> Image:
        results: Dict = self._data
        img_np: np.ndarray = np.asarray(self._img)

        if results is None:
            box_s = []
            names = None
        else:
            box_s = results.get("result", [])
            names = results.get("names", None)

        # 随机的颜色,绘制包围框
        color_count = 1
        if names is not None:
            color_count = len(names)
        colors = [[random.randint(0, 255) for _ in range(3)] for _ in
                  range(color_count)]
        for box in box_s:
            box_xyxy = box[:4]
            t_l = round(0.002 * (img_np.shape[0] + img_np.shape[1]) / 2) + 1
            c_1, c_2 = box_xyxy[0:2], box_xyxy[2:]
            label = None if names is None else names[str(box[-1])]
            color = colors[0] if names is None else colors[box[-1]]
            if label is not None:
                label += f":{round(box[-2] * 100, 2)}%"
                label: str
                text_arg = TextArgument(
                    text=label,
                    color=tuple(color),
                    place=(c_1[0], c_1[1] - 32),
                    size=32
                )

                img_np = put_text_to_ndarray(img_np, text_arg)
            # pylint:disable=no-member
            cv2.rectangle(img_np, c_1, c_2, color, thickness=t_l,
                          lineType=cv2.LINE_AA)

        return Image.fromarray(img_np)
