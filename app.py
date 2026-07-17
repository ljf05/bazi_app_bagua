import streamlit as st
import datetime
import plotly.graph_objects as go
import random
import base64
import io
from enum import Enum
from typing import Dict, List, Tuple
from io import BytesIO
import os
from PIL import Image, ImageDraw, ImageFont
import qrcode
import requests
import time
import pandas as pd

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

CITY_LONGITUDE = {
    "北京": 116.4, "上海": 121.5, "天津": 117.2, "重庆": 106.5,
    "广州": 113.3, "深圳": 114.1, "杭州": 120.2, "成都": 104.1,
    "武汉": 114.3, "南京": 118.8, "西安": 108.9, "沈阳": 123.4,
    "昆明": 102.7, "长沙": 113.0, "郑州": 113.7, "济南": 117.0,
    "哈尔滨": 126.6, "长春": 125.3, "兰州": 103.8, "西宁": 101.8,
    "拉萨": 91.1, "乌鲁木齐": 87.6, "呼和浩特": 111.7, "南宁": 108.4,
    "海口": 110.3, "台北": 121.5, "香港": 114.2, "澳门": 113.5,
    "太原": 112.5, "石家庄": 114.5, "合肥": 117.3, "福州": 119.3,
    "南昌": 115.9, "贵阳": 106.7, "银川": 106.3, "驻马店": 114.0,
}

# ==================== 今日黄历 ====================
def get_today_almanac():
    try:
        from lunar_python import Lunar
        today = datetime.datetime.now()
        lunar = Lunar.fromDate(today)
        day = lunar.getDay()
        yi = day.getYi() if hasattr(day, 'getYi') else ["出行", "签约", "会友", "祈福", "求财"]
        ji = day.getJi() if hasattr(day, 'getJi') else ["动土", "安葬", "开市"]
        lunar_date = f"{lunar.getYear()}年{lunar.getMonth()}月{lunar.getDay()}日"
        zodiac = lunar.getYearZodiac() if hasattr(lunar, 'getYearZodiac') else "龙"
        return {"lunar_date": lunar_date, "zodiac": zodiac, "yi": yi[:5], "ji": ji[:5]}
    except:
        return {"lunar_date": "农历五月廿八", "zodiac": "龙", "yi": ["出行", "签约", "会友", "祈福", "求财"], "ji": ["动土", "安葬", "开市", "破土"]}

# ==================== 八字配对 ====================
def bazi_match(bazi1, bazi2):
    day_element1 = TIAN_GAN_INFO[bazi1["日柱"][0]]["element"]
    day_element2 = TIAN_GAN_INFO[bazi2["日柱"][0]]["element"]
    if day_element1 == day_element2:
        element_score = 80
        element_desc = "五行相同，志趣相投"
    elif day_element2 == FiveElements.generate(day_element1):
        element_score = 95
        element_desc = "相生关系，互相成就"
    elif day_element1 == FiveElements.generate(day_element2):
        element_score = 90
        element_desc = "相生关系，互补互益"
    elif day_element2 == FiveElements.restrained(day_element1):
        element_score = 60
        element_desc = "相克关系，需要磨合"
    elif day_element1 == FiveElements.restrained(day_element2):
        element_score = 55
        element_desc = "相克关系，互相制约"
    else:
        element_score = 70
        element_desc = "五行平衡，相处融洽"
    yin_yang1 = TIAN_GAN_INFO[bazi1["日柱"][0]]["yin_yang"]
    yin_yang2 = TIAN_GAN_INFO[bazi2["日柱"][0]]["yin_yang"]
    if yin_yang1 != yin_yang2:
        yy_score = 20
        yy_desc = "阴阳互补，相互吸引"
    else:
        yy_score = 10
        yy_desc = "阴阳相同，气场相近"
    total_score = min(100, element_score + yy_score + random.randint(-5, 5))
    if total_score >= 85:
        advice = "天作之合！你们在五行和性格上都非常契合，是令人羡慕的佳偶。"
    elif total_score >= 70:
        advice = "良缘佳配！你们在一起能够互相成就，共同成长。"
    elif total_score >= 55:
        advice = "缘分天成！虽然偶有摩擦，但彼此珍惜就能长久。"
    else:
        advice = "需要更多包容和理解，多沟通会让关系更和谐。"
    return {"score": total_score, "element_desc": element_desc, "yy_desc": yy_desc, "advice": advice}

