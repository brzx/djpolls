## Django 的 sessions

> ### [How to use sessions](https://docs.djangoproject.com/en/2.1/topics/http/sessions/)

> 翻译官: Brian Zhu

Django为匿名会话提供全面支持。 会话框架允许您基于每个站点访问者存储和检索任意数据。 它在服务器端存储数据并抽象 cookies 的发送和接收。 Cookies 包含会话ID - 而不是数据本身(除非您使用基于cookie的后端 [cookie based backend](https://docs.djangoproject.com/en/2.1/topics/http/sessions/#cookie-session-backend) )。

### 启用会话

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

当 SessionMiddleware 被激活时， 每个 HttpRequest 对象 - 任何Django视图函数的第一个参数 - 都含有 session 属性， 这是一个类似字典的对象。

您可以在视图中的任何位置读取它， 或者写入 request.session。 您也可以多次编辑它。

**class backends.base.SessionBase**

这是所有会话对象的基类。 它具有以下标准字典方法：

**__getitem__(key)**

  例如： fav_color = request.session['fav_color']

**__setitem__(key, value)**

  例如： request.session['fav_color'] = 'blue'

**__delitem__(key)**

  例如： del request.session['fav_color']. 如果给定的键不在会话中， 则会引发 KeyError。

**__contains__(key)**

  例如： 'fav_color' in request.session

**get(key, default=None)**

  例如： fav_color = request.session.get('fav_color', 'red')

**pop(key, default=__not_given)**

  例如： fav_color = request.session.pop('fav_color', 'blue')

**keys()**

**items()**

**setdefault()**

**clear()**

它还有以下方法：

**flush()**

从会话中删除当前会话数据并删除会话cookie。 如果要确保无法从用户的浏览器再次访问先前的会话数据(例如， django.contrib.auth.logout() 函数调用它)， 则使用此方法。

**set_test_cookie()**

设置测试cookie以确定用户的浏览器是否支持cookie。 由于Cookies的工作方式， 在用户的下一页请求之前， 您将无法对此进行测试。 有关详细信息， 请参阅下面的 [Setting test cookies](https://docs.djangoproject.com/en/2.1/topics/http/sessions/#setting-test-cookies) 。

**test_cookie_worked()**

返回 True 或 False， 具体取决于用户的浏览器是否接受测试cookie。 由于Cookies的工作方式， 您必须在之前单独的页面请求上调用 set_test_cookie()。 有关详细信息， 请参阅下面的 [Setting test cookies](https://docs.djangoproject.com/en/2.1/topics/http/sessions/#setting-test-cookies) 。

**delete_test_cookie()**

删除测试cookie。 用它来清理自己。

**set_expiry(value)**

设置会话的过期时间。 您可以传递许多不同的值：

- 如果 value 是一个整数， 则会话将在经过多秒不活动后过期。 例如， 调用 request.session.set_expiry(300) 会使会话在5分钟后过期。

- 如果 value 是 datetime 或 timedelta 对象， 则会话将在该特定日期/时间过期。 请注意， 如果您使用的是 PickleSerializer， 则 datetime 和 timedelta 值只能序列化。

- 如果 value 为 0， 则用户的会话cookie将在用户的Web浏览器关闭时过期。

- 如果 value 为 None， 则会话将恢复为使用全局会话到期策略。

读取会话不被视为过期目的的活动。 会话过期时间是从上次修改会话时计算出来的。

**get_expiry_age()**

返回此会话过期之前的秒数。 对于没有自定义过期的会话(或设置为在浏览器关闭时过期的会话)， 这将等于 SESSION_COOKIE_AGE。

此函数接受与 get_expiry_age() 相同的关键字参数。

**get_expire_at_browser_close()**

返回 True 或 False， 具体取决于用户的Web浏览器关闭时用户的会话cookie是否过期。

**clear_expired()**

从会话存储中删除过期的会话。 这个类方法由 [clearsessions](https://docs.djangoproject.com/en/2.1/ref/django-admin/#django-admin-clearsessions) 调用。

**cycle_key()**

在保留当前会话数据的同时创建新的会话键。 django.contrib.auth.login() 调用此方法来减轻会话固定(mitigate against session fixation) 。

#### 会话序列化

默认情况下， Django使用JSON序列化会话数据。 您可以使用 [SESSION_SERIALIZER](https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-SESSION_SERIALIZER) 设置来自定义会话序列化格式。 即使您编写自己的序列化 [Write your own serializer](https://docs.djangoproject.com/en/2.1/topics/http/sessions/#custom-serializers) 程序中描述了警告， 我们强烈建议您坚持使用JSON序列化， 尤其是在使用cookie后端时。

例如， 如果您使用 [pickle](https://docs.python.org/3/library/pickle.html#module-pickle) 来序列化会话数据， 下面是一个攻击情境。 如果您正在使用 [signed cookie session backend](https://docs.djangoproject.com/en/2.1/topics/http/sessions/#cookie-session-backend) 并且攻击者知道你的 SECRET_KEY (Django中没有可能导致其泄漏的固有漏洞)， 则攻击者可以在其会话中插入一个字符串， 当执行反序列化时， 可以在服务器上执行任意代码。 这样做的技术很简单， 并且可以在互联网上轻松获得。 虽然cookie会话存储会对cookie存储的数据进行签名以防止篡改， 但 SECRET_KEY 泄漏会立即升级为远程执行代码漏洞。

##### 捆绑序列化器 (Bundled serializers)

**class serializers.JSONSerializer**

来自 django.core.signing 的JSON序列化程序的包装器。 只能序列化基本数据类型。

此外， 由于JSON仅支持字符串键， 请注意在 request.session 中使用非字符串键将无法按预期工作：

    >>> # initial assignment
    >>> request.session[0] = 'bar'
    >>> # subsequent requests following serialization & deserialization
    >>> # of session data
    >>> request.session[0]  # KeyError
    >>> request.session['0']
    'bar'

同样， 无法以JSON编码的数据， 例如非UTF8字节(non-UTF8 bytes) ， 如 '\ xd9' (引发UnicodeDecodeError)， 也无法存储。

有关JSON序列化限制的更多详细信息， 请参阅编写您自己的序列化程序 [Write your own serializer](https://docs.djangoproject.com/en/2.1/topics/http/sessions/#custom-serializers) 部分。 

**class serializers.PickleSerializer**

支持任意Python对象， 但如上所述， 如果攻击者知道 SECRET_KEY， 则可能导致远程代码执行漏洞。

-------------

##### 编写自己的序列化程序

请注意， 与 PickleSerializer 不同， JSONSerializer 无法处理任意Python数据类型。 通常情况下， 需要在便利性和安全性之间进行权衡。 如果您希望在JSON支持的会话中存储更多高级数据类型(包括 datetime 和Decimal )， 则需要编写自定义序列化程序(或者将这些值转换为JSON可序列化对象， 然后将它们存储在 request.session 中)。 虽然序列化这些值非常简单( DjangoJSONEncoder 可能会有所帮助)， 但编写一个能够可靠地恢复您放入的相同内容的解码器更加脆弱。 例如， 您冒着返回日期时间的风险，该 datetime 实际上是恰好是为 datetimes 选择的相同格式的字符串。

您的序列化程序类必须实现两个方法， dumps(self, obj) 和 loads(self, data)， 分别序列化和反序列化会话数据字典。

-------------

### 会话对象指南

- 在 request.session 上使用普通的Python字符串作为字典键。 这更像是一种惯例而非硬性规则。

- 以下划线开头的会话字典键被保留， 并供Django内部使用。

- 不要使用新对象覆盖request.session， 也不要访问或设置其属性。 像Python字典一样使用它。

-------------

#### 例子

下面这个简单的视图在用户发布评论后将 has_commented 变量设置为True。 它不允许用户多次发表评论：

    def post_comment(request, new_comment):
        if request.session.get('has_commented', False):
            return HttpResponse("You've already commented.")
        c = comments.Comment(comment=new_comment)
        c.save()
        request.session['has_commented'] = True
        return HttpResponse('Thanks for your comment!')


下面这个简单的视图记录了网站的“成员”：

    def login(request):
        m = Member.objects.get(username=request.POST['username'])
        if m.password == request.POST['password']:
            request.session['member_id'] = m.id
            return HttpResponse("You're logged in.")
        else:
            return HttpResponse("Your username and password didn't match.")

...根据上面的login()， 下面这个视图记录了网站成员登出：

    def logout(request):
        try:
            del request.session['member_id']
        except KeyError:
            pass
        return HttpResponse("You're logged out.")

标准的 django.contrib.auth.logout() 函数实际上比这更多， 以防止无意中的数据泄漏。 它调用 request.session 的 flush() 方法。 我们使用此示例演示如何使用会话对象， 而不是完整的 logout() 实现。

-------------

#### 设置测试 cookies











