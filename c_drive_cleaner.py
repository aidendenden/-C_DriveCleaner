from __future__ import annotations

import argparse
import ctypes
import fnmatch
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable


APP_NAME = "C Drive Cleaner"
VERSION = "1.0.0"
DEFAULT_DRIVE = "C:"
SIZE_UNITS = ("B", "KB", "MB", "GB", "TB")
DEFAULT_LANG = "zh"


TEXT = {
    "en": {
        "app_name": "C Drive Cleaner",
        "lang_label": "Language",
        "lang_chinese": "Chinese",
        "lang_english": "English",
        "gui.scan": "Scan",
        "gui.clean_selected": "Clean selected",
        "gui.default_preset": "Default preset",
        "gui.deep_preset": "Deep preset",
        "gui.clear_selection": "Clear selection",
        "gui.note": (
            "Deep items are off by default. The cleaner only uses allow-listed paths and "
            "skips links, junctions, locked files, and broad system roots."
        ),
        "gui.col_use": "Use",
        "gui.col_tier": "Tier",
        "gui.col_category": "Category",
        "gui.col_size": "Cleanable size",
        "gui.col_files": "Files",
        "gui.col_status": "Status",
        "gui.log": "Log",
        "gui.initial_log": "Click Scan first. Cleanup requires a second confirmation.",
        "gui.starting_scan": "Starting scan...",
        "gui.scanning": "Scanning {label}",
        "gui.starting_cleanup": "Starting cleanup...",
        "gui.cleaning": "Cleaning {label}",
        "gui.scan_complete": "Scan complete.",
        "gui.cleanup_complete": "Cleanup complete.",
        "gui.select_one": "Select at least one item.",
        "gui.scan_first": "Scan first, then clean.",
        "gui.nothing_selected": "Selected items have nothing cleanable.",
        "gui.cancelled": "Cleanup cancelled by user.",
        "gui.confirm": "Clean {count} files and reclaim about {size}?",
        "gui.warnings": "Warnings",
        "gui.and_more": "and {count} more",
        "gui.no_path": "No matching path found",
        "gui.skipped_locked": "skipped locked/no-access items: {count}",
        "gui.skipped_links": "skipped links/junctions: {count}",
        "gui.deleted_summary": "{label}: deleted {files} files, freed {size}",
        "gui.removed_empty": "removed {count} empty folders",
        "gui.failed": "failed {count}",
        "tier.default": "default",
        "tier.deep": "deep",
        "tier.system": "system",
        "cli.category": "Category",
        "cli.files": "Files",
        "cli.size": "Size",
        "cli.location": "Location",
        "cli.deleted": "Deleted",
        "cli.freed": "Freed",
        "cli.status": "Status",
        "cli.done": "done",
        "cli.partial_failure": "partial failure: {count}",
        "cli.note": "note",
        "cli.warning": "Warning",
        "cli.cancelled": "Cancelled.",
        "cli.no_cleanable": "No cleanable items were found.",
        "cli.confirm": "Clean {count} files and reclaim about {size}? Type yes to continue: ",
        "cli.skipped_locked": "skipped locked/no-access items: {count}",
        "cli.skipped_links": "skipped links/junctions: {count}",
        "admin_warning": "Some selected items require administrator rights; locked or protected files may fail.",
        "component_store_scan": "Size is not estimated here. DISM will reclaim safe component-store data during cleanup.",
        "component_store_admin": "Administrator rights are required to run this cleanup.",
        "dism_completed": "DISM component-store cleanup completed.",
    },
    "zh": {
        "app_name": "C盘清理工具",
        "lang_label": "语言",
        "lang_chinese": "中文",
        "lang_english": "English",
        "gui.scan": "扫描",
        "gui.clean_selected": "清理选中项",
        "gui.default_preset": "默认预设",
        "gui.deep_preset": "深度预设",
        "gui.clear_selection": "清空选择",
        "gui.note": "深度项目默认关闭。工具只使用白名单路径，并跳过链接、联接、锁定文件和过宽系统根目录。",
        "gui.col_use": "选择",
        "gui.col_tier": "层级",
        "gui.col_category": "分类",
        "gui.col_size": "可清理大小",
        "gui.col_files": "文件数",
        "gui.col_status": "状态",
        "gui.log": "日志",
        "gui.initial_log": "请先点击“扫描”。清理前会再次确认。",
        "gui.starting_scan": "开始扫描...",
        "gui.scanning": "扫描 {label}",
        "gui.starting_cleanup": "开始清理...",
        "gui.cleaning": "清理 {label}",
        "gui.scan_complete": "扫描完成。",
        "gui.cleanup_complete": "清理完成。",
        "gui.select_one": "请至少选择一个项目。",
        "gui.scan_first": "请先扫描，再清理。",
        "gui.nothing_selected": "选中项目没有可清理内容。",
        "gui.cancelled": "用户取消清理。",
        "gui.confirm": "将清理 {count} 个文件，预计释放 {size}。",
        "gui.warnings": "警告",
        "gui.and_more": "等 {count} 项",
        "gui.no_path": "未找到匹配路径",
        "gui.skipped_locked": "跳过锁定/无权限项: {count}",
        "gui.skipped_links": "跳过链接/联接: {count}",
        "gui.deleted_summary": "{label}: 删除 {files} 个文件，释放 {size}",
        "gui.removed_empty": "移除 {count} 个空文件夹",
        "gui.failed": "失败 {count} 个",
        "tier.default": "默认",
        "tier.deep": "深度",
        "tier.system": "系统",
        "cli.category": "分类",
        "cli.files": "文件数",
        "cli.size": "大小",
        "cli.location": "路径",
        "cli.deleted": "删除",
        "cli.freed": "释放空间",
        "cli.status": "状态",
        "cli.done": "完成",
        "cli.partial_failure": "部分失败: {count}",
        "cli.note": "提示",
        "cli.warning": "警告",
        "cli.cancelled": "已取消。",
        "cli.no_cleanable": "没有发现可清理项目。",
        "cli.confirm": "将清理 {count} 个文件，预计释放 {size}。输入 yes 继续: ",
        "cli.skipped_locked": "跳过锁定/无权限项: {count}",
        "cli.skipped_links": "跳过链接/联接: {count}",
        "admin_warning": "部分选中项目需要管理员权限；锁定或受保护文件可能会失败。",
        "component_store_scan": "此处不估算大小。DISM 会在清理时回收安全的组件存储数据。",
        "component_store_admin": "运行此清理需要管理员权限。",
        "dism_completed": "DISM 组件存储清理已完成。",
        "target.user_temp.label": "用户临时文件",
        "target.user_temp.description": "当前用户 TEMP/TMP 中超过保留天数的文件。",
        "target.windows_temp.label": "Windows 临时文件",
        "target.windows_temp.description": "Windows Temp 中超过保留天数的文件，部分文件需要管理员权限。",
        "target.browser_cache.label": "浏览器缓存",
        "target.browser_cache.description": "Chrome、Edge、Edge WebView2 和 Firefox 缓存目录。",
        "target.shader_cache.label": "着色器缓存",
        "target.shader_cache.description": "DirectX、NVIDIA 和 AMD 用户级着色器缓存，会自动重建。",
        "target.crash_reports.label": "崩溃报告",
        "target.crash_reports.description": "Windows 错误报告归档和应用崩溃转储。",
        "target.recycle_bin.label": "回收站",
        "target.recycle_bin.description": "清空所选磁盘的回收站。",
        "target.recycle_bin.warning": "将永久删除所选磁盘回收站内容。",
        "target.thumbnail_cache.label": "缩略图和图标缓存",
        "target.thumbnail_cache.description": "Explorer 缩略图和图标数据库文件，锁定文件会跳过。",
        "target.windows_logs.label": "旧 Windows 日志",
        "target.windows_logs.description": "Windows Logs 下的旧日志、ETL 跟踪和压缩 CBS 日志。",
        "target.system_dumps.label": "系统崩溃转储",
        "target.system_dumps.description": "MEMORY.DMP 和 Minidump 崩溃转储文件。",
        "target.driver_installers.label": "GPU 驱动安装器缓存",
        "target.driver_installers.description": "常见 NVIDIA/AMD 驱动解压和下载缓存。",
        "target.delivery_optimization.label": "传递优化缓存",
        "target.delivery_optimization.description": "Windows 传递优化下载缓存，Windows Update 活动时不要清理。",
        "target.windows_update_download.label": "Windows 更新下载缓存",
        "target.windows_update_download.description": "Windows Update 下载目录，更新安装中不要清理。",
        "target.windows_old.label": "旧 Windows 安装",
        "target.windows_old.description": "以前 Windows 安装留下的文件，通常是 C:\\Windows.old。",
        "target.windows_old.warning": "删除以前 Windows 安装的回滚文件。",
        "target.upgrade_leftovers.label": "Windows 升级残留",
        "target.upgrade_leftovers.description": "$WINDOWS.~BT 和 $WINDOWS.~WS 等旧升级工作目录。",
        "target.upgrade_leftovers.warning": "Windows 安装或功能更新进行中不要使用。",
        "target.component_store.label": "组件存储清理",
        "target.component_store.description": "运行 DISM StartComponentCleanup 清理 WinSxS，由 Windows 决定可回收内容。",
        "target.component_store.warning": "可能需要数分钟，并需要管理员权限。",
    },
}


