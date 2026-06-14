# Quiet Atlas / 长日记事

个人旅行专题资料库，用来维护国家专题、探店数据、工具页面和服务器端辅助服务。

## 目录

- `work/`：生成脚本、数据处理脚本、服务端代码、部署模板。
- `outputs/`：整理后的专题、表格和交付文件。静态站生成目录与压缩包不提交。
- `work/server_deploy/`：服务器部署所需的 systemd、依赖和配置模板。

## 本地生成

```bash
python3 work/build_notes_site.py
```

生成后的静态站在：

```text
outputs/uzbek-notes-site/
```

## 线上地址

```text
http://139.224.254.142/quiet-atlas/
```

## 注意

不要把本地环境配置、订单数据、支付凭证、用户证件信息、服务器连接文件提交到仓库。