# ==================== 命理答题 ====================
# ==================== 命理答题 ====================
def get_quiz_result(answers):
    element_scores = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for answer in answers:
        if answer in element_scores:
            element_scores[answer] += 1
    max_element = max(element_scores, key=element_scores.get)
    max_score = element_scores[max_element]
    personality_map = {
        "木": {
            "title": "🌳 木命人 · 温暖治愈型",
            "desc": "你像一棵大树，给人安全感和温暖。性格温和、善良、有耐心，善于倾听和关心他人。",
            "strengths": "善良、有爱心、善于倾听、包容性强",
            "weaknesses": "有时过于优柔寡断、容易心软",
            "advice": "适合从事教育、医疗、心理咨询、文化创作等工作。",
            "color": "#4CAF50"
        },
        "火": {
            "title": "🔥 火命人 · 热情开朗型",
            "desc": "你像一团火焰，充满能量和热情。性格外向、积极、有感染力。",
            "strengths": "热情、自信、有领导力、行动力强",
            "weaknesses": "有时冲动、缺乏耐心、容易急躁",
            "advice": "适合从事销售、管理、演讲、演艺等工作。",
            "color": "#F44336"
        },
        "土": {
            "title": "🏔️ 土命人 · 稳重可靠型",
            "desc": "你像大地一样厚重可靠，是朋友最信任的依靠。",
            "strengths": "稳重、可靠、诚信、有责任心",
            "weaknesses": "有时保守固执、缺乏灵活性",
            "advice": "适合从事建筑、管理、金融、法律等工作。",
            "color": "#FF9800"
        },
        "金": {
            "title": "⚔️ 金命人 · 果断干练型",
            "desc": "你像金属一样坚硬锋利，做事果断利落。",
            "strengths": "果断、理性、有魄力、执行力强",
            "weaknesses": "有时过于强势、缺乏同理心",
            "advice": "适合从事技术、法律、管理、创业等工作。",
            "color": "#616161"
        },
        "水": {
            "title": "🌊 水命人 · 灵活智慧型",
            "desc": "你像水一样灵动多变，充满智慧。",
            "strengths": "聪明、灵活、善于思考、适应力强",
            "weaknesses": "有时过于犹豫、缺乏决断力",
            "advice": "适合从事科研、咨询、策划、创作等工作。",
            "color": "#0D47A1"
        }
    }
    result = personality_map[max_element]
    result["score"] = max_score
    result["element"] = max_element
    result["scores"] = element_scores
    return result

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
        advice["颜色"] = f"{element_color.get(weak_elements[0] if weak_elements else self.day_master_element.value, '中性色')}"
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

