"""模板管理界面 - 食材期效模板 + 食品留样模板"""

from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.metrics import dp

from core.storage import (
    get_ingredient_templates, add_ingredient_template, remove_ingredient_template,
    get_food_sample_templates, add_food_sample_template, remove_food_sample_template,
)
from core.config import STORAGE_TYPES, INGREDIENT_CATEGORIES
from utils import log


# ============================================================
# 食材模板管理
# ============================================================

class IngredientTemplateScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        # 标题栏
        title_bar = BoxLayout(size_hint_y=None, height=dp(48))
        title_bar.add_widget(Button(
            text='← 返回', size_hint_x=None, width=dp(80),
            on_release=lambda x: setattr(self.manager, 'current', 'template_manage')
        ))
        title_bar.add_widget(Label(
            text='[b]食材期效模板[/b]', markup=True,
            halign='center', valign='middle', font_size=dp(18)
        ))
        title_bar.add_widget(Label(size_hint_x=None, width=dp(80)))
        root.add_widget(title_bar)

        # 添加区域
        form_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6))

        name_row = BoxLayout(size_hint_y=None, height=dp(40))
        name_row.add_widget(Label(text='品名:', size_hint_x=None, width=dp(60)))
        self.name_input = TextInput(hint_text='如: 芒果肉', multiline=False, size_hint_x=1)
        name_row.add_widget(self.name_input)
        form_box.add_widget(name_row)

        storage_row = BoxLayout(size_hint_y=None, height=dp(40))
        storage_row.add_widget(Label(text='储存:', size_hint_x=None, width=dp(60)))
        self.storage_spinner = Spinner(
            text='常温', values=STORAGE_TYPES,
            size_hint_x=1
        )
        storage_row.add_widget(self.storage_spinner)
        form_box.add_widget(storage_row)

        hours_row = BoxLayout(size_hint_y=None, height=dp(40))
        hours_row.add_widget(Label(text='有效期:', size_hint_x=None, width=dp(60)))
        self.hours_input = TextInput(hint_text='24', multiline=False, input_filter='int', size_hint_x=0.4)
        hours_row.add_widget(self.hours_input)
        hours_row.add_widget(Label(text=' 小时', size_hint_x=None, width=dp(50)))
        self.category_input = TextInput(hint_text='小料', multiline=False, size_hint_x=0.5)
        hours_row.add_widget(self.category_input)
        form_box.add_widget(hours_row)

        root.add_widget(form_box)

        root.add_widget(Button(
            text='+ 添加模板',
            size_hint_y=None, height=dp(44),
            background_color=(0.2, 0.6, 0.3, 1),
            on_release=lambda x: self._add_template()
        ))

        root.add_widget(Label(
            text='已保存的食材模板',
            size_hint_y=None, height=dp(25),
            halign='left', font_size=dp(13), color=(0.5, 0.5, 0.5, 1)
        ))

        self.list_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(self.list_container)
        root.add_widget(scroll)

        self.empty_label = Label(
            text='暂无模板，请添加', size_hint_y=None, height=dp(60),
            color=(0.6, 0.6, 0.6, 1)
        )
        root.add_widget(self.empty_label)

        self.add_widget(root)
        self._refresh_list()

    def _refresh_list(self):
        self.list_container.clear_children()
        templates = get_ingredient_templates()
        if not templates:
            self.empty_label.height = dp(60)
        else:
            self.empty_label.height = 0
            for t in templates:
                row = IngredientTemplateRow(
                    template=t,
                    on_delete=lambda n: self._delete_template(n)
                )
                self.list_container.add_widget(row)

    def _add_template(self):
        name = self.name_input.text.strip()
        storage = self.storage_spinner.text
        hours_text = self.hours_input.text.strip()
        category = self.category_input.text.strip()

        if not name:
            self._show_toast('请输入品名')
            return
        try:
            hours = int(hours_text) if hours_text else 24
        except ValueError:
            self._show_toast('有效期需为数字')
            return

        add_ingredient_template(name, storage, hours, category)
        self.name_input.text = ''
        self.hours_input.text = ''
        self._refresh_list()
        self._show_toast(f'已添加: {name}')

    def _delete_template(self, name):
        remove_ingredient_template(name)
        self._refresh_list()

    def _show_toast(self, text):
        popup = Popup(
            title='提示', content=Label(text=text),
            size_hint=(0.8, None), height=dp(100),
            auto_dismiss=True
        )
        popup.open()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)


class IngredientTemplateRow(BoxLayout):
    def __init__(self, template, on_delete, **kwargs):
        super().__init__(
            orientation='horizontal', size_hint_y=None, height=dp(44),
            spacing=dp(4), **kwargs
        )
        t = template
        info = f"{t['name']} | {t['storage_type']} | {t['valid_hours']}h"
        if t.get('category'):
            info += f" | {t['category']}"
        self.add_widget(Button(
            text=info, size_hint_x=1,
            background_color=(0.95, 0.95, 0.95, 1),
            color=(0.2, 0.2, 0.2, 1)
        ))
        self.add_widget(Button(
            text='删除', size_hint_x=None, width=dp(60),
            background_color=(0.9, 0.3, 0.3, 1),
            on_release=lambda x: on_delete(t['name'])
        ))


