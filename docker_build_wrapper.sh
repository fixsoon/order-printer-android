#!/bin/bash
# 本地 Docker 构建 Buildozer APK
# 挂载 Gradle 缓存避免下载失败
docker run --rm \
  -v "/Users/meetfun/order-printer-android:/home/user/hostcwd" \
  -v "/Users/meetfun/buildozer-cache:/root/.buildozer" \
  -v "/Users/meetfun/.gradle:/root/.gradle" \
  -w /home/user/hostcwd \
  --entrypoint bash \
  docker.1ms.run/kivy/buildozer:latest \
  /home/user/hostcwd/docker_build.sh 2>&1
