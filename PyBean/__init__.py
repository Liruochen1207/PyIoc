import os
from PyBean.banner import Banner as bn
root = os.getcwd()
resourcePath = root + "\\resource\\"
resourceExists = os.path.exists(resourcePath)
banner = bn.dBanner
if resourceExists:
    bannerExists = os.path.exists(resourcePath + "\\banner.txt")
    if bannerExists:
        with open(resourcePath + "\\banner.txt", 'r') as f:
            banner = f.read()




print(banner)