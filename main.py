import requests
import re
import os

# --- 云端专用：直接连接，无需代理 ---
SOURCE_URLS = [
    # 范明明 (IPv6 主力)
    "https://live.fanmingming.com/tv/m3u/ipv6.m3u",
    # YanG (地方台补充)
    "https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
    # APTV (备用)
    "https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u"
]

class CloudAggregator:
    def __init__(self):
        self.channels = {}

    def normalize(self, name):
        name = name.upper().strip().replace(" ", "").replace("-", "")
        name = re.sub(r'\[.*?\]', '', name)
        if "CCTV" in name:
            num = re.findall(r'\d+', name)
            if num: return f"CCTV-{num[0]}"
            if "5+" in name: return "CCTV-5+"
            if "4K" in name: return "CCTV-4K"
            if "8K" in name: return "CCTV-8K"
        return name

    def get_group(self, name):
        if "4K" in name or "8K" in name: return "💎 4K/8K"
        if "CCTV" in name: return "📺 央视"
        if "卫视" in name: return "📡 卫视"
        if "CHC" in name or "电影" in name: return "🎬 影院"
        if "少儿" in name or "动画" in name: return "🧸 少儿"
        if "体育" in name: return "⚽️ 体育"
        return "🏙 地方/其他"

    def run(self):
        print("🚀 GitHub Action 启动...")
        for url in SOURCE_URLS:
            try:
                print(f"Downloading {url}...")
                resp = requests.get(url, timeout=30) # 云端网络很好，直接拉
                if resp.status_code == 200:
                    self.parse(resp.text)
            except Exception as e:
                print(f"Error: {e}")
        
        self.export()

    def parse(self, text):
        lines = text.split('\n')
        name = ""
        logo = ""
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith("#EXTINF"):
                l = re.search(r'tvg-logo="(.*?)"', line)
                logo = l.group(1) if l else ""
                name = line.split(',')[-1].strip()
            elif not line.startswith("#"):
                # 简单过滤 IPv6
                if "[" not in line and line.count(":") < 2: continue
                
                std = self.normalize(name)
                if std not in self.channels:
                    self.channels[std] = {
                        "group": self.get_group(std),
                        "logo": logo,
                        "url": line,
                        "name": std
                    }

    def export(self):
        # 简单排序
        data = sorted(self.channels.values(), key=lambda x: x['name'])
        
        with open("ipv6.m3u", "w", encoding="utf-8") as f:
            f.write('#EXTM3U x-tvg-url="https://live.fanmingming.com/e.xml"\n')
            for c in data:
                f.write(f'#EXTINF:-1 group-title="{c["group"]}" tvg-name="{c["name"]}" tvg-logo="{c["logo"]}",{c["name"]}\n')
                f.write(f'{c["url"]}\n')
        print(f"✅ 生成完毕，包含 {len(data)} 个频道")

if __name__ == "__main__":
    CloudAggregator().run()
