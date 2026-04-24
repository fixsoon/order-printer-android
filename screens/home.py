"""主页 - 导入数据、筛选、打印操作（纯 Kivy）"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.metrics import dp
import threading

from core.data_handler import read_excel, filter_orders, group_orders_for_receipt
from core.storage import get_default_printer, is_cup_product
from core.feie_api import print_html as feie_print
from core.templates import receipt_html, cup_label_html
from utils import log


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.df = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        # 标题
        root.add_widget(Label(
            text='[b]飞鹅餐饮订单打印[/b]',
            markup=True, halign='center', valign='middle',
            font_size=dp(20), size_hint_y=None, height=dp(50)
        ))

        # 导入按钮
        root.add_widget(Button(
            text='📂 导入 Excel 文件',
            background_color=(0.2, 0.5, 0.9, 1),
            size_hint_y=None, height=dp(48),
            on_release=lambda x: self._import_excel()
        ))

        # 数据信息标签
        self.info_label = Label(
            text='未加载数据',
            halign='center', valign='middle',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None, height=dp(28)
        )
        root.add_widget(self.info_label)

        # 筛选区域
        filter_card = BoxLayout(orientation='vertical', padding=dp(10), size_hint_y=None, height=dp(130))
        from kivy.uix.widget import Widget
        filter_card.add_widget(Label(
            text='[b]接龙号范围筛选[/b]', markup=True,
            size_hint_y=None, height=dp(25)
        ))

        range_box = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(36))
        self.chain_start = TextInput(hint_text='起始号', multiline=False, size_hint_x=0.4,
                                     input_filter='int', padding=[dp(8), dp(8), 0, 0])
        self.chain_end = TextInput(hint_text='结束号', multiline=False, size_hint_x=0.4,
                                   input_filter='int', padding=[dp(8), dp(8), 0, 0])
        range_box.add_widget(self.chain_start)
        range_box.add_widget(Label(text='到', halign='center', size_hint_x=0.2))
        range_box.add_widget(self.chain_end)
        filter_card.add_widget(range_box)

        cancel_box = BoxLayout(size_hint_y=None, height=dp(30))
        self.cancel_check = CheckBox(active=True, size_hint_x=None, width=dp(40))
        cancel_box.add_widget(self.cancel_check)
        cancel_box.add_widget(Label(text='排除已取消订单', halign='left', valign='middle'))
        filter_card.add_widget(cancel_box)
        root.add_widget(filter_card)

        # 打印按钮区
        btn_box = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(46))
        btn_box.add_widget(Button(
            text='打印收银小票',
            background_color=(0.2, 0.6, 0.8, 1),
            on_release=lambda x: self._print_receipts()
        ))
        btn_box.add_widget(Button(
            text='打印饮品杯贴',
            background_color=(0.9, 0.5, 0.2, 1),
            on_release=lambda x: self._print_cups()
        ))
        root.add_widget(btn_box)

        btn_box2 = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(46))
        btn_box2.add_widget(Button(
            text='打印汇总单',
            background_color=(0.3, 0.7, 0.3, 1),
            on_release=lambda x: self._print_summary()
        ))
        btn_box2.add_widget(Button(
            text='临时加单',
            background_color=(0.6, 0.3, 0.7, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'temp_order')
        ))
        root.add_widget(btn_box2)

        # 数据预览
        self.preview_label = Label(
            text='', halign='left', valign='top',
            color=(0.4, 0.4, 0.4, 1), font_size=dp(12)
        )
        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(self.preview_label)
        root.add_widget(scroll)

        # 底部导航
        nav_box = BoxLayout(spacing=dp(6), size_hint_y=None, height=dp(46))
        nav_box.add_widget(Button(
            text='🖨 打印机',
            background_color=(0.3, 0.3, 0.3, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'printer')
        ))
        nav_box.add_widget(Button(
            text='🥤 杯贴商品库',
            background_color=(0.3, 0.3, 0.3, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'cup_products')
        ))
        nav_box.add_widget(Button(
            text='📐 排版预览',
            background_color=(0.3, 0.3, 0.3, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'preview')
        ))
        root.add_widget(nav_box)

        # 期效标签入口
        expiry_box = BoxLayout(spacing=dp(6), size_hint_y=None, height=dp(46))
        expiry_box.add_widget(Button(
            text='🏷 期效标签打印',
            background_color=(0.9, 0.55, 0.2, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'label_main')
        ))
        expiry_box.add_widget(Button(
            text='👤 经手人设置',
            background_color=(0.3, 0.6, 0.8, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'operator_manage')
        ))
        expiry_box.add_widget(Button(
            text='📋 模板管理',
            background_color=(0.6, 0.3, 0.8, 1),
            on_release=lambda x: setattr(self.manager, 'current', 'template_manage')
        ))
        root.add_widget(expiry_box)

        self.add_widget(root)

    def _show_toast(self, text):
        popup = Popup(
            title='提示', content=Label(text=text),
            size_hint=(0.8, None), height=dp(120),
            auto_dismiss=True
        )
        popup.open()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: popup.dismiss(), 3)

    def _import_excel(self):
        log("_import_excel 被调用")
        try:
            from plyer import filechooser
            log("plyer filechooser 准备启动")
            filechooser.open_file(
                on_selection=self._on_file_selected,
                filters=[['Excel', '*.xlsx', '*.xls']],
            )
            log("filechooser 已启动")
        except Exception as e:
            import traceback
            log(f"_import_excel 异常: {e}")
            traceback.print_exc()
            self._show_toast('文件选择失败，请检查权限')

    def _on_file_selected(self, selection):
        if selection:
            from kivy.clock import Clock
            filepath = selection[0]
            log(f"文件已选中: {filepath}")
            Clock.schedule_once(lambda dt: self._load_excel(filepath))

    def _load_excel(self, filepath):
        from core.data_handler import read_excel as _read_excel
        self.info_label.text = '正在读取...'
        log(f"_load_excel 开始: {filepath}")
        import threading

        def _do():
            try:
                df = _read_excel(filepath)
                log(f"read_excel 完成: {len(df)} 条")
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._on_excel_loaded(df))
            except Exception as e:
                import traceback
                traceback.print_exc()
                log(f"read_excel 异常: {e}")
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._on_excel_error(str(e)))

        threading.Thread(target=_do, daemon=True).start()

    def _on_excel_loaded(self, df):
        count = len(df)
        chains = df['接龙号'].nunique()
        self.df = df
        self.info_label.text = f'已加载 {count} 条订单，{chains} 个接龙'
        log(f"加载成功: {count} 条, {chains} 个接龙")
        self._show_preview()

    def _on_excel_error(self, err_msg):
        log(f"导入失败: {err_msg}")
        self.info_label.text = f'导入失败: {err_msg}'

    def _get_filtered(self):
        if self.df is None:
            return None
        start = end = None
        try:
            if self.chain_start.text.strip():
                start = int(self.chain_start.text.strip())
            if self.chain_end.text.strip():
                end = int(self.chain_end.text.strip())
        except ValueError:
            pass
        return filter_orders(self.df, start, end, self.cancel_check.active)

    def _show_preview(self):
        df = self._get_filtered()
        if df is None:
            return
        lines = [f'共 {len(df)} 条订单\n']
        for _, row in df.head(30).iterrows():
            lines.append(
                f"{row.get('接龙号','')} | {row.get('学生姓名','')} | "
                f"{row.get('商品名称','')} x{row.get('数量', 0)}"
            )
        if len(df) > 30:
            lines.append(f'\n... 还有 {len(df)-30} 条')
        self.preview_label.text = '\n'.join(lines)

    def _print_receipts(self):
        df = self._get_filtered()
        if df is None or len(df) == 0:
            self._show_toast('没有可打印的订单数据')
            return
        printer = get_default_printer('receipt')
        if not printer:
            self._show_toast('请先在打印机设置中添加收银小票打印机')
            return
        orders = group_orders_for_receipt(df)
        self._run_print(orders, receipt_html, printer, f'收银小票 {len(orders)} 张')

    def _print_cups(self):
        df = self._get_filtered()
        if df is None or len(df) == 0:
            self._show_toast('没有数据')
            return
        printer = get_default_printer('cup')
        if not printer:
            self._show_toast('请先设置杯贴打印机')
            return
        cup_df = df[df['商品名称'].apply(lambda x: is_cup_product(str(x)))]
        if len(cup_df) == 0:
            self._show_toast('没有匹配的杯贴商品')
            return
        cups = []
        for _, row in cup_df.iterrows():
            cups.append({
                'chain': row.get('接龙号', ''),
                'school': row.get('学校', ''),
                'grade': row.get('年段', ''),
                'class_name': row.get('班级', ''),
                'student': row.get('学生姓名', ''),
                'user_note': row.get('用户备注', ''),
                'time': row.get('下单时间', ''),
                'product_name': row.get('商品名称', ''),
                'qty': int(row.get('数量', 1)),
            })
        self._run_print(cups, lambda o: cup_label_html(o, o['product_name']), printer, f'杯贴 {len(cups)} 张')

    def _print_summary(self):
        self._show_toast('汇总单功能开发中')

    def _run_print(self, items, html_fn, printer, title):
        def do_print():
            ok = fail = 0
            import time
            for item in items:
                try:
                    html = html_fn(item)
                    feie_print(printer['sn'], html, printer.get('key', ''))
                    ok += 1
                    time.sleep(0.5)
                except Exception:
                    fail += 1
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self._show_toast(f'{title}\n成功: {ok}  失败: {fail}'))

        threading.Thread(target=do_print, daemon=True).start()
        self._show_toast(f'正在打印 {title}...')
