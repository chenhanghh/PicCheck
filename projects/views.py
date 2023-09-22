from django.views import View
from django.db import transaction
from django.db.models import Count, Q
from common.models import Project, ProjectUser, Folder, File
import json
from django.http import JsonResponse, HttpResponse, FileResponse

import logging

from projects.forms import FileFieldForm
from django.views.generic.edit import FormView

import os

logger = logging.getLogger('django')


# 创建项目
class AddProjectView(View):
    def post(self, request):
        try:
            # 涉及到多表操作 对数据库的操作在一个事务中进行 执行失败，事务回滚
            with transaction.atomic():
                # 获取项目名称、包含用户
                name = request.POST.get('name')
                userlist = request.POST.get('userlist')
                # 解析字符串
                userlist = json.loads(userlist)
                new_project = Project.objects.create(name=name,
                                                     # 写入json格式的用户数据到 userlist 中
                                                     userlist=json.dumps(userlist)
                                                     )
                batch = [ProjectUser(project_id=new_project.id,
                                     user_id=user['id'])
                         for user in userlist]
                # 在多对多关系表中，添加多条关联记录
                ProjectUser.objects.bulk_create(batch)
            return JsonResponse({'code': 200, 'msg': '项目新建成功！', 'id': new_project.id})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '项目新建异常！'})


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


# 删除项目
class DelProjectView(View):
    def post(self, request):
        # 获取项目id
        project_id = request.POST.get('project_id')
        try:
            project = Project.objects.get(id=project_id)

            with transaction.atomic():
                # 删除项目内所有文件夹、文件
                folders = Folder.objects.filter(project_id=project_id).values('id')
                folderslist = list(folders)
                for f in folderslist:
                    del_folder(f['id'])
                # 先删除 ProjectUser 里面的记录
                ProjectUser.objects.filter(project_id=project_id).delete()
                # 再删除项目记录
                project.delete()
            return JsonResponse({'code': 200, 'msg': '项目删除成功！'})

        except Project.DoesNotExist:
            return JsonResponse({'code': 400, 'msg': f'id 为`{project_id}`的项目不存在'})

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '项目删除异常！'})


# 新建文件夹
class AddFolderView(View):
    def post(self, request):
        try:
            # 获取文件夹名、所属项目id、所属父文件夹id
            title = request.POST.get('title')
            project_id = request.POST.get('project_id')
            parent_folder_id = request.POST.get('parent_folder_id')
            new_folder = Folder.objects.create(title=title, project_id=project_id, parent_folder_id=parent_folder_id)
            return JsonResponse({'code': 200, 'msg': '文件夹新建成功！', 'id': new_folder.id})

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '文件夹新建异常！'})


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


# 上传单个文件
class UploadFileView(View):
    def post(self, request):
        try:
            # 接收参数
            user_id = request.POST.get('user_id')
            project_id = request.POST.get('project_id')
            folder_id = request.POST.get('folder_id')
            file = request.FILES.get('file')
            title = file.name
            size = file.size
            if File.objects.filter(title=title, folder_id=folder_id):
                return JsonResponse({'code': 400, 'msg': '文件名已存在，请重新上传或将文件重命名！'})
            else:
                new_file = File.objects.create(title=title,
                                               user_id=user_id,
                                               project_id=project_id,
                                               folder_id=folder_id,
                                               size=size,
                                               file=file)

                return JsonResponse({'code': 200, 'msg': '文件上传成功！', 'id': new_file.id})

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '文件上传异常！'})


# 批量删除文件
class DelFileView(View):
    def post(self, request):
        # 获取要删除的所有文件id
        id_list = request.POST.get('id_list')
        try:
            # 解析字符串
            id_list = json.loads(id_list)
            for f_id in id_list:
                file_id = f_id['id']
                file = File.objects.get(id=file_id)
                # 拼接文件的完整路径
                filepath = 'media/' + file.file.name
                # 删除存储文件
                os.remove(filepath)
                # 删除数据库中记录
                file.delete()
            return JsonResponse({'code': 200, 'msg': '文件删除成功！'})

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '文件删除异常！'})


