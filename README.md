# 飞鹅餐饮订单打印系统 - Android 版

基于 KivyMD 的安卓应用，复用桌面版核心模块。

## 功能

- 导入 Excel 接龙订单数据（支持手机文件选择器）
- 打印收银小票 / 饮品杯贴
- 接龙号范围筛选
- 打印机管理
- 杯贴商品库管理
- 排版预览
- 临时加单

## 开发运行（桌面调试）

```bash
pip install -r requirements.txt
python main.py
```

## 打包 Android APK

```bash
# 安装 buildozer
pip install buildozer

# 首次构建（会自动下载 Android SDK/NDK，约需 30-60 分钟）
buildozer android debug

# 生成的 APK 在 ./bin/ 目录下
```

## 文件结构

```
order-printer-android/
├── main.py              # KivyMD 入口
├── buildozer.spec       # Android 打包配置
├── requirements.txt
├── screens/
│   ├── home.py          # 主页
│   ├── printer.py       # 打印机管理
│   ├── cup_products.py  # 杯贴商品库
│   ├── preview.py       # 排版预览
│   └── temp_order.py    # 临时加单
└── core/                # 复用桌面版核心模块
    ├── feie_api.py
    ├── data_handler.py
    ├── storage.py
    ├── templates.py
    └── config.py
```
