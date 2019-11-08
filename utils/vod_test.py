from qcloud_vod.vod_upload_client import VodUploadClient
from qcloud_vod.model import VodUploadRequest


def get_video_url(file_name):
    client = VodUploadClient("AKID97weBSjSCl8KMDhHZgbKsFSOGxTocveE", "QehaIp382hHgvyqWyLLEvSnZPFtFUYQB")
    request = VodUploadRequest()
    request.MediaFilePath = "../../../media/videos/" + file_name
    try:
        response = client.upload("ap-guangzhou", request)
    except Exception as err:
        # 处理业务异常
        print(err)
        return False
    else:
        return response.MediaUrl

