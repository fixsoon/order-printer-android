"""飞鹅餐饮订单打印系统 - Android 版 (纯 Kivy)"""

import sys
import os
import traceback

os.environ.setdefault('KIVY_NO_ARGS', '1')
import kivy
kivy.require('2.1.0')
from kivy.config import Config
Config.set('kivy', 'copy_kivy_files', '0')
Config.set('kivy', 'default_font', ['NotoSansSC',
    'fonts/NotoSansSC-Regular.ttf',
    'fonts/NotoSansSC-Regular.ttf',
    'fonts/NotoSansSC-Regular.ttf',
    'fonts/NotoSansSC-Regular.ttf'])

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.text import LabelBase
from kivy.resources import resource_find

from core.storage import init_db
from screens.home import HomeScreen
from screens.printer import PrinterScreen
from screens.cup_products import CupProductsScreen
from screens.preview import PreviewScreen
from screens.temp_order import TempOrderScreen
from screens.operator_manage import OperatorManageScreen
from screens.template_manage import TemplateManageScreen, IngredientTemplateScreen, FoodSampleTemplateScreen
from screens.expiry_label import ExpiryLabelScreen, IngredientPrintScreen, SamplePrintScreen
from screens.label_main import LabelMainScreen


def log(msg):
    print(f"[OrderPrinter] {msg}", flush=True)


class OrderPrinterApp(App):
    def build(self):
        log("build() 开始")

        # 注册中文字体
        font_path = resource_find("fonts/NotoSansSC-Regular.ttf")
        if font_path:
            LabelBase.register(name="NotoSansSC", fn_regular=font_path)
            log(f"中文字体已注册: {font_path}")
        else:
            log("警告: 未找到中文字体")

        try:
            log("init_db() 开始")
            init_db()
            log("init_db() 完成")
        except Exception as e:
            log(f"init_db() 失败: {e}")
            traceback.print_exc()

        try:
            log("创建 ScreenManager")
            sm = ScreenManager()
            log("添加 HomeScreen")
            sm.add_widget(HomeScreen(name="home"))
            log("添加 PrinterScreen")
            sm.add_widget(PrinterScreen(name="printer"))
            log("添加 CupProductsScreen")
            sm.add_widget(CupProductsScreen(name="cup_products"))
            log("添加 PreviewScreen")
            sm.add_widget(PreviewScreen(name="preview"))
            log("添加 TempOrderScreen")
            sm.add_widget(TempOrderScreen(name="temp_order"))
            log("添加 OperatorManageScreen")
            sm.add_widget(OperatorManageScreen(name="operator_manage"))
            log("添加 TemplateManageScreen")
            sm.add_widget(TemplateManageScreen(name="template_manage"))
            log("添加 IngredientTemplateScreen")
            sm.add_widget(IngredientTemplateScreen(name="ingredient_template"))
            log("添加 FoodSampleTemplateScreen")
            sm.add_widget(FoodSampleTemplateScreen(name="food_sample_template"))
            log("添加 ExpiryLabelScreen")
            sm.add_widget(ExpiryLabelScreen(name="expiry_label"))
            log("添加 IngredientPrintScreen")
            sm.add_widget(IngredientPrintScreen(name="ingredient_print"))
            log("添加 SamplePrintScreen")
            sm.add_widget(SamplePrintScreen(name="sample_print"))
            log("添加 LabelMainScreen")
            sm.add_widget(LabelMainScreen(name="label_main"))
            log("ScreenManager 创建完成")
            return sm
        except Exception as e:
            log(f"build() 失败: {e}")
            traceback.print_exc()
            raise


if __name__ == "__main__":
    log("App 启动")
    try:
        OrderPrinterApp().run()
    except Exception as e:
        log(f"FATAL: {e}")
        traceback.print_exc()
