#!/bin/bash
set -e

SDK=/root/.buildozer/android/platform/android-sdk

echo ">>> 安装系统依赖..."
apt-get update -qq && apt-get install -y -qq gettext autopoint 2>&1 | tail -3

echo ">>> 修复 buildozer root 检查..."
sed -i "s/cont = input.*/cont = 'y'/" /home/user/.venv/lib/python3.12/site-packages/buildozer/__init__.py

# 修复 Cython 交叉编译问题：write_depfile 需要先创建目录
sed -i "s/with open(target+'.dep', 'w')/os.makedirs(os.path.dirname(target), exist_ok=True)\n    with open(target+'.dep', 'w')/" \
  /home/user/.venv/lib/python3.12/site-packages/Cython/Utils.py

# 修复 Gradle 下载地址：改用腾讯云镜像
echo ">>> 替换 Gradle 下载源为腾讯云镜像..."
find /home/user/hostcwd/.buildozer/android/platform -name "gradle-wrapper.properties" 2>/dev/null | while read f; do
  sed -i 's|https\\://services.gradle.org/distributions/gradle-8.0.2-all.zip|https\\://mirrors.cloud.tencent.com/gradle/gradle-8.0.2-all.zip|g' "$f"
done

# 构建
echo ">>> 开始构建 APK..."
buildozer android debug
echo ">>> 构建完成！"
ls -la bin/ 2>/dev/null || echo "APK 未生成"
