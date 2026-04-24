[app]

title = 标签打印Hermes
package.name = orderprinter
package.domain = com.feie.orderprinter
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db,ttf,ttc
source.exclude_dirs = .venv, .git, .github, bin, __pycache__, buildozer, .buildozer
version = 1.0.0

requirements = python3,kivy==2.1.0,openpyxl,et_xmlfile,pandas,requests,plyer,pillow,numpy,chardet

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.accept_sdk_license = True

android.env_vars = KIVY_GL_BACKEND=sdl2,KIVY_WINDOW=sdl2

[buildozer]
log_level = 2
warn_on_root = 1
