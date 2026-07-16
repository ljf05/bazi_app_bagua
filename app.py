import streamlit as st
import datetime
import plotly.graph_objects as go
import random
import base64
from enum import Enum
from typing import Dict, List, Tuple
from io import BytesIO
import os

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="命理小精灵 · 八字排盘",
    page_icon="🧚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== 基础数据 ====================

class FiveElements(Enum):
    WOOD = "木"
    FIRE = "火"
    EARTH = "土"
    METAL = "金"
    WATER = "水"

    @classmethod
    def generate(cls, ele):
        map = {
            cls.WOOD: cls.FIRE,
            cls.FIRE: cls.EARTH,
            cls.EARTH: cls.METAL,
            cls.METAL: cls.WATER,
            cls.WATER: cls.WOOD,
        }
        return map.get(ele)

    @classmethod
    def restrained(cls, ele):
        map = {
            cls.WOOD: cls.EARTH,
            cls.EARTH: cls.WATER,
            cls.WATER: cls.FIRE,
            cls.FIRE: cls.METAL,
            cls.METAL: cls.WOOD,
        }
        return map.get(ele)


TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
TIAN_GAN_INFO = {
    "甲": {"element": FiveElements.WOOD, "yin_yang": "阳"},
    "乙": {"element": FiveElements.WOOD, "yin_yang": "阴"},
    "丙": {"element": FiveElements.FIRE, "yin_yang": "阳"},
    "丁": {"element": FiveElements.FIRE, "yin_yang": "阴"},
    "戊": {"element": FiveElements.EARTH, "yin_yang": "阳"},
    "己": {"element": FiveElements.EARTH, "yin_yang": "阴"},
    "庚": {"element": FiveElements.METAL, "yin_yang": "阳"},
    "辛": {"element": FiveElements.METAL, "yin_yang": "阴"},
    "壬": {"element": FiveElements.WATER, "yin_yang": "阳"},
    "癸": {"element": FiveElements.WATER, "yin_yang": "阴"},
}

DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
DI_ZHI_INFO = {
    "子": {"element": FiveElements.WATER, "zodiac": "鼠", "hidden": [("癸", 1.0)]},
    "丑": {"element": FiveElements.EARTH, "zodiac": "牛", "hidden": [("己", 0.6), ("癸", 0.3), ("辛", 0.1)]},
    "寅": {"element": FiveElements.WOOD, "zodiac": "虎", "hidden": [("甲", 0.6), ("丙", 0.3), ("戊", 0.1)]},
    "卯": {"element": FiveElements.WOOD, "zodiac": "兔", "hidden": [("乙", 1.0)]},
    "辰": {"element": FiveElements.EARTH, "zodiac": "龙", "hidden": [("戊", 0.6), ("乙", 0.3), ("癸", 0.1)]},
    "巳": {"element": FiveElements.FIRE, "zodiac": "蛇", "hidden": [("丙", 0.6), ("庚", 0.3), ("戊", 0.1)]},
    "午": {"element": FiveElements.FIRE, "zodiac": "马", "hidden": [("丁", 0.7), ("己", 0.3)]},
    "未": {"element": FiveElements.EARTH, "zodiac": "羊", "hidden": [("己", 0.6), ("丁", 0.3), ("乙", 0.1)]},
    "申": {"element": FiveElements.METAL, "zodiac": "猴", "hidden": [("庚", 0.6), ("壬", 0.3), ("戊", 0.1)]},
    "酉": {"element": FiveElements.METAL, "zodiac": "鸡", "hidden": [("辛", 1.0)]},
    "戌": {"element": FiveElements.EARTH, "zodiac": "狗", "hidden": [("戊", 0.6), ("辛", 0.3), ("丁", 0.1)]},
    "亥": {"element": FiveElements.WATER, "zodiac": "猪", "hidden": [("壬", 0.7), ("甲", 0.3)]},
}

SOLAR_TERMS = [
    ("立春", 2, 4), ("惊蛰", 3, 6), ("清明", 4, 5), ("立夏", 5, 6),
    ("芒种", 6, 6), ("小暑", 7, 7), ("立秋", 8, 7), ("白露", 9, 8),
    ("寒露", 10, 8), ("立冬", 11, 7), ("大雪", 12, 7), ("小寒", 1, 6),
]

MONTH_ZHI_MAP = {
    "寅": "立春", "卯": "惊蛰", "辰": "清明", "巳": "立夏",
    "午": "芒种", "未": "小暑", "申": "立秋", "酉": "白露",
    "戌": "寒露", "亥": "立冬", "子": "大雪", "丑": "小寒",
}

# ==================== 全国城市经度库 ====================