# ============================================================
# 留样模板管理
# ============================================================

class FoodSampleTemplateScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        # 标题栏
        title_bar = BoxLayout(size_hint_y=None, height=dp(48))
        title_bar.add_widget(Button(
            text='← 返回', size_hint_x=None, width=dp(80),
            on_release=lambda x: setattr(self.manager, 'current', 'template_manage')
        ))
        title_bar.add_widget(Label(
            text='[b]食品留样模板[/b]', markup=True,
            halign='center', valign='middle', font_size=dp(18)
        ))
        title_bar.add_widget(Label(size_hint_x=None, width=dp(80)))
        root.add_widget(title_bar)

        # 添加区域
        add_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.name_input = TextInput(hint_text='食品名称', multiline=False, size_hint_x=0.5)
        self.weight_input = TextInput(hint_text='150g', multiline=False, size_hint_x=0.25)
        add_box.add_widget(self.name_input)
        add_box.add_widget(self.weight_input)
        add_box.add_widget(Button(
            text='添加', size_hint_x=None, width=dp(70),
            background_color=(0.2, 0.6, 0.3, 1),
            on_release=lambda x: self._add_template()
        ))
        root.add_widget(add_box)

        root.add_widget(Label(
            text='已保存的留样模板',
            size_hint_y=None, height=dp(25),
            halign='left', font_size=dp(13), color=(0.5, 0.5, 0.5, 1)
        ))

        self.list_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(self.list_container)
        root.add_widget(scroll)

        self.empty_label = Label(
            text='暂无模板，请添加', size_hint_y=None, height=dp(60),
            color=(0.6, 0.6, 0.6, 1)
        )
        root.add_widget(self.empty_label)

        self.add_widget(root)
        self._refresh_list()

    def _refresh_list(self):
        self.list_container.clear_children()
        templates = get_food_sample_templates()
        if not templates:
            self.empty_label.height = dp(60)
        else:
            self.empty_label.height = 0
            for t in templates:
                row = FoodSampleTemplateRow(
                    template=t,
                    on_delete=lambda n: self._delete_template(n)
                )
                self.list_container.add_widget(row)

    def _add_template(self):
        name = self.name_input.text.strip()
        weight = self.weight_input.text.strip() or '150g'
        if not name:
            self._show_toast('请输入食品名称')
            return
        add_food_sample_template(name, weight)
        self.name_input.text = ''
        self._refresh_list()
        self._show_toast(f'已添加: {name}')

    def _delete_template(self, name):
        remove_food_sample_template(name)
        self._refresh_list()

    def _show_toast(self, text):
        popup = Popup(
            title='提示', content=Label(text=text),
            size_hint=(0.8, None), height=dp(100),
            auto_dismiss=True
        )
        popup.open()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)


class FoodSampleTemplateRow(BoxLayout):
    def __init__(self, template, on_delete, **kwargs):
        super().__init__(
            orientation='horizontal', size_hint_y=None, height=dp(44),
            spacing=dp(4), **kwargs
        )
        t = template
        info = f"{t['name']} | 默认: {t['default_weight']}"
        self.add_widget(Button(
            text=info, size_hint_x=1,
            background_color=(0.95, 0.95, 0.95, 1),
            color=(0.2, 0.2, 0.2, 1)
        ))
        self.add_widget(Button(
            text='删除', size_hint_x=None, width=dp(60),
            background_color=(0.9, 0.3, 0.3, 1),
            on_release=lambda x: on_delete(t['name'])
        ))


# ============================================================
# 模板管理主界面（入口）
# ============================================================

class TemplateManageScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))

        # 标题栏
        title_bar = BoxLayout(size_hint_y=None, height=dp(48))
        title_bar.add_widget(Button(
            text='← 返回', size_hint_x=None, width=dp(80),
            on_release=lambda x: setattr(self.manager, 'current', 'home')
        ))
        title_bar.add_widget(Label(
            text='[b]打印模板管理[/b]', markup=True,
            halign='center', valign='middle', font_size=dp(18)
        ))
        title_bar.add_widget(Label(size_hint_x=None, width=dp(80)))
        root.add_widget(title_bar)

        root.add_widget(Label(
            text='选择要管理的模板类型',
            size_hint_y=None, height=dp(30),
            color=(0.5, 0.5, 0.5, 1)
        ))

        root.add_widget(Button(
            text='🥭 食材期效模板\n（品名 / 储存温度 / 有效期）',
            size_hint_y=None, height=dp(90),
            background_color=(0.9, 0.55, 0.2, 1),
            font_size=dp(16),
            on_release=lambda x: setattr(self.manager, 'current', 'ingredient_template')
        ))

        root.add_widget(Button(
            text='🍽 食品留样模板\n（食品名称 / 默认重量）',
            size_hint_y=None, height=dp(90),
            background_color=(0.6, 0.3, 0.8, 1),
            font_size=dp(16),
            on_release=lambda x: setattr(self.manager, 'current', 'food_sample_template')
        ))

        self.add_widget(root)