def normalize_lang(lang: str | None) -> str:
    value = (lang or DEFAULT_LANG).strip().lower()
    if value in ("zh", "zh-cn", "cn", "chinese"):
        return "zh"
    if value in ("en", "en-us", "english"):
        return "en"
    raise ValueError("lang must be zh or en")


def tr(key: str, lang: str = DEFAULT_LANG, **kwargs: object) -> str:
    lang = normalize_lang(lang)
    value = TEXT.get(lang, {}).get(key) or TEXT["en"].get(key) or key
    return value.format(**kwargs) if kwargs else value


def localize_error(message: str, lang: str = DEFAULT_LANG) -> str:
    for key in ("component_store_scan", "component_store_admin", "dism_completed"):
        if message == TEXT["en"][key]:
            return tr(key, lang)
    return message


@dataclass(frozen=True)
class CleanTarget:
    key: str
    label: str
    description: str
    roots: tuple[Path, ...] = ()
    min_age_days: int = 1
    default_enabled: bool = True
    deep_enabled: bool = False
    kind: str = "files"
    patterns: tuple[str, ...] = ("*",)
    recursive: bool = True
    requires_admin: bool = False
    warning: str = ""


@dataclass(frozen=True)
class ScanResult:
    target: CleanTarget
    bytes_total: int = 0
    file_count: int = 0
    roots_found: tuple[Path, ...] = ()
    missing_roots: tuple[Path, ...] = ()
    inaccessible_count: int = 0
    skipped_links: int = 0
    errors: tuple[str, ...] = ()

    @property
    def selectable(self) -> bool:
        return self.target.kind == "component_store" or self.bytes_total > 0 or self.file_count > 0


@dataclass(frozen=True)
class CleanResult:
    target: CleanTarget
    bytes_deleted: int = 0
    files_deleted: int = 0
    dirs_removed: int = 0
    failed_count: int = 0
    errors: tuple[str, ...] = ()


def normalize_drive(drive: str) -> str:
    drive = (drive or DEFAULT_DRIVE).strip().upper()
    if len(drive) == 1 and drive.isalpha():
        drive += ":"
    if not (len(drive) == 2 and drive[0].isalpha() and drive[1] == ":"):
        raise ValueError("drive must look like C: or D:")
    return drive


def drive_root(drive: str) -> Path:
    return Path(f"{normalize_drive(drive)}\\")


def human_size(num_bytes: int) -> str:
    value = float(max(0, num_bytes))
    unit = SIZE_UNITS[0]
    for unit in SIZE_UNITS:
        if value < 1024 or unit == SIZE_UNITS[-1]:
            break
        value /= 1024
    if unit == "B":
        return f"{int(value)} {unit}"
    return f"{value:.1f} {unit}"


def path_on_drive(path: Path, drive: str) -> bool:
    expected = normalize_drive(drive)
    actual = path.drive.upper()
    return bool(actual) and actual == expected


def existing_on_drive(paths: Iterable[Path], drive: str) -> tuple[Path, ...]:
    seen: set[str] = set()
    kept: list[Path] = []
    for path in paths:
        expanded = Path(os.path.expandvars(str(path))).expanduser()
        key = os.path.normcase(str(expanded))
        if key in seen:
            continue
        seen.add(key)
        if path_on_drive(expanded, drive):
            kept.append(expanded)
    return tuple(kept)


