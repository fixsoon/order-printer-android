#!/bin/bash
set -e

SDK=/root/.buildozer/android/platform/android-sdk
mkdir -p $SDK/cmdline-tools/latest

echo ">>> 下载 commandlinetools v11076708..."
python3 -c "
import urllib.request, zipfile, os

# 使用 docker_build.sh 原始版本（buildozer 兼容）
url = 'https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip'
urllib.request.urlretrieve(url, '/tmp/cmdline.zip')
print('下载完成:', os.path.getsize('/tmp/cmdline.zip'))

with zipfile.ZipFile('/tmp/cmdline.zip', 'r') as z:
    names = z.namelist()
    top = set(n.split('/')[0] for n in names)
    print('顶层条目:', top)
    print('前3条:', names[:3])
    z.extractall('/tmp/ct')

print('/tmp/ct 内容:', os.listdir('/tmp/ct'))
"

echo ">>> 建立 latest 结构..."
python3 -c "
import os, shutil

ct = '/tmp/ct'
top = os.listdir(ct)
print('ct top-level:', top)

if 'cmdline-tools' in top:
    src = os.path.join(ct, 'cmdline-tools')
    print('zip结构: cmdline-tools/...')
elif 'tools' in top:
    src = os.path.join(ct, 'tools')
    print('zip结构: tools/... (重命名为cmdline-tools)')
else:
    # 直接是 bin/lib 等
    src = ct
    print('zip结构: 直接 bin/lib 等')

dst = '/tmp/latest'
os.makedirs(dst)
for item in os.listdir(src):
    src_item = os.path.join(src, item)
    dst_item = os.path.join(dst, item)
    if os.path.isdir(src_item):
        shutil.copytree(src_item, dst_item)
    else:
        shutil.copy2(src_item, dst_item)
print('重组完成')
print('latest内容:', os.listdir('/tmp/latest'))
"

echo ">>> 复制到 SDK 目录..."
rm -rf $SDK/cmdline-tools/latest
cp -r /tmp/latest $SDK/cmdline-tools/latest
chmod -R +x $SDK/cmdline-tools/latest/bin/ 2>/dev/null || true
ls $SDK/cmdline-tools/latest/bin/

echo ">>> 接受协议..."
yes | $SDK/cmdline-tools/latest/bin/sdkmanager --sdk_root=$SDK --licenses 2>/dev/null || true

echo ">>> 安装 SDK 组件..."
$SDK/cmdline-tools/latest/bin/sdkmanager --sdk_root=$SDK 'platforms;android-33' 'build-tools;33.0.2' 'platform-tools' 2>&1

echo ">>> 验证..."
ls $SDK/platforms/
ls $SDK/build-tools/
echo ">>> SDK 安装完成！"