# ==================== 小精灵生成 ====================
def generate_pet_data(calc, gender):
    day_element = calc.day_master_element
    boy_map = {
        FiveElements.WOOD: {"emoji": "🌳", "name": "小森", "personality": "阳光开朗，像一棵大树给人安全感", "actions": ["张开双臂拥抱 🤗", "帅气地挥手 👋", "开心地跳起来 ✨"]},
        FiveElements.FIRE: {"emoji": "🔥", "name": "小火", "personality": "热情活泼，充满能量的小太阳", "actions": ["跳起来击掌 🖐️", "转圈圈 🔄", "比个耶 ✌️"]},
        FiveElements.EARTH: {"emoji": "🏔️", "name": "小山", "personality": "稳重可靠，是个值得信赖的小伙伴", "actions": ["拍拍胸脯 💪", "竖起大拇指 👍", "温和地微笑 😊"]},
        FiveElements.METAL: {"emoji": "⚔️", "name": "小锋", "personality": "果断干脆，做事雷厉风行", "actions": ["帅气地拨头发 💇", "眨眨眼睛 😉", "酷酷地点头 👌"]},
        FiveElements.WATER: {"emoji": "🌊", "name": "小浪", "personality": "灵活聪明，总有好主意", "actions": ["俏皮地眨眼 😉", "转个圈 🌀", "开心地欢呼 🎉"]},
    }
    girl_map = {
        FiveElements.WOOD: {"emoji": "🌸", "name": "小樱", "personality": "温柔治愈，像春风一样让人舒服", "actions": ["甜甜地微笑 😊", "轻轻挥手 👋", "害羞地捂脸 😳"]},
        FiveElements.FIRE: {"emoji": "🌺", "name": "小焰", "personality": "热情开朗，是人群中的小太阳", "actions": ["开心地转圈 🌀", "比个心 ❤️", "蹦蹦跳跳 🦘"]},
        FiveElements.EARTH: {"emoji": "🌻", "name": "小禾", "personality": "温柔大方，让人感觉踏实安心", "actions": ["轻轻拍拍你 🤗", "温暖地微笑 😊", "点点头 👍"]},
        FiveElements.METAL: {"emoji": "⭐", "name": "小星", "personality": "聪明伶俐，做事干净利落", "actions": ["俏皮地眨眼 😉", "拨一下头发 💇", "可爱地歪头 🤔"]},
        FiveElements.WATER: {"emoji": "💧", "name": "小雨", "personality": "温柔灵动，善解人意的小天使", "actions": ["歪头微笑 😊", "轻轻转圈 🌀", "比个爱心 ❤️"]},
    }
    if gender == "男":
        pet = boy_map.get(day_element, boy_map[FiveElements.WOOD])
        avatar_emoji = "👦"
    else:
        pet = girl_map.get(day_element, girl_map[FiveElements.WOOD])
        avatar_emoji = "👧"
    action = random.choice(pet["actions"])
    flow = calc.get_current_year_analysis()
    flow_impact = flow["对日主影响"]
    today_tips = {
        "比肩助身": {"say": "今天朋友运爆棚！快约好朋友一起玩吧~", "eat": "火锅、烧烤（和朋友一起吃更香）", "play": "桌游、剧本杀、密室逃脱", "with": "老朋友、好兄弟/闺蜜", "fish": "开会时坐在后排，假装记笔记实际在刷手机 📱"},
        "印星生扶": {"say": "今天超适合学习！脑子转得飞快！", "eat": "核桃、坚果、鱼（补脑神器）", "play": "图书馆、书店、博物馆", "with": "学霸朋友、老师、导师", "fish": "看资料时顺便刷两页小说，看完还能说自己在查资料 😏"},
        "食伤泄秀": {"say": "今天灵感爆棚！有什么创作赶紧做！", "eat": "甜品、奶茶（激发灵感）", "play": "画画、写小说、拍视频", "with": "志同道合的朋友", "fish": "戴着耳机听音乐，别人以为你在专注工作，实际在听播客 🎧"},
        "官杀克身": {"say": "今天压力有点大，记得对自己好一点~", "eat": "热汤、面条（暖暖的很治愈）", "play": "散步、冥想、泡澡", "with": "自己待着，或者找最懂你的人聊聊", "fish": "假装在忙重要项目，实际在发呆放空，没人敢打扰你 😌"},
        "财星耗身": {"say": "今天财运不错，但花钱也猛，控制住手！", "eat": "性价比高的美食（别被宰了）", "play": "逛街只看不买、理财学习", "with": "会省钱的朋友", "fish": "对着电脑屏幕假装看报表，实际在看购物车 🛒"},
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

# ==================== K线图 ====================
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

# ==================== 显示小精灵 ====================
def display_pet(pet_data, gender):
    st.divider()
    st.subheader("🧚 你的命理小精灵 · 今日指南")
    boy_video_url = "https://gitee.com/lijiangfeng2005/bazi_app/raw/main/boy.mp4"
    girl_video_url = "https://gitee.com/lijiangfeng2005/bazi_app/raw/main/girl.mp4"
    if gender == "男":
        video_url = boy_video_url
        primary_color = "#1976D2"
        light_color = "#e3f2fd"
    else:
        video_url = girl_video_url
        primary_color = "#C62828"
        light_color = "#fce4ec"
    action_text = random.choice(["开心挥手", "比心微笑", "蹦跳开心", "转圈圈", "打招呼", "卖个萌"])
    col1, col2 = st.columns([1, 2])
    with col1:
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

# ==================== 生成分享卡片 ====================
def generate_share_card(pet_data, result, gender, bazi_str, city, is_anonymous=False):
    width, height = 600, 780
    img = Image.new('RGB', (width, height), color='#F8F6F0')
    draw = ImageDraw.Draw(img)
    colors = {
        "木": {"main": "#2E7D32", "light": "#C8E6C9"},
        "火": {"main": "#C62828", "light": "#FFCDD2"},
        "土": {"main": "#E65100", "light": "#FFE0B2"},
        "金": {"main": "#616161", "light": "#E0E0E0"},
        "水": {"main": "#0D47A1", "light": "#BBDEFB"},
    }
    day_element = result['日主五行']
    color = colors.get(day_element, colors["木"])
    main_color = color["main"]
    light_color = color["light"]
    try:
        font_big = ImageFont.truetype("simhei.ttf", 44)
        font_mid = ImageFont.truetype("simhei.ttf", 24)
        font_small = ImageFont.truetype("simhei.ttf", 18)
        font_tiny = ImageFont.truetype("simhei.ttf", 14)
    except:
        font_big = font_mid = font_small = font_tiny = ImageFont.load_default()
    draw.rectangle([(0, 0), (width, 12)], fill=main_color)
    draw.rectangle([(0, 12), (width, 90)], fill=light_color)
    pillars = ["年柱", "月柱", "日柱", "时柱"]
    pillar_values = [result['八字'][p] for p in pillars]
    y_start = 30
    total_width = 4 * 130
    start_x = (width - total_width) // 2
    for i, (name, value) in enumerate(zip(pillars, pillar_values)):
        x = start_x + i * 130
        draw.text((x + 15, y_start), name, fill="#888", font=font_small)
        draw.text((x + 10, y_start + 28), value, fill=main_color, font=font_big)
    if is_anonymous:
        draw.text((width-120, 20), "🔒 匿名分享", fill="#888", font=font_small)
    summary = pet_data['say']
    try:
        bbox = draw.textbbox((0, 0), summary, font=font_mid)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except:
        text_w = len(summary) * 16
        text_h = 30
    x_center = (width - text_w) // 2 - 16
    y_summary = 105
    draw.rounded_rectangle([(x_center - 10, y_summary - 6), (x_center + text_w + 10, y_summary + text_h + 6)], radius=12, fill=main_color)
    draw.text((x_center, y_summary), summary, fill="#FFFFFF", font=font_mid)
    info_line = f"🎭 {pet_data['personality']} ｜ {pet_data['action']}"
    draw.text((30, 165), info_line, fill="#666", font=font_small)
    draw.line([(30, 195), (width-30, 195)], fill="#E8E8E8", width=1)
    y_lucky = 215
    draw.text((30, y_lucky), "🌟 今日幸运物", fill=main_color, font=font_small)
    draw.text((30, y_lucky + 28), f"🍽️ {pet_data['eat']}", fill="#444", font=font_small)
    draw.text((30, y_lucky + 56), f"🎨 幸运色：", fill="#444", font=font_small)
    color_block_x = 30 + len("🎨 幸运色：") * 16
    draw.rectangle([(color_block_x, y_lucky + 56), (color_block_x + 36, y_lucky + 80)], fill=main_color, outline=main_color)
    draw.text((color_block_x + 40, y_lucky + 56), result['命理建议']['颜色'], fill=main_color, font=font_small)
    draw.text((320, y_lucky), "🎯 今日宜做", fill=main_color, font=font_small)
    draw.text((320, y_lucky + 28), f"🎮 {pet_data['play']}", fill="#444", font=font_small)
    draw.text((320, y_lucky + 56), f"👥 {pet_data['with']}", fill="#444", font=font_small)
    y_fish = 310
    draw.rounded_rectangle([(30, y_fish), (width-30, y_fish + 60)], radius=8, fill="#FFF3E0")
    draw.text((48, y_fish + 10), "🐟 今日摸鱼指南", fill="#E65100", font=font_small)
    draw.text((48, y_fish + 36), pet_data['fish'], fill="#555", font=font_tiny)
    y_bottom = height - 70
    avatar_emoji = "👦" if gender == "男" else "👧"
    if is_anonymous:
        draw.text((30, y_bottom - 10), f"{avatar_emoji} 匿名用户 · 命理小精灵", fill=main_color, font=font_small)
    else:
        draw.text((30, y_bottom - 10), f"{avatar_emoji} 命理小精灵 · {pet_data['name']}", fill=main_color, font=font_small)
    try:
        qr = qrcode.QRCode(box_size=2, border=1)
        qr.add_data("https://bazi-app-bagua-iw5jfhvghayccvpfgcnpq.streamlit.app/")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=main_color, back_color="white")
        qr_img = qr_img.resize((60, 60))
        img.paste(qr_img, (width-85, height-80))
    except:
        pass
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((30, height-30), f"生成于 {now}", fill="#BBB", font=font_tiny)
    draw.rectangle([(0, height-6), (width, height)], fill=main_color)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    return img_base64

