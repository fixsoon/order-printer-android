[app]

title = 飞鹅餐饮订单打印
package.name = orderprinter
package.domain = com.feie.orderprinter
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db
version = 1.0.0

requirements = python3,kivy==2.3.0,kivymd==1.1.1,openpyxl,requests,plyer,pillow,sqlite3

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.accept_sdk_license = True

# 构建方式
# p4a.source_dir = 
# p4a.fork = 
# p4a.branch = 

[buildozer]
log_level = 2
warn_on_root = 1