# 文件重命名
class RenFileView(View):
    def post(self, request):
        # 获取文件id及所属文件夹id、所属项目id
        file_id = request.POST.get('file_id')
        folder_id = request.POST.get('folder_id')
        project_id = request.POST.get('project_id')
        try:
            new_title = request.POST.get('new_title')
            file = File.objects.get(id=file_id)

            if File.objects.filter(title=new_title, folder_id=folder_id, project_id=project_id):
                return JsonResponse({'code': 400, 'msg': '文件名已存在，请重新命名！'})
            else:
                filepath = 'media/' + file.file.name
                # 数据库文件名重命名
                file.title = new_title
                file.file.name = os.path.dirname(file.file.name) + '/' + new_title
                file.save()

                new_filepath = 'media/' + file.file.name
                # 文件保存路径下重命名
                if os.path.exists(new_filepath):
                    # 如果新文件路径已存在，添加数字后缀
                    base_name, ext = os.path.splitext(new_filepath)
                    counter = 1
                    while os.path.exists(new_filepath):
                        new_filepath = f"{base_name}_{counter}{ext}"
                        parts = new_title.split(".")
                        file.file.name = os.path.dirname(file.file.name) + '/' + f"{parts[0]}_.{counter}{parts[1]}"
                        file.save()
                        counter += 1
                os.rename(filepath, new_filepath)
            return JsonResponse({'code': 200, 'msg': '文件重命名成功！'})

        except File.DoesNotExist:
            return JsonResponse({'code': 400, 'msg': f'id 为`{file_id}`的文件不存在'})

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '文件重命名异常！'})


# 文件获取
class FileInfoView(View):
    def post(self, request):
        # 获取文件id
        file_id = request.POST.get('file_id')
        try:
            file = File.objects.get(id=file_id)
            filepath = 'media/' + file.file.name

            # 使用FileResponse返回文件给用户
            return FileResponse(open(filepath, 'rb'))
        except File.DoesNotExist:
            return JsonResponse({'code': 400, 'msg': f'id 为`{file_id}`的文件不存在'})


# 批量删除文件夹，文件夹内文件也同步删除
class DelFolderView(View):
    def post(self, request):
        # 获取要删除的所有文件夹id
        id_list = request.POST.get('id_list')
        try:
            # 解析字符串
            id_list = json.loads(id_list)
            for f_id in id_list:
                del_folder(f_id['id'])
            return JsonResponse({'code': 200, 'msg': '文件夹删除成功！'})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '文件夹删除异常！'})


# 获取文件夹内目录信息
class FolderInfoView(View):
    def post(self, request):
        # 获取文件夹id
        folder_id = request.POST.get('folder_id')
        try:
            # 子文件
            files = File.objects.filter(folder_id=folder_id).values('id', 'title', 'create_date',
                                                                    'user_id', 'size')
            fileslist = list(files)
            # 子文件夹
            folders = Folder.objects.filter(parent_folder_id=folder_id).values('id', 'title', 'create_date')
            folderslist = list(folders)
            return JsonResponse(
                {'code': 200, 'msg': '文件夹获取成功！', 'fileslist': fileslist, 'folderslist': folderslist})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '文件夹获取异常！'})


# 文件夹重命名
class RenFolderView(View):
    def post(self, request):
        # 获取文件夹id、新名字
        folder_id = request.POST.get('folder_id')
        try:
            folder = Folder.objects.get(id=folder_id)
            folder.title = request.POST.get('new_title')
            folder.save()
            return JsonResponse({'code': 200, 'msg': '文件夹重命名成功！'})
        except Folder.DoesNotExist:
            return {'code': 400, 'msg': f'id 为`{folder_id}`的文件夹不存在'}


# 获取项目内目录信息
class ProjectInfoView(View):
    def post(self, request):
        # 获取项目id
        project_id = request.POST.get('project_id')
        try:
            folders = Folder.objects.filter(project_id=project_id).annotate(file_count=Count('id')).values(
                'id', 'create_date', 'file_count'
            )
            folderslist = list(folders)
            files = File.objects.filter(folder_id='null').values('id', 'title', 'create_date',
                                                                 'user_id', 'size')
            fileslist = list(files)
            return JsonResponse({'code': 200, 'msg': '文件夹获取成功！', 'folderslist': folderslist, 'fileslist': fileslist})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '文件夹获取异常！'})


# 项目重命名
class RenProjectView(View):
    def post(self, request):
        # 获取项目id、新名字
        project_id = request.POST.get('project_id')
        try:
            project = Project.objects.get(id=project_id)
            project.name = request.POST.get('new_name')
            project.save()
            return JsonResponse({'code': 200, 'msg': '项目重命名成功！'})
        except Project.DoesNotExist:
            return {'code': 400, 'msg': f'id 为`{project_id}`的项目不存在'}


# 搜索文件名
class SearchView(View):
    def post(self, request):
        # 获取项目id、关键词
        keywords = request.POST.get('keywords')
        project_id = request.POST.get('project_id')
        try:
            files = File.objects.filter(Q(project_id=project_id) & Q(title__icontains=keywords)).values(
                'id', 'title', 'create_date', 'user_id', 'size'
            )
            fileslist = list(files)
            return JsonResponse({'code': 200, 'msg': '文件搜索成功！', 'file_list': fileslist})
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'msg': '文件搜索异常！'})
