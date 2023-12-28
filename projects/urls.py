from django.urls import path

from projects.views import AddProjectAPI, UploadFileAPI, AddFolderAPI, DelFileAPI, FileRetrieveAPI, DelFolderAPI, \
    FolderRenameAPI, FolderInfoAPI, ProjectInfoAPI, ProjectRenameAPI, DelProjectAPI, SearchAPI, JoinProjectAPI, \
    ProjectDetailAPI, PromoteMemberToAdminView, DemoteAdminToMemberView, TransferOwnershipView, \
    RemoveUserFromProjectView, ExitProjectAPI, UserProjectsAPI, FileRenameAPI, DownloadFileAPI

# 路由 就是指：根据HTTP请求的url路径，设置由哪个函数来处理这个请求。
# urlpatterns 列表：Django 的 url 路由的入口
urlpatterns = [

    # 创建项目
    path('api/addproject/', AddProjectAPI.as_view()),
    # 通过邀请码加入项目
    path('api/joinproject/', JoinProjectAPI.as_view()),
    # 获取项目所包含的用户信息
    path('api/userinfo/<int:pk>/', ProjectDetailAPI.as_view()),

    path('api/<int:project_id>/promote/<int:user_id>/', PromoteMemberToAdminView.as_view()),
    path('api/<int:project_id>/demote/<int:user_id>/', DemoteAdminToMemberView.as_view()),
    path('api/<int:project_id>/transfer-ownership/<int:user_id_to_transfer>/', TransferOwnershipView.as_view()),
    path('api/<int:project_id>/remove-user/<int:user_id_to_remove>/', RemoveUserFromProjectView.as_view()),

    # 退出项目
    path('api/exit/<int:project_id>/', ExitProjectAPI.as_view()),
    # 获取项目id和名称
    path('api/user_projects/', UserProjectsAPI.as_view()),

    # 删除项目
    path('api/delproject/<int:project_id>/', DelProjectAPI.as_view()),
    # 获取项目文件夹目录
    path('api/projectinfo/<int:project_id>/', ProjectInfoAPI.as_view()),
    # 项目重命名
    path('api/renproject/<int:project_id>/', ProjectRenameAPI.as_view()),

    # 新建文件夹
    path('api/addfolder/', AddFolderAPI.as_view()),
    # 删除文件夹
    path('api/delfolder/', DelFolderAPI.as_view()),
    # 获取文件夹内文件目录
    path('api/folderinfo/<int:folder_id>/', FolderInfoAPI.as_view()),
    # 文件夹重命名
    path('api/renfolder/<int:folder_id>/', FolderRenameAPI.as_view()),

    # 上传文件
    path('api/upload/', UploadFileAPI.as_view()),
    # 删除文件
    path('api/files/bulk_delete/', DelFileAPI.as_view()),
    # 获取文件
    path('api/file/<int:pk>/', FileRetrieveAPI.as_view()),
    # 下载文件
    path('api/download-file/<int:file_id>/', DownloadFileAPI.as_view()),
    # 文件重命名
    path('api/rename/<int:file_id>/', FileRenameAPI.as_view()),

    # 搜索文件
    path('search/', SearchAPI.as_view()),

]

