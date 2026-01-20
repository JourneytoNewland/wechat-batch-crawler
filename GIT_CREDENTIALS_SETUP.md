# Git 凭据配置说明

## ✅ 配置完成

Git 凭据已成功配置到系统环境变量,后续使用 Git 命令时无需再输入用户名、密码或 Token。

## 🔐 已配置的内容

### 1. 环境变量
- ✅ `GITHUB_TOKEN` 已添加到 `~/.zshrc`
- ✅ `GITHUB_TOKEN` 已添加到 `~/.bash_profile`

### 2. Git 全局配置
```bash
user.name=JourneytoNewland
user.email=13809047402@139.com
credential.helper=store --file ~/.git-credentials-file/github
```

### 3. 凭据存储
- 📁 位置: `~/.git-credentials-file/github`
- 🔐 内容: GitHub Token (加密存储)
- 🚀 自动使用: Git push 时自动读取

## 📝 使用方法

### 日常使用
```bash
# 直接使用 Git 命令,无需输入凭据
git add .
git commit -m "your message"
git push origin main  # ✅ 无需输入用户名密码!

# 推送标签
git tag v1.1
git push origin v1.1  # ✅ 无需输入凭据!
```

### 新终端会话
```bash
# 加载环境变量
source ~/.zshrc

# 或直接使用,新终端会自动加载
git push origin main
```

## 🔧 配置文件位置

| 文件 | 用途 |
|------|------|
| `~/.zshrc` | Zsh 环境变量配置 |
| `~/.bash_profile` | Bash 环境变量配置 |
| `~/.git-credentials-file/github` | Git 凭据存储 |
| `~/.gitconfig` | Git 全局配置 |

## 🔄 更新 Token

如果需要更新 GitHub Token:

### 方法 1: 编辑脚本重新运行
```bash
cd /Users/wangzheng/Downloads/playDemo/AntigravityDemo/wxmp_scrapy
# 编辑 init_git_credentials.sh 中的 GITHUB_TOKEN
vim init_git_credentials.sh
# 重新运行
./init_git_credentials.sh
```

### 方法 2: 直接编辑凭据文件
```bash
# 编辑凭据文件
vim ~/.git-credentials-file/github

# 格式: https://<username>:<token>@github.com
# 示例: https://JourneytoNewland:ghp_xxx@github.com
```

### 方法 3: 使用 Git 命令
```bash
# 清除旧凭据
git config --global --unset credential.helper

# 重新设置
git config --global credential.helper store
git push origin main
# 输入新的用户名和 Token
```

## 🔒 安全注意事项

1. **文件权限**
   - 凭据文件权限已设置为 600 (仅所有者可读写)
   - 请勿修改权限

2. **不要分享**
   - ❌ 不要分享 `~/.git-credentials-file/github`
   - ❌ 不要将此文件提交到 Git
   - ✅ 已在 `.gitignore` 中忽略

3. **定期更新**
   - 建议每 3-6 个月更新一次 Token
   - GitHub Token 可以设置过期时间

4. **撤销旧 Token**
   - 访问: https://github.com/settings/tokens
   - 删除不再使用的 Token

## 🧪 测试配置

### 测试 Git Push
```bash
cd /Users/wangzheng/Downloads/playDemo/AntigravityDemo/wxmp_scrapy

# 创建测试分支
git checkout -b test-credentials

# 修改文件
echo "test" > test.txt

# 提交并推送
git add test.txt
git commit -m "test: 测试凭据配置"
git push origin test-credentials

# 如果成功推送,无需输入密码,说明配置生效!

# 清理
git checkout main
git branch -D test-credentials
git push origin --delete test-credentials
```

## 📚 相关命令

### 查看当前配置
```bash
# 查看所有 Git 配置
git config --global --list

# 查看用户信息
git config --global user.name
git config --global user.email

# 查看凭据助手
git config --global credential.helper
```

### 查看环境变量
```bash
# 查看 GITHUB_TOKEN
echo $GITHUB_TOKEN

# 查看所有环境变量
env | grep GITHUB
```

### 清除凭据
```bash
# 清除 Git 凭据
rm ~/.git-credentials-file/github

# 清除环境变量 (从配置文件中手动删除)
vim ~/.zshrc      # 删除 GITHUB_TOKEN 行
vim ~/.bash_profile  # 删除 GITHUB_TOKEN 行
```

## 🆘 常见问题

### Q: Git push 还是需要输入密码?
A: 检查以下几点:
1. 确认已执行 `source ~/.zshrc`
2. 检查凭据文件是否存在: `ls -la ~/.git-credentials-file/github`
3. 查看 Git 配置: `git config --global credential.helper`

### Q: Token 失效了怎么办?
A: 按照上面的"更新 Token"方法重新配置

### Q: 多个 GitHub 账号如何配置?
A: 需要使用 SSH 密钥或配置不同的 credential helper

### Q: 如何撤销 Token?
A: 访问 https://github.com/settings/tokens,删除对应的 Token

## 📞 需要帮助?

- GitHub 官方文档: https://docs.github.com/en/authentication
- Git 凭据存储: https://git-scm.com/docs/git-credential-store

---

**配置日期**: 2026-01-20
**配置脚本**: `init_git_credentials.sh`
**状态**: ✅ 已配置并测试通过
