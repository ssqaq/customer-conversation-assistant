# 发布与校验

## 本地检查

使用 Python 3.12，依赖仅用于开发和发布，不是 Skill 运行依赖。

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/release.py validate
python scripts/release.py build --tag v1.1.0
python scripts/release.py verify --tag v1.1.0 --archive dist/customer-conversation-assistant-1.1.0.zip --manifest dist/customer-conversation-assistant-1.1.0-manifest.json
```

输出已存在时构建拒绝覆盖；重复试验用 `--out` 指定新的工作目录。版本唯一来源为 Skill 的 `metadata.version`，发布前同步 README 下载信息。

## GitHub 自动执行

提交到 main、提交 PR、推送 `v*` 标签会触发 `.github/workflows/release.yml`。

1. Windows 和 Linux 均运行固定提交的 OpenAI 官方 `quick_validate.py`、本仓库反例测试和实际构建。
2. 校验三文件集合、UTF-8/LF、YAML、引用与锚点、版本、调用信息及占位残留；拒绝符号链接和多余客户文件。
3. 标签发布必须与 Skill 版本精确一致。ZIP 固定排序、时间和权限，使用无压缩存储保证跨平台字节一致，附逐文件 SHA-256 清单。
4. 仅标签触发发布。两个平台包逐字节相同后，上传到 draft Release，从 GitHub 下载附件，再与标签源码、构建包和清单核对。
5. 下载核对成功才正式发布。中途失败保留 draft；同一提交的 draft 可重跑。已正式发布或指向其他提交的同版本拒绝覆盖，应修复后发布新版本。

校验 job 只读；发布 job 才拥有 `contents: write`。不使用 `pull_request_target`，PR 不发布。Actions 依赖和官方校验器固定完整提交 ID。

```sh
git push origin main
# 等待 main 的两个平台检查成功，再发布该提交。
git tag v1.1.0
git push origin v1.1.0
```

需仓库启用 Actions 且有可用运行额度。普通 main/PR 运行只产生临时构建附件，不产生正式 Release。自动检查能确认格式和包完整，不能判断真实客户感受、证明不存在AI味或代替模型行为验证。涉及回复规则改动时，还应使用虚构客户记录检查事实、条件、称呼、联系限制及实际输出。