def is_windows() -> bool:
    return os.name == "nt"


def is_admin() -> bool:
    if not is_windows():
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def browser_cache_roots(local_app_data: Path, app_data: Path, drive: str) -> tuple[Path, ...]:
    roots: list[Path] = []
    chromium_bases = (
        local_app_data / "Google" / "Chrome" / "User Data",
        local_app_data / "Microsoft" / "Edge" / "User Data",
        local_app_data / "Microsoft" / "EdgeWebView" / "User Data",
    )
    for base in chromium_bases:
        if not path_on_drive(base, drive) or not base.exists():
            continue
        try:
            profiles = tuple(base.iterdir())
        except OSError:
            continue
        for profile in profiles:
            if not profile.is_dir():
                continue
            roots.extend(
                (
                    profile / "Cache" / "Cache_Data",
                    profile / "Code Cache",
                    profile / "GPUCache",
                    profile / "Service Worker" / "CacheStorage",
                    profile / "Media Cache",
                )
            )

    firefox_profiles = app_data / "Mozilla" / "Firefox" / "Profiles"
    if path_on_drive(firefox_profiles, drive) and firefox_profiles.exists():
        try:
            profiles = tuple(firefox_profiles.iterdir())
        except OSError:
            profiles = ()
        for profile in profiles:
            if profile.is_dir():
                roots.extend((profile / "cache2", profile / "startupCache"))

    return tuple(root for root in existing_on_drive(roots, drive) if root.exists())


def build_default_targets(drive: str = DEFAULT_DRIVE) -> list[CleanTarget]:
    drive = normalize_drive(drive)
    root = drive_root(drive)
    system_root = Path(os.environ.get("SystemRoot", str(root / "Windows")))
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    program_data = Path(os.environ.get("ProgramData", str(root / "ProgramData")))
    temp_root = Path(tempfile.gettempdir())

    shader_roots = (
        local_app_data / "D3DSCache",
        local_app_data / "NVIDIA" / "DXCache",
        local_app_data / "NVIDIA" / "GLCache",
        local_app_data / "AMD" / "DxCache",
        local_app_data / "AMD" / "GLCache",
    )
    crash_roots = (
        local_app_data / "CrashDumps",
        local_app_data / "Microsoft" / "Windows" / "WER" / "ReportArchive",
        local_app_data / "Microsoft" / "Windows" / "WER" / "ReportQueue",
        program_data / "Microsoft" / "Windows" / "WER" / "ReportArchive",
        program_data / "Microsoft" / "Windows" / "WER" / "ReportQueue",
    )
    driver_installer_roots = (
        root / "NVIDIA",
        root / "AMD",
        program_data / "NVIDIA Corporation" / "Downloader",
        local_app_data / "NVIDIA" / "NvBackend" / "Packages",
    )

    return [
        CleanTarget(
            key="user_temp",
            label="User temp files",
            description="Current user's TEMP/TMP files older than the retention period.",
            roots=existing_on_drive((temp_root,), drive),
            min_age_days=1,
            default_enabled=True,
        ),
        CleanTarget(
            key="windows_temp",
            label="Windows temp files",
            description="Windows Temp files older than the retention period. Some files need admin rights.",
            roots=existing_on_drive((system_root / "Temp",), drive),
            min_age_days=2,
            default_enabled=True,
            requires_admin=True,
        ),
        CleanTarget(
            key="browser_cache",
            label="Browser cache",
            description="Chrome, Edge, Edge WebView2, and Firefox cache folders.",
            roots=browser_cache_roots(local_app_data, app_data, drive),
            min_age_days=1,
            default_enabled=True,
        ),
        CleanTarget(
            key="shader_cache",
            label="Shader cache",
            description="DirectX, NVIDIA, and AMD user-level shader caches. They are rebuilt automatically.",
            roots=tuple(root for root in existing_on_drive(shader_roots, drive) if root.exists()),
            min_age_days=1,
            default_enabled=True,
        ),
        CleanTarget(
            key="crash_reports",
            label="Crash reports",
            description="Windows Error Reporting archives and app crash dumps.",
            roots=tuple(root for root in existing_on_drive(crash_roots, drive) if root.exists()),
            min_age_days=7,
            default_enabled=True,
        ),
        CleanTarget(
            key="recycle_bin",
            label="Recycle Bin",
            description="Empty the Recycle Bin on the selected drive.",
            kind="recycle_bin",
            default_enabled=False,
            deep_enabled=True,
            min_age_days=0,
            warning="This permanently removes Recycle Bin contents for the selected drive.",
        ),
        CleanTarget(
            key="thumbnail_cache",
            label="Thumbnail and icon cache",
            description="Explorer thumbnail and icon database files. Locked files are skipped.",
            roots=existing_on_drive((local_app_data / "Microsoft" / "Windows" / "Explorer",), drive),
            patterns=("thumbcache_*.db", "iconcache_*.db"),
            recursive=False,
            min_age_days=0,
            default_enabled=False,
            deep_enabled=True,
        ),
        CleanTarget(
            key="windows_logs",
            label="Old Windows logs",
            description="Old logs, ETL traces, and compressed CBS logs under Windows Logs.",
            roots=existing_on_drive((system_root / "Logs",), drive),
            patterns=("*.log", "*.etl", "*.cab", "*.tmp"),
            min_age_days=14,
            default_enabled=False,
            deep_enabled=True,
            requires_admin=True,
        ),
        CleanTarget(
            key="system_dumps",
            label="System crash dumps",
            description="MEMORY.DMP and Minidump crash dump files.",
            roots=existing_on_drive((system_root / "MEMORY.DMP", system_root / "Minidump"), drive),
            patterns=("*.dmp",),
            min_age_days=0,
            default_enabled=False,
            deep_enabled=True,
            requires_admin=True,
        ),
        CleanTarget(
            key="driver_installers",
            label="GPU driver installer caches",
            description="Common NVIDIA/AMD installer extraction and downloader caches.",
            roots=tuple(root for root in existing_on_drive(driver_installer_roots, drive) if root.exists()),
            min_age_days=7,
            default_enabled=False,
            deep_enabled=True,
        ),
        CleanTarget(
            key="delivery_optimization",
            label="Delivery Optimization cache",
            description="Windows Delivery Optimization download cache. Avoid while Windows Update is active.",
            roots=existing_on_drive(
                (program_data / "Microsoft" / "Windows" / "DeliveryOptimization" / "Cache",),
                drive,
            ),
            min_age_days=7,
            default_enabled=False,
            deep_enabled=True,
            requires_admin=True,
        ),
        CleanTarget(
            key="windows_update_download",
            label="Windows Update download cache",
            description="Windows Update download folder. Avoid while updates are installing.",
            roots=existing_on_drive((system_root / "SoftwareDistribution" / "Download",), drive),
            min_age_days=14,
            default_enabled=False,
            deep_enabled=True,
            requires_admin=True,
        ),
        CleanTarget(
            key="windows_old",
            label="Previous Windows installation",
            description="Files from a previous Windows installation, usually C:\\Windows.old.",
            roots=existing_on_drive((root / "Windows.old",), drive),
            min_age_days=0,
            default_enabled=False,
            deep_enabled=True,
            requires_admin=True,
            warning="Deletes rollback files for the previous Windows installation.",
        ),
        CleanTarget(
            key="upgrade_leftovers",
            label="Windows upgrade leftovers",
            description="Old Windows upgrade working folders such as $WINDOWS.~BT and $WINDOWS.~WS.",
            roots=existing_on_drive((root / "$WINDOWS.~BT", root / "$WINDOWS.~WS"), drive),
            min_age_days=14,
            default_enabled=False,
            deep_enabled=True,
            requires_admin=True,
            warning="Do not use while Windows setup or feature updates are in progress.",
        ),
        CleanTarget(
            key="component_store",
            label="Component store cleanup",
            description="Run DISM StartComponentCleanup for WinSxS. Windows decides what is safe to reclaim.",
            roots=existing_on_drive((system_root / "WinSxS",), drive),
            kind="component_store",
            default_enabled=False,
            deep_enabled=False,
            requires_admin=True,
            warning="This can take several minutes and requires administrator rights.",
        ),
    ]