CITY_LONGITUDE = {
    "北京": 116.4, "上海": 121.5, "天津": 117.2, "重庆": 106.5,
    "石家庄": 114.5, "唐山": 118.2, "秦皇岛": 119.6, "邯郸": 114.5,
    "邢台": 114.5, "保定": 115.5, "张家口": 114.9, "承德": 117.9,
    "沧州": 116.8, "廊坊": 116.7, "衡水": 115.7,
    "太原": 112.5, "大同": 113.3, "阳泉": 113.6, "长治": 113.1,
    "晋城": 112.9, "朔州": 112.4, "晋中": 112.8, "运城": 111.0,
    "忻州": 112.7, "临汾": 111.5, "吕梁": 111.1,
    "呼和浩特": 111.7, "包头": 109.8, "乌海": 106.8, "赤峰": 118.9,
    "通辽": 122.3, "鄂尔多斯": 110.0, "呼伦贝尔": 119.7,
    "巴彦淖尔": 107.4, "乌兰察布": 113.1, "兴安盟": 122.1,
    "锡林郭勒盟": 116.0, "阿拉善盟": 105.7,
    "沈阳": 123.4, "大连": 121.6, "鞍山": 123.0, "抚顺": 123.9,
    "本溪": 123.8, "丹东": 124.4, "锦州": 121.1, "营口": 122.2,
    "阜新": 121.7, "辽阳": 123.2, "盘锦": 122.1, "铁岭": 123.9,
    "朝阳": 120.5, "葫芦岛": 120.8,
    "长春": 125.3, "吉林市": 126.5, "四平": 124.4, "辽源": 125.1,
    "通化": 125.9, "白山": 126.4, "松原": 124.8, "白城": 122.8,
    "延边": 129.5,
    "哈尔滨": 126.6, "齐齐哈尔": 123.9, "鸡西": 130.9, "鹤岗": 130.3,
    "双鸭山": 131.2, "大庆": 125.1, "伊春": 128.9, "佳木斯": 130.4,
    "七台河": 131.0, "牡丹江": 129.6, "黑河": 127.5, "绥化": 126.9,
    "大兴安岭": 124.1,
    "南京": 118.8, "无锡": 120.3, "徐州": 117.2, "常州": 119.9,
    "苏州": 120.6, "南通": 120.9, "连云港": 119.2, "淮安": 119.0,
    "盐城": 120.1, "扬州": 119.4, "镇江": 119.4, "泰州": 119.9,
    "宿迁": 118.3,
    "杭州": 120.2, "宁波": 121.6, "温州": 120.7, "嘉兴": 120.8,
    "湖州": 120.1, "绍兴": 120.6, "金华": 119.6, "衢州": 118.9,
    "舟山": 122.2, "台州": 121.4, "丽水": 119.9,
    "合肥": 117.3, "芜湖": 118.4, "蚌埠": 117.3, "淮南": 116.9,
    "马鞍山": 118.5, "淮北": 116.8, "铜陵": 117.8, "安庆": 117.1,
    "黄山": 118.3, "滁州": 118.3, "阜阳": 115.8, "宿州": 117.0,
    "六安": 116.5, "亳州": 115.8, "池州": 117.5, "宣城": 118.8,
    "福州": 119.3, "厦门": 118.1, "莆田": 119.0, "三明": 117.6,
    "泉州": 118.6, "漳州": 117.7, "南平": 118.2, "龙岩": 117.0,
    "宁德": 119.5,
    "南昌": 115.9, "景德镇": 117.2, "萍乡": 113.9, "九江": 116.0,
    "新余": 114.9, "鹰潭": 117.0, "赣州": 114.9, "吉安": 115.0,
    "宜春": 114.4, "抚州": 116.4, "上饶": 118.0,
    "济南": 117.0, "青岛": 120.4, "淄博": 118.1, "枣庄": 117.3,
    "东营": 118.5, "烟台": 121.4, "潍坊": 119.1, "济宁": 116.6,
    "泰安": 117.1, "威海": 122.1, "日照": 119.5, "临沂": 118.3,
    "德州": 116.3, "聊城": 115.9, "滨州": 118.0, "菏泽": 115.4,
    "郑州": 113.7, "开封": 114.3, "洛阳": 112.4, "平顶山": 113.3,
    "安阳": 114.4, "鹤壁": 114.3, "新乡": 113.9, "焦作": 113.2,
    "濮阳": 115.1, "许昌": 113.8, "漯河": 114.0, "三门峡": 111.2,
    "南阳": 112.5, "商丘": 115.7, "信阳": 114.1, "周口": 114.6,
    "驻马店": 114.0, "济源": 112.6,
    "武汉": 114.3, "黄石": 115.1, "十堰": 110.8, "宜昌": 111.3,
    "襄阳": 112.2, "鄂州": 114.9, "荆门": 112.2, "孝感": 113.9,
    "荆州": 112.3, "黄冈": 114.9, "咸宁": 114.3, "随州": 113.4,
    "恩施": 109.5, "仙桃": 113.4, "潜江": 112.9, "天门": 113.2,
    "神农架": 110.7,
    "长沙": 113.0, "株洲": 113.1, "湘潭": 112.9, "衡阳": 112.6,
    "邵阳": 111.5, "岳阳": 113.1, "常德": 111.7, "张家界": 110.5,
    "益阳": 112.4, "郴州": 113.0, "永州": 111.6, "怀化": 110.0,
    "娄底": 112.0, "湘西": 109.7,
    "广州": 113.3, "韶关": 113.6, "深圳": 114.1, "珠海": 113.6,
    "汕头": 116.7, "佛山": 113.1, "江门": 113.1, "湛江": 110.4,
    "茂名": 110.9, "肇庆": 112.5, "惠州": 114.4, "梅州": 116.1,
    "汕尾": 115.4, "河源": 114.7, "阳江": 111.9, "清远": 113.0,
    "东莞": 113.7, "中山": 113.4, "潮州": 116.6, "揭阳": 116.4,
    "云浮": 112.0,
    "南宁": 108.4, "柳州": 109.4, "桂林": 110.3, "梧州": 111.3,
    "北海": 109.1, "防城港": 108.4, "钦州": 108.7, "贵港": 109.6,
    "玉林": 110.1, "百色": 106.6, "贺州": 111.5, "河池": 108.1,
    "来宾": 109.2, "崇左": 107.4,
    "海口": 110.3, "三亚": 109.5, "三沙": 112.3, "儋州": 109.6,
    "成都": 104.1, "自贡": 104.8, "攀枝花": 101.7, "泸州": 105.4,
    "德阳": 104.4, "绵阳": 104.7, "广元": 105.8, "遂宁": 105.6,
    "内江": 105.1, "乐山": 103.8, "南充": 106.1, "眉山": 103.8,
    "宜宾": 104.6, "广安": 106.6, "达州": 107.5, "雅安": 103.0,
    "巴中": 106.8, "资阳": 104.6, "阿坝": 102.2, "甘孜": 101.9,
    "凉山": 102.3,
    "贵阳": 106.7, "六盘水": 104.8, "遵义": 106.9, "安顺": 105.9,
    "毕节": 105.3, "铜仁": 109.2, "黔西南": 104.9, "黔东南": 107.9,
    "黔南": 107.5,
    "昆明": 102.7, "曲靖": 103.8, "玉溪": 102.5, "保山": 99.2,
    "昭通": 103.7, "丽江": 100.2, "普洱": 100.9, "临沧": 100.1,
    "楚雄": 101.5, "红河": 103.4, "文山": 104.2, "西双版纳": 100.8,
    "大理": 100.3, "德宏": 98.6, "怒江": 98.9, "迪庆": 99.7,
    "拉萨": 91.1, "日喀则": 88.9, "昌都": 97.2, "林芝": 94.4,
    "山南": 91.8, "那曲": 92.1, "阿里": 80.1,
    "西安": 108.9, "铜川": 109.1, "宝鸡": 107.1, "咸阳": 108.7,
    "渭南": 109.5, "延安": 109.5, "汉中": 107.0, "榆林": 109.7,
    "安康": 109.0, "商洛": 109.9,
    "兰州": 103.8, "嘉峪关": 98.3, "金昌": 102.2, "白银": 104.2,
    "天水": 105.7, "武威": 102.6, "张掖": 100.5, "平凉": 106.7,
    "酒泉": 98.5, "庆阳": 107.6, "定西": 104.6, "陇南": 104.9,
    "临夏": 103.2, "甘南": 102.9,
    "西宁": 101.8, "海东": 102.4, "海北": 100.9, "黄南": 102.0,
    "海南州": 101.5, "果洛": 100.3, "玉树": 97.0, "海西": 97.4,
    "银川": 106.3, "石嘴山": 106.4, "吴忠": 106.2, "固原": 106.3,
    "中卫": 105.2,
    "乌鲁木齐": 87.6, "克拉玛依": 84.9, "吐鲁番": 89.2, "哈密": 93.5,
    "昌吉": 87.3, "博尔塔拉": 82.1, "巴音郭楞": 86.1, "阿克苏": 80.3,
    "克孜勒苏": 76.1, "喀什": 76.0, "和田": 79.9, "伊犁": 81.3,
    "塔城": 83.0, "阿勒泰": 88.1, "石河子": 86.0, "五家渠": 87.5,
    "图木舒克": 79.1, "阿拉尔": 81.3,
    "香港": 114.2, "澳门": 113.5, "台北": 121.5, "高雄": 120.3,
    "台中": 120.7, "台南": 120.2, "新竹": 121.0, "基隆": 121.7,
    "嘉义": 120.4,
}


