
## 前端地址

[https://github.com/ermaozi/my_bot_web](https://github.com/ermaozi/my_bot_web)

## 安装docker

docker -v  2> /dev/null|| curl -sSL https://get.daocloud.io/docker | sh

## 安装数据库
docker run  --name="mongo"  -p27017:27017 -p28017:28017 -v /docker-data/mongo:/data/db -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=pwd  -d mongo

## 安装my_bot

sudo mkdir -p /etc/my_bot/

sudo vi /etc/my_bot/config.yml

``` yaml

# 项目配置文件
node_info:
  # openssl rand -hex 32
  secret_key: ~
  # 主节点hostname, 如果只有一个节点该字段千万不要填写, 多个节点必须填写, 后续考虑自动生成
  main_host: ~
  domain: 127.0.0.1

# 数据站设置
jx3api:
  # ws链接地址
  ws_path: wss://socket.nicemoe.cn
  # ws的token授权，关联ws服务器推送消息类型
  ws_token: ~
  # 主站地址
  jx3_url:  https://www.jx3api.com
  # 主站token，不填将不能访问带ticket的接口
  jx3_token: ~

# 剑三沙盘的用户信息
jx3sand:
  account: ~
  password: ~

# 邮件通知配置
mail:
  sender: 二猫子的猛男助理
  # 默认 smtp 服务器地址
  default_host: smtp.mxhichina.com
  # 默认端口号
  default_pord: 465
  # 默认密码
  default_passwd: ~
  # mail 必填, 其他选填, 如果其他项不填, 则使用默认配置
  mail_list:
      # 邮箱地址
    - mail: ~
      # smtp服务器地址
      host: smtp.mxhichina.com
      # 端口号
      pord: 465
      # 密码，可能是授权码
      passwd: ~

# 百度违规词检测
baidusdkcore:
  # https://console.bce.baidu.com/ai/?_&fromai=1#/ai/antiporn/overview/index
  client_id: ~
  client_secret: ~

# mongodb
mongodb:
  # docker 部署时需要写宿主机公网ip或内网, 不能直接写127.0.0.1
  mongdb_list:
    - 127.0.0.1:27017
  mongodb_username: 用户名
  mongodb_password: ~

# 默认设置
default:
  # 插件debug日志是否显示在控制台
  logger_debug: true

bot_conf:
  # 机器人管理群(无视机器人加群限制)
  manage_group: []

# 腾讯云自然语言处理, 就是机器人搭话的功能
nlp:
  # https://console.cloud.tencent.com/cam/capi
  secretId: ~
  secretKey: ~

```

docker run --name="my_bot" --hostname=$(hostname) -v /etc/my_bot:/my_bot/conf -p 8899:8899 -itd ermaozi/my_bot

如果启动没问题再加上自动重启

docker update --restart=always my_bot

自动更新

docker run -d --name watchtower --restart always -v /var/run/docker.sock:/var/run/docker.sock containrrr/watchtower --cleanup -i 300 my_bot

## 交流群

[937593602](https://qm.qq.com/cgi-bin/qm/qr?k=pG7qtpP1M80tTVE4moII3dqcRsFi8NBT&jump_from=webapi)