def is_link_or_junction(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        return bool(is_junction and is_junction())
    except OSError:
        return True


def is_protected_root(path: Path) -> bool:
    normalized = Path(os.path.normpath(str(path)))
    if not normalized.is_absolute():
        return True
    if normalized == Path(normalized.anchor):
        return True

    protected = [
        Path(os.environ.get("SystemRoot", r"C:\Windows")),
        Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32",
        Path(os.environ.get("ProgramData", r"C:\ProgramData")),
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")),
        Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")),
        Path.home(),
    ]
    normalized_case = os.path.normcase(str(normalized))
    return any(normalized_case == os.path.normcase(str(Path(item))) for item in protected)


def validate_target_root(root: Path) -> None:
    if is_protected_root(root):
        raise ValueError(f"Refusing to clean an over-broad directory: {root}")


def validate_direct_file(path: Path) -> None:
    normalized = Path(os.path.normpath(str(path)))
    if not normalized.is_absolute() or normalized.parent == Path(normalized.anchor):
        raise ValueError(f"Refusing to clean an unsafe file path: {path}")


def matches_patterns(path: Path, patterns: tuple[str, ...]) -> bool:
    name = path.name.lower()
    return any(fnmatch.fnmatch(name, pattern.lower()) for pattern in patterns)


def candidate_for_file(
    path: Path,
    cutoff_timestamp: float,
    patterns: tuple[str, ...],
) -> tuple[tuple[Path, int] | None, int, int, tuple[str, ...]]:
    try:
        if is_link_or_junction(path):
            return None, 0, 1, ()
        if not path.is_file():
            return None, 0, 0, ()
        if not matches_patterns(path, patterns):
            return None, 0, 0, ()
        stat = path.stat()
        if stat.st_mtime <= cutoff_timestamp:
            return (path, int(stat.st_size)), 0, 0, ()
        return None, 0, 0, ()
    except OSError as exc:
        return None, 1, 0, (f"{path}: {exc}",)


def iter_candidate_files(
    root: Path,
    cutoff_timestamp: float,
    patterns: tuple[str, ...],
    recursive: bool,
) -> tuple[list[tuple[Path, int]], int, int, tuple[str, ...]]:
    candidates: list[tuple[Path, int]] = []
    inaccessible = 0
    skipped_links = 0
    errors: list[str] = []
    stack = [root]

    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    try:
                        if is_link_or_junction(path):
                            skipped_links += 1
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if recursive:
                                stack.append(path)
                            continue
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        if not matches_patterns(path, patterns):
                            continue
                        stat = entry.stat(follow_symlinks=False)
                        if stat.st_mtime <= cutoff_timestamp:
                            candidates.append((path, int(stat.st_size)))
                    except OSError as exc:
                        inaccessible += 1
                        errors.append(f"{path}: {exc}")
        except OSError as exc:
            inaccessible += 1
            errors.append(f"{current}: {exc}")

    return candidates, inaccessible, skipped_links, tuple(errors[:20])


def scan_file_target(target: CleanTarget) -> ScanResult:
    roots_found: list[Path] = []
    missing_roots: list[Path] = []
    errors: list[str] = []
    bytes_total = 0
    file_count = 0
    inaccessible = 0
    skipped_links = 0
    cutoff = time.time() - max(0, target.min_age_days) * 24 * 60 * 60

    for root in target.roots:
        if not root.exists():
            missing_roots.append(root)
            continue
        if root.is_file():
            try:
                validate_direct_file(root)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            candidate, denied, links, file_errors = candidate_for_file(root, cutoff, target.patterns)
            roots_found.append(root)
            if candidate:
                bytes_total += candidate[1]
                file_count += 1
            inaccessible += denied
            skipped_links += links
            errors.extend(file_errors)
            continue

        try:
            validate_target_root(root)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if is_link_or_junction(root):
            skipped_links += 1
            errors.append(f"Skipped link or junction directory: {root}")
            continue

        roots_found.append(root)
        candidates, denied, links, candidate_errors = iter_candidate_files(
            root,
            cutoff,
            target.patterns,
            target.recursive,
        )
        bytes_total += sum(size for _, size in candidates)
        file_count += len(candidates)
        inaccessible += denied
        skipped_links += links
        errors.extend(candidate_errors)

    return ScanResult(
        target=target,
        bytes_total=bytes_total,
        file_count=file_count,
        roots_found=tuple(roots_found),
        missing_roots=tuple(missing_roots),
        inaccessible_count=inaccessible,
        skipped_links=skipped_links,
        errors=tuple(errors[:30]),
    )


class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_longlong),
        ("i64NumItems", ctypes.c_longlong),
    ]


