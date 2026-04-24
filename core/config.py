"""全局配置"""

# 飞鹅云 API 配置
FEIE_USER = "foulmosquito@163.com"
FEIE_UKEY = "xwvC5XcgSAy4AAGu"
FEIE_API_URL = "https://api.feieyun.cn/Api/Open/"
FEIE_SERVER = "https://api.feieyun.cn"

# 打印机默认配置
DEFAULT_RECEIPT_SN = "932613530"
DEFAULT_CUP_SN = "570202889"
DEFAULT_RECEIPT_KEY = ""
DEFAULT_CUP_KEY = "7bn46rwu"

# 小票排版
RECEIPT_WIDTH = 380  # 像素，58mm热敏纸

# 杯贴排版
LABEL_WIDTH = 380

# 学校与自提点映射
SCHOOL_PICKUP_MAP = {
    "音西一中": ["音西一中后门一厢门店取餐"],
    "文光中学": ["文光西门"],
    "滨江中学": ["滨江中学北门外卖架"],
    "二中东校区": ["二中东部校区"],
}

# 默认饮品规格选项
DEFAULT_TEMPERATURES = ["热", "温", "常温", "冰", "去冰"]
DEFAULT_SWEETNESS = ["正常糖", "少糖", "半糖", "微糖", "不另外加糖"]
DEFAULT_CUP_SIZES = ["大杯", "中杯", "小杯"]

# 期效标签尺寸：40mm x 30mm（飞鹅标签打印机）
LABEL_WIDTH_MM = 40
LABEL_HEIGHT_MM = 30
LABEL_DPI = 200  # 打印机 DPI
# 换算为像素：40mm * 200 / 25.4 ≈ 315px, 30mm * 200 / 25.4 ≈ 236px
LABEL_WIDTH_PX = int(LABEL_WIDTH_MM * LABEL_DPI / 25.4)
LABEL_HEIGHT_PX = int(LABEL_HEIGHT_MM * LABEL_DPI / 25.4)

# 储存温度选项
STORAGE_TYPES = ["常温", "冷冻", "冷藏"]

# 品类选项
INGREDIENT_CATEGORIES = ["水果", "罐头", "小料", "原料", "酱料", "其他"]

# 餐别选项
MEAL_TYPES = ["早餐", "午餐", "晚餐"]

# 标签打印机（期效标签用）
DEFAULT_LABEL_SN = "570202889"
DEFAULT_LABEL_KEY = "7bn46rwu"