# ==================== 八字核心类 ====================

class BaziCalculator:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int = 0, longitude: float = 120.0):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.longitude = longitude
        self.bazi = {}
        self.five_elements = {}
        self.ten_gods = {}
        self.day_master = ""
        self.day_master_element = None
        self.month_order = ""
        self.wang_shuai = {}

        if self.hour == 23:
            self._adjust_for_late_night()

    def _adjust_for_late_night(self):
        self.day += 1
        if self.day > self._days_in_month(self.year, self.month):
            self.day = 1
            self.month += 1
            if self.month > 12:
                self.month = 1
                self.year += 1
        self.hour = 0

    def _days_in_month(self, year, month):
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif month in [4, 6, 9, 11]:
            return 30
        else:
            if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0):
                return 29
            return 28

    def _get_solar_term_month(self):
        if self.month == 1 and self.day < 6:
            return "丑", 12
        if self.month == 1 and self.day < 4:
            return "丑", 12
        if self.month == 2 and self.day >= 4:
            return "寅", 2
        for m, d, zhi in [
            (2, 4, "寅"), (3, 6, "卯"), (4, 5, "辰"), (5, 6, "巳"),
            (6, 6, "午"), (7, 7, "未"), (8, 7, "申"), (9, 8, "酉"),
            (10, 8, "戌"), (11, 7, "亥"), (12, 7, "子"),
        ]:
            if self.month == m and self.day >= d:
                return zhi, m
        return "寅", 2

    def _get_year_gan_zhi(self):
        if self.month == 1 or (self.month == 2 and self.day < 4):
            year = self.year - 1
        else:
            year = self.year
        offset = year - 1900
        gan_index = (offset + 6) % 10
        zhi_index = offset % 12
        return TIAN_GAN[gan_index], DI_ZHI[zhi_index]

    def _get_month_gan_zhi(self, year_gan):
        month_gan_map = {
            "甲": [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],
            "乙": [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "丙": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],
            "丁": [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],
            "戊": [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],
            "己": [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],
            "庚": [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "辛": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],
            "壬": [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],
            "癸": [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],
        }
        month_zhi, _ = self._get_solar_term_month()
        zhi_index = DI_ZHI.index(month_zhi)
        gan_index = month_gan_map[year_gan][zhi_index]
        return TIAN_GAN[gan_index], month_zhi

    def _get_day_gan_zhi(self):
        base = datetime.date(1900, 1, 1)
        target = datetime.date(self.year, self.month, self.day)
        offset = (target - base).days
        gan_index = (offset + 6) % 10
        zhi_index = offset % 12
        return TIAN_GAN[gan_index], DI_ZHI[zhi_index]

    def _get_hour_gan_zhi(self, day_gan):
        time_diff = (self.longitude - 120.0) * 4
        local_time = self.hour + self.minute / 60.0 + time_diff / 60.0
        if local_time >= 24:
            local_time -= 24
        elif local_time < 0:
            local_time += 24

        zhi_index = int((local_time + 1) // 2) % 12
        hour_zhi = DI_ZHI[zhi_index]

        hour_gan_map = {
            "甲": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],
            "乙": [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],
            "丙": [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],
            "丁": [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],
            "戊": [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "己": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],
            "庚": [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],
            "辛": [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],
            "壬": [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],
            "癸": [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        }
        gan_index = hour_gan_map[day_gan][zhi_index]
        return TIAN_GAN[gan_index], hour_zhi

    def _analyze_wang_shuai(self):
        day_gan = self.bazi["日柱"][0]
        day_element = TIAN_GAN_INFO[day_gan]["element"]
        month_zhi = self.bazi["月柱"][1]
        month_element = DI_ZHI_INFO[month_zhi]["element"]

        sheng = FiveElements.generate(month_element)
        ke = FiveElements.restrained(month_element)

        if day_element == month_element:
            strength = "旺"
        elif day_element == sheng:
            strength = "相"
        elif day_element == ke:
            strength = "休"
        else:
            if FiveElements.restrained(day_element) == month_element:
                strength = "囚"
            else:
                strength = "死"

        support_count = 0
        for pillar in self.bazi.values():
            gan = pillar[0]
            zhi = pillar[1]
            if TIAN_GAN_INFO[gan]["element"] == day_element:
                support_count += 1
            elif TIAN_GAN_INFO[gan]["element"] == FiveElements.generate(day_element):
                support_count += 0.5
            if DI_ZHI_INFO[zhi]["element"] == day_element:
                support_count += 1
            elif DI_ZHI_INFO[zhi]["element"] == FiveElements.generate(day_element):
                support_count += 0.5

        if strength in ["旺", "相"] and support_count > 2:
            final = "身旺"
        elif strength in ["囚", "死"] and support_count < 1.5:
            final = "身弱"
        else:
            final = "中和"

        self.wang_shuai = {"月令": strength, "生扶": f"{support_count:.1f}", "综合": final}
        self.month_order = month_zhi

    def calculate_bazi(self):
        year_gan, year_zhi = self._get_year_gan_zhi()
        month_gan, month_zhi = self._get_month_gan_zhi(year_gan)
        day_gan, day_zhi = self._get_day_gan_zhi()
        hour_gan, hour_zhi = self._get_hour_gan_zhi(day_gan)

        self.bazi = {
            "年柱": year_gan + year_zhi,
            "月柱": month_gan + month_zhi,
            "日柱": day_gan + day_zhi,
            "时柱": hour_gan + hour_zhi,
        }
        self.day_master = day_gan
        self.day_master_element = TIAN_GAN_INFO[day_gan]["element"]
        self._analyze_wang_shuai()
        return self.bazi

    def analyze_five_elements(self):
        elements_count = {e: 0.0 for e in FiveElements}
        for pillar_name, gan_zhi in self.bazi.items():
            gan = gan_zhi[0]
            zhi = gan_zhi[1]
            elements_count[TIAN_GAN_INFO[gan]["element"]] += 1.0
            elements_count[DI_ZHI_INFO[zhi]["element"]] += 1.0
            for hidden_gan, weight in DI_ZHI_INFO[zhi]["hidden"]:
                elements_count[TIAN_GAN_INFO[hidden_gan]["element"]] += weight

        result = {}
        for ele in FiveElements:
            count = elements_count[ele]
            if count >= 3.0:
                level = "旺"
            elif count >= 2.0:
                level = "偏旺"
            elif count >= 1.0:
                level = "平衡"
            elif count >= 0.5:
                level = "偏弱"
            else:
                level = "弱"
            result[ele.value] = {"score": f"{count:.1f}", "level": level}
        self.five_elements = result
        return result

    def get_ten_gods(self):
        ri_gan = self.bazi["日柱"][0]
        ri_index = TIAN_GAN.index(ri_gan)
        ri_yin_yang = TIAN_GAN_INFO[ri_gan]["yin_yang"]

        def get_god(gan):
            g_index = TIAN_GAN.index(gan)
            g_yin_yang = TIAN_GAN_INFO[gan]["yin_yang"]
            offset = (g_index - ri_index) % 10
            if offset == 0:
                return "比肩"
            elif offset == 1:
                return "劫财"
            elif offset == 2:
                return "食神" if ri_yin_yang == g_yin_yang else "伤官"
            elif offset == 3:
                return "伤官" if ri_yin_yang == g_yin_yang else "食神"
            elif offset == 4:
                return "偏财" if ri_yin_yang == g_yin_yang else "正财"
            elif offset == 5:
                return "正财" if ri_yin_yang == g_yin_yang else "偏财"
            elif offset == 6:
                return "七杀" if ri_yin_yang == g_yin_yang else "正官"
            elif offset == 7:
                return "正官" if ri_yin_yang == g_yin_yang else "七杀"
            elif offset == 8:
                return "偏印" if ri_yin_yang == g_yin_yang else "正印"
            elif offset == 9:
                return "正印" if ri_yin_yang == g_yin_yang else "偏印"
            return "未知"

        result = {}
        pillars = ["年柱", "月柱", "日柱", "时柱"]
        for i, pillar in enumerate(pillars):
            gan = self.bazi[pillar][0]
            if i == 2:
                result["日主"] = f"{gan}(日主)"
            else:
                result[f"{pillar}干"] = f"{gan}({get_god(gan)})"
        self.ten_gods = result
        return result

    def get_luck_years(self, gender="男"):
        month_zhi = self.bazi["月柱"][1]
        term_name = MONTH_ZHI_MAP.get(month_zhi, "立春")
        term_month, term_day = 2, 4
        for name, m, d in SOLAR_TERMS:
            if name == term_name:
                term_month, term_day = m, d
                break

        try:
            term_date = datetime.date(self.year, term_month, term_day)
            birth_date = datetime.date(self.year, self.month, self.day)
            diff_days = abs((birth_date - term_date).days)
        except:
            diff_days = 15

        start_age = max(1, int(diff_days / 3) + 1)

        luck_years = []
        year_gan = self.bazi["年柱"][0]
        is_yang = TIAN_GAN_INFO[year_gan]["yin_yang"] == "阳"

        for i in range(8):
            age_start = start_age + i * 10
            age_end = age_start + 9

            if (is_yang and gender == "男") or (not is_yang and gender == "女"):
                gan_idx = (TIAN_GAN.index(self.bazi["月柱"][0]) + i + 1) % 10
                zhi_idx = (DI_ZHI.index(self.bazi["月柱"][1]) + i + 1) % 12
            else:
                gan_idx = (TIAN_GAN.index(self.bazi["月柱"][0]) - i - 1) % 10
                zhi_idx = (DI_ZHI.index(self.bazi["月柱"][1]) - i - 1) % 12

            luck_years.append({
                "运程": f"{age_start}-{age_end}岁",
                "干支": TIAN_GAN[gan_idx] + DI_ZHI[zhi_idx],
                "五行": TIAN_GAN_INFO[TIAN_GAN[gan_idx]]["element"].value
            })
        return luck_years

    def get_current_year_analysis(self, current_year=None):
        if current_year is None:
            current_year = datetime.datetime.now().year

        offset = current_year - 1900
        gan_idx = (offset + 6) % 10
        zhi_idx = offset % 12
        year_gan = TIAN_GAN[gan_idx]
        year_zhi = DI_ZHI[zhi_idx]

        day_gan = self.bazi["日柱"][0]
        day_element = TIAN_GAN_INFO[day_gan]["element"]
        flow_element = TIAN_GAN_INFO[year_gan]["element"]

        if flow_element == day_element:
            impact = "比肩助身"
        elif flow_element == FiveElements.generate(day_element):
            impact = "印星生扶"
        elif day_element == FiveElements.generate(flow_element):
            impact = "食伤泄秀"
        elif flow_element == FiveElements.restrained(day_element):
            impact = "官杀克身"
        else:
            impact = "财星耗身"

        suggestions = {
            "比肩助身": "今天朋友运爆棚！快约好朋友一起玩吧~",
            "印星生扶": "今天超适合学习！脑子转得飞快！",
            "食伤泄秀": "今天灵感爆棚！有什么创作赶紧做！",
            "官杀克身": "今天压力有点大，记得对自己好一点~",
            "财星耗身": "今天财运不错，但花钱也猛，控制住手！",
        }

        return {
            "流年": f"{year_gan}{year_zhi}",
            "五行": flow_element.value,
            "生肖": DI_ZHI_INFO[year_zhi]["zodiac"],
            "对日主影响": impact,
            "运势建议": suggestions.get(impact, "流年平顺，稳中求进。")
        }

    def _generate_fortune_scores(self, gender="男"):
        luck_years = self.get_luck_years(gender)
        scores = []
        day_element = self.day_master_element

        for i, luck in enumerate(luck_years):
            gan = luck["干支"][0]
            gan_element = TIAN_GAN_INFO[gan]["element"]
            zhi = luck["干支"][1]
            zhi_element = DI_ZHI_INFO[zhi]["element"]

            base_score = 0
            if gan_element == FiveElements.generate(day_element):
                base_score += 2
            if zhi_element == FiveElements.generate(day_element):
                base_score += 1
            if gan_element == day_element:
                base_score += 1
            if zhi_element == day_element:
                base_score += 0.5
            if gan_element == FiveElements.restrained(day_element):
                base_score -= 2
            if zhi_element == FiveElements.restrained(day_element):
                base_score -= 1

            random.seed(i + self.year)
            noise = random.uniform(-1.5, 1.5)

            age_center = 30 + i * 10
            age_factor = 0
            if 20 <= age_center <= 50:
                age_factor = 1.5 * (1 - abs(age_center - 35) / 15)

            score = base_score + noise + age_factor
            score = max(-8, min(8, score))
            scores.append(round(score, 2))

        return scores

    def get_full_analysis(self, gender="男"):
        self.calculate_bazi()
        self.analyze_five_elements()
        self.get_ten_gods()

        weak_elements = [ele for ele, info in self.five_elements.items() if "弱" in info["level"]]

        advice = {}
        if weak_elements:
            advice["补益"] = f"五行{'、'.join(weak_elements)}偏弱，宜补此五行。"
        else:
            advice["补益"] = "五行分布均衡，无需特别补益。"

        element_color = {"木": "绿色", "火": "红色", "土": "黄色", "金": "白色", "水": "黑色"}
        advice["颜色"] = f"宜用颜色：{element_color.get(weak_elements[0] if weak_elements else self.day_master_element.value, '中性色')}"

        fortune_scores = self._generate_fortune_scores(gender)

        pet_data = generate_pet_data(self, gender)

        return {
            "八字": self.bazi,
            "日主": self.day_master,
            "日主五行": self.day_master_element.value,
            "月令": self.month_order,
            "旺衰": self.wang_shuai,
            "五行分布": self.five_elements,
            "十神": self.ten_gods,
            "大运": self.get_luck_years(gender),
            "流年": self.get_current_year_analysis(),
            "命理建议": advice,
            "运势得分": fortune_scores,
            "宠物": pet_data,
        }


# ==================== 🆕 增强版小精灵生成 ====================

def generate_pet_data(calc, gender):
    """根据八字和性别生成Q版小人的数据"""
    day_element = calc.day_master_element

    # ===== 男孩角色库 =====
    boy_map = {
        FiveElements.WOOD: {
            "emoji": "🌳", "name": "小森",
            "personality": "阳光开朗，像一棵大树给人安全感",
            "actions": ["张开双臂拥抱 🤗", "帅气地挥手 👋", "开心地跳起来 ✨"]
        },
        FiveElements.FIRE: {
            "emoji": "🔥", "name": "小火",
            "personality": "热情活泼，充满能量的小太阳",
            "actions": ["跳起来击掌 🖐️", "转圈圈 🔄", "比个耶 ✌️"]
        },
        FiveElements.EARTH: {
            "emoji": "🏔️", "name": "小山",
            "personality": "稳重可靠，是个值得信赖的小伙伴",
            "actions": ["拍拍胸脯 💪", "竖起大拇指 👍", "温和地微笑 😊"]
        },
        FiveElements.METAL: {
            "emoji": "⚔️", "name": "小锋",
            "personality": "果断干脆，做事雷厉风行",
            "actions": ["帅气地拨头发 💇", "眨眨眼睛 😉", "酷酷地点头 👌"]
        },
        FiveElements.WATER: {
            "emoji": "🌊", "name": "小浪",
            "personality": "灵活聪明，总有好主意",
            "actions": ["俏皮地眨眼 😉", "转个圈 🌀", "开心地欢呼 🎉"]
        },
    }

    # ===== 女孩角色库 =====
    girl_map = {
        FiveElements.WOOD: {
            "emoji": "🌸", "name": "小樱",
            "personality": "温柔治愈，像春风一样让人舒服",
            "actions": ["甜甜地微笑 😊", "轻轻挥手 👋", "害羞地捂脸 😳"]
        },
        FiveElements.FIRE: {
            "emoji": "🌺", "name": "小焰",
            "personality": "热情开朗，是人群中的小太阳",
            "actions": ["开心地转圈 🌀", "比个心 ❤️", "蹦蹦跳跳 🦘"]
        },
        FiveElements.EARTH: {
            "emoji": "🌻", "name": "小禾",
            "personality": "温柔大方，让人感觉踏实安心",
            "actions": ["轻轻拍拍你 🤗", "温暖地微笑 😊", "点点头 👍"]
        },
        FiveElements.METAL: {
            "emoji": "⭐", "name": "小星",
            "personality": "聪明伶俐，做事干净利落",
            "actions": ["俏皮地眨眼 😉", "拨一下头发 💇", "可爱地歪头 🤔"]
        },
        FiveElements.WATER: {
            "emoji": "💧", "name": "小雨",
            "personality": "温柔灵动，善解人意的小天使",
            "actions": ["歪头微笑 😊", "轻轻转圈 🌀", "比个爱心 ❤️"]
        },
    }

    if gender == "男":
        pet = boy_map.get(day_element, boy_map[FiveElements.WOOD])
        avatar_emoji = "👦"
    else:
        pet = girl_map.get(day_element, girl_map[FiveElements.WOOD])
        avatar_emoji = "👧"

    # 随机选一个动作
    action = random.choice(pet["actions"])

    # 今日运势
    flow = calc.get_current_year_analysis()
    flow_impact = flow["对日主影响"]

    today_tips = {
        "比肩助身": {
            "say": "今天朋友运爆棚！快约好朋友一起玩吧~",
            "eat": "火锅、烧烤（和朋友一起吃更香）",
            "play": "桌游、剧本杀、密室逃脱",
            "with": "老朋友、好兄弟/闺蜜",
            "fish": "开会时坐在后排，假装记笔记实际在刷手机 📱"
        },
        "印星生扶": {
            "say": "今天超适合学习！脑子转得飞快！",
            "eat": "核桃、坚果、鱼（补脑神器）",
            "play": "图书馆、书店、博物馆",
            "with": "学霸朋友、老师、导师",
            "fish": "看资料时顺便刷两页小说，看完还能说自己在查资料 😏"
        },
        "食伤泄秀": {
            "say": "今天灵感爆棚！有什么创作赶紧做！",
            "eat": "甜品、奶茶（激发灵感）",
            "play": "画画、写小说、拍视频",
            "with": "志同道合的朋友",
            "fish": "戴着耳机听音乐，别人以为你在专注工作，实际在听播客 🎧"
        },
        "官杀克身": {
            "say": "今天压力有点大，记得对自己好一点~",
            "eat": "热汤、面条（暖暖的很治愈）",
            "play": "散步、冥想、泡澡",
            "with": "自己待着，或者找最懂你的人聊聊",
            "fish": "假装在忙重要项目，实际在发呆放空，没人敢打扰你 😌"
        },
        "财星耗身": {
            "say": "今天财运不错，但花钱也猛，控制住手！",
            "eat": "性价比高的美食（别被宰了）",
            "play": "逛街只看不买、理财学习",
            "with": "会省钱的朋友",
            "fish": "对着电脑屏幕假装看报表，实际在看购物车 🛒"
        },
    }

    tip = today_tips.get(flow_impact, today_tips["比肩助身"])

    return {
        "avatar_emoji": avatar_emoji,
        "emoji": pet["emoji"],
        "name": pet["name"],
        "personality": pet["personality"],
        "action": action,
        "say": tip["say"],
        "eat": tip["eat"],
        "play": tip["play"],
        "with": tip["with"],
        "fish": tip["fish"],
    }


# ==================== 🆕 绘制K线图 ====================

def draw_life_k_line(scores: List[float]) -> go.Figure:
    ages = list(range(10, 81, 10))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ages,
        y=scores,
        mode='lines+markers+text',
        name='运势',
        line=dict(color='#FF6B35', width=3),
        marker=dict(
            size=10,
            color=['#FF4444' if s < 0 else '#00CC66' for s in scores],
            symbol='circle',
            line=dict(width=2, color='white')
        ),
        text=[f'{s:.1f}' for s in scores],
        textposition='top center',
        textfont=dict(size=10, color='#333'),
        hovertemplate='<b>%{x}岁</b><br>运势得分：%{y:.1f}<extra></extra>'
    ))

    fig.add_hline(y=0, line_dash="dash", line_color="#999", line_width=1, opacity=0.5)
    fig.add_hrect(y0=0, y1=10, line_width=0, fillcolor="rgba(0, 204, 102, 0.08)", opacity=0.5)
    fig.add_hrect(y0=-10, y1=0, line_width=0, fillcolor="rgba(255, 68, 68, 0.08)", opacity=0.5)

    key_ages = {30: "🔥 30岁", 40: "⭐ 40岁", 50: "💪 50岁"}
    for age, label in key_ages.items():
        if age in ages:
            idx = ages.index(age)
            fig.add_annotation(
                x=age,
                y=scores[idx] + 0.8 if scores[idx] >= 0 else scores[idx] - 0.8,
                text=label,
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1,
                arrowcolor="#FF6B35",
                font=dict(size=11, color="#FF6B35", family="Arial Black")
            )

    fig.update_layout(
        title=dict(text="📈 人生K线图 · 大运走势", font=dict(size=20, color="#333"), x=0.5),
        xaxis=dict(title="年龄（岁）", title_font=dict(size=14), tickfont=dict(size=12), tickmode='linear', dtick=10, range=[5, 85]),
        yaxis=dict(title="运势得分", title_font=dict(size=14), tickfont=dict(size=12), range=[-10, 10]),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=450,
        hovermode='x unified',
    )
    return fig


