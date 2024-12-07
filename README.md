## 环境配置

我们使用 Linux（或 WSL）环境与 `Python=3.9` 配置，推荐你使用 `conda` 创建一个新的虚拟环境：

```bash
conda create -n django_hw python=3.9 -y
conda activate django_hw
```

在此环境的基础之上，你可以运行下述命令安装依赖，注意请确保你的当前工作路径在克隆的仓库中：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

然后，你可以运行如下指令检查环境配置是否成功：

```bash
python3 manage.py runserver
```

这会在 `localhost:8000` 开启服务端进行监听网络请求。你可以打开浏览器，访问 http://localhost:8000/startup 来检查服务端是否正常启动。


