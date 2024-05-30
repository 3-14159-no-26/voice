from datetime import datetime, timedelta, timezone
import pymysql
import requests
import uuid
import time
from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv(".sync.env")
host = os.getenv("HOST")
user = os.getenv("USER")
password = os.getenv("PASSWORD")
database = os.getenv("DATABASE")
line_notify_token = os.getenv("LINE_NOTIFY_TOKEN")
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
google_refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")


# 打开数据库连接
db = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

# 使用 cursor() 方法创建一个游标对象 cursor
cursor = db.cursor()

# 使用 execute()  方法执行 SQL 查询
cursor.execute("SELECT VERSION()")

# 使用 fetchone() 方法获取单条数据.
data = cursor.fetchone()

print("Database version : %s " % data)

# 查詢 Account 有幾筆資料 (COUNT)
cursor.execute("SELECT COUNT(*) FROM `Account`")
Account_count = cursor.fetchone()
print("Account count : %s " % Account_count)
print(type(Account_count), "+", Account_count)

# 查詢 Account 的 所有ID
cursor.execute("SELECT `id` FROM `Account`")
Account_id = cursor.fetchall()
print("Account id : ", Account_id)


def LineNotifyHeart(startTime, nowTime, lowHeartRate, highHeartRate, avgHeartRate):
    url = "https://notify-api.line.me/api/notify"
    token = line_notify_token
    headers = {"Authorization": "Bearer " + token}
    data = {
        "message": "\n"
        + startTime.strftime("%Y-%m-%d %H:%M:%S")
        + "\n"
        + nowTime.strftime("%Y-%m-%d %H:%M:%S")
        + "\n最低心率: "
        + str(lowHeartRate)
        + "\n最高心率: "
        + str(highHeartRate)
        + "\n平均心率: "
        + str(avgHeartRate)
    }
    requests.post(url, headers=headers, data=data)


def LineNotifyStep(startTime, nowTime, step):
    goal = 3000
    message = "\n" + startTime.strftime("%Y-%m-%d %H:%M:%S") + "\n" + \
        nowTime.strftime("%Y-%m-%d %H:%M:%S") + "\n目前步數: " + str(step)
    if step >= goal:
        print("恭喜達成目標 " + str(goal) + " 步")
        message += "\n恭喜達成目標 " + str(goal) + " 步"
    url = 'https://notify-api.line.me/api/notify'
    token = line_notify_token
    headers = {
        'Authorization': 'Bearer ' + token
    }
    data = {
        'message': message
    }
    requests.post(url, headers=headers, data=data)


# 更新 access_token
def UpdateAccessToken(Account_id, Account_access_token):
    print("更新 access_token")
    # 查詢 Account 的 refresh_token
    cursor.execute(
        "SELECT `refresh_token` FROM `Account` WHERE `id` = %s", Account_id)
    Account_refresh_token = cursor.fetchone()
    print(
        "Account_id : %s " % Account_id,
        "Account_refresh_token : %s " % Account_refresh_token,
    )

    # 更新 access_token
    body = {
        "grant_type": "refresh_token",
        "client_id": google_client_id,
        "client_secret": google_client_secret,
        "refresh_token": google_refresh_token,
    }
    data = requests.post(
        "https://oauth2.googleapis.com/token",
        json=body,
    ).json()
    print(data)
    print("更新 access_token : ", data["access_token"])
    cursor.execute(
        "UPDATE `Account` SET `access_token` = %s WHERE `id` = %s",
        (data["access_token"], Account_id),
    )
    db.commit()

# UpdateAccessToken("xxxo", google_refresh_token)
# 無限迴圈 定時執行 一天一次 每天 00:00:00


