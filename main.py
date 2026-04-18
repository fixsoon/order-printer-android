"""飞鹅餐饮订单打印系统 - Android 版 (KivyMD)"""

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from core.storage import init_db
from screens.home import HomeScreen
from screens.printer import PrinterScreen
from screens.cup_products import CupProductsScreen
from screens.preview import PreviewScreen
from screens.temp_order import TempOrderScreen


class OrderPrinterApp(MDApp):
    def build(self):
        self.title = "飞鹅餐饮订单打印"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"

        init_db()

        sm = MDScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(PrinterScreen(name="printer"))
        sm.add_widget(CupProductsScreen(name="cup_products"))
        sm.add_widget(PreviewScreen(name="preview"))
        sm.add_widget(TempOrderScreen(name="temp_order"))
        return sm


if __name__ == "__main__":
    OrderPrinterApp().run()
