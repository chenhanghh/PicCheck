from django.db import transaction
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

from common.models import Project, ProjectUser, Folder, File, User
from django.http import JsonResponse
import os

from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from .serializers import ProjectSerializer, FileAddSerializer, FolderSerializer, FileDelSerializer, FileSerializer, \
    FolderRenameSerializer, FolderInfoSerializer, FileInfoSerializer, ProjectRenameSerializer
from rest_framework.response import Response

from projects.forms import FileFieldForm
from django.views.generic.edit import FormView

import logging

logger = logging.getLogger(__name__)


# 创建项目
class AddProjectAPI(generics.CreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def create(self, request, *args, **kwargs):
        # 解析请求数据
        project_data = request.data
        user_data = project_data.pop('users', [])

        # 创建项目
        project_serializer = self.get_serializer(data=project_data)
        if project_serializer.is_valid():
            project = project_serializer.save()

            # 将用户添加到项目中
            for user_id in user_data:
                try:
                    user = User.objects.get(id=user_id)
                    project.users.add(user)
                except User.DoesNotExist:
                    pass

            return Response(project_serializer.data, status=201)
        return Response(project_serializer.errors, status=400)


# 新建文件夹
class AddFolderAPI(generics.CreateAPIView):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer


# 上传文件
class UploadFileAPI(generics.CreateAPIView):
    queryset = File.objects.all()
    serializer_class = FileAddSerializer
    # 视图能解析多部份表单数据和常规表单数据（如文件上传和文本字段）
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]  # 控制访问权限

    def perform_create(self, serializer):
        # 获取上传的文件对象
        uploaded_file = self.request.FILES.get('file')

        # 设置文件名称和大小到 validated_data 中
        serializer.validated_data['file_name'] = uploaded_file.name
        serializer.validated_data['file_size'] = uploaded_file.size

        # 关联上传的文件与当前登录用户
        serializer.validated_data['user'] = self.request.user

        # 调用父类的 perform_create 方法保存文件
        super().perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