def scan_recycle_bin(target: CleanTarget, drive: str) -> ScanResult:
    if not is_windows():
        return ScanResult(target=target, errors=("Recycle Bin scan is only supported on Windows.",))
    root = f"{normalize_drive(drive)}\\"
    info = SHQUERYRBINFO()
    info.cbSize = ctypes.sizeof(info)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(ctypes.c_wchar_p(root), ctypes.byref(info))
    if result != 0:
        return ScanResult(target=target, errors=(f"Cannot query {root} Recycle Bin. Error code: {result}",))
    return ScanResult(
        target=target,
        bytes_total=max(0, int(info.i64Size)),
        file_count=max(0, int(info.i64NumItems)),
        roots_found=(Path(root) / "$Recycle.Bin",),
    )


def scan_component_store(target: CleanTarget) -> ScanResult:
    errors = ("Size is not estimated here. DISM will reclaim safe component-store data during cleanup.",)
    if target.requires_admin and not is_admin():
        errors += ("Administrator rights are required to run this cleanup.",)
    return ScanResult(target=target, file_count=1, roots_found=target.roots, errors=errors)


def scan_target(target: CleanTarget, drive: str = DEFAULT_DRIVE) -> ScanResult:
    if target.kind == "recycle_bin":
        return scan_recycle_bin(target, drive)
    if target.kind == "component_store":
        return scan_component_store(target)
    return scan_file_target(target)


def iter_candidate_paths_from_target(target: CleanTarget) -> Iterable[tuple[Path, int]]:
    cutoff = time.time() - max(0, target.min_age_days) * 24 * 60 * 60
    for root in target.roots:
        if not root.exists():
            continue
        if root.is_file():
            validate_direct_file(root)
            candidate, _, _, _ = candidate_for_file(root, cutoff, target.patterns)
            if candidate:
                yield candidate
            continue
        validate_target_root(root)
        if is_link_or_junction(root):
            continue
        candidates, _, _, _ = iter_candidate_files(root, cutoff, target.patterns, target.recursive)
        yield from candidates


def remove_empty_dirs(root: Path) -> int:
    if not root.exists() or not root.is_dir():
        return 0

    dirs_to_try: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if is_link_or_junction(path):
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            dirs_to_try.append(path)
                            stack.append(path)
                    except OSError:
                        continue
        except OSError:
            continue

    removed = 0
    for path in reversed(dirs_to_try):
        try:
            path.rmdir()
            removed += 1
        except OSError:
            pass
    return removed


def clean_file_target(target: CleanTarget) -> CleanResult:
    scan = scan_file_target(target)
    files_deleted = 0
    bytes_deleted = 0
    failed = 0
    dirs_removed = 0
    errors: list[str] = list(scan.errors[:10])

    for path, size in iter_candidate_paths_from_target(target):
        try:
            path.unlink()
            files_deleted += 1
            bytes_deleted += size
        except OSError as exc:
            failed += 1
            if len(errors) < 30:
                errors.append(f"{path}: {exc}")

    for root in scan.roots_found:
        if root.is_dir():
            dirs_removed += remove_empty_dirs(root)

    return CleanResult(
        target=target,
        bytes_deleted=bytes_deleted,
        files_deleted=files_deleted,
        dirs_removed=dirs_removed,
        failed_count=failed,
        errors=tuple(errors[:30]),
    )


def clean_recycle_bin(target: CleanTarget, drive: str) -> CleanResult:
    if not is_windows():
        return CleanResult(target=target, failed_count=1, errors=("Recycle Bin cleanup is only supported on Windows.",))
    before = scan_recycle_bin(target, drive)
    root = f"{normalize_drive(drive)}\\"
    flags = 0x00000001 | 0x00000002 | 0x00000004
    result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, ctypes.c_wchar_p(root), flags)
    if result != 0:
        return CleanResult(
            target=target,
            failed_count=1,
            errors=(f"Cannot empty {root} Recycle Bin. Error code: {result}",),
        )
    return CleanResult(target=target, bytes_deleted=before.bytes_total, files_deleted=before.file_count)


def clean_component_store(target: CleanTarget) -> CleanResult:
    if not is_windows():
        return CleanResult(target=target, failed_count=1, errors=("DISM cleanup is only supported on Windows.",))
    command = ["dism.exe", "/Online", "/Cleanup-Image", "/StartComponentCleanup"]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60 * 60,
        )
    except OSError as exc:
        return CleanResult(target=target, failed_count=1, errors=(f"Cannot start DISM: {exc}",))
    except subprocess.TimeoutExpired:
        return CleanResult(target=target, failed_count=1, errors=("DISM cleanup timed out after 60 minutes.",))

    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    tail = tuple(line for line in output.splitlines()[-8:] if line.strip())
    if completed.returncode != 0:
        return CleanResult(
            target=target,
            failed_count=1,
            errors=(f"DISM exited with code {completed.returncode}.", *tail),
        )
    return CleanResult(target=target, errors=("DISM component-store cleanup completed.", *tail[:5]))


def clean_target(target: CleanTarget, drive: str = DEFAULT_DRIVE) -> CleanResult:
    if target.kind == "recycle_bin":
        return clean_recycle_bin(target, drive)
    if target.kind == "component_store":
        return clean_component_store(target)
    return clean_file_target(target)


def select_targets(
    targets: list[CleanTarget],
    categories: str | None,
    include_deep: bool = False,
    include_all: bool = False,
) -> list[CleanTarget]:
    if categories:
        wanted = [item.strip() for item in categories.split(",") if item.strip()]
        by_key = {target.key: target for target in targets}
        missing = sorted(set(wanted) - set(by_key))
        if missing:
            raise ValueError(f"Unknown categories: {', '.join(missing)}")
        return [by_key[key] for key in dict.fromkeys(wanted)]

    if include_all:
        return targets
    if include_deep:
        return [target for target in targets if target.default_enabled or target.deep_enabled]
    return [target for target in targets if target.default_enabled]


