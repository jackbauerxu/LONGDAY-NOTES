# Quiet Atlas 部署说明

## 前端：Cloudflare Pages

上传 `outputs/uzbek-notes-site` 目录。

如果 API 部署在 `https://api.example.com`，把静态站里的：

`tools/runtime-config.js`

改成：

```js
window.QUIET_ATLAS_API_BASE = "https://api.example.com";
```

本地预览保持空字符串即可。

## 服务端：Oracle Cloud Always Free 或现有服务器

部署目录建议：

`/opt/quiet-atlas-api`

步骤：

```bash
sudo mkdir -p /opt/quiet-atlas-api
sudo cp train_ticket_assisted_server.py /opt/quiet-atlas-api/
sudo cp requirements.txt /opt/quiet-atlas-api/
sudo cp train-ticket.env.example /opt/quiet-atlas-api/train-ticket.env
cd /opt/quiet-atlas-api
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/playwright install chromium
sudo cp quiet-atlas-train.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now quiet-atlas-train
```

健康检查：

```bash
curl http://127.0.0.1:8787/health
```

## 关键配置

`train-ticket.env` 里必须配置：

- `TRAIN_TICKET_ALLOWED_ORIGINS`
- `TRAIN_TICKET_ALIPAY_QR_URL`

实时同步规则已经内置在服务端：服务端会按路线和日期进入英文火车票结果页，读取车次、当地时间、运行时长、座席、余票、座位/铺位号和当地票价。同步不到时，服务端会明确返回暂时不可用，不会给用户展示旧车次或估算价格。