# ==================== 大运倒计时 ====================
def get_next_luck_countdown(luck_years, current_age):
    for luck in luck_years:
        age_range = luck["运程"].replace("岁", "").split("-")
        start_age = int(age_range[0])
        end_age = int(age_range[1])
        if current_age < start_age:
            days_to_start = int((start_age - current_age) * 365.25)
            return {
                "next_luck": luck,
                "days": days_to_start,
                "start_age": start_age,
                "end_age": end_age,
                "gan_zhi": luck["干支"],
                "element": luck["五行"],
            }
    return None

# ==================== 表情切换 ====================
def get_expression(level: str) -> str:
    expressions = {
        "旺": "😍 超开心！运势爆棚！",
        "偏旺": "😊 心情不错，今天挺顺的~",
        "平衡": "🙂 平平淡淡才是真~",
        "偏弱": "😐 有点小低落，需要充充电",
        "弱": "😴 今天想躺平...休息一下",
    }
    return expressions.get(level, "😊")

# ==================== 主界面 ====================
st.title("☯ 生辰八字 · 五行命理排盘")
st.caption("🧚 基于《渊海子平》《三命通会》· 含真太阳时、节气月令、藏干权重 · 命理小精灵伴你左右")

# ==================== 侧边栏：功能导航 ====================
with st.sidebar:
    st.header("🧭 功能导航")
    page = st.radio(
        "选择功能",
        ["🔮 八字排盘", "📅 今日黄历", "💑 八字配对", "🧠 命理答题"],
        index=0
    )
    st.divider()
    voice_enabled = st.toggle("🔊 语音播报", value=True)
    st.caption("💡 小提示：\n• 八字排盘含K线图+小精灵\n• 今日黄历每日更新\n• 八字配对需双方生日")

