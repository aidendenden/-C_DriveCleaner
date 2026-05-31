# C Drive Cleaner

当前版本：`v1.0.0`

一个 Windows C 盘清理工具，使用 Python 标准库实现，支持图形界面和命令行。

## 功能

- 扫描 C 盘常见临时目录、浏览器缓存、着色器缓存、崩溃报告等可清理空间
- 默认只清理白名单目录，不扫描或删除任意系统目录
- 按文件年龄过滤，避免删除刚创建或正在使用的文件
- 自动跳过符号链接、目录联接、锁定文件和无权限文件
- GUI 模式需要先扫描、再确认清理
- CLI 模式默认只扫描，执行清理必须显式传入 `--clean`
- 支持深度清理预设，覆盖缩略图缓存、旧日志、系统转储、驱动安装器缓存、旧系统安装目录等
- GUI 和 CLI 支持中英文切换，默认中文

## 运行

Windows 上建议使用 Python Launcher：

```powershell
py c_drive_cleaner.py
```

无参数运行会打开图形界面。

也可以直接双击无控制台窗口启动：

```text
start_cleaner.vbs
```

如果需要查看错误输出或使用命令行参数，可以运行：

```text
start_cleaner.bat
```

英文界面：

```powershell
py c_drive_cleaner.py --lang en
```

中文界面：

```powershell
py c_drive_cleaner.py --lang zh
```

命令行扫描：

```powershell
py c_drive_cleaner.py --scan
```

列出分类：

```powershell
py c_drive_cleaner.py --list
```

清理默认分类：

```powershell
py c_drive_cleaner.py --clean
```

跳过交互确认：

```powershell
py c_drive_cleaner.py --clean --yes
```

只清理指定分类：

```powershell
py c_drive_cleaner.py --clean --categories user_temp,browser_cache
```

包含高级分类：

```powershell
py c_drive_cleaner.py --scan --all
```

深度扫描：

```powershell
py c_drive_cleaner.py --scan --deep
```

深度清理会先扫描并再次确认：

```powershell
py c_drive_cleaner.py --clean --deep
```

系统工具项，例如 DISM 组件存储清理，只在 `--all` 或显式指定分类时出现：

```powershell
py c_drive_cleaner.py --clean --categories component_store
```

## 清理分类

| key | 分类 | 层级 |
| --- | --- | --- |
| `user_temp` | 用户临时文件 | 默认 |
| `windows_temp` | Windows 临时文件 | 默认 |
| `browser_cache` | Chrome、Edge、Edge WebView2、Firefox 缓存 | 默认 |
| `shader_cache` | DirectX、NVIDIA、AMD 着色器缓存 | 默认 |
| `crash_reports` | 崩溃和错误报告 | 默认 |
| `recycle_bin` | 回收站 | 深度 |
| `thumbnail_cache` | Explorer 缩略图和图标缓存 | 深度 |
| `windows_logs` | 旧 Windows 日志、ETL、CBS 压缩日志 | 深度 |
| `system_dumps` | `MEMORY.DMP` 和 Minidump 系统转储 | 深度 |
| `driver_installers` | NVIDIA/AMD 驱动安装器缓存 | 深度 |
| `delivery_optimization` | 传递优化缓存 | 深度 |
| `windows_update_download` | Windows 更新下载缓存 | 深度 |
| `windows_old` | 旧 Windows 安装目录 | 深度 |
| `upgrade_leftovers` | Windows 升级残留目录 | 深度 |
| `component_store` | DISM 组件存储清理 | 系统工具 |

## 安全边界

这个工具不会清理磁盘根目录、用户目录根、`LOCALAPPDATA` 根、`APPDATA` 根、`ProgramData` 根或 `Windows` 根目录。每个文件分类只删除目标目录下超过保留天数的普通文件，并在删除后尝试移除空目录。

深度分类默认不勾选。GUI 里可以点 `Deep preset` 选择默认项和深度项；CLI 用 `--deep`。清理 Windows 更新相关缓存、`Windows.old` 或升级残留前，建议先确认系统没有正在安装或回滚更新。部分系统目录需要管理员权限，否则会显示为跳过或失败。

`component_store` 不会手动删除 WinSxS 文件，而是调用 Windows 自带的：

```powershell
dism.exe /Online /Cleanup-Image /StartComponentCleanup
```

这个操作可能运行数分钟，通常需要管理员权限。

## 测试

```powershell
py -m unittest discover -s tests -v
```