def override_min_age(targets: list[CleanTarget], older_than: int | None) -> list[CleanTarget]:
    if older_than is None:
        return targets
    if older_than < 0:
        raise ValueError("--older-than cannot be negative")
    return [
        replace(target, min_age_days=older_than) if target.kind == "files" else target
        for target in targets
    ]


def target_tier(target: CleanTarget) -> str:
    if target.default_enabled:
        return "default"
    if target.deep_enabled:
        return "deep"
    return "system"


def target_label(target: CleanTarget, lang: str = DEFAULT_LANG) -> str:
    return tr(f"target.{target.key}.label", lang) if lang == "zh" else target.label


def target_description(target: CleanTarget, lang: str = DEFAULT_LANG) -> str:
    return tr(f"target.{target.key}.description", lang) if lang == "zh" else target.description


def target_warning(target: CleanTarget, lang: str = DEFAULT_LANG) -> str:
    if lang == "zh":
        translated = TEXT["zh"].get(f"target.{target.key}.warning")
        if translated:
            return translated
    return target.warning


def tier_label(target: CleanTarget, lang: str = DEFAULT_LANG) -> str:
    return tr(f"tier.{target_tier(target)}", lang)


def warning_lines(results: Iterable[ScanResult], lang: str = DEFAULT_LANG) -> list[str]:
    lines: list[str] = []
    admin_needed = False
    for result in results:
        target = result.target
        warning = target_warning(target, lang)
        if warning:
            lines.append(f"{target_label(target, lang)}: {warning}")
        if target.requires_admin:
            admin_needed = True
    if admin_needed and not is_admin():
        lines.append(tr("admin_warning", lang))
    return lines


def print_scan_results(results: list[ScanResult], lang: str = DEFAULT_LANG) -> None:
    print(f"{tr('cli.category', lang):<34} {tr('cli.files', lang):>10} {tr('cli.size', lang):>12}  {tr('cli.location', lang)}")
    print("-" * 96)
    for result in results:
        roots = "; ".join(str(root) for root in result.roots_found) or tr("gui.no_path", lang)
        if result.errors and not result.roots_found:
            roots = localize_error(result.errors[0], lang)
        print(
            f"{target_label(result.target, lang):<34} {result.file_count:>10} "
            f"{human_size(result.bytes_total):>12}  {roots}"
        )
        if result.inaccessible_count:
            print(f"{'':<34} {'':>10} {'':>12}  {tr('cli.skipped_locked', lang, count=result.inaccessible_count)}")
        if result.skipped_links:
            print(f"{'':<34} {'':>10} {'':>12}  {tr('cli.skipped_links', lang, count=result.skipped_links)}")
        for error in result.errors[:2]:
            print(f"{'':<34} {'':>10} {'':>12}  {tr('cli.note', lang)}: {localize_error(error, lang)}")


def print_clean_results(results: list[CleanResult], lang: str = DEFAULT_LANG) -> None:
    print(f"{tr('cli.category', lang):<34} {tr('cli.deleted', lang):>10} {tr('cli.freed', lang):>12}  {tr('cli.status', lang)}")
    print("-" * 84)
    for result in results:
        status = tr("cli.done", lang) if not result.failed_count else tr("cli.partial_failure", lang, count=result.failed_count)
        print(
            f"{target_label(result.target, lang):<34} {result.files_deleted:>10} "
            f"{human_size(result.bytes_deleted):>12}  {status}"
        )
        for error in result.errors[:3]:
            print(f"{'':<34} {'':>10} {'':>12}  {localize_error(error, lang)}")


def confirm_cli(results: list[ScanResult], lang: str = DEFAULT_LANG) -> bool:
    total = sum(result.bytes_total for result in results)
    count = sum(result.file_count for result in results if result.target.kind != "component_store")
    for line in warning_lines(results, lang):
        print(f"{tr('cli.warning', lang)}: {line}")
    answer = input(tr("cli.confirm", lang, count=count, size=human_size(total)))
    return answer.strip().lower() == "yes"


