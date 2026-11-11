import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog


def detect_drivable_area(image_path, out_path="可行驶区域识别效果图.png"):
    # ---------- 0. 读取图像 ----------
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise FileNotFoundError(f"图片读取失败，路径：{image_path}")
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]
    R, G, B = img[:, :, 0].astype(int), img[:, :, 1].astype(int), img[:, :, 2].astype(int)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    yy = np.arange(h)[:, None]   # 每个像素的行号，用于空间先验

    # ---------- 1. 植被掩膜：ExG 超绿指数 + 绿色色相 ----------
    ExG = 2 * G - R - B
    veg = ((ExG > 18) | ((H >= 30) & (H <= 95) & (S > 45))).astype(np.uint8)
    veg = cv2.morphologyEx(veg, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    veg = cv2.morphologyEx(veg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    # ---------- 2. 天空掩膜：高亮低饱和 + 必须连通到图像顶边 ----------
    sky_seed = ((V > 232) & (S < 45)).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(sky_seed, 8)
    top_ids = set(np.unique(lab[0:5, :])) - {0}
    sky = np.isin(lab, list(top_ids)).astype(np.uint8) if top_ids else np.zeros_like(sky_seed)

    # ---------- 3. GrabCut 精分割：种子初始化 + 高斯混合模型迭代 ----------
    gc = np.full((h, w), cv2.GC_PR_BGD, np.uint8)       # 默认：可能是背景
    gc[veg.astype(bool)] = cv2.GC_BGD                   # 植被 → 确定背景
    gc[sky.astype(bool)] = cv2.GC_BGD                   # 天空 → 确定背景
    gc[V < 80] = cv2.GC_BGD                             # 暗色树冠/树干 → 确定背景
    road_seed = (S < 45) & (V > 150) & (yy > 0.70 * h) & (veg == 0)
    gc[road_seed] = cv2.GC_FGD                          # 下部路面色区域 → 确定前景
    gc[(gc == cv2.GC_PR_BGD) & (yy > 0.36 * h)] = cv2.GC_PR_FGD  # 地平线以下 → 可能前景

    bgd_model, fgd_model = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img_bgr, gc, None, bgd_model, fgd_model, 8, cv2.GC_INIT_WITH_MASK)
    road = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)

    # ---------- 4. 后处理：亮度过滤 → 形态学 → 底边连通最大区域 → 轮廓填充 ----------
    road[(yy > 0.50 * h) & (V < 180)] = 0                 # 剔除阴影泥地
    road = cv2.morphologyEx(road, cv2.MORPH_OPEN, np.ones((11, 11), np.uint8))
    road = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
    n2, lab2, stats2, _ = cv2.connectedComponentsWithStats(road, 8)
    bottom_ids = set(np.unique(lab2[-5:, :])) - {0}
    if not bottom_ids:
        raise RuntimeError("未能在图像底边找到连通的可行驶区域，"
                           "请换一张道路图片或适当放宽阈值（如降低亮度过滤 180）")
    best = max(bottom_ids, key=lambda i: stats2[i, cv2.CC_STAT_AREA])
    road_mask = (lab2 == best).astype(np.uint8)
    cnts, _ = cv2.findContours(road_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(road_mask, cnts, -1, 1, cv2.FILLED)

    # ---------- 5. 可视化：半透明叠加 + 轮廓 + 标注 ----------
    result = img.copy().astype(np.float64)
    m = road_mask.astype(bool)
    result[m] = 0.50 * result[m] + 0.50 * np.array([30, 205, 110])  # 绿色半透明叠加
    result_bgr = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_RGB2BGR)
    cv2.drawContours(result_bgr, cnts, -1, (0, 230, 255), 3)  # 黄色边界轮廓

    # 保存（imencode + tofile 的写法支持中文路径）
    cv2.imencode('.png', result_bgr)[1].tofile(out_path)
    print(f"识别完成，可行驶区域占比 {road_mask.mean() * 100:.1f}%，结果已保存至 {out_path}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # 隐藏空白小窗口
    path = filedialog.askopenfilename(
        title="请选择要分析的图片",
        filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp")]
    )
    if path:
        detect_drivable_area(path)