def Heart():
    nowTime = datetime.now(timezone(timedelta(hours=8))
                           ) - timedelta(days=1)  # 再減一天
    print(nowTime.strftime("%Y-%m-%d %H:%M:%S"))
    # 每半小時執行一次 00 or 30
    # if date.strftime("%M") == "00" or date.strftime("%M") == "30":
    for i in range(0, Account_count[0]):
        # 查詢 Account 的 access_token
        cursor.execute(
            "SELECT `access_token` FROM `Account` WHERE `id` = %s", Account_id[i]
        )
        Account_access_token = cursor.fetchone()
        print("Account access_token : %s " % Account_access_token)
        print(type(Account_access_token), "+", Account_access_token)

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + Account_access_token[0],
        }
        # 目前時間減30分鐘
        startTime = nowTime - timedelta(minutes=30)
        print(startTime.strftime("%Y-%m-%d %H:%M:%S"))
        startTimeMillis = int(startTime.timestamp() * 1000)
        endTimeMillis = int(nowTime.timestamp() * 1000)

        # startTimeMillis = datetime(2023, 11, 6, 0, 0, 0, 0, timezone(timedelta(hours=8))).timestamp() * 1000
        # endTimeMillis = startTimeMillis + 1800000
        
        print("開始時間: ", startTimeMillis)
        print("結束時間: ", endTimeMillis)
        
        body = {
            "aggregateBy": [
                {
                    "dataSourceId": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm",
                },
            ],
            "bucketByTime": {"durationMillis": 1800000},
            "startTimeMillis": startTimeMillis,
            "endTimeMillis": endTimeMillis,
        }
        
        data = requests.post(
            "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
            headers=headers,
            json=body,
        ).json()
        # {'error': {'code': 401, 'message': 'Request had invalid authentication credentials. Expected OAuth 2 access token, login cookie or other valid authentication credential. See https://developers.google.com/identity/sign-in/web/devconsole-project.', 'errors': [{'message': 'Invalid Credentials', 'domain': 'global', 'reason': 'authError', 'location': 'Authorization', 'locationType': 'header'}], 'status': 'UNAUTHENTICATED'}}
        print(data)
        if "error" in data:
            print("error")
            print(data["error"]["code"])
            if (
                "Request had invalid authentication credentials. Expected OAuth 2 access token, login cookie or other valid authentication credential"
                in data["error"]["message"]
            ):
                print("access_token 過期")
                
                # 查詢 Account 的 refresh_token
                cursor.execute(
                    "SELECT `refresh_token` FROM `Account` WHERE `id` = %s",
                    Account_id[i],
                )
                Account_refresh_token = cursor.fetchone()
                print(
                    "Account_id : %s " % Account_id[i],
                    "Account_refresh_token : %s " % Account_refresh_token,
                )
                
                # 更新 access_token
                UpdateAccessToken(Account_id[i][0], Account_refresh_token[0])
                
            print("#" * 100)
            continue

        print("#" * 100)
        print("Account_id", Account_id[i][0])

        uid = uuid.uuid4()

        print(
            "data['bucket'][0]['dataset'][0]['point'] : ",
            data["bucket"][0]["dataset"][0]["point"],
        )
        if data["bucket"][0]["dataset"][0]["point"] != []:
            print(str(uid))
            # 查詢 此 id 的 userId
            cursor.execute(
                "SELECT `userId` FROM `Account` WHERE `id` = %s", Account_id[i][0]
            )
            Account_userId = cursor.fetchone()
            print("Account userId : %s " % Account_userId)
            lowHeartRate = int(
                data["bucket"][0]["dataset"][0]["point"][0]["value"][0]["fpVal"]
            )
            highHeartRate = int(
                data["bucket"][0]["dataset"][0]["point"][0]["value"][1]["fpVal"]
            )
            avgHeartRate = int(
                data["bucket"][0]["dataset"][0]["point"][0]["value"][2]["fpVal"]
            )

            print("最低心率: ", lowHeartRate)
            print("最高心率: ", highHeartRate)
            print("平均心率: ", avgHeartRate)

            # LINE Notify
            warn = 0
            # 若最低心率低於 60 或 最高心率高於 100
            if lowHeartRate < 60 or highHeartRate > 100:
                print("心率異常")
                # 發送 LINE Notify
                LineNotifyHeart(
                    startTime, nowTime, lowHeartRate, highHeartRate, avgHeartRate
                )
                warn = 1
            else:
                LineNotifyHeart(
                    startTime, nowTime, lowHeartRate, highHeartRate, avgHeartRate
                )
                print("心率正常")
                warn = 0
            cursor.execute(
                "INSERT INTO `heart` (`id`, `userId`, `low`, `high`, `avg`, `warn`, `timestamp`) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    uid,
                    Account_userId[0],
                    lowHeartRate,
                    highHeartRate,
                    avgHeartRate,
                    warn,
                    nowTime.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            db.commit()
        else:
            print("數據為空")
        print("*" * 100)


def Step():
    nowTime = datetime.now(timezone(timedelta(hours=8)))
    print(nowTime.strftime("%Y-%m-%d %H:%M:%S"))
    # 每半小時執行一次 00 or 30
    # if date.strftime("%M") == "00" or date.strftime("%M") == "30":
    for i in range(0, Account_count[0]):
        # 查詢 Account 的 access_token
        cursor.execute(
            "SELECT `access_token` FROM `Account` WHERE `id` = %s", Account_id[i]
        )
        Account_access_token = cursor.fetchone()
        print("Account access_token : %s " % Account_access_token)
        print(type(Account_access_token), "+", Account_access_token)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + Account_access_token[0],
        }
        # 今天 00:00:00
        startTime = nowTime.replace(
            hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        startTimeMillis = int(startTime.timestamp() * 1000)
        endTimeMillis = int(nowTime.timestamp() * 1000)
        # startTimeMillis = datetime(2023, 11, 6, 0, 0, 0, 0, timezone(timedelta(hours=8))).timestamp() * 1000
        # endTimeMillis = startTimeMillis + 1800000
        print("開始時間: ", startTimeMillis)
        print("結束時間: ", endTimeMillis)
        body = {
            "aggregateBy": [
                {
                    "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps",
                },
            ],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis":  startTimeMillis,
            "endTimeMillis": endTimeMillis,
        }
        data = requests.post(
            "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
            headers=headers,
            json=body,
        ).json()
        print(data)
        if 'error' in data:
            print("error")
            print(data['error']['code'])
            if (
                "Request had invalid authentication credentials. Expected OAuth 2 access token, login cookie or other valid authentication credential"
                    in data['error']['message']):
                print("access_token 過期")
            print("#"*100)
            continue
        print("#"*100)
        print("Account_id", Account_id[i][0])
        uid = uuid.uuid4()
        print("data['bucket'][0]['dataset'][0]['point'] : ",
              data['bucket'][0]['dataset'][0]['point'])
        if data['bucket'][0]['dataset'][0]['point'] != []:
            print(str(uid))
            # 查詢 此 id 的 userId
            cursor.execute(
                "SELECT `userId` FROM `Account` WHERE `id` = %s", Account_id[i][0])
            Account_userId = cursor.fetchone()
            print("Account userId : %s " % Account_userId)
            cursor.execute(
                "SELECT `userId` FROM `Account` WHERE `id` = %s", Account_id[i][0])
            Account_userId = cursor.fetchone()
            print("Account userId : %s " % Account_userId)
            step = int(data['bucket'][0]['dataset'][0]
                       ['point'][0]['value'][0]['intVal'])
            # LINE Notify
            # 若 目前時間 是 00:00
            print("目前時間: ", nowTime.strftime("%H:%M"))
            if nowTime.strftime("%H:%M") == "00:00":
                LineNotifyStep(startTime, nowTime, step)
            cursor.execute(
                "INSERT INTO `step` (`id`, `userId`, `steps`, `timestamp`) VALUES (%s, %s, %s, %s)",
                (
                    str(uid),
                    Account_userId[0],
                    step,
                    startTime.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            db.commit()
        else:
            print("data['bucket'][0]['dataset'][0]['point'] is []")
        print("*"*100)

if __name__ == "__main__":
    while True:
        try:
            Heart()
            Step()
            for i in range(0, 55):
                print("*", end="", flush=True)
                time.sleep(1)
        except KeyboardInterrupt:
            print("手動結束程式")
            break
            db.close()