"""主页 - 导入数据、筛选、打印操作"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp
from kivy.clock import Clock
import threading

from core.data_handler import read_excel, filter_orders, sort_by_school_chain, group_orders_for_receipt
from core.storage import get_default_printer, is_cup_product
from core.feie_api import print_html as feie_print
from core.templates import receipt_html, cup_label_html, summary_html


class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.df = None
        self._build_ui()

    def _build_ui(self):
        layout = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15))

        # 标题
        layout.add_widget(MDLabel(
            text="飞鹅餐饮订单打印",
            halign="center",
            font_style="H5",
            size_hint_y=None,
            height=dp(50),
        ))

        # 导入按钮
        layout.add_widget(MDRaisedButton(
            text="📂 导入 Excel 文件",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(48),
            on_release=lambda x: self._import_excel(),
        ))

        # 数据信息
        self.info_label = MDLabel(
            text="未加载数据",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30),
        )
        layout.add_widget(self.info_label)

        # 筛选区域
        filter_card = MDCard(
            padding=dp(10),
            size_hint_y=None,
            height=dp(120),
            elevation=2,
        )
        filter_box = MDBoxLayout(orientation="vertical", spacing=dp(5))
        filter_box.add_widget(MDLabel(
            text="接龙号范围筛选",
            font_style="Subtitle2",
            size_hint_y=None,
            height=dp(25),
        ))

        range_box = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
        self.chain_start = MDTextField(hint_text="起始号", mode="rectangle", size_hint_x=0.4)
        self.chain_end = MDTextField(hint_text="结束号", mode="rectangle", size_hint_x=0.4)
        range_box.add_widget(self.chain_start)
        range_box.add_widget(MDLabel(text="到", halign="center", size_hint_x=0.2))
        range_box.add_widget(self.chain_end)
        filter_box.add_widget(range_box)

        cancel_box = MDBoxLayout(size_hint_y=None, height=dp(30))
        self.cancel_check = MDCheckbox(active=True, size_hint_x=None, width=dp(30))
        cancel_box.add_widget(self.cancel_check)
        cancel_box.add_widget(MDLabel(text="排除已取消订单", size_hint_x=1))
        filter_box.add_widget(cancel_box)

        filter_card.add_widget(filter_box)
        layout.add_widget(filter_card)

        # 打印按钮区
        btn_box = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(48))
        btn_box.add_widget(MDRaisedButton(
            text="打印收银小票",
            on_release=lambda x: self._print_receipts(),
            md_bg_color=(0.2, 0.6, 0.8, 1),
        ))
        btn_box.add_widget(MDRaisedButton(
            text="打印饮品杯贴",
            on_release=lambda x: self._print_cups(),
            md_bg_color=(0.9, 0.5, 0.2, 1),
        ))
        layout.add_widget(btn_box)

        btn_box2 = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(48))
        btn_box2.add_widget(MDRaisedButton(
            text="打印汇总单",
            on_release=lambda x: self._print_summary(),
            md_bg_color=(0.3, 0.7, 0.3, 1),
        ))
        btn_box2.add_widget(MDRaisedButton(
            text="临时加单",
            on_release=lambda x: self._temp_order(),
            md_bg_color=(0.6, 0.3, 0.7, 1),
        ))
        layout.add_widget(btn_box2)

        # 数据预览
        self.preview_label = MDLabel(
            text="",
            halign="left",
            theme_text_color="Secondary",
        )
        scroll = MDScrollView()
        scroll.add_widget(self.preview_label)
        layout.add_widget(scroll)

        # 底部导航按钮
        nav_box = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(48))
        nav_box.add_widget(MDFlatButton(
            text="🖨 打印机设置",
            on_release=lambda x: self._goto("printer"),
        ))
        nav_box.add_widget(MDFlatButton(
            text="🥤 杯贴商品库",
            on_release=lambda x: self._goto("cup_products"),
        ))
        nav_box.add_widget(MDFlatButton(
            text="📐 排版预览",
            on_release=lambda x: self._goto("preview"),
        ))
        layout.add_widget(nav_box)

        self.add_widget(layout)

    def _goto(self, screen_name):
        self.manager.current = screen_name

    def _import_excel(self):
        """导入 Excel（使用 plyer 文件选择器）"""
        try:
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self._on_file_selected,
                filters=[["Excel", "*.xlsx", "*.xls"]],
            )
        except Exception:
            # plyer 不可用时弹出输入路径对话框
            dialog = MDDialog(
                title="输入文件路径",
                type="custom",
                content_cls=MDTextField(hint_text="/path/to/file.xlsx", mode="rectangle"),
                buttons=[
                    MDFlatButton(text="取消", on_release=lambda x: dialog.dismiss()),
                    MDRaisedButton(text="导入", on_release=lambda x: self._import_by_path(dialog)),
                ],
            )
            dialog.open()

    def _import_by_path(self, dialog):
        textfield = dialog.content_cls
        path = textfield.text.strip()
        dialog.dismiss()
        if path:
            self._load_excel(path)

    def _on_file_selected(self, selection):
        if selection:
            self._load_excel(selection[0])

    def _load_excel(self, filepath):
        self.info_label.text = "正在读取..."
        try:
            self.df = read_excel(filepath)
            count = len(self.df)
            chains = self.df["接龙号"].nunique()
            self.info_label.text = f"已加载 {count} 条订单，{chains} 个接龙"
            self._show_preview()
        except Exception as e:
            self.info_label.text = f"导入失败: {e}"

    def _get_filtered(self):
        if self.df is None:
            return None
        start = None
        end = None
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
        lines = [f"共 {len(df)} 条订单\n"]
        for _, row in df.head(50).iterrows():
            lines.append(
                f"{row.get('接龙号','')} | {row.get('学校','')} | "
                f"{row.get('学生姓名','')} | {row.get('商品名称','')} | "
                f"x{row.get('数量',0)} | ￥{row.get('商品金额',0)}"
            )
        if len(df) > 50:
            lines.append(f"\n... 还有 {len(df)-50} 条")
        self.preview_label.text = "\n".join(lines)

    def _print_receipts(self):
        df = self._get_filtered()
        if df is None or len(df) == 0:
            self._show_msg("没有可打印的订单数据")
            return
        printer = get_default_printer("receipt")
        if not printer:
            self._show_msg("请先在打印机设置中添加收银小票打印机")
            return

        orders = group_orders_for_receipt(df)
        self._run_print(orders, receipt_html, printer, f"收银小票 {len(orders)} 张")

    def _print_cups(self):
        df = self._get_filtered()
        if df is None or len(df) == 0:
            self._show_msg("没有数据")
            return
        printer = get_default_printer("cup")
        if not printer:
            self._show_msg("请先设置杯贴打印机")
            return

        cup_df = df[df["商品名称"].apply(lambda x: is_cup_product(str(x)))]
        if len(cup_df) == 0:
            self._show_msg("没有匹配的杯贴商品")
            return

        cups = []
        for _, row in cup_df.iterrows():
            cups.append({
                "chain": row.get("接龙号", ""),
                "school": row.get("学校", ""),
                "grade": row.get("年段", ""),
                "class_name": row.get("班级", ""),
                "student": row.get("学生姓名", ""),
                "user_note": row.get("用户备注", ""),
                "time": row.get("下单时间", ""),
                "product_name": row.get("商品名称", ""),
                "qty": int(row.get("数量", 1)),
            })

        self._run_print(cups, lambda o: cup_label_html(o, o["product_name"]), printer, f"杯贴 {len(cups)} 张")

    def _print_summary(self):
        df = self._get_filtered()
        if df is None or len(df) == 0:
            self._show_msg("没有数据")
            return
        self._show_msg("汇总单功能：请使用桌面版，或联系开发者适配")

    def _temp_order(self):
        self.manager.current = "temp_order"

    def _run_print(self, items, html_fn, printer, title):
        def do_print():
            ok = 0
            fail = 0
            for item in items:
                try:
                    html = html_fn(item)
                    feie_print(printer["sn"], html, printer.get("key", ""))
                    ok += 1
                    import time
                    time.sleep(0.5)
                except Exception:
                    fail += 1
            Clock.schedule_once(lambda dt: self._show_msg(f"{title}\n成功: {ok}  失败: {fail}"))

        threading.Thread(target=do_print, daemon=True).start()
        self._show_msg(f"正在打印 {title}...")

    def _show_msg(self, text):
        dialog = MDDialog(
            title="提示",
            text=text,
            buttons=[MDFlatButton(text="确定", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()