def run_cli(args: argparse.Namespace) -> int:
    try:
        lang = normalize_lang(args.lang)
        drive = normalize_drive(args.drive)
        targets = build_default_targets(drive)
        targets = override_min_age(targets, args.older_than)
        selected = select_targets(targets, args.categories, args.deep, args.all)
    except ValueError as exc:
        print(f"Argument error: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for target in targets:
            admin = " admin" if target.requires_admin else ""
            print(
                f"{target.key:<26} {tier_label(target, lang):<8}{admin:<7} "
                f"{target_label(target, lang)} - {target_description(target, lang)}"
            )
        return 0

    results = [scan_target(target, drive) for target in selected]
    print_scan_results(results, lang)

    if not args.clean:
        return 0

    cleanable = [result for result in results if result.selectable]
    if not cleanable:
        print(tr("cli.no_cleanable", lang))
        return 0
    if not args.yes and not confirm_cli(cleanable, lang):
        print(tr("cli.cancelled", lang))
        return 1

    clean_results = [clean_target(result.target, drive) for result in cleanable]
    print_clean_results(clean_results, lang)
    return 0


class CleanerApp:
    def __init__(self, drive: str = DEFAULT_DRIVE, lang: str = DEFAULT_LANG) -> None:
        import tkinter as tk
        from tkinter import scrolledtext, ttk

        self.tk = tk
        self.ttk = ttk
        self.scrolledtext = scrolledtext
        self.drive = normalize_drive(drive)
        self.lang = normalize_lang(lang)
        self.targets = build_default_targets(self.drive)
        self.results: dict[str, ScanResult] = {}
        self.queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self.root = tk.Tk()
        self.root.title(f"{tr('app_name', self.lang)} v{VERSION} - {self.drive}")
        self.root.geometry("1100x760")
        self.root.minsize(920, 620)

        self.vars: dict[str, tk.BooleanVar] = {}
        self.text_vars: dict[str, tk.StringVar] = {}
        self.target_label_vars: dict[str, tk.StringVar] = {}
        self.tier_label_vars: dict[str, tk.StringVar] = {}
        self.size_labels: dict[str, tk.StringVar] = {}
        self.count_labels: dict[str, tk.StringVar] = {}
        self.status_labels: dict[str, tk.StringVar] = {}
        self.buttons: list[ttk.Button] = []
        self.language_display_to_code: dict[str, str] = {}
        self.language_var = tk.StringVar()
        self.title_var = tk.StringVar()

        self.build_ui()
        self.root.after(100, self.pump_queue)

    def text_var(self, key: str, **kwargs: object):
        var = self.tk.StringVar(value=tr(key, self.lang, **kwargs))
        self.text_vars[key] = var
        return var

    def refresh_language(self) -> None:
        self.root.title(f"{tr('app_name', self.lang)} v{VERSION} - {self.drive}")
        self.title_var.set(f"{tr('app_name', self.lang)} v{VERSION} ({self.drive})")
        for key, var in self.text_vars.items():
            var.set(tr(key, self.lang))
        for target in self.targets:
            self.target_label_vars[target.key].set(target_label(target, self.lang))
            self.tier_label_vars[target.key].set(tier_label(target, self.lang))
            if target.key not in self.results:
                self.status_labels[target.key].set(target_description(target, self.lang))
            else:
                self.update_scan_result(self.results[target.key])
        display = tr("lang_chinese", self.lang) if self.lang == "zh" else tr("lang_english", self.lang)
        self.language_var.set(display)

    def change_language(self, _event: object | None = None) -> None:
        selected = self.language_var.get()
        code = self.language_display_to_code.get(selected)
        if code and code != self.lang:
            self.lang = code
            self.refresh_language()

    def build_ui(self) -> None:
        tk = self.tk
        ttk = self.ttk

        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main)
        header.pack(fill=tk.X)
        self.title_var.set(f"{tr('app_name', self.lang)} v{VERSION} ({self.drive})")
        title = ttk.Label(header, textvariable=self.title_var, font=("", 18, "bold"))
        title.pack(side=tk.LEFT)
        lang_frame = ttk.Frame(header)
        lang_frame.pack(side=tk.RIGHT)
        ttk.Label(lang_frame, textvariable=self.text_var("lang_label")).pack(side=tk.LEFT, padx=(0, 6))
        zh_display = tr("lang_chinese", "zh")
        en_display = tr("lang_english", "en")
        self.language_display_to_code = {zh_display: "zh", en_display: "en"}
        self.language_var.set(zh_display if self.lang == "zh" else en_display)
        language_box = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=(zh_display, en_display),
            state="readonly",
            width=10,
        )
        language_box.pack(side=tk.LEFT)
        language_box.bind("<<ComboboxSelected>>", self.change_language)

        toolbar = ttk.Frame(main)
        toolbar.pack(fill=tk.X, pady=(14, 10))
        scan_btn = ttk.Button(toolbar, textvariable=self.text_var("gui.scan"), command=self.start_scan)
        clean_btn = ttk.Button(toolbar, textvariable=self.text_var("gui.clean_selected"), command=self.start_clean)
        default_btn = ttk.Button(toolbar, textvariable=self.text_var("gui.default_preset"), command=self.select_default)
        deep_btn = ttk.Button(toolbar, textvariable=self.text_var("gui.deep_preset"), command=self.select_deep)
        none_btn = ttk.Button(toolbar, textvariable=self.text_var("gui.clear_selection"), command=lambda: self.set_all(False))
        for button in (scan_btn, clean_btn, default_btn, deep_btn, none_btn):
            button.pack(side=tk.LEFT, padx=(0, 8))
            self.buttons.append(button)

        note = ttk.Label(
            main,
            textvariable=self.text_var("gui.note"),
            foreground="#555555",
        )
        note.pack(anchor=tk.W, pady=(0, 10))

        grid = ttk.Frame(main)
        grid.pack(fill=tk.X)
        headers = ("gui.col_use", "gui.col_tier", "gui.col_category", "gui.col_size", "gui.col_files", "gui.col_status")
        widths = (6, 9, 28, 16, 10, 54)
        for col, (key, width) in enumerate(zip(headers, widths)):
            label = ttk.Label(grid, textvariable=self.text_var(key), font=("", 10, "bold"), width=width)
            label.grid(row=0, column=col, sticky=tk.W, padx=(0, 8), pady=(0, 6))

        for row, target in enumerate(self.targets, start=1):
            var = tk.BooleanVar(value=target.default_enabled)
            self.vars[target.key] = var
            self.target_label_vars[target.key] = tk.StringVar(value=target_label(target, self.lang))
            self.tier_label_vars[target.key] = tk.StringVar(value=tier_label(target, self.lang))
            self.size_labels[target.key] = tk.StringVar(value="-")
            self.count_labels[target.key] = tk.StringVar(value="-")
            self.status_labels[target.key] = tk.StringVar(value=target_description(target, self.lang))

            ttk.Checkbutton(grid, variable=var).grid(row=row, column=0, sticky=tk.W, padx=(0, 8), pady=3)
            ttk.Label(grid, textvariable=self.tier_label_vars[target.key], width=9).grid(
                row=row, column=1, sticky=tk.W, padx=(0, 8), pady=3
            )
            ttk.Label(grid, textvariable=self.target_label_vars[target.key], width=28).grid(
                row=row, column=2, sticky=tk.W, padx=(0, 8), pady=3
            )
            ttk.Label(grid, textvariable=self.size_labels[target.key], width=16).grid(
                row=row, column=3, sticky=tk.W, padx=(0, 8), pady=3
            )
            ttk.Label(grid, textvariable=self.count_labels[target.key], width=10).grid(
                row=row, column=4, sticky=tk.W, padx=(0, 8), pady=3
            )
            ttk.Label(grid, textvariable=self.status_labels[target.key], wraplength=470).grid(
                row=row, column=5, sticky=tk.W, pady=3
            )

        log_label = ttk.Label(main, textvariable=self.text_var("gui.log"), font=("", 10, "bold"))
        log_label.pack(anchor=tk.W, pady=(16, 4))
        self.log_box = self.scrolledtext.ScrolledText(main, height=10, wrap=tk.WORD)
        self.log_box.pack(fill=tk.BOTH, expand=True)
        self.log(tr("gui.initial_log", self.lang))

    def set_all(self, value: bool) -> None:
        for var in self.vars.values():
            var.set(value)

    def select_default(self) -> None:
        for target in self.targets:
            self.vars[target.key].set(target.default_enabled)

    def select_deep(self) -> None:
        for target in self.targets:
            self.vars[target.key].set(target.default_enabled or target.deep_enabled)

    def set_busy(self, busy: bool) -> None:
        state = self.tk.DISABLED if busy else self.tk.NORMAL
        for button in self.buttons:
            button.configure(state=state)

    def log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.insert(self.tk.END, f"[{timestamp}] {message}\n")
        self.log_box.see(self.tk.END)

    def start_scan(self) -> None:
        self.set_busy(True)
        self.results.clear()
        self.queue.put(("log", tr("gui.starting_scan", self.lang)))
        threading.Thread(target=self.worker_scan, daemon=True).start()

    def worker_scan(self) -> None:
        for target in self.targets:
            self.queue.put(("log", tr("gui.scanning", self.lang, label=target_label(target, self.lang))))
            result = scan_target(target, self.drive)
            self.queue.put(("result", result))
        self.queue.put(("done", "scan"))

    def start_clean(self) -> None:
        from tkinter import messagebox

        selected = [key for key, var in self.vars.items() if var.get()]
        if not selected:
            messagebox.showinfo(tr("app_name", self.lang), tr("gui.select_one", self.lang))
            return
        if len(self.results) != len(self.targets):
            messagebox.showinfo(tr("app_name", self.lang), tr("gui.scan_first", self.lang))
            return

        selected_results = [
            self.results[key] for key in selected if key in self.results and self.results[key].selectable
        ]
        if not selected_results:
            messagebox.showinfo(tr("app_name", self.lang), tr("gui.nothing_selected", self.lang))
            return

        total_bytes = sum(result.bytes_total for result in selected_results)
        total_files = sum(
            result.file_count for result in selected_results if result.target.kind != "component_store"
        )
        warnings = "\n".join(warning_lines(selected_results, self.lang))
        message = tr("gui.confirm", self.lang, count=total_files, size=human_size(total_bytes))
        if warnings:
            message += f"\n\n{tr('gui.warnings', self.lang)}:\n{warnings}"
        ok = messagebox.askyesno(tr("app_name", self.lang), message)
        if not ok:
            self.log(tr("gui.cancelled", self.lang))
            return

        self.set_busy(True)
        self.queue.put(("log", tr("gui.starting_cleanup", self.lang)))
        threading.Thread(target=self.worker_clean, args=(selected_results,), daemon=True).start()

    def worker_clean(self, selected_results: list[ScanResult]) -> None:
        for scan_result in selected_results:
            self.queue.put(("log", tr("gui.cleaning", self.lang, label=target_label(scan_result.target, self.lang))))
            result = clean_target(scan_result.target, self.drive)
            self.queue.put(("clean_result", result))
            refreshed = scan_target(scan_result.target, self.drive)
            self.queue.put(("result", refreshed))
        self.queue.put(("done", "clean"))

    def pump_queue(self) -> None:
        while True:
            try:
                event, payload = self.queue.get_nowait()
            except queue.Empty:
                break
            if event == "log":
                self.log(str(payload))
            elif event == "result":
                self.update_scan_result(payload)  # type: ignore[arg-type]
            elif event == "clean_result":
                self.update_clean_result(payload)  # type: ignore[arg-type]
            elif event == "done":
                self.set_busy(False)
                self.log(tr("gui.scan_complete", self.lang) if payload == "scan" else tr("gui.cleanup_complete", self.lang))
        self.root.after(100, self.pump_queue)

    def update_scan_result(self, result: ScanResult) -> None:
        self.results[result.target.key] = result
        self.size_labels[result.target.key].set(human_size(result.bytes_total))
        self.count_labels[result.target.key].set(str(result.file_count))
        if result.roots_found:
            status = "; ".join(str(root) for root in result.roots_found[:3])
            if len(result.roots_found) > 3:
                status += f" {tr('gui.and_more', self.lang, count=len(result.roots_found) - 3)}"
        elif result.errors:
            status = localize_error(result.errors[0], self.lang)
        else:
            status = tr("gui.no_path", self.lang)
        if result.inaccessible_count:
            status += f"; {tr('gui.skipped_locked', self.lang, count=result.inaccessible_count)}"
        if result.skipped_links:
            status += f"; {tr('gui.skipped_links', self.lang, count=result.skipped_links)}"
        self.status_labels[result.target.key].set(status)

    def update_clean_result(self, result: CleanResult) -> None:
        parts = [
            tr(
                "gui.deleted_summary",
                self.lang,
                label=target_label(result.target, self.lang),
                files=result.files_deleted,
                size=human_size(result.bytes_deleted),
            )
        ]
        if result.dirs_removed:
            parts.append(tr("gui.removed_empty", self.lang, count=result.dirs_removed))
        if result.failed_count:
            parts.append(tr("gui.failed", self.lang, count=result.failed_count))
        self.log(", ".join(parts))
        for error in result.errors[:5]:
            self.log(f"  {localize_error(error, self.lang)}")

    def run(self) -> None:
        self.root.mainloop()


