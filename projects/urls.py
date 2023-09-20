from django.urls import path

from projects import views
from projects.views import AddProjectView, DelProjectView, AddFolderView, UploadFilesView, UploadFileView, DelFileView, \
    RenFileView, FileInfoView, DelFolderView, FolderInfoView, RenFolderView, ProjectInfoView, RenProjectView, SearchView

# from users.views import

# 路由 就是指：根据HTTP请求的url路径，设置由哪个函数来处理这个请求。
# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 创建项目
    path('api/addproject/', AddProjectView.as_view()),
    # 删除项目
    path('api/delproject/', DelProjectView.as_view()),
    # 获取项目文件夹目录
    path('api/projectinfo/', ProjectInfoView.as_view()),
    # 项目重命名
    path('api/renproject/', RenProjectView.as_view()),

    # 新建文件夹
    path('api/addfolder/', AddFolderView.as_view()),
    # 删除文件夹
    path('api/delfolder/', DelFolderView.as_view()),
    # 获取文件夹内文件目录
    path('api/folderinfo/', FolderInfoView.as_view()),
    # 文件夹重命名
    path('api/renfolder/', RenFolderView.as_view()),

    # 上传文件
    path('uploads/', UploadFilesView.as_view()),
    path('upload/', UploadFileView.as_view()),
    # 删除文件
    path('api/delfile/', DelFileView.as_view()),
    # 文件重命名
    path('api/renfile/', RenFileView.as_view()),
    # 获取文件
    path('api/fileinfo/', FileInfoView.as_view()),

    # 搜索文件
    path('search/', SearchView.as_view()),

]