# ==================== 🆕 小精灵显示（GIF动图版 + 眨眼 + 语音） ====================

def display_pet(pet_data, gender):
    """显示Q版小精灵（直接播放MP4动画）"""
    st.divider()
    st.subheader("🧚 你的命理小精灵 · 今日指南")

    # ===== 你的MP4直接链接 =====
    boy_video_url = "https://github.com/ljf05/bazi_app_bagua/raw/refs/heads/main/boy.mp4"
    girl_video_url = "https://github.com/ljf05/bazi_app_bagua/raw/refs/heads/main/girl.mp4"

    # 根据性别选择视频和颜色
    if gender == "男":
        video_url = boy_video_url
        primary_color = "#1976D2"
        light_color = "#e3f2fd"
    else:
        video_url = girl_video_url
        primary_color = "#C62828"
        light_color = "#fce4ec"

    # 随机选择一个动作描述（仅用于文字显示）
    action_text = random.choice(["开心挥手", "比心微笑", "蹦跳开心", "转圈圈", "打招呼", "卖个萌"])

    col1, col2 = st.columns([1, 2])

    with col1:
        # 使用HTML5 video标签播放MP4，实现自动循环播放（像GIF一样）
        st.markdown(f"""
        <div style="text-align: center; padding: 10px;">
            <div style="display: inline-block; animation: float 3s ease-in-out infinite;">
                <video autoplay muted loop playsinline style="width: 150px; height: 150px; border-radius: 20px; object-fit: cover; box-shadow: 0 4px 20px rgba(0,0,0,0.10);">
                    <source src="{video_url}" type="video/mp4">
                    您的浏览器不支持视频播放。
                </video>
            </div>
            <div style="margin-top: 8px; font-size: 14px; font-weight: bold; color: {primary_color};">
                {pet_data['name']}
            </div>
            <div style="font-size: 13px; color: #888;">
                {gender}孩 · {action_text}
            </div>
        </div>
        <style>
        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0px); }}
        }}
        </style>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: #f8f9fa; border-radius: 16px; padding: 16px 20px; min-height: 130px; display: flex; flex-direction: column; justify-content: center; border-left: 4px solid {primary_color};">
            <div style="font-size: 16px; color: #333;">💬 <b>“{pet_data['say']}”</b></div>
            <div style="font-size: 13px; color: #666; margin-top: 6px;">🎭 性格：{pet_data['personality']}</div>
        </div>
        """, unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(f"""
        <div style="background: #f8f9fa; border-radius: 16px; padding: 12px 16px; border-left: 4px solid #4CAF50;">
            <div style="font-size: 13px; color: #666;">⭐ <b>今日幸运物</b></div>
            <div style="font-size: 14px; color: #333;">🍽️ {pet_data['eat']}</div>
            <div style="font-size: 14px; color: #333;">🎮 {pet_data['play']}</div>
            <div style="font-size: 14px; color: #333;">👥 {pet_data['with']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fff8e1, #ffecb3); border-radius: 16px; padding: 12px 16px; border: 2px dashed #FF9800; min-height: 85px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 14px; font-weight: bold; color: #E65100;">🐟 今日摸鱼指南</div>
            <div style="font-size: 14px; color: #333;">{pet_data['fish']}</div>
        </div>
        """, unsafe_allow_html=True)

        
# ==================== 表情切换 ====================

def get_expression(level: str) -> str:
    """根据运势等级返回对应表情"""
    expressions = {
        "旺": "😍 超开心！运势爆棚！",
        "偏旺": "😊 心情不错，今天挺顺的~",
        "平衡": "🙂 平平淡淡才是真~",
        "偏弱": "😐 有点小低落，需要充充电",
        "弱": "😴 今天想躺平...休息一下",
    }
    return expressions.get(level, "😊")


# ==================== Streamlit 界面 ====================

st.title("☯ 生辰八字 · 五行命理排盘")
st.caption("🧚 基于《渊海子平》《三命通会》· 含真太阳时、节气月令、藏干权重 · 命理小精灵伴你左右")

# ===== 侧边栏：语音开关 =====
with st.sidebar:
    st.header("⚙️ 设置")
    voice_enabled = st.toggle("🔊 语音播报", value=True, help="开启后，排盘结果会自动语音播报今日运势")
    st.divider()
    st.caption("💡 小提示：\n• 把小精灵GIF放到同目录下\n• 男/女不同形象\n• 支持真太阳时校正")

# ===== 主表单 =====
with st.form("bazi_form"):
    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("📅 出生年份", min_value=1900, max_value=2100, value=2004, step=1)
        day = st.number_input("📆 出生日期", min_value=1, max_value=31, value=27, step=1)
        minute = st.number_input("🕐 出生分钟", min_value=0, max_value=59, value=30, step=1)
    with col2:
        month = st.number_input("📆 出生月份", min_value=1, max_value=12, value=2, step=1)
        hour = st.number_input("🕐 出生小时", min_value=0, max_value=23, value=12, step=1)
        gender = st.selectbox("👤 性别", ["男", "女"], index=0)  # index=0 表示默认选中"男"

    city = st.text_input("📍 出生城市（如：北京、上海、广州、驻马店）", value="驻马店")
    submitted = st.form_submit_button("🔮 排盘分析", use_container_width=True)

# ===== 结果展示 =====
if submitted:
    with st.spinner("🧚 小精灵正在为你排盘..."):
        longitude = CITY_LONGITUDE.get(city.strip(), 120.0)

        calc = BaziCalculator(year, month, day, hour, minute, longitude)
        result = calc.get_full_analysis(gender)

        st.divider()

        # 八字四柱
        cols = st.columns(4)
        pillars = ["年柱", "月柱", "日柱", "时柱"]
        for i, col in enumerate(cols):
            col.metric(pillars[i], result["八字"][pillars[i]])

        st.divider()

        # 日主 + 表情
        expression = get_expression(result["旺衰"]["综合"])
        st.markdown(f"**日主：{result['日主']}（{result['日主五行']}）** ｜ 月令：{result['月令']} ｜ 旺衰：{result['旺衰']['综合']} ｜ {expression}")

        # 五行分布
        st.subheader("五行分布")
        cols = st.columns(5)
        for i, (ele, info) in enumerate(result["五行分布"].items()):
            cols[i].metric(ele, info["score"], delta=info["level"])

        # 十神
        st.subheader("十神解析")
        st.write(" | ".join([f"{k}：{v}" for k, v in result["十神"].items()]))

        # 大运
        st.subheader("大运排盘")
        luck_text = " ｜ ".join([f"{l['运程']} {l['干支']}({l['五行']})" for l in result["大运"]])
        st.write(luck_text)

        # K线图
        st.divider()
        st.subheader("📈 人生K线图 · 大运走势")

        scores = result["运势得分"]
        if scores:
            fig = draw_life_k_line(scores)
            st.plotly_chart(fig, use_container_width=True)

            max_score = max(scores)
            max_age = 10 + scores.index(max_score) * 10
            min_score = min(scores)
            min_age = 10 + scores.index(min_score) * 10

            col1, col2, col3 = st.columns(3)
            col1.metric("📈 运势最高峰", f"{max_age}岁", delta=f"{max_score:.1f}分")
            col2.metric("📉 运势最低谷", f"{min_age}岁", delta=f"{min_score:.1f}分")
            avg_score = sum(scores) / len(scores)
            col3.metric("🌟 总体运势", "吉运偏多" if avg_score > 0 else "凶运偏多", delta=f"平均{avg_score:.1f}分")

        # 小精灵展示
        display_pet(result["宠物"], gender)

        # 语音播报
        if voice_enabled:
            try:
                from gtts import gTTS
                voice_text = f"你好，我是你的命理小精灵{result['宠物']['name']}。{result['宠物']['say']}今天适合吃{result['宠物']['eat']}，适合玩{result['宠物']['play']}，适合找{result['宠物']['with']}一起玩。"
                tts = gTTS(text=voice_text, lang='zh-cn', slow=False)
                audio_bytes = BytesIO()
                tts.write_to_fp(audio_bytes)
                audio_bytes.seek(0)
                audio_base64 = base64.b64encode(audio_bytes.read()).decode()
                st.markdown(f'<audio controls style="width:100%;margin-top:8px;"><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg"></audio>', unsafe_allow_html=True)
            except:
                st.warning("⚠️ 语音播报暂时不可用，请检查网络连接")

        # 流年
        st.divider()
        st.subheader(f"{datetime.datetime.now().year}年流年分析")
        flow = result["流年"]
        st.write(f"流年：{flow['流年']}（{flow['五行']}，生肖{flow['生肖']}）")
        st.write(f"影响：{flow['对日主影响']}")
        st.info(flow["运势建议"])

        # 命理建议
        st.subheader("📝 命理建议")
        for key, value in result["命理建议"].items():
            st.write(f"• {key}：{value}")

        st.caption("⚠️ 仅供传统文化学习参考 · 人生把握在自己手中 · 🧚 命理小精灵祝你天天开心！")
