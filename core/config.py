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
