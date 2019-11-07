from qcloud_vod.vod_upload_client import VodUploadClient
from qcloud_vod.model import VodUploadRequest

client = VodUploadClient("AKID97weBSjSCl8KMDhHZgbKsFSOGxTocveE", "QehaIp382hHgvyqWyLLEvSnZPFtFUYQB")
request = VodUploadRequest()
request.MediaFilePath = "data/file/5AM.mp4"
request.CoverFilePath = "data/file/5AM.png"
try:
    response = client.upload("ap-guangzhou", request)
    print(response.FileId)
    print(response.MediaUrl)
    print(response.CoverUrl)
except Exception as err:
    # 处理业务异常
    print(err)