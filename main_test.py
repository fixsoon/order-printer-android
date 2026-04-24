"""最小化测试 - 排除是否是屏幕代码的问题"""

import os
os.environ.setdefault('KIVY_NO_ARGS', '1')
import kivy
kivy.require('2.1.0')
from kivy.config import Config
Config.set('kivy', 'copy_kivy_files', '0')

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel


def log(msg):
    print(f"[TEST] {msg}", flush=True)


class TestApp(MDApp):
    def build(self):
        log("build() 开始")
        self.title = "飞鹅餐饮订单打印"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"

        sm = MDScreenManager()
        sm.add_widget(MDScreen(name="test"))
        sm.get_screen("test").add_widget(MDLabel(
            text="Hello KivyMD!", halign="center", font_style="H4"
        ))
        log("ScreenManager 创建完成")
        return sm


if __name__ == "__main__":
    TestApp().run()
