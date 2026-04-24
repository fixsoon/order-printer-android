"""期效标签打印主界面 - 左右分栏布局"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock
from datetime import datetime, timedelta
import threading

from core.storage import (
    get_categories, get_templates_by_category, get_food_sample_templates,
    get_default_operator, get_default_printer, add_ingredient_template,
    add_category, remove_category, add_operator, set_default_operator,
    get_operators, init_categories
)
from core.templates import ingredient_label_html, food_sample_label_html
from core.feie_api import print_html as feie_print
from core.config import STORAGE_TYPES, MEAL_TYPES, DEFAULT_LABEL_SN, DEFAULT_LABEL_KEY
from utils import log


# ============================================================
# 主界面 - 左右分栏
# ============================================================

class LabelMainScreen(Screen):
    """期效标签打印主界面 - 左右分栏"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._expanded_sections = {'ingredient': True, 'sample': False}
        self._selected_category = None
        self._selected_template = None
        self._build_ui()

    def on_enter(self):
        self._refresh_all()

    def _build_ui(self):
        # 根布局：左右分栏
        root = BoxLayout(padding=0, spacing=0)

        # 左侧栏：分类树
        left_panel = self._build_left_panel()
        root.add_widget(left_panel)

        # 右侧栏：模板列表 + 预览
        right_panel = self._build_right_panel()
        root.add_widget(right_panel)

        self.add_widget(root)

    def _build_left_panel(self):
        """左侧分类栏"""
        panel = BoxLayout(orientation='vertical', size_hint_x=0.38, padding=dp(8), spacing=dp(4))
        panel.bind(width=lambda *x: setattr(panel, 'size_hint_x', 0.38))

        # 标题
        panel.add_widget(Label(
            text='[b]标签分类[/b]', markup=True,
            size_hint_y=None, height=dp(40),
            font_size=dp(15)
        ))

        # 经手人提示
        self.op_label = Label(
            text='经手人: 未设置',
            size_hint_y=None, height=dp(28),
            color=(0.9, 0.3, 0.3, 1), font_size=dp(12)
        )
        panel.add_widget(self.op_label)

        # 分类列表（可滚动）
        self.category_scroll = ScrollView(size_hint_y=1)
        self.category_content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        self.category_content.bind(minimum_height=self.category_content.setter('height'))
        self.category_scroll.add_widget(self.category_content)
        panel.add_widget(self.category_scroll)

        # 添加分类按钮
        panel.add_widget(Button(
            text='+ 新增小类',
            size_hint_y=None, height=dp(36),
            background_color=(0.3, 0.7, 0.4, 1),
            font_size=dp(13),
            on_release=lambda x: self._show_add_category_popup()
        ))

        return panel

    def _build_right_panel(self):
        """右侧模板栏"""
        panel = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))

        # 右上角操作按钮行
        top_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        top_bar.add_widget(Button(
            text='+ 添加模板',
            background_color=(0.2, 0.6, 0.8, 1),
            font_size=dp(13),
            on_release=lambda x: self._on_add_template()
        ))
        top_bar.add_widget(Button(
            text='设置打印机',
            background_color=(0.5, 0.5, 0.5, 1),
            font_size=dp(13),
            on_release=lambda x: setattr(self.manager, 'current', 'printer')
        ))
        top_bar.add_widget(Button(
            text='经手人',
            background_color=(0.6, 0.3, 0.8, 1),
            font_size=dp(13),
            on_release=lambda x: self._show_operator_popup()
        ))
        panel.add_widget(top_bar)

        # 当前选中标题
        self.section_title = Label(
            text='请选择左侧分类',
            size_hint_y=None, height=dp(32),
            color=(0.3, 0.3, 0.3, 1), font_size=dp(14)
        )
        panel.add_widget(self.section_title)

        # 标签预览区
        preview_card = BoxLayout(orientation='vertical', padding=dp(8), size_hint_y=0.45)
        preview_card.canvas.before.clear()
        with preview_card.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            preview_card._bg_rect = Rectangle(pos=preview_card.pos, size=preview_card.size)
        preview_card.bind(pos=lambda *x: setattr(preview_card._bg_rect, 'pos', preview_card.pos))
        preview_card.bind(size=lambda *x: setattr(preview_card._bg_rect, 'size', preview_card.size))

        preview_card.add_widget(Label(
            text='[b]标签预览[/b]', markup=True,
            size_hint_y=None, height=dp(28),
            font_size=dp(13)
        ))

        # 预览画布（模拟标签外观）
        self.preview_box = BoxLayout(size_hint_y=1, padding=dp(6))
        self.preview_label = Label(
            text='选择模板查看预览',
            halign='center', valign='middle',
            color=(0.5, 0.5, 0.5, 1), font_size=dp(12)
        )
        self.preview_box.add_widget(self.preview_label)
        preview_card.add_widget(self.preview_box)
        panel.add_widget(preview_card)

        # 模板列表
        list_label = Label(
            text='模板列表',
            size_hint_y=None, height=dp(28),
            color=(0.4, 0.4, 0.4, 1), font_size=dp(13)
        )
        panel.add_widget(list_label)

        self.template_list = ScrollView(size_hint_y=0.5)
        self.template_content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))
        self.template_content.bind(minimum_height=self.template_content.setter('height'))
        self.template_list.add_widget(self.template_content)
        panel.add_widget(self.template_list)

        return panel

    def _build_category_tree(self):
        """构建分类树"""
        self.category_content.clear_widgets()
        init_categories()

        # ---- 期效标签（可展开）----
        ing_header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        ing_header.canvas.before.clear()
        with ing_header.canvas.before:
            Color(0.9, 0.55, 0.2, 1)
            ing_header._bg = Rectangle(pos=ing_header.pos, size=ing_header.size)
        ing_header.bind(pos=lambda *x: setattr(ing_header._bg, 'pos', ing_header.pos))
        ing_header.bind(size=lambda *x: setattr(ing_header._bg, 'size', ing_header.size))

        arrow = '▼' if self._expanded_sections.get('ingredient') else '▶'
        ing_header.add_widget(Button(
            text=f'{arrow} 期效标签',
            background_color=(0, 0, 0, 0),
            bold=True, font_size=dp(14),
            on_release=lambda x: self._toggle_section('ingredient')
        ))
        self.category_content.add_widget(ing_header)

        # 期效标签子分类
        if self._expanded_sections.get('ingredient'):
            categories = get_categories()
            for cat in categories:
                cat_btn = Button(
                    text=f'  {cat["name"]}',
                    size_hint_y=None, height=dp(36),
                    background_color=(1, 1, 1, 0.3),
                    halign='left', valign='middle',
                    font_size=dp(13),
                    on_release=lambda x, c=cat['name']: self._select_category(c)
                )
                cat_btn.bind(size=lambda *_: setattr(cat_btn, 'text_size', (cat_btn.width - dp(16), None)))
                self.category_content.add_widget(cat_btn)

        # ---- 食品留样标签 ----
        sample_header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        sample_header.canvas.before.clear()
        with sample_header.canvas.before:
            Color(0.6, 0.3, 0.8, 1)
            sample_header._bg = Rectangle(pos=sample_header.pos, size=sample_header.size)
        sample_header.bind(pos=lambda *x: setattr(sample_header._bg, 'pos', sample_header.pos))
        sample_header.bind(size=lambda *x: setattr(sample_header._bg, 'size', sample_header.size))

        arrow = '▼' if self._expanded_sections.get('sample') else '▶'
        sample_header.add_widget(Button(
            text=f'{arrow} 食品留样标签',
            background_color=(0, 0, 0, 0),
            bold=True, font_size=dp(14),
            color=(1, 1, 1, 1),
            on_release=lambda x: self._toggle_section('sample')
        ))
        self.category_content.add_widget(sample_header)

        # 食品留样子分类
        if self._expanded_sections.get('sample'):
            sample_btn = Button(
                text='  留样记录',
                size_hint_y=None, height=dp(36),
                background_color=(1, 1, 1, 0.3),
                halign='left', valign='middle',
                font_size=dp(13),
                color=(1, 1, 1, 1),
                on_release=lambda x: self._select_sample()
            )
            sample_btn.bind(size=lambda *_: setattr(sample_btn, 'text_size', (sample_btn.width - dp(16), None)))
            self.category_content.add_widget(sample_btn)

    def _toggle_section(self, section):
        self._expanded_sections[section] = not self._expanded_sections.get(section, False)
        self._build_category_tree()

    def _select_category(self, category):
        """选择分类"""
        self._selected_category = category
        self._selected_template = None
        self.section_title.text = f'📦 {category}'
        self._load_templates(category)

    def _select_sample(self):
        """选择食品留样"""
        self._selected_category = '__sample__'
        self._selected_template = None
        self.section_title.text = '🍽 食品留样标签'
        self._load_sample_templates()

    def _load_templates(self, category):
        """加载分类下的模板"""
        templates = get_templates_by_category(category)
        self._render_template_list(templates, 'ingredient')

    def _load_sample_templates(self):
        """加载留样模板"""
        templates = get_food_sample_templates()
        self._render_template_list(templates, 'sample')

    def _render_template_list(self, templates, template_type):
        """渲染模板列表"""
        self.template_content.clear_widgets()
        self.template_content.size_hint_y = None
        self.template_content.height = dp(80) * max(len(templates), 1)

        if not templates:
            self.template_content.add_widget(Label(
                text='该分类暂无模板\n点击右上角「添加模板」',
                size_hint_y=None, height=dp(80),
                color=(0.6, 0.6, 0.6, 1), font_size=dp(12)
            ))
            self.preview_label.text = '选择模板查看预览'
            return

        for t in templates:
            card = self._make_template_card(t, template_type)
            self.template_content.add_widget(card)

    def _make_template_card(self, template, template_type):
        """生成模板卡片"""
        card = BoxLayout(orientation='vertical', padding=dp(8), size_hint_y=None, height=dp(76))
        card.canvas.before.clear()
        with card.canvas.before:
            Color(1, 1, 1, 1)
            card._bg = Rectangle(pos=card.pos, size=card.size)
        card.bind(pos=lambda *x: setattr(card._bg, 'pos', card.pos))
        card.bind(size=lambda *x: setattr(card._bg, 'size', card.size))

        # 品名 + 标签
        top_row = BoxLayout(size_hint_y=None, height=dp(24))
        name_label = Label(
            text=f'[b]{template["name"]}[/b]',
            markup=True, size_hint_x=0.6,
            halign='left', valign='middle',
            font_size=dp(14), color=(0.2, 0.2, 0.2, 1)
        )
        top_row.add_widget(name_label)

        # 储存温度标签
        if template_type == 'ingredient':
            storage = template.get('storage_type', '常温')
            color_map = {"常温": (0.9, 0.5, 0.2, 1), "冷冻": (0.2, 0.6, 0.9, 1), "冷藏": (0.2, 0.8, 0.4, 1)}
            btn_color = color_map.get(storage, (0.5, 0.5, 0.5, 1))
            storage_btn = Button(
                text=storage, size_hint_x=None, width=dp(50),
                background_color=btn_color, font_size=dp(10)
            )
            top_row.add_widget(storage_btn)

        # 操作按钮行
        bottom_row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(6))
        bottom_row.add_widget(Button(
            text='预览/打印',
            size_hint_x=0.5,
            background_color=(0.2, 0.6, 0.8, 1),
            font_size=dp(11),
            on_release=lambda x, t=template, ty=template_type: self._on_preview_print(t, ty)
        ))
        bottom_row.add_widget(Button(
            text='编辑',
            size_hint_x=0.25,
            background_color=(0.6, 0.6, 0.6, 1),
            font_size=dp(11),
            on_release=lambda x, t=template, ty=template_type: self._on_edit_template(t, ty)
        ))
        bottom_row.add_widget(Button(
            text='删除',
            size_hint_x=0.25,
            background_color=(0.9, 0.3, 0.3, 1),
            font_size=dp(11),
            on_release=lambda x, t=template, ty=template_type: self._on_delete_template(t, ty)
        ))
        card.add_widget(top_row)
        card.add_widget(bottom_row)

        # 点击卡片选中
        card.bind(on_touch_down=lambda inst, touch: self._on_card_tap(inst, touch, template, template_type))

        return card

    def _on_card_tap(self, card, touch, template, template_type):
        """点击卡片选中"""
        if card.collide_point(*touch.pos):
            self._selected_template = template
            self._update_preview(template, template_type)

    def _update_preview(self, template, template_type):
        """更新预览"""
        now = datetime.now()
        if template_type == 'ingredient':
            html = ingredient_label_html(
                template['name'],
                template.get('storage_type', '常温'),
                now,
                int(template.get('valid_hours', 24))
            )
        else:
            operator = get_default_operator()
            op_name = operator['name'] if operator else ''
            html = food_sample_label_html(
                template['name'],
                '午餐',
                now,
                template.get('default_weight', '150g'),
                op_name
            )

        # 简单预览文本
        if template_type == 'ingredient':
            expire = now + timedelta(hours=int(template.get('valid_hours', 24)))
            preview_text = (
                f'[b]{template["name"]}[/b]\n'
                f'储存: {template.get("storage_type", "常温")}\n'
                f'制作: {now.strftime("%m-%d %H:%M")}\n'
                f'有效至: {expire.strftime("%m-%d %H:%M")}'
            )
        else:
            preview_text = (
                f'[b]{template["name"]}[/b]\n'
                f'午餐 | {now.strftime("%m-%d %H:%M")}\n'
                f'{template.get("default_weight", "150g")} | '
                f'经手人: {get_default_operator()["name"] if get_default_operator() else "未设置"}'
            )

        self.preview_label.text = preview_text
        self.preview_label.markup = True

    def _on_preview_print(self, template, template_type):
        """预览打印"""
        if template_type == 'ingredient':
            self._show_ingredient_print_popup(template)
        else:
            self._show_sample_print_popup(template)

    def _show_ingredient_print_popup(self, template):
        """食材打印弹窗"""
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        content.add_widget(Label(
            text=f'[b]打印: {template["name"]}[/b]',
            markup=True, size_hint_y=None, height=dp(30)
        ))

        copies_row = BoxLayout(size_hint_y=None, height=dp(36))
        copies_row.add_widget(Label(text='打印份数:', size_hint_x=None, width=dp(70)))
        copy_input = TextInput(text='1', multiline=False, input_filter='int', size_hint_x=0.5)
        copies_row.add_widget(copy_input)
        content.add_widget(copies_row)

        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_row.add_widget(Button(
            text='取消',
            background_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: popup.dismiss()
        ))
        btn_row.add_widget(Button(
            text='打印',
            background_color=(0.2, 0.6, 0.8, 1),
            on_release=lambda x: self._do_print_ingredient(template, copy_input.text, popup)
        ))
        content.add_widget(btn_row)

        popup = Popup(
            title='食材期效标签打印',
            content=content,
            size_hint=(0.8, None), height=dp(200),
            auto_dismiss=True
        )
        popup.open()

    def _do_print_ingredient(self, template, copies_text, popup):
        """执行食材打印"""
        popup.dismiss()
        try:
            copies = int(copies_text) if copies_text.strip() else 1
        except ValueError:
            copies = 1

        now = datetime.now()
        printer = get_default_printer('label') or get_default_printer('cup')
        sn = DEFAULT_LABEL_SN
        key = DEFAULT_LABEL_KEY
        if printer:
            sn = printer.get('sn', sn)
            key = printer.get('key', key)

        def do():
            ok = 0
            for i in range(copies):
                try:
                    html = ingredient_label_html(
                        template['name'],
                        template.get('storage_type', '常温'),
                        now,
                        int(template.get('valid_hours', 24))
                    )
                    feie_print(sn, html, key)
                    ok += 1
                except Exception as e:
                    log(f'打印失败: {e}')

            Clock.schedule_once(lambda dt: self._show_toast(f'成功 {ok}/{copies} 张'))

        threading.Thread(target=do, daemon=True).start()
        self._show_toast(f'正在打印 {copies} 张...')

    def _show_sample_print_popup(self, template):
        """留样打印弹窗"""
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        content.add_widget(Label(
            text=f'[b]打印: {template["name"]}[/b]',
            markup=True, size_hint_y=None, height=dp(30)
        ))

        # 餐别选择
        meal_row = BoxLayout(size_hint_y=None, height=dp(36))
        meal_row.add_widget(Label(text='餐别:', size_hint_x=None, width=dp(70)))
        meal_spin = Spinner(text='午餐', values=MEAL_TYPES, size_hint_x=0.6)
        meal_row.add_widget(meal_spin)
        content.add_widget(meal_row)

        # 重量
        weight_row = BoxLayout(size_hint_y=None, height=dp(36))
        weight_row.add_widget(Label(text='留样重量:', size_hint_x=None, width=dp(70)))
        weight_input = TextInput(text=template.get('default_weight', '150g'), multiline=False, size_hint_x=0.6)
        weight_row.add_widget(weight_input)
        content.add_widget(weight_row)

        # 份数
        copies_row = BoxLayout(size_hint_y=None, height=dp(36))
        copies_row.add_widget(Label(text='打印份数:', size_hint_x=None, width=dp(70)))
        copy_input = TextInput(text='1', multiline=False, input_filter='int', size_hint_x=0.5)
        copies_row.add_widget(copy_input)
        content.add_widget(copies_row)

        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_row.add_widget(Button(
            text='取消',
            background_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: popup.dismiss()
        ))
        btn_row.add_widget(Button(
            text='打印',
            background_color=(0.6, 0.3, 0.8, 1),
            on_release=lambda x: self._do_print_sample(template, meal_spin.text, weight_input.text, copy_input.text, popup)
        ))
        content.add_widget(btn_row)

        popup = Popup(
            title='食品留样标签打印',
            content=content,
            size_hint=(0.85, None), height=dp(280),
            auto_dismiss=True
        )
        popup.open()

    def _do_print_sample(self, template, meal, weight, copies_text, popup):
        """执行留样打印"""
        popup.dismiss()
        try:
            copies = int(copies_text) if copies_text.strip() else 1
        except ValueError:
            copies = 1

        now = datetime.now()
        operator = get_default_operator()
        op_name = operator['name'] if operator else ''

        printer = get_default_printer('label') or get_default_printer('cup')
        sn = DEFAULT_LABEL_SN
        key = DEFAULT_LABEL_KEY
        if printer:
            sn = printer.get('sn', sn)
            key = printer.get('key', key)

        def do():
            ok = 0
            for i in range(copies):
                try:
                    html = food_sample_label_html(template['name'], meal, now, weight, op_name)
                    feie_print(sn, html, key)
                    ok += 1
                except Exception as e:
                    log(f'打印失败: {e}')

            Clock.schedule_once(lambda dt: self._show_toast(f'成功 {ok}/{copies} 张'))

        threading.Thread(target=do, daemon=True).start()
        self._show_toast(f'正在打印 {copies} 张...')

    def _on_add_template(self):
        """添加模板"""
        if self._selected_category == '__sample__':
            self._show_add_sample_template_popup()
        elif self._selected_category:
            self._show_add_ingredient_template_popup()
        else:
            self._show_toast('请先在左侧选择分类')

    def _show_add_ingredient_template_popup(self):
        """添加食材模板弹窗"""
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        content.add_widget(Label(
            text=f'[b]添加到: {self._selected_category}[/b]',
            markup=True, size_hint_y=None, height=dp(30)
        ))

        name_row = BoxLayout(size_hint_y=None, height=dp(36))
        name_row.add_widget(Label(text='品名:', size_hint_x=None, width=dp(70)))
        name_input = TextInput(hint_text='如: 芒果肉', multiline=False, size_hint_x=1)
        name_row.add_widget(name_input)
        content.add_widget(name_row)

        storage_row = BoxLayout(size_hint_y=None, height=dp(36))
        storage_row.add_widget(Label(text='储存温度:', size_hint_x=None, width=dp(70)))
        storage_spin = Spinner(text='常温', values=STORAGE_TYPES, size_hint_x=1)
        storage_row.add_widget(storage_spin)
        content.add_widget(storage_row)

        hours_row = BoxLayout(size_hint_y=None, height=dp(36))
        hours_row.add_widget(Label(text='有效时长:', size_hint_x=None, width=dp(70)))
        hours_input = TextInput(text='24', hint_text='24', multiline=False, input_filter='int', size_hint_x=0.5)
        hours_row.add_widget(hours_input)
        hours_row.add_widget(Label(text='小时', size_hint_x=None, width=dp(50)))
        content.add_widget(hours_row)

        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_row.add_widget(Button(
            text='取消',
            background_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: popup.dismiss()
        ))
        btn_row.add_widget(Button(
            text='保存',
            background_color=(0.2, 0.6, 0.8, 1),
            on_release=lambda x: self._save_ingredient_template(
                name_input.text, storage_spin.text, hours_input.text, popup
            )
        ))
        content.add_widget(btn_row)

        popup = Popup(
            title='新增食材模板',
            content=content,
            size_hint=(0.85, None), height=dp(250),
            auto_dismiss=True
        )
        popup.open()

    def _save_ingredient_template(self, name, storage, hours_text, popup):
        """保存食材模板"""
        name = name.strip()
        if not name:
            self._show_toast('请输入品名')
            return
        try:
            hours = int(hours_text) if hours_text.strip() else 24
        except ValueError:
            hours = 24

        add_ingredient_template(name, storage, hours, self._selected_category)
        popup.dismiss()
        self._show_toast(f'已保存: {name}')
        self._load_templates(self._selected_category)
        self._build_category_tree()

    def _show_add_sample_template_popup(self):
        """添加留样模板弹窗"""
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        content.add_widget(Label(
            text='[b]新增食品留样模板[/b]',
            markup=True, size_hint_y=None, height=dp(30)
        ))

        name_row = BoxLayout(size_hint_y=None, height=dp(36))
        name_row.add_widget(Label(text='食品名称:', size_hint_x=None, width=dp(80)))
        name_input = TextInput(hint_text='如: 红烧肉', multiline=False, size_hint_x=1)
        name_row.add_widget(name_input)
        content.add_widget(name_row)

        weight_row = BoxLayout(size_hint_y=None, height=dp(36))
        weight_row.add_widget(Label(text='默认重量:', size_hint_x=None, width=dp(80)))
        weight_input = TextInput(text='150g', hint_text='150g', multiline=False, size_hint_x=0.6)
        weight_row.add_widget(weight_input)
        content.add_widget(weight_row)

        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_row.add_widget(Button(
            text='取消',
            background_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: popup.dismiss()
        ))
        btn_row.add_widget(Button(
            text='保存',
            background_color=(0.6, 0.3, 0.8, 1),
            on_release=lambda x: self._save_sample_template(name_input.text, weight_input.text, popup)
        ))
        content.add_widget(btn_row)

        popup = Popup(
            title='新增留样模板',
            content=content,
            size_hint=(0.85, None), height=dp(200),
            auto_dismiss=True
        )
        popup.open()

    def _save_sample_template(self, name, weight, popup):
        """保存留样模板"""
        from core.storage import add_food_sample_template
        name = name.strip()
        if not name:
            self._show_toast('请输入食品名称')
            return
        add_food_sample_template(name, weight)
        popup.dismiss()
        self._show_toast(f'已保存: {name}')
        self._load_sample_templates()

    def _on_edit_template(self, template, template_type):
        """编辑模板"""
        if template_type == 'ingredient':
            self._show_edit_ingredient_popup(template)
        else:
            self._show_edit_sample_popup(template)

    def _show_edit_ingredient_popup(self, template):
        """编辑食材模板"""
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        content.add_widget(Label(
            text=f'[b]编辑: {template["name"]}[/b]',
            markup=True, size_hint_y=None, height=dp(30)
        ))

        name_row = BoxLayout(size_hint_y=None, height=dp(36))
        name_row.add_widget(Label(text='品名:', size_hint_x=None, width=dp(70)))
        name_input = TextInput(text=template['name'], multiline=False, size_hint_x=1)
        name_row.add_widget(name_input)
        content.add_widget(name_row)

        storage_row = BoxLayout(size_hint_y=None, height=dp(36))
        storage_row.add_widget(Label(text='储存温度:', size_hint_x=None, width=dp(70)))
        storage_spin = Spinner(text=template.get('storage_type', '常温'), values=STORAGE_TYPES, size_hint_x=1)
        storage_row.add_widget(storage_spin)
        content.add_widget(storage_row)

        hours_row = BoxLayout(size_hint_y=None, height=dp(36))
        hours_row.add_widget(Label(text='有效时长:', size_hint_x=None, width=dp(70)))
        hours_input = TextInput(text=str(template.get('valid_hours', 24)), multiline=False, input_filter='int', size_hint_x=0.5)
        hours_row.add_widget(hours_input)
        hours_row.add_widget(Label(text='小时', size_hint_x=None, width=dp(50)))
        content.add_widget(hours_row)

        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_row.add_widget(Button(
            text='取消',
            background_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: popup.dismiss()
        ))
        btn_row.add_widget(Button(
            text='保存',
            background_color=(0.2, 0.6, 0.8, 1),
            on_release=lambda x: self._do_edit_ingredient(
                template['id'], name_input.text, storage_spin.text, hours_input.text, popup
            )
        ))
        content.add_widget(btn_row)

        popup = Popup(
            title='编辑食材模板',
            content=content,
            size_hint=(0.85, None), height=dp(250),
            auto_dismiss=True
        )
        popup.open()

    def _do_edit_ingredient(self, template_id, name, storage, hours_text, popup):
        """执行编辑"""
        from core.storage import get_conn
        name = name.strip()
        if not name:
            self._show_toast('品名不能为空')
            return
        try:
            hours = int(hours_text) if hours_text.strip() else 24
        except ValueError:
            hours = 24

        conn = get_conn()
        conn.execute(
            "UPDATE ingredient_templates SET name=?, storage_type=?, valid_hours=? WHERE id=?",
            (name, storage, hours, template_id)
        )
        conn.commit()
        conn.close()

        popup.dismiss()
        self._show_toast(f'已更新: {name}')
        if self._selected_category:
            self._load_templates(self._selected_category)

    def _show_edit_sample_popup(self, template):
        """编辑留样模板"""
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        content.add_widget(Label(
            text=f'[b]编辑: {template["name"]}[/b]',
            markup=True, size_hint_y=None, height=dp(30)
        ))

        name_row = BoxLayout(size_hint_y=None, height=dp(36))
        name_row.add_widget(Label(text='食品名称:', size_hint_x=None, width=dp(80)))
        name_input = TextInput(text=template['name'], multiline=False, size_hint_x=1)
        name_row.add_widget(name_input)
        content.add_widget(name_row)

        weight_row = BoxLayout(size_hint_y=None, height=dp(36))
        weight_row.add_widget(Label(text='默认重量:', size_hint_x=None, width=dp(80)))
        weight_input = TextInput(text=template.get('default_weight', '150g'), multiline=False, size_hint_x=0.6)
        weight_row.add_widget(weight_input)
        content.add_widget(weight_row)

        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_row.add_widget(Button(
            text='取消',
            background_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: popup.dismiss()
        ))
        btn_row.add_widget(Button(
            text='保存',
            background_color=(0.6, 0.3, 0.8, 1),
            on_release=lambda x: self._do_edit_sample(template['id'], name_input.text, weight_input.text, popup)
        ))
        content.add_widget(btn_row)

        popup = Popup(
            title='编辑留样模板',
            content=content,
            size_hint=(0.85, None), height=dp(200),
            auto_dismiss=True
        )
        popup.open()

    def _do_edit_sample(self, template_id, name, weight, popup):
        """执行编辑留样"""
        from core.storage import get_conn
        name = name.strip()
        if not name:
            self._show_toast('名称不能为空')
            return

        conn = get_conn()
        conn.execute(
            "UPDATE food_sample_templates SET name=?, default_weight=? WHERE id=?",
            (name, weight, template_id)
        )
        conn.commit()
        conn.close()

        popup.dismiss()
        self._show_toast(f'已更新: {name}')
        self._load_sample_templates()

    def _on_delete_template(self, template, template_type):
        """删除模板"""
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        content.add_widget(Label(
            text=f'确定删除模板 "{template["name"]}" 吗？',
            size_hint_y=1
        ))
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_row.add_widget(Button(
            text='取消',
            background_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: popup.dismiss()
        ))
        btn_row.add_widget(Button(
            text='删除',
            background_color=(0.9, 0.3, 0.3, 1),
            on_release=lambda x: self._do_delete_template(template, template_type, popup)
        ))
        content.add_widget(btn_row)

        popup = Popup(
            title='确认删除',
            content=content,
            size_hint=(0.8, None), height=dp(150),
            auto_dismiss=True
        )
        popup.open()

    def _do_delete_template(self, template, template_type, popup):
        """执行删除"""
        from core.storage import remove_ingredient_template, remove_food_sample_template
        popup.dismiss()

        if template_type == 'ingredient':
            remove_ingredient_template(template['name'])
            if self._selected_category:
                self._load_templates(self._selected_category)
        else:
            remove_food_sample_template(template['name'])
            self._load_sample_templates()

        self._show_toast(f'已删除: {template["name"]}')

    def _show_add_category_popup(self):
        """新增小类弹窗"""
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        content.add_widget(Label(text='输入新分类名称', size_hint_y=1))
        name_input = TextInput(hint_text='如: 茶叶', multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(name_input)

        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_row.add_widget(Button(
            text='取消', background_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: popup.dismiss()
        ))
        btn_row.add_widget(Button(
            text='添加', background_color=(0.3, 0.7, 0.4, 1),
            on_release=lambda x: self._do_add_category(name_input.text, popup)
        ))
        content.add_widget(btn_row)

        popup = Popup(
            title='新增小类',
            content=content,
            size_hint=(0.8, None), height=dp(160),
            auto_dismiss=True
        )
        popup.open()

    def _do_add_category(self, name, popup):
        name = name.strip()
        if not name:
            self._show_toast('请输入分类名称')
            return
        add_category(name)
        popup.dismiss()
        self._show_toast(f'已添加: {name}')
        self._build_category_tree()

    def _show_operator_popup(self):
        """经手人设置弹窗"""
        operators = get_operators()
        default_op = get_default_operator()

        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(6))

        content.add_widget(Label(
            text='[b]经手人设置[/b]',
            markup=True, size_hint_y=None, height=dp(30)
        ))

        # 添加新经手人
        add_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        add_input = TextInput(hint_text='输入姓名', multiline=False, size_hint_x=1)
        add_row.add_widget(add_input)
        add_row.add_widget(Button(
            text='添加',
            size_hint_x=None, width=dp(60),
            background_color=(0.3, 0.7, 0.4, 1),
            on_release=lambda x: self._add_operator_and_refresh(add_input.text, popup)
        ))
        content.add_widget(add_row)

        # 列表
        list_view = ScrollView(size_hint_y=1)
        list_content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))
        list_content.bind(minimum_height=list_content.setter('height'))
        list_view.add_widget(list_content)
        content.add_widget(list_view)

        for op in operators:
            op_row = BoxLayout(size_hint_y=None, height=dp(36))
            is_default = default_op and default_op.get('name') == op['name']
            check = CheckBox(active=is_default, size_hint_x=None, width=dp(40))
            check.bind(active=lambda c, state, n=op['name']: self._set_default_operator(n, state, popup))
            op_row.add_widget(check)
            op_row.add_widget(Label(text=op['name'], halign='left', valign='middle'))
            if is_default:
                op_row.add_widget(Label(text='[默认]', markup=True, color=(0.2, 0.7, 0.3, 1)))
            list_content.add_widget(op_row)

        if not operators:
            list_content.add_widget(Label(
                text='暂无经手人，请添加',
                color=(0.6, 0.6, 0.6, 1), size_hint_y=None, height=dp(50)
            ))

        content.add_widget(Button(
            text='关闭',
            size_hint_y=None, height=dp(36),
            background_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: popup.dismiss()
        ))

        popup = Popup(
            title='经手人设置（全局生效）',
            content=content,
            size_hint=(0.85, None), height=dp(350),
            auto_dismiss=True
        )
        popup.open()

    def _add_operator_and_refresh(self, name, popup):
        name = name.strip()
        if not name:
            return
        add_operator(name)
        popup.dismiss()
        self._show_operator_popup()

    def _set_default_operator(self, name, state, popup):
        if state:
            set_default_operator(name)
            popup.dismiss()
            self._refresh_operator()
            self._show_toast(f'已设为默认经手人: {name}')

    def _refresh_all(self):
        self._build_category_tree()
        self._refresh_operator()
        self._refresh_printer_info()

    def _refresh_operator(self):
        default_op = get_default_operator()
        if default_op:
            self.op_label.text = f'经手人: {default_op["name"]}'
            self.op_label.color = (0.3, 0.6, 0.3, 1)
        else:
            self.op_label.text = '经手人: 未设置'
            self.op_label.color = (0.9, 0.3, 0.3, 1)

    def _refresh_printer_info(self):
        pass

    def _show_toast(self, text):
        popup = Popup(
            title='提示', content=Label(text=text),
            size_hint=(0.8, None), height=dp(100),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