# 批量删除文件
class DelFileAPI(APIView):
    def post(self, request):
        serializer = FileDelSerializer(data=request.data)
        if serializer.is_valid():
            file_ids = serializer.validated_data['file_ids']
            # 执行批量删除操作
            try:
                deleted_files = File.objects.filter(id__in=file_ids)
                for file in deleted_files:
                    # 删除服务器本地文件系统中的文件
                    file_path = 'media/' + file.file.name
                    # 删除存储文件
                    os.remove(file_path)
                    # 删除数据库中的文件记录
                    file.delete()

                return Response({"message": "文件删除成功"}, status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                return Response({"message": "删除文件时出错"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 获取文件
class FileRetrieveAPI(generics.RetrieveAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer


# 删除文件夹
def del_folder(folder_id):
    # 获取要删除的文件夹对象
    folder = Folder.objects.get(id=folder_id)

    # 递归删除文件夹内的子文件夹和子文件
    def delete_contents(folder):
        # 子文件夹
        for subfolder in Folder.objects.filter(parent_folder_id=folder.id):
            delete_contents(subfolder)
            # 删除与子文件夹相关的内容
            subfolder.delete()
        # 子文件
        for file in File.objects.filter(folder_id=folder.id):
            filepath = 'media/' + file.file.name
            # 删除存储文件
            os.remove(filepath)
            # 删除数据库中记录
            file.delete()

    delete_contents(folder)
    # 删除数据库中与该文件夹相关的内容
    folder.delete()


# 删除文件夹
class DelFolderAPI(APIView):
    def post(self, request):
        folder_ids = request.data.get('folder_ids', [])

        for folder_id in folder_ids:
            try:
                del_folder(folder_id)
            except Exception as e:
                return Response({"message": "删除文件夹时出错"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "文件夹删除成功"}, status=status.HTTP_204_NO_CONTENT)


# 文件夹重命名
class FolderRenameAPI(APIView):
    def put(self, request, folder_id):
        folder = Folder.objects.get(pk=folder_id)
        serializer = FolderRenameSerializer(data=request.data)

        if serializer.is_valid():
            new_title = serializer.validated_data['new_title']
            folder.title = new_title
            folder.save()
            return Response({"message": "文件夹重命名成功"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 获取文件夹信息
class FolderInfoAPI(APIView):
    def get(self, request, folder_id):
        try:
            folder = Folder.objects.get(pk=folder_id)
        except Folder.DoesNotExist:
            return Response({"message": "文件夹不存在"}, status=status.HTTP_404_NOT_FOUND)

        subfolders = Folder.objects.filter(parent_folder_id=folder_id)
        files = File.objects.filter(folder_id=folder_id)

        subfolder_serializer = FolderInfoSerializer(subfolders, many=True)
        file_serializer = FileInfoSerializer(files, many=True)

        data = {
            "subfolders": subfolder_serializer.data,
            "files": file_serializer.data
        }

        return Response(data, status=status.HTTP_200_OK)


# 获取项目根文件夹和跟文件信息
class ProjectInfoAPI(APIView):
    def get(self, request, project_id):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({"message": "项目不存在"}, status=status.HTTP_404_NOT_FOUND)

        subfolders = Folder.objects.filter(parent_folder_id=None, project_id=project_id)
        files = File.objects.filter(folder_id=None, project_id=project_id)

        subfolder_serializer = FolderInfoSerializer(subfolders, many=True)
        file_serializer = FileInfoSerializer(files, many=True)

        data = {
            "subfolders": subfolder_serializer.data,
            "files": file_serializer.data
        }

        return Response(data, status=status.HTTP_200_OK)


# 项目重命名
class ProjectRenameAPI(APIView):
    def put(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        serializer = ProjectRenameSerializer(data=request.data)

        if serializer.is_valid():
            new_name = serializer.validated_data['new_name']
            project.name = new_name
            project.save()
            return Response({"message": "文件夹重命名成功"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 删除项目
class DelProjectAPI(APIView):
    def post(self, project_id):

        try:
            project = Project.objects.get(pk=project_id)

            with transaction.atomic():
                # 删除项目内所有文件夹、文件
                folders = Folder.objects.filter(project_id=project_id, parent_folder_id=None).values('id')
                folderslist = list(folders)
                for f in folderslist:
                    del_folder(f['id'])
                # 先删除 ProjectUser 里面的记录
                ProjectUser.objects.filter(project_id=project_id).delete()
                # 再删除项目记录
                project.delete()
            return Response({"message": "项目删除成功"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"message": "删除项目时出错"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 在项目内搜索文件或文件夹
class SearchAPI(APIView):
    def get(self, request):
        # 获取项目id、关键词
        project_id = request.data.get('project_id')
        keywords = request.data.get('keywords')
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "项目不存在"}, status=status.HTTP_404_NOT_FOUND)
        files = File.objects.filter(Q(project_id=project_id) & Q(file_name__icontains=keywords))
        folders = Folder.objects.filter(Q(project_id=project_id) & Q(title__icontains=keywords))

        folder_serializer = FolderInfoSerializer(folders, many=True)
        file_serializer = FileInfoSerializer(files, many=True)

        data = {
            "folders": folder_serializer.data,
            "files": file_serializer.data
        }

        return Response(data, status=status.HTTP_200_OK)


# 批量上传文件
class UploadFilesView(FormView):

    form_class = FileFieldForm

    def post(self, request, *args, **kwargs):
        try:

            # form = FileFieldForm(request.POST, request.FILES)

            # 接收参数
            user_id = request.POST.get('user_id')
            folder_id = request.POST.get('folder_id')

            form_class = self.get_form_class()
            form = self.get_form(form_class)
            # 判断表单数据是否合法
            if form.is_valid():
                # 获取多个文件上传的文件列表
                files = request.FILES.getlist('file')
                for f in files:
                    title = f.name
                    size = f.size
                    new_file = File.objects.create(title=title,
                                                   user_id=user_id,
                                                   folder_id=folder_id,
                                                   size=size,
                                                   file=f)
                return JsonResponse({'code': 200, 'msg': '文件上传成功！'})
            else:
                error_messages = form.errors
                return JsonResponse({'code': 400, 'msg': '文件上传失败！', 'error': error_messages})

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '文件上传异常！'})
