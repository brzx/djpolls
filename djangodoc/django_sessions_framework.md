## Django 的 sessions

> ### [How to use sessions](https://docs.djangoproject.com/en/2.1/topics/http/sessions/)

> 翻译官: Brian Zhu

Django为匿名会话提供全面支持。 会话框架允许您基于每个站点访问者存储和检索任意数据。 它在服务器端存储数据并抽象 cookies 的发送和接收。 Cookies 包含会话ID - 而不是数据本身(除非您使用基于cookie的后端 [cookie based backend](https://docs.djangoproject.com/en/2.1/topics/http/sessions/#cookie-session-backend) )。

### Enabling sessions

会话通过一些中间件 [middleware](https://docs.djangoproject.com/en/2.1/ref/middleware/) 实现。

要启用会话功能， 请执行以下操作：

- 编辑 MIDDLEWARE 设置并确保它包含 'django.contrib.sessions.middleware.SessionMiddleware'。 django-admin startproject 创建的默认 settings.py 已激活 SessionMiddleware。

如果您不想使用会话， 您也可以从 MIDDLEWARE 中删除 SessionMiddleware 行， 并从 INSTALLED_APPS 中删除 “django.contrib.sessions”。 它会为您节省一点开销。

-------------

### 配置会话引擎

默认情况下， Django将会话存储在您的数据库中(使用模型 django.contrib.sessions.models.Session)。 虽然这很方便， 但在某些设置中， 将会话数据存储在其他位置的速度更快， 因此可以将Django配置为在文件系统或缓存中存储会话数据。

#### 使用数据库支持的会话

如果要使用数据库支持的会话， 则需要将 “django.contrib.sessions” 添加到 INSTALLED_APPS 设置中。

配置安装后， 运行 manage.py migrate 以安装存储会话数据的单个数据库表。

-------------

#### 使用基于缓存的会话

为了获得更好的性能， 您可能希望使用基于缓存的会话后端。

要使用Django的缓存系统存储会话数据， 首先需要确保已配置缓存; 有关详细信息， 请参阅缓存 [cache documentation](https://docs.djangoproject.com/en/2.1/topics/cache/) 文档。

> 警告

> 如果您正在使用Memcached缓存后端， 则应该只使用基于缓存的会话。 本地内存缓存后端不会保留足够长的数据以作为一个好的选择， 并且直接使用文件或数据库会话而不是通过文件或数据库缓存后端发送所有内容会更快。 此外， 本地内存缓存后端不是多进程安全的， 因此可能不适合生产环境。

如果在 CACHES 中定义了多个缓存， Django将使用默认缓存。 要使用另一个缓存， 请将 SESSION_CACHE_ALIAS 设置为该缓存的名称。

配置缓存后， 您有两种方法可以在缓存中存储数据：

- 将 SESSION_ENGINE 设置为 “django.contrib.sessions.backends.cache” 以获取简单的缓存会话存储。 会话数据将直接存储在缓存中。 但是， 会话数据可能不是持久性的： 如果缓存填满或缓存服务器重新启动， 则缓存数据可能会被清除。

- 对于持久性缓存数据， 请将 SESSION_ENGINE 设置为 “django.contrib.sessions.backends.cached_db”。 这使用直写高速缓存 - 每次写入高速缓存也将写入数据库。 如果数据尚未存在于缓存中， 则会话只读使用数据库。

两个会话存储都非常快， 但简单的缓存更快， 因为它忽略了持久性。 在大多数情况下， cached_db 后端将足够快， 但如果您需要最后一点性能， 并且愿意让会话数据不时被清除， 则 cache 后端适合您。

-------------

#### 使用基于文件的会话

要使用基于文件的会话， 请将 SESSION_ENGINE 设置为 “django.contrib.sessions.backends.file”。

您可能还想设置 SESSION_FILE_PATH 设置(默认为 tempfile.gettempdir() 输出， 很可能是 /tmp)来控制Django存储会话文件的位置。 请务必检查您的Web服务器是否具有读取和写入此位置的权限。

-------------

#### 使用基于 cookie 的会话

要使用基于cookie的会话， 请将 SESSION_ENGINE 设置为 “django.contrib.sessions.backends.signed_cookies”。 会话数据将使用Django的加密签名 [cryptographic signing](https://docs.djangoproject.com/en/2.1/topics/signing/) 工具和 [SECRET_KEY](https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-SECRET_KEY) 设置进行存储。

> 注意

> 建议将 SESSION_COOKIE_HTTPONLY 设置保留为 True 以防止从JavaScript访问存储的数据。

> 警告

> **如果 SECRET_KEY 没有保密并且您正在使用 [PickleSerializer](https://docs.djangoproject.com/en/2.1/topics/http/sessions/#django.contrib.sessions.serializers.PickleSerializer) ， 则可能导致任意远程代码执行。**

> 拥有 SECRET_KEY 的攻击者不仅可以生成您的站点将信任的伪造会话数据， 还可以远程执行任意代码， 因为数据是使用pickle序列化的。

> 如果您使用基于cookie的会话，请特别注意您的密钥始终保密， 对于任何可远程访问的系统。

> **会话数据已签名但未加密**

> 使用cookie后端时， 客户端可以读取会话数据。

> MAC(消息认证码)用于保护数据免受客户端的更改， 以便会话数据在被篡改时无效。 如果存储cookie的客户端(例如用户的浏览器)无法存储所有会话cookie并丢弃数据， 则会发生相同的失效。 即使Django压缩数据， 它仍然完全有可能超过每个cookie 4096字节 [common limit of 4096 bytes](https://tools.ietf.org/html/rfc2965#section-5.3) 的公共限制。

> **不保证保鲜(No freshness guarantee)**

> 还要注意， 尽管 MAC 可以保证数据的真实性(它是由您的站点生成的， 而不是其他人生成的)， 以及数据的完整性(它都存在且正确)， 但它无法保证新鲜度， 即你被送回客户的最后一件事。 这意味着对于会话数据的某些用途， cookie后端可能会让您遭受重播攻击 [replay attacks](https://en.wikipedia.org/wiki/Replay_attack) 。 与保存每个会话的服务器端记录并在用户注销时使其无效的其他会话后端不同， 当用户注销时， 基于cookie的会话不会失效。 因此， 如果攻击者窃取用户的cookie， 即使用户退出， 他们也可以使用该cookie以该用户身份登录。 如果Cookie超过您的 [SESSION_COOKIE_AGE](https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-SESSION_COOKIE_AGE) ， 则只会将其检测为“陈旧” (stale)。

> **性能**

> 最后， Cookie的大小会对您网站的速度产生影响 [speed of your site](https://yuiblog.com/blog/2007/03/01/performance-research-part-3/) 。

-------------

#### 在视图中使用会话








































