# ==================== 页面1：八字排盘 ====================
if page == "🔮 八字排盘":
    with st.form("bazi_form"):
        col1, col2 = st.columns(2)
        with col1:
            year = st.number_input("📅 出生年份", min_value=1900, max_value=2100, value=2004, step=1)
            day = st.number_input("📆 出生日期", min_value=1, max_value=31, value=27, step=1)
            minute = st.number_input("🕐 出生分钟", min_value=0, max_value=59, value=30, step=1)
        with col2:
            month = st.number_input("📆 出生月份", min_value=1, max_value=12, value=2, step=1)
            hour = st.number_input("🕐 出生小时", min_value=0, max_value=23, value=12, step=1)
            gender = st.selectbox("👤 性别", ["男", "女"])
        city = st.text_input("📍 出生城市（如：北京、上海、广州、驻马店）", value="驻马店")
        submitted = st.form_submit_button("🔮 排盘分析", use_container_width=True)

    if submitted:
        with st.spinner("🧚 小精灵正在为你排盘..."):
            longitude = CITY_LONGITUDE.get(city.strip(), 120.0)
            calc = BaziCalculator(year, month, day, hour, minute, longitude)
            result = calc.get_full_analysis(gender)
            
            st.divider()
            cols = st.columns(4)
            pillars = ["年柱", "月柱", "日柱", "时柱"]
            for i, col in enumerate(cols):
                col.metric(pillars[i], result["八字"][pillars[i]])
            st.divider()
            
            expression = get_expression(result["旺衰"]["综合"])
            st.markdown(f"**日主：{result['日主']}（{result['日主五行']}）** ｜ 月令：{result['月令']} ｜ 旺衰：{result['旺衰']['综合']} ｜ {expression}")
            
            st.subheader("五行分布")
            cols = st.columns(5)
            for i, (ele, info) in enumerate(result["五行分布"].items()):
                cols[i].metric(ele, info["score"], delta=info["level"])
            
            st.subheader("十神解析")
            st.write(" | ".join([f"{k}：{v}" for k, v in result["十神"].items()]))
            
            st.subheader("大运排盘")
            luck_text = " ｜ ".join([f"{l['运程']} {l['干支']}({l['五行']})" for l in result["大运"]])
            st.write(luck_text)
            
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
                
                # 大运倒计时
                st.divider()
                st.subheader("⏳ 大运倒计时")
                current_age = datetime.datetime.now().year - year
                next_info = get_next_luck_countdown(result["大运"], current_age)
                if next_info:
                    days = next_info["days"]
                    gan_zhi = next_info["gan_zhi"]
                    element = next_info["element"]
                    start_age = next_info["start_age"]
                    end_age = next_info["end_age"]
                    years = days // 365
                    remaining_days = days % 365
                    if days < 30:
                        color = "#F44336"
                        emoji = "🔥"
                        msg = "马上就要到了！准备好迎接新大运！"
                    elif days < 90:
                        color = "#FF9800"
                        emoji = "⚡"
                        msg = "快了！再坚持一下！"
                    else:
                        color = "#4CAF50"
                        emoji = "🌱"
                        msg = "正在积累能量，厚积薄发！"
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #f8f9fa, #e8f5e9); border-radius: 16px; padding: 16px 20px; border-left: 4px solid {color};">
                            <div style="font-size: 14px; color: #666;">距离进入 <b>{gan_zhi}({element})</b> 大运</div>
                            <div style="font-size: 28px; font-weight: bold; color: {color};">
                                {years}年 {remaining_days}天
                            </div>
                            <div style="font-size: 13px; color: #888;">（{start_age}-{end_age}岁）</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div style="background: #f8f9fa; border-radius: 16px; padding: 16px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 32px;">{emoji}</div>
                            <div style="font-size: 13px; color: #666;">{msg}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div style="background: #f8f9fa; border-radius: 16px; padding: 12px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 13px; color: #666;">当前大运</div>
                            <div style="font-size: 16px; font-weight: bold; color: #333;">{result['大运'][0]['干支']}</div>
                            <div style="font-size: 12px; color: #888;">{result['大运'][0]['运程']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("🎯 已进入最后一个大运，把握当下！")
            
            display_pet(result["宠物"], gender)
            
            # 分享卡片
            st.divider()
            st.subheader("📸 分享运势卡片")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption("生成图片后长按保存，分享到朋友圈/小红书")
            with col2:
                is_anonymous = st.checkbox("🔒 匿名分享", value=False, help="开启后不显示你的昵称")
            
            bazi_str = f"{result['八字']['年柱']} {result['八字']['月柱']} {result['八字']['日柱']} {result['八字']['时柱']}"
            card_base64 = generate_share_card(
                result["宠物"], result, gender, bazi_str, city, is_anonymous
            )
            st.image(f"data:image/png;base64,{card_base64}", caption="📸 " + ("🔒 匿名模式" if is_anonymous else "长按保存图片分享"), use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="💾 保存卡片到相册",
                    data=base64.b64decode(card_base64),
                    file_name=f"命理运势_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.png",
                    mime="image/png",
                    use_container_width=True
                )
            with col2:
                if is_anonymous:
                    st.caption("🔒 匿名模式已开启，不显示个人信息")
            
            if voice_enabled:
                try:
                    from gtts import gTTS
                    voice_text = f"你好，我是你的命理小精灵{result['宠物']['name']}。{result['宠物']['say']}今天适合吃{result['宠物']['eat']}，适合玩{result['宠物']['play']}。"
                    tts = gTTS(text=voice_text, lang='zh-cn', slow=False)
                    audio_bytes = BytesIO()
                    tts.write_to_fp(audio_bytes)
                    audio_bytes.seek(0)
                    audio_base64 = base64.b64encode(audio_bytes.read()).decode()
                    st.markdown(f'<audio controls style="width:100%;margin-top:8px;"><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg"></audio>', unsafe_allow_html=True)
                except:
                    pass
            
            st.divider()
            st.subheader(f"{datetime.datetime.now().year}年流年分析")
            flow = result["流年"]
            st.write(f"流年：{flow['流年']}（{flow['五行']}，生肖{flow['生肖']}）")
            st.write(f"影响：{flow['对日主影响']}")
            st.info(flow["运势建议"])
            
            st.subheader("📝 命理建议")
            for key, value in result["命理建议"].items():
                st.write(f"• {key}：{value}")
            
            st.caption("⚠️ 仅供传统文化学习参考 · 人生把握在自己手中 · 🧚 命理小精灵祝你天天开心！")

# ==================== 页面2：今日黄历 ====================
elif page == "📅 今日黄历":
    st.divider()
    st.subheader("📅 今日黄历 · 宜忌指南")
    almanac = get_today_almanac()
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FFF8E1, #FFECB3); border-radius: 16px; padding: 20px; text-align: center;">
            <div style="font-size: 14px; color: #888;">📆 农历</div>
            <div style="font-size: 28px; font-weight: bold; color: #E65100;">{almanac['lunar_date']}</div>
            <div style="font-size: 16px; color: #666;">生肖：{almanac['zodiac']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background: #f8f9fa; border-radius: 16px; padding: 16px 20px;">
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <div>
                    <div style="font-size: 14px; color: #4CAF50; font-weight: bold;">✅ 宜</div>
                    {"".join([f'<span style="display: inline-block; background: #E8F5E9; padding: 4px 12px; border-radius: 12px; margin: 3px; font-size: 14px;">{item}</span>' for item in almanac['yi']])}
                </div>
                <div>
                    <div style="font-size: 14px; color: #F44336; font-weight: bold;">❌ 忌</div>
                    {"".join([f'<span style="display: inline-block; background: #FFEBEE; padding: 4px 12px; border-radius: 12px; margin: 3px; font-size: 14px;">{item}</span>' for item in almanac['ji']])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.caption(f"📌 数据来源：农历算法 ｜ 更新日期：{datetime.datetime.now().strftime('%Y-%m-%d')}")

# ==================== 页面3：八字配对 ====================
elif page == "💑 八字配对":
    st.divider()
    st.subheader("💑 八字配对 · 缘分测试")
    st.caption("输入你和TA的出生信息，看看你们的八字合不合~")
    with st.form("match_form"):
        st.markdown("**👤 你的信息**")
        col1, col2 = st.columns(2)
        with col1:
            year1 = st.number_input("出生年份", min_value=1900, max_value=2100, value=2000, key="y1")
            day1 = st.number_input("出生日期", min_value=1, max_value=31, value=1, key="d1")
        with col2:
            month1 = st.number_input("出生月份", min_value=1, max_value=12, value=1, key="m1")
            hour1 = st.number_input("出生小时", min_value=0, max_value=23, value=0, key="h1")
        gender1 = st.selectbox("性别", ["男", "女"], key="g1")
        city1 = st.text_input("出生城市", value="北京", key="c1")
        st.divider()
        st.markdown("**👤 TA的信息**")
        col1, col2 = st.columns(2)
        with col1:
            year2 = st.number_input("出生年份", min_value=1900, max_value=2100, value=2000, key="y2")
            day2 = st.number_input("出生日期", min_value=1, max_value=31, value=1, key="d2")
        with col2:
            month2 = st.number_input("出生月份", min_value=1, max_value=12, value=1, key="m2")
            hour2 = st.number_input("出生小时", min_value=0, max_value=23, value=0, key="h2")
        gender2 = st.selectbox("性别", ["男", "女"], key="g2")
        city2 = st.text_input("出生城市", value="北京", key="c2")
        submitted_match = st.form_submit_button("💞 查看配对结果", use_container_width=True)
    
    if submitted_match:
        with st.spinner("🔮 正在分析你们的缘分..."):
            lon1 = CITY_LONGITUDE.get(city1.strip(), 120.0)
            lon2 = CITY_LONGITUDE.get(city2.strip(), 120.0)
            calc1 = BaziCalculator(year1, month1, day1, hour1, 0, lon1)
            calc2 = BaziCalculator(year2, month2, day2, hour2, 0, lon2)
            bazi1 = calc1.calculate_bazi()
            bazi2 = calc2.calculate_bazi()
            match_result = bazi_match(bazi1, bazi2)
            
            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 60px;">💞</div>
                    <div style="font-size: 48px; font-weight: bold; color: {'#4CAF50' if match_result['score'] >= 70 else '#FF9800' if match_result['score'] >= 55 else '#F44336'};">
                        {match_result['score']}分
                    </div>
                    <div style="font-size: 18px; color: #666;">配对契合度</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="background: #f8f9fa; border-radius: 12px; padding: 16px;">
                    <div style="font-weight: bold; color: #333;">👤 你的八字</div>
                    <div style="font-size: 20px; color: #1976D2;">{bazi1['年柱']} {bazi1['月柱']} {bazi1['日柱']} {bazi1['时柱']}</div>
                    <div style="font-size: 14px; color: #888;">日主：{TIAN_GAN_INFO[bazi1['日柱'][0]]['element'].value}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: #f8f9fa; border-radius: 12px; padding: 16px;">
                    <div style="font-weight: bold; color: #333;">👤 TA的八字</div>
                    <div style="font-size: 20px; color: #C62828;">{bazi2['年柱']} {bazi2['月柱']} {bazi2['日柱']} {bazi2['时柱']}</div>
                    <div style="font-size: 14px; color: #888;">日主：{TIAN_GAN_INFO[bazi2['日柱'][0]]['element'].value}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            st.markdown(f"""
            <div style="background: #f8f9fa; border-radius: 12px; padding: 16px;">
                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div><span style="font-weight: bold;">五行关系：</span>{match_result['element_desc']}</div>
                    <div><span style="font-weight: bold;">阴阳关系：</span>{match_result['yy_desc']}</div>
                </div>
                <div style="margin-top: 12px; padding: 12px; background: {'#E8F5E9' if match_result['score'] >= 70 else '#FFF3E0'}; border-radius: 8px;">
                    💬 {match_result['advice']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("⚠️ 仅供娱乐参考 · 缘分还需用心经营 💕")

# ==================== 页面4：命理答题 ====================
elif page == "🧠 命理答题":
    st.divider()
    st.subheader("🧠 命理人格 · 性格测试")
    st.caption("回答6道题，测测你的命理人格类型~ 只需30秒！")
    st.divider()
    
    questions = [
        {
            "id": 1,
            "question": "🌤️ 你更喜欢哪种天气？",
            "options": ["阳光明媚的晴天 ☀️", "细雨绵绵的雨天 🌧️", "微风习习的阴天 🌥️", "大雪纷飞的雪天 ❄️"],
            "scores": {"阳光明媚的晴天 ☀️": "火", "细雨绵绵的雨天 🌧️": "水", "微风习习的阴天 🌥️": "木", "大雪纷飞的雪天 ❄️": "金"}
        },
        {
            "id": 2,
            "question": "👥 在团队中你通常扮演什么角色？",
            "options": ["领导者，带大家前进 🚀", "协调者，缓和气氛 🤝", "执行者，踏实做事 💪", "创新者，出谋划策 💡"],
            "scores": {"领导者，带大家前进 🚀": "火", "协调者，缓和气氛 🤝": "水", "执行者，踏实做事 💪": "土", "创新者，出谋划策 💡": "木"}
        },
        {
            "id": 3,
            "question": "🎨 你最喜欢的颜色是？",
            "options": ["红色/橙色 🔴", "蓝色/黑色 🔵", "绿色/青色 🟢", "黄色/棕色 🟡", "白色/金色 ⚪"],
            "scores": {"红色/橙色 🔴": "火", "蓝色/黑色 🔵": "水", "绿色/青色 🟢": "木", "黄色/棕色 🟡": "土", "白色/金色 ⚪": "金"}
        },
        {
            "id": 4,
            "question": "💪 面对困难时你通常会？",
            "options": ["迎难而上，主动解决 💥", "冷静分析，寻找方法 🔍", "寻求帮助，团队协作 🤗", "顺其自然，等待转机 🌊"],
            "scores": {"迎难而上，主动解决 💥": "火", "冷静分析，寻找方法 🔍": "金", "寻求帮助，团队协作 🤗": "土", "顺其自然，等待转机 🌊": "水"}
        },
        {
            "id": 5,
            "question": "💎 你更看重哪种品质？",
            "options": ["热情 ❤️", "智慧 🧠", "善良 🌸", "稳重 ⛰️", "勇敢 ⚔️"],
            "scores": {"热情 ❤️": "火", "智慧 🧠": "水", "善良 🌸": "木", "稳重 ⛰️": "土", "勇敢 ⚔️": "金"}
        },
        {
            "id": 6,
            "question": "🎯 空闲时间你更喜欢做什么？",
            "options": ["户外运动 🏃", "看书学习 📚", "朋友聚会 🎉", "独处放松 😌", "创作发明 🎨"],
            "scores": {"户外运动 🏃": "火", "看书学习 📚": "金", "朋友聚会 🎉": "土", "独处放松 😌": "水", "创作发明 🎨": "木"}
        },
    ]
    
    answers = []
    for q in questions:
        st.markdown(f"**{q['question']}**")
        answer = st.radio(
            "选择你的答案",
            q['options'],
            key=f"quiz_{q['id']}",
            label_visibility="collapsed",
            horizontal=False
        )
        answers.append(answer)
        st.divider()
    
    if st.button("🔮 查看我的命理人格", use_container_width=True):
    # 把答案转换成五行对应的值
        quiz_answers = []
        for i, answer in enumerate(answers):
            q = questions[i]
            if answer in q['scores']:
                quiz_answers.append(q['scores'][answer])
        result = get_quiz_result(quiz_answers)
        
        st.divider()
        st.subheader("🔮 你的命理人格结果")
        
        st.markdown("**📊 五行得分分布**")
        cols = st.columns(5)
        element_emojis = {"木": "🌳", "火": "🔥", "土": "🏔️", "金": "⚔️", "水": "🌊"}
        for i, (ele, score) in enumerate(result["scores"].items()):
            with cols[i]:
                st.metric(f"{element_emojis[ele]} {ele}", f"{score}分")
        
        st.divider()
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {result['color']}10, #f8f9fa); 
                    border-radius: 20px; padding: 24px; border-left: 6px solid {result['color']};">
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 12px;">
                <div style="font-size: 48px;">{result['title'][:2]}</div>
                <div>
                    <div style="font-size: 24px; font-weight: bold; color: {result['color']};">{result['title']}</div>
                    <div style="font-size: 14px; color: #888;">最高得分：{result['element']}（{result['score']}分）</div>
                </div>
            </div>
            <div style="font-size: 16px; color: #333; line-height: 1.8; margin-top: 12px;">
                {result['desc']}
            </div>
            <div style="margin-top: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div style="background: #E8F5E9; border-radius: 12px; padding: 12px;">
                    <div style="font-weight: bold; color: #2E7D32;">🌟 你的优势</div>
                    <div style="font-size: 14px; color: #555; margin-top: 4px;">{result['strengths']}</div>
                </div>
                <div style="background: #FFF3E0; border-radius: 12px; padding: 12px;">
                    <div style="font-weight: bold; color: #E65100;">⚠️ 需要注意</div>
                    <div style="font-size: 14px; color: #555; margin-top: 4px;">{result['weaknesses']}</div>
                </div>
            </div>
            <div style="background: #E3F2FD; border-radius: 12px; padding: 12px; margin-top: 12px;">
                <div style="font-weight: bold; color: #0D47A1;">💡 建议</div>
                <div style="font-size: 14px; color: #555; margin-top: 4px;">{result['advice']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.info("📸 截图分享到朋友圈，看看朋友是什么命！")
        with col2:
            share_text = f"我测出我是{result['title']}！{result['desc'][:30]}... 快来测测你的命理人格吧！🔮"
            st.code(f"📋 复制这段话分享：\n{share_text}", language="text")
        
        st.caption("⚠️ 仅供娱乐参考 · 人生把握在自己手中 ✨")
