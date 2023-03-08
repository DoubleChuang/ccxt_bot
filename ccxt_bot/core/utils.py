# -*- coding: utf-8 -*-

import requests

def notify_line(token: str, msg: str):
    if not token: return
    
    # message you want to send
    # tpe_date = datetime.now(tz=timezone(timedelta(hours=+8))).strftime("%Y/%m/%d")

    # HTTP headers and message
    headers = {"Authorization": f"Bearer {token}"}
    data = { 'message': msg }

    # Image want to sens
    # image = open('my_image.jpg', 'rb')
    # files = { 'imageFile': image }

    # send line notify by Line API
    requests.post(
        "https://notify-api.line.me/api/notify",
        headers = headers,
        data = data,
        # files = files
    )