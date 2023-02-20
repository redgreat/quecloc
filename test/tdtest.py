import taosrest

url="https://gw.us-east-1.aws.cloud.tdengine.com"
token="84be6cfebe3e8c4dd63be3c55d99430cb5634ba2"

taoscloud_conn = taosrest.connect(url=url, token=token)

taos_cur = taoscloud_conn.cursor()
sql = "CREATE STABLE `test`.`locdaily` (`LocTime` TIMESTAMP, `Lng` FLOAT, `Lat` FLOAT) TAGS (`DeviceId` INT);"
taos_cur.execute(sql)
taoscloud_conn.commit()
taos_cur.close()