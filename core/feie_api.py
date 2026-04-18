"""飞鹅云打印 API 封装"""

import time
import hashlib
import requests
import json
from core.config import FEIE_USER, FEIE_UKEY, FEIE_API_URL


def _sign(user, ukey, stime):
    """生成 API 签名"""
    return hashlib.md5(f"{user}{ukey}{stime}".encode()).hexdigest()


def _post(action, data=None):
    """发送飞鹅 API 请求"""
    stime = str(int(time.time()))
    sig = _sign(FEIE_USER, FEIE_UKEY, stime)
    payload = {
        "user": FEIE_USER,
        "stime": stime,
        "sig": sig,
        "apiname": action,
    }
    if data:
        payload.update(data)
    resp = requests.post(FEIE_API_URL, data=payload, timeout=30)
    return resp.json()


def print_html(sn, content, key=""):
    """
    发送 HTML 内容到飞鹅打印机
    sn: 打印机编号
    content: HTML 格式的打印内容
    key: 打印机密钥（部分打印机需要）
    返回: 打印任务ID 或 None
    """
    data = {
        "sn": sn,
        "content": content,
    }
    if key:
        data["key"] = key

    result = _post("Open_printMsg", data)
    if result.get("ret") == 0:
        print_id = result.get("data")
        return print_id
    else:
        error = result.get("msg", "未知错误")
        raise Exception(f"打印失败: {error}")


def print_batch(sn_list, content, key=""):
    """
    批量打印到多台打印机
    sn_list: 打印机编号列表
    """
    results = []
    for sn in sn_list:
        try:
            pid = print_html(sn, content, key)
            results.append({"sn": sn, "success": True, "print_id": pid})
        except Exception as e:
            results.append({"sn": sn, "success": False, "error": str(e)})
    return results


def query_printer(sn):
    """查询打印机状态"""
    result = _post("Open_queryPrinterStatus", {"sn": sn})
    return result


def query_print_state(sn, print_id):
    """查询打印任务状态"""
    result = _post("Open_queryOrderState", {"sn": sn, "orderid": print_id})
    return result