def run_gui(drive: str = DEFAULT_DRIVE, lang: str = DEFAULT_LANG) -> int:
    try:
        app = CleanerApp(drive, lang)
        app.run()
        return 0
    except Exception as exc:  # pragma: no cover - GUI fallback
        print(f"Cannot start GUI: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan and clean common C drive temp files and caches.")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} v{VERSION}")
    parser.add_argument("--drive", default=DEFAULT_DRIVE, help="Drive to clean, for example C:. Default: C:")
    parser.add_argument("--gui", action="store_true", help="Start the GUI. This is the default with no action.")
    parser.add_argument("--scan", action="store_true", help="Scan from the command line without cleaning.")
    parser.add_argument("--clean", action="store_true", help="Clean from the command line after scanning.")
    parser.add_argument("--yes", action="store_true", help="Skip the yes prompt for command-line cleanup.")
    parser.add_argument("--list", action="store_true", help="List available cleanup categories.")
    parser.add_argument("--categories", help="Comma-separated category keys, for example user_temp,browser_cache.")
    parser.add_argument("--deep", action="store_true", help="Include deep cleanup categories in scan/cleanup.")
    parser.add_argument("--all", action="store_true", help="Include every category, including system-tool actions.")
    parser.add_argument("--older-than", type=int, help="Override minimum file age for file-based categories.")
    parser.add_argument("--lang", choices=("zh", "en"), default=DEFAULT_LANG, help="Interface language: zh or en.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    no_action = not any((args.scan, args.clean, args.list, args.gui))
    if args.gui or no_action:
        return run_gui(args.drive, args.lang)
    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
