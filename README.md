# 可行驶区域识别（Drivable Area Detection）

基于传统计算机视觉方法的可行驶区域识别程序：输入一张道路场景图片，自动分割出可行驶路面，
并以半透明绿色叠加 + 黄色轮廓的方式输出效果图。

## 项目功能

- 读取用户选择的一张道路图片（支持 jpg / jpeg / png / bmp）；
- 组合多种视觉线索分割可行驶区域：
  1. **植被掩膜**：ExG 超绿指数 + HSV 绿色色相范围，排除路边植被；
  2. **天空掩膜**：高亮低饱和区域且连通到图像顶边，排除天空；
  3. **GrabCut 精分割**：以植被/天空/暗色区域为背景种子、下部亮色路面为前景种子，
     通过高斯混合模型迭代优化分割；
  4. **后处理**：亮度过滤剔除阴影泥地、形态学开闭运算去噪、保留与底边连通的最大区域、
     轮廓填充得到完整路面掩膜；
- 输出识别效果图（绿色半透明叠加 + 黄色边界轮廓），并在终端打印可行驶区域占比。

## 环境要求

| 项目 | 说明 |
| --- | --- |
| 操作系统 | Windows 10/11（也可在 Ubuntu / macOS 上运行，需有图形界面） |
| Python | 3.9 – 3.12（开发时使用 3.10） |
| 主要依赖 | opencv-python ≥ 4.5，numpy ≥ 1.21 |

> 本项目使用传统视觉算法，**无需 GPU、无需任何模型权重**。

## 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/<你的用户名>/drivable-area-detection.git
cd drivable-area-detection

# 2. 创建并激活虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
# source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序（会弹出文件选择对话框，选择一张道路图片即可）
python src/detect_drivable_area.py
```

识别结果默认保存为当前目录下的 `可行驶区域识别效果图.png`，
终端会输出类似：`识别完成，可行驶区域占比 34.2%，结果已保存至 可行驶区域识别效果图.png`。

也可以在代码中直接调用函数：

```python
from src.detect_drivable_area import detect_drivable_area
detect_drivable_area("your_image.jpg", "output.png")
```

## 模型权重如何获取

本项目**不包含、也不需要深度学习模型权重**——分割完全由
ExG 指数、HSV 阈值、GrabCut 等传统算法完成，开箱即用，无需下载任何额外文件。

## 运行效果

![运行效果](assets/demo.png)

（上图：左侧为输入的道路场景原图，右侧为程序输出的可行驶区域识别效果图，
绿色半透明区域为识别出的可行驶路面，黄色曲线为区域边界。）

## 常见问题（FAQ）

1. **弹不出文件选择对话框 / 报 tkinter 相关错误**
   - Windows 和 macOS 的官方 Python 自带 tkinter；部分 Linux 发行版需要额外安装：
     `sudo apt install python3-tk`。
   - 若在无图形界面的服务器（如纯 SSH）上运行，文件对话框无法弹出，
     请改用代码调用方式传入图片路径。
2. **图片读取失败 `FileNotFoundError`**
   - 确认路径正确；中文路径在大多数环境下可正常读取，若仍失败，
     可将图片移动到纯英文路径再试。
3. **报 `RuntimeError: 未能在图像底边找到连通的可行驶区域`**
   - 说明图片中没有与底边连通的亮色路面区域（如夜间、雪地、水面路面），
     或路面偏暗被亮度过滤误剔除；可放宽 `V < 180` 的亮度过滤阈值，
     或换一张光照正常的道路图片。
4. **识别效果不理想（漏检路面 / 误检草地）**
   - 算法基于颜色与空间先验，对强光、阴影、雪地、夜间场景效果会下降；
   - 可尝试调整 `src/detect_drivable_area.py` 中的阈值，如 ExG 阈值 `18`、
     路面种子条件 `V > 150`、`yy > 0.70*h` 等。
5. **依赖安装失败**
   - 确认 Python 版本 ≥ 3.9；若 opencv-python 安装缓慢，可换国内镜像：
     `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`。

## 目录结构

```
drivable-area-detection/
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   └── detect_drivable_area.py   # 主程序
└── assets/
    └── demo.png                  # 运行效果图
```
