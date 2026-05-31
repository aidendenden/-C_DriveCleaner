# C Drive Cleaner v1.0.0

首个正式版本。

## 功能

- 图形界面和命令行双模式
- 中英文界面切换，默认中文
- 隐藏控制台窗口的 `start_cleaner.vbs` 启动器
- 默认清理：用户临时文件、Windows 临时文件、浏览器缓存、着色器缓存、崩溃报告
- 深度清理：回收站、缩略图/图标缓存、旧 Windows 日志、系统崩溃转储、GPU 驱动安装器缓存、Windows 更新缓存、旧 Windows 安装和升级残留
- 系统工具项：通过 DISM 执行组件存储清理，不手动删除 WinSxS
- 删除前必须扫描和确认
- 自动跳过链接、联接、锁定文件、无权限文件和过宽系统目录

## 使用

推荐下载 Windows zip 包，解压后运行：

```text
CDriveCleaner.exe
```

如使用源码运行：

```powershell
py c_drive_cleaner.py
```
