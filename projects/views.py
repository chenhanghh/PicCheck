from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from rest_framework.permissions import IsAuthenticated

from common.models import Project, ProjectUser, FolderinProject, FileinProject, User
import os

from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from .serializers import ProjectSerializer, FileAddSerializer, FolderSerializer, FileDelSerializer, FileSerializer, \
    FolderRenameSerializer, FolderInfoSerializer, FileInfoSerializer, ProjectRenameSerializer, ProjectUserSerializer, \
    ProjectDetailSerializer, FileRenameSerializer
from rest_framework.response import Response

import logging

logger = logging.getLogger(__name__)


class AddProjectAPI(generics.CreateAPIView):
    """
    创建项目
    """
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def create(self, request, *args, **kwargs):
        # 解析请求数据
        project_data = request.data

        # 生成并保存邀请码
        project_serializer = self.get_serializer(data=project_data)
        if project_serializer.is_valid():
            project = project_serializer.save()
            project.invitation_code = project.generate_invitation_code()
            project.save()

            # 将当前登录用户添加到项目中，并设置为项目负责人
            project_user = ProjectUser(project=project, user=request.user, user_level='owner')
            project_user.save()

            return Response({'status': 201, 'data': project_serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'status': 400, 'error': project_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class JoinProjectAPI(generics.CreateAPIView):
    """
    通过邀请码加入项目
    """
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def create(self, request, *args, **kwargs):
        # 解析请求数据
        join_data = request.data

        # 获取邀请码
        invitation_code = join_data.get('invitation_code', None)

        if invitation_code:
            # 查找项目
            try:
                project = Project.objects.get(invitation_code=invitation_code)
            except Project.DoesNotExist:
                return Response({'status': 404, 'error': 'Project does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            # 检查用户是否已经加入项目
            if ProjectUser.objects.filter(project=project, user=request.user).exists():
                return Response({'status': 400, 'error': 'User has already joined the project.'}, status=status.HTTP_400_BAD_REQUEST)

            # 将当前登录用户添加到项目中
            project_user = ProjectUser(project=project, user=request.user, user_level='member')
            project_user.save()

            return Response({'status': 200, 'message': 'Successfully join the project.', 'project_id': project.id, 'project_name': project.name}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 400, 'error': 'Missing invitation code.'}, status=status.HTTP_400_BAD_REQUEST)


class UserProjectsAPI(generics.ListAPIView):
    """
    获取当前认证用户所属的所有项目的ID和名称
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # 获取当前认证的用户
            user = request.user

            # 查询用户所属的所有项目
            project_users = ProjectUser.objects.filter(user=user).select_related('project')

            # 构建包含项目ID和名称的列表
            projects_info = [{'id': project_user.project.id, 'name': project_user.project.name, 'user_level': project_user.user_level} for project_user in project_users]

            return Response({'status': 200, 'data': projects_info}, status=status.HTTP_200_OK)

        except ProjectUser.DoesNotExist:
            return Response({'error': '未找到用户所属的项目'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # 捕捉其他意外错误
            return Response({'error': '服务器内部错误: {}'.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExitProjectAPI(generics.DestroyAPIView):
    """
    用户退出项目
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectUserSerializer

    def delete(self, request, *args, **kwargs):
        project_id = kwargs.get('project_id', None)
        if not project_id:
            return Response({'status': 400, 'error': '未提供项目ID'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取项目
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'status': 404, 'error': '项目未找到'}, status=status.HTTP_404_NOT_FOUND)

        # 检查用户是否为项目成员
        try:
            project_user = ProjectUser.objects.get(project=project, user=request.user)
        except ProjectUser.DoesNotExist:
            return Response({'status': 404, 'error': '用户不是该项目的成员'}, status=status.HTTP_404_NOT_FOUND)

        # 阻止项目所有者直接退出（他们应该转让所有权或删除项目）
        if project_user.user_level == 'owner':
            return Response({'status': 403, 'error': '项目所有者不能直接退出项目'}, status=status.HTTP_403_FORBIDDEN)

        # 从项目中删除用户
        project_user.delete()
        return Response({'status': 200, 'message': '用户成功退出项目'}, status=status.HTTP_200_OK)


class ProjectDetailAPI(generics.RetrieveAPIView):
    """
    获取项目所包含的用户信息
    """
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()
    serializer_class = ProjectDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            # 使用 ProjectSerializer 序列化项目信息
            project_serializer = self.get_serializer(instance)
            project_data = project_serializer.data

            # 获取项目中包含的用户信息
            project_users = ProjectUser.objects.filter(project=instance)
            # 使用 ProjectUserSerializer 序列化用户信息
            user_serializer = ProjectUserSerializer(project_users, many=True)
            project_data['users'] = user_serializer.data
            return Response({'status': 200, 'message': project_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': 500, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PromoteMemberToAdminView(generics.UpdateAPIView):
    """
    项目负责人提升普通用户为管理员
    """
    permission_classes = [IsAuthenticated]
    queryset = ProjectUser.objects.all()
    serializer_class = ProjectUserSerializer

    def update(self, request, *args, **kwargs):
        # 获取当前登录用户
        current_user = request.user
        # 获取项目和用户
        project_id = kwargs.get('project_id')
        user_id = kwargs.get('user_id')

        try:
            project_user = ProjectUser.objects.get(project__id=project_id, user__id=current_user.id)
        except ProjectUser.DoesNotExist:
            return Response({'status': 404, "error": "Project user not found"}, status=status.HTTP_404_NOT_FOUND)

        # 验证当前用户是否为项目 owner
        if project_user.user_level == 'owner':
            try:
                user_to_promote = ProjectUser.objects.get(project__id=project_id, user__id=user_id, user_level='member')
            except ProjectUser.DoesNotExist:
                return Response({'status': 404, "error": "User not found or not a member"},
                                status=status.HTTP_404_NOT_FOUND)

            # 将 member 提升为 admin
            user_to_promote.user_level = 'admin'
            user_to_promote.save()

            serializer = self.get_serializer(user_to_promote)
            return Response({'status': 200, 'message': serializer.data}, status=status.HTTP_200_OK)

        return Response({'status': 403, "error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)


class DemoteAdminToMemberView(generics.UpdateAPIView):
    """
    项目负责人降级管理员为普通用户
    """
    permission_classes = [IsAuthenticated]
    queryset = ProjectUser.objects.all()
    serializer_class = ProjectUserSerializer

    def update(self, request, *args, **kwargs):
        # 获取当前登录用户
        current_user = request.user

        # 获取项目和用户
        project_id = kwargs.get('project_id')
        user_id = kwargs.get('user_id')

        try:
            project_user = ProjectUser.objects.get(project__id=project_id, user__id=current_user.id)
        except ProjectUser.DoesNotExist:
            return Response({'status': 404, "error": "Project user not found"}, status=status.HTTP_404_NOT_FOUND)

        # 验证当前用户是否为项目 owner
        if project_user.user_level == 'owner':
            try:
                admin_to_demote = ProjectUser.objects.get(project__id=project_id, user__id=user_id, user_level='admin')
            except ProjectUser.DoesNotExist:
                return Response({'status': 404, "error": "User not found or not an admin"}, status=status.HTTP_404_NOT_FOUND)

            # 将 admin 降级为 member
            admin_to_demote.user_level = 'member'
            admin_to_demote.save()

            serializer = self.get_serializer(admin_to_demote)
            return Response({'status': 200, 'message': serializer.data}, status=status.HTTP_200_OK)

        return Response({'status': 403, "error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)


class TransferOwnershipView(generics.UpdateAPIView):
    """
    项目负责人将项目负责人角色转让给项目所包含的其中一个用户
    """
    permission_classes = [IsAuthenticated]
    queryset = ProjectUser.objects.all()
    serializer_class = ProjectUserSerializer

    def update(self, request, *args, **kwargs):
        # 获取当前登录用户
        current_user = request.user

        # 获取项目和用户
        project_id = kwargs.get('project_id')
        user_id_to_transfer = kwargs.get('user_id_to_transfer')

        try:
            project_user = ProjectUser.objects.get(project__id=project_id, user__id=current_user.id)
        except ProjectUser.DoesNotExist:
            return Response({'status': 404, "error": "Project user not found"}, status=status.HTTP_404_NOT_FOUND)

        # 验证当前用户是否为项目 owner
        if project_user.user_level == 'owner':
            try:
                user_to_transfer = ProjectUser.objects.get(project__id=project_id, user__id=user_id_to_transfer)
            except ProjectUser.DoesNotExist:
                return Response({'status': 404, "error": "User not found or not a member of the project"}, status=status.HTTP_404_NOT_FOUND)

            # 将当前 owner 的角色转让给另一个用户
            project_user.user_level = 'member'
            project_user.save()

            user_to_transfer.user_level = 'owner'
            user_to_transfer.save()

            serializer_current_owner = self.get_serializer(project_user)
            serializer_new_owner = self.get_serializer(user_to_transfer)

            return Response({
                'status': 200,
                'message': f"Ownership transferred from {current_user.username} to {user_to_transfer.user.username}",
                'current_owner': serializer_current_owner.data,
                'new_owner': serializer_new_owner.data
            }, status=status.HTTP_200_OK)

        return Response({'status': 403, "error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)


class RemoveUserFromProjectView(generics.DestroyAPIView):
    """
    项目管理员或负责人从项目中删除普通用户
    """
    permission_classes = [IsAuthenticated]
    queryset = ProjectUser.objects.all()
    serializer_class = ProjectUserSerializer

    def destroy(self, request, *args, **kwargs):
        # 获取当前登录用户
        current_user = request.user

        # 获取项目和用户
        project_id = kwargs.get('project_id')
        user_id_to_remove = kwargs.get('user_id_to_remove')

        try:
            project_user = ProjectUser.objects.get(project__id=project_id, user__id=current_user.id)
        except ProjectUser.DoesNotExist:
            return Response({'status': 404, "error": "Project user not found"}, status=status.HTTP_404_NOT_FOUND)

        # 验证当前用户是否为项目 owner 或 admin
        if project_user.user_level in ['owner', 'admin']:
            try:
                user_to_remove = ProjectUser.objects.get(project__id=project_id, user__id=user_id_to_remove,
                                                         user_level='member')
            except ProjectUser.DoesNotExist:
                return Response({'status': 404, "error": "User not found or not a member of the project"},
                                status=status.HTTP_404_NOT_FOUND)

            # 从项目中删除普通用户
            user_to_remove.delete()

            return Response(
                {'status': 200, 'message': f"User {user_to_remove.user.username} removed from the project"},
                status=status.HTTP_200_OK)

        return Response({'status': 403, "error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)


class AddFolderAPI(generics.CreateAPIView):
    """
    新建文件夹
    """
    permission_classes = [IsAuthenticated]

    queryset = FolderinProject.objects.all()
    serializer_class = FolderSerializer
    print(serializer_class['title'], serializer_class['project'])

    def create(self, request, *args, **kwargs):
        try:
            # 调用原始的 create 方法
            return super().create(request, *args, **kwargs)
        except ValueError as e:
            # 捕获特定错误，如数据验证错误
            return Response({'status': 400, "error": f"值错误: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # 捕获其他所有可能的异常
            return Response({'status': 500, "error": f"服务器内部错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 上传文件
class UploadFileAPI(generics.CreateAPIView):
    """
    上传文件
    """

    queryset = FileinProject.objects.all()
    serializer_class = FileAddSerializer
    # 视图能解析多部份表单数据和常规表单数据（如文件上传和文本字段）
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]  # 控制访问权限

    def perform_create(self, serializer):
        # 获取上传的文件对象列表
        files = self.request.FILES.getlist('file')

        # 处理多个文件
        for file in files:
            # 设置文件名称和大小到 validated_data 中
            serializer.validated_data['title'] = file.name
            serializer.validated_data['file_size'] = file.size
            serializer.validated_data['type'] = file.name.split(".")[-1]

            # 关联上传的文件与当前登录用户
            serializer.validated_data['user'] = self.request.user

            # 调用父类的 perform_create 方法保存文件
            super().perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DelFileAPI(APIView):
    """
    批量删除文件
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FileDelSerializer(data=request.data)
        if serializer.is_valid():
            file_ids = serializer.validated_data['file_ids']
            # 执行批量删除操作
            try:
                deleted_files = FileinProject.objects.filter(id__in=file_ids)
                for file in deleted_files:
                    # 删除服务器本地文件系统中的文件
                    file_path = 'media/' + file.file.name
                    # 删除存储文件
                    os.remove(file_path)
                    # 删除数据库中的文件记录
                    file.delete()

                return Response({'status': 200, "message": "Delete file successfully."}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'status': 500, "message": "File delete error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'status': 400, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class FileRetrieveAPI(generics.RetrieveAPIView):
    """
    获取文件
    """
    permission_classes = [IsAuthenticated]
    queryset = FileinProject.objects.all()
    serializer_class = FileSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            # 调用原始的 retrieve 方法获取文件
            return super().retrieve(request, *args, **kwargs)
        except FileinProject.DoesNotExist:
            # 如果文件不存在，返回 404 错误
            return Response({'status': 404, "error": "文件未找到"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # 捕捉其他意外错误
            return Response({'status': 500, "error": f"服务器内部错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DownloadFileAPI(APIView):
    """
    文件下载
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        try:
            # 通过文件ID查找文件
            file = FileinProject.objects.get(pk=file_id)

            # 文件路径
            file_path = file.file.path

            # 创建响应，将文件作为附件发送
            response = FileResponse(open(file_path, 'rb'), as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{file.title}"'
            response.data = {'status': 200, 'message': '文件下载成功'}

            return response
        except FileinProject.DoesNotExist:
            return Response({'status': 404, 'error': '文件未找到'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'status': 500, 'error': f'服务器错误: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FileRenameAPI(APIView):
    """
    文件重命名
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, file_id):
        try:
            file = FileinProject.objects.get(pk=file_id)
        except FileinProject.DoesNotExist:
            return Response({'error': '文件未找到'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FileRenameSerializer(data=request.data)
        if serializer.is_valid():
            file.title = serializer.validated_data['new_title']
            file.save()
            return Response({'message': '文件重命名成功'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 删除文件夹
def del_folder(folder_id):
    # 获取要删除的文件夹对象
    folder = FolderinProject.objects.get(id=folder_id)

    # 递归删除文件夹内的子文件夹和子文件
    def delete_contents(folder):
        # 子文件夹
        for subfolder in FolderinProject.objects.filter(parent_folder_id=folder.id):
            delete_contents(subfolder)
            # 删除与子文件夹相关的内容
            subfolder.delete()
        # 子文件
        for file in FileinProject.objects.filter(folder_id=folder.id):
            filepath = 'media/' + file.file.name
            # 删除存储文件
            os.remove(filepath)
            # 删除数据库中记录
            file.delete()

    delete_contents(folder)
    # 删除数据库中与该文件夹相关的内容
    folder.delete()


class DelFolderAPI(APIView):
    """
    删除文件夹
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        folder_ids = request.data.get('folder_ids', [])
        print(folder_ids)

        for folder_id in folder_ids:
            try:
                del_folder(folder_id)
                print('dadada')
            except Exception as e:
                return Response({'status': 500, "message": "Folder delete error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'status': 200, "message": "Delete folder successfully."}, status=status.HTTP_200_OK)


class FolderRenameAPI(APIView):
    """
    文件夹重命名
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, folder_id):
        folder = FolderinProject.objects.get(pk=folder_id)
        serializer = FolderRenameSerializer(data=request.data)

        if serializer.is_valid():
            new_title = serializer.validated_data['new_title']
            folder.title = new_title
            folder.save()
            return Response({"message": "The folder was successfully renamed."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FolderInfoAPI(APIView):
    """
    获取文件夹信息
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, folder_id):
        try:
            folder = FolderinProject.objects.get(pk=folder_id)
        except FolderinProject.DoesNotExist:
            return Response({'status': 404, "message": "Folder foes not exist."}, status=status.HTTP_404_NOT_FOUND)

        subfolders = FolderinProject.objects.filter(parent_folder_id=folder_id)
        files = FileinProject.objects.filter(folder_id=folder_id)

        subfolder_serializer = FolderInfoSerializer(subfolders, many=True)
        file_serializer = FileInfoSerializer(files, many=True)

        content = subfolder_serializer.data + file_serializer.data

        return Response({'status': 200, 'data': content}, status=status.HTTP_200_OK)


class ProjectInfoAPI(APIView):
    """
    获取项目根文件夹和跟文件信息
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'status': 404, "message": "Project does not exist."}, status=status.HTTP_404_NOT_FOUND)

        subfolders = FolderinProject.objects.filter(parent_folder_id=None, project_id=project_id)
        files = FileinProject.objects.filter(folder_id=None, project_id=project_id)

        subfolder_serializer = FolderInfoSerializer(subfolders, many=True)
        file_serializer = FileInfoSerializer(files, many=True)

        content = subfolder_serializer.data + file_serializer.data

        return Response({'status': 200, 'data': content}, status=status.HTTP_200_OK)


class ProjectRenameAPI(APIView):
    """
    项目重命名
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        serializer = ProjectRenameSerializer(data=request.data)

        if serializer.is_valid():
            new_name = serializer.validated_data['new_name']
            project.name = new_name
            project.save()
            return Response({'status': 200, "message": "The project was successfully renamed."}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 400, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class DelProjectAPI(APIView):
    """
    删除项目
    """
    permission_classes = [IsAuthenticated]

    def post(self, project_id):

        try:
            project = Project.objects.get(pk=project_id)

            with transaction.atomic():
                # 删除项目内所有文件夹、文件
                folders = FolderinProject.objects.filter(project_id=project_id, parent_folder_id=None).values('id')
                folderslist = list(folders)
                for f in folderslist:
                    del_folder(f['id'])
                # 先删除 ProjectUser 里面的记录
                ProjectUser.objects.filter(project_id=project_id).delete()
                # 再删除项目记录
                project.delete()
            return Response({'status': 200, "message": "Delete project successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 500, "message": "Project delete error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchAPI(APIView):
    """
    在项目内搜索文件或文件夹
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取项目id、关键词
        project_id = request.data.get('project_id')
        keywords = request.data.get('keywords')
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "Project does not exist."}, status=status.HTTP_404_NOT_FOUND)
        files = FileinProject.objects.filter(Q(project_id=project_id) & Q(file_name__icontains=keywords))
        folders = FolderinProject.objects.filter(Q(project_id=project_id) & Q(title__icontains=keywords))

        folder_serializer = FolderInfoSerializer(folders, many=True)
        file_serializer = FileInfoSerializer(files, many=True)

        data = {
            "folders": folder_serializer.data,
            "files": file_serializer.data
        }

        return Response(data, status=status.HTTP_200_OK)
